# standard libraries
import requests
import json
import time 
from typing import List, Callable
from functools import partial

# installed libraries
from starlette.responses import JSONResponse
from fastapi.routing import APIRouter

# custom libraries
from common import common, config


from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import asyncio


from langfuse import Langfuse

_logger = common.get_logger("controller.langchain")
router = APIRouter(prefix="/api", tags=["langchain"])

 
langfuse = Langfuse(
    secret_key=config.LANGFUSE_SECRET_KEY,
    public_key=config.LANGFUSE_PUBLIC_KEY,
    host=config.LANGFUSE_HOST
)


def retry_with_exp_backoff(request_func: Callable, expected_status_codes: list) -> requests.Response:
    wait_time = 2
    while True:
        response = request_func()
        if response.status_code not in expected_status_codes:
            _logger.info("received unexpected status code, retrying with backoff", status_code=response.status_code, backoff_duration=wait_time)
            time.sleep(wait_time)
            wait_time = wait_time * 2
            if wait_time > 600:
                response.raise_for_status() 
        else: 
            _logger.info("received expected response")
            return response




async def stream_response(response: httpx.Response, trace, generation):
    full_output = ""

    async for chunk in response.aiter_bytes():
        decoded = chunk.decode("utf-8")
        for line in decoded.strip().split("\n"):
            if not line.strip():
                continue
            data = json.loads(line)
            text_piece = data.get("response", "")
            full_output += text_piece
            yield line.encode("utf-8") + b"\n"  # re-yield raw NDJSON line

    generation.end(output=full_output)
    trace.update(output=full_output)


def get_embedded_text(text):
    url = config.EMBED_URL
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": config.EMBED_MODEL,
        "input": text
    }

    req_func = partial(requests.post, url=url, headers=headers, json=data)
    expected_status_codes = [200]

    response = retry_with_exp_backoff(req_func, expected_status_codes)
    return response.json()["embeddings"][0]


def get_k_similar(vector, k): 
    url = f"{config.ZILLIZ_URL}/{config.ZILLIZ_QUERY_ENDPOINT}"
    data = {
        "collectionName": config.ZILLIZ_COLLECTION_NAME,
        "data": [vector],
        "limit": k,
        "outputFields": [
            "text"
        ]
    }
    headers = {
        'Authorization': "Bearer "+config.ZILLIZ_TOKEN,
        'Accept': "application/json",
        'Content-Type': "application/json"
    }

    req_func = partial(requests.post, url=url, headers=headers, json=data)
    expected_status_codes = [200]

    response = retry_with_exp_backoff(req_func, expected_status_codes)
    return response.json()["data"]
    
    
def augment_prompt(prompt: str, similar_docs: List[dict]) -> str:
    context_complete_prompt = ""

    context_complete_prompt = context_complete_prompt + "using the following as the context: <context-start>\n"
    for doc in similar_docs:
        context_complete_prompt = context_complete_prompt + doc["text"] + "\n"

    context_complete_prompt = context_complete_prompt + "<context-end>\n"
    context_complete_prompt = context_complete_prompt + "answer the following question\n"
    context_complete_prompt = context_complete_prompt + prompt
    return context_complete_prompt



async def call_ollama_generate(prompt_data: dict, url: str):
    headers = {"Content-Type": "application/json"}
    try:
        # Using a very long timeout, effectively disabling it
        # This allows Ollama to take as long as needed to start streaming
        async with httpx.AsyncClient(timeout=None) as client:
            return await client.post(
                url, 
                content=json.dumps(prompt_data), 
                headers=headers
            )
    except Exception as e:
        _logger.error(f"Error calling Ollama: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error calling Ollama: {str(e)}"}
        )


async def call_ollama_chat(prompt_data: dict, url: str):
    headers = {"Content-Type": "application/json"}
    try:
        # Using no timeout to allow Ollama time to process and begin streaming
        async with httpx.AsyncClient(timeout=None) as client:
            return await client.post(
                url, 
                content=json.dumps(prompt_data), 
                headers=headers
            )
    except Exception as e:
        _logger.error(f"Error calling Ollama: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error calling Ollama: {str(e)}"}
        )


# POST /api/generate
@router.post("/generate")
async def generate(request: Request):
    trace = langfuse.trace(name="rag-gen-flow")

    try:
        body = await request.json()
        headers = {"Content-Type": "application/json"}

        user_email = request.headers.get("email")
        user_uuid = request.headers.get("uuid")
        prompt = body["prompt"]

        trace.update(input=prompt, user_id=user_uuid, user_email=user_email)
        
        retrieval = trace.span(name="retrieval", input=prompt)
        
        embedding = retrieval.span(name="embedding", input=prompt)
        vector = get_embedded_text(prompt)
        embedding.end(output=vector)

        vector_db_query = retrieval.span(name="vector-query", input=vector, k=config.K_CLOSEST)
        k_similar = get_k_similar(vector, config.K_CLOSEST)
        vector_db_query.end(output=k_similar)

        retrieval.end(output=k_similar)

        augment = trace.span(name="augment", input=prompt)
        prompt = augment_prompt(prompt, k_similar)
        augment.end(output=prompt)
        body["prompt"] = prompt

        generation = trace.span(name="generation", input=prompt)

        # Call Ollama without any timeout - wait as long as needed
        ollama_response = await call_ollama_generate(body, f"{config.OLLAMA_BASE_URL}/api/generate")
        
        # Check if the response is a JSONResponse (error occurred)
        if isinstance(ollama_response, JSONResponse):
            generation.end(error=ollama_response.body.decode())
            trace.end(error=ollama_response.body.decode())
            return ollama_response
            
        if ollama_response.headers.get("content-type") == "application/x-ndjson":
            return StreamingResponse(
                stream_response(ollama_response, trace, generation), 
                media_type="application/x-ndjson"
            )
        else:
            response_json = ollama_response.json()
            generation.end(output=response_json)
            trace.end(output=response_json)
            return JSONResponse(
                content=response_json, 
                status_code=ollama_response.status_code
            )
    
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        _logger.error(error_msg)
        
        # End any outstanding spans
        if 'generation' in locals():
            generation.end(error=error_msg)
        if 'trace' in locals():
            trace.end(error=error_msg)
            
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )


# POST /api/chat
@router.post("/chat")
async def chat(request: Request):
    trace = langfuse.trace(name="rag-gen-flow")

    try:
        body = await request.json()
        headers = {"Content-Type": "application/json"}

        user_email = request.headers.get("email")
        user_uuid = request.headers.get("uuid")
        prompt = body["prompt"]

        trace.update(input=prompt, user_id=user_uuid, user_email=user_email)
        
        retrieval = trace.span(name="retrieval", input=prompt)
        
        embedding = retrieval.span(name="embedding", input=prompt)
        vector = get_embedded_text(prompt)
        embedding.end(output=vector)

        vector_db_query = retrieval.span(name="vector-query", input=vector, k=config.K_CLOSEST)
        k_similar = get_k_similar(vector, config.K_CLOSEST)
        vector_db_query.end(output=k_similar)

        retrieval.end(output=k_similar)

        augment = trace.span(name="augment", input=prompt)
        prompt = augment_prompt(prompt, k_similar)
        augment.end(output=prompt)
        body["prompt"] = prompt

        generation = trace.span(name="generation", input=prompt)

        # Call Ollama without any timeout - wait as long as needed
        ollama_response = await call_ollama_chat(body, f"{config.OLLAMA_BASE_URL}/api/chat")
        
        # Check if the response is a JSONResponse (error occurred)
        if isinstance(ollama_response, JSONResponse):
            generation.end(error=ollama_response.body.decode())
            trace.end(error=ollama_response.body.decode())
            return ollama_response
            
        if ollama_response.headers.get("content-type") == "application/x-ndjson":
            return StreamingResponse(
                stream_response(ollama_response, trace, generation), 
                media_type="application/x-ndjson"
            )
        else:
            response_json = ollama_response.json()
            generation.end(output=response_json)
            trace.end(output=response_json)
            return JSONResponse(
                content=response_json, 
                status_code=ollama_response.status_code
            )
    
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        _logger.error(error_msg)
        
        # End any outstanding spans
        if 'generation' in locals():
            generation.end(error=error_msg)
        if 'trace' in locals():
            trace.end(error=error_msg)
            
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

# GET /api/tags
@router.get("/tags")
async def list_models():
    async with httpx.AsyncClient() as client:
        ollama_response = await client.get(f"{config.OLLAMA_BASE_URL}/api/tags")
        return JSONResponse(content=ollama_response.json(), status_code=ollama_response.status_code)


# POST /api/pull
@router.post("/pull")
async def pull_model(request: Request):
    body = await request.body()
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        ollama_response = await client.post(f"{config.OLLAMA_BASE_URL}/api/pull", content=body, headers=headers)
        return JSONResponse(content=ollama_response.json(), status_code=ollama_response.status_code)


# DELETE /api/delete
@router.delete("/delete")
async def delete_model(request: Request):
    body = await request.body()
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        ollama_response = await client.delete(f"{config.OLLAMA_BASE_URL}/api/delete", content=body, headers=headers)
        return JSONResponse(content=ollama_response.json(), status_code=ollama_response.status_code)


# GET /api/show
@router.get("/show")
async def show_model(name: str):
    async with httpx.AsyncClient() as client:
        ollama_response = await client.get(f"{config.OLLAMA_BASE_URL}/api/show", params={"name": name})
        return JSONResponse(content=ollama_response.json(), status_code=ollama_response.status_code)
    
    