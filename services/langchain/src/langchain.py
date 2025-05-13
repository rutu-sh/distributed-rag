# standard
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
import logging
import asyncio

# third-party
import httpx
from langfuse import Langfuse
from langchain.vectorstores import Zilliz
from langchain.embeddings import OllamaEmbeddings
from langchain.chat_models import ChatOllama
from langchain.chains import RetrievalQA
from langchain.schema.runnable import RunnableConfig
from langchain.callbacks.tracers.langfuse import LangfuseTracer
from sse_starlette.sse import EventSourceResponse

# project
from common import common, config

router = APIRouter(prefix="/api", tags=["langchain"])
_logger = common.get_logger("controller.langchain")


langfuse = Langfuse(
    secret_key=config.LANGFUSE_SECRET,
    public_key=config.LANGFUSE_PUBLIC,
    host=config.LANGFUSE_HOST
)


def get_langchain_chain(user_uuid=None, user_email=None):
    tracer = LangfuseTracer()
    config_tracer = RunnableConfig(
        callbacks=[tracer],
        metadata={"user_id": user_uuid, "user_email": user_email}
    )

    embeddings = OllamaEmbeddings(model=config.EMBED_MODEL)
    vectorstore = Zilliz.from_existing_index(
        embedding=embeddings,
        collection_name=config.ZILLIZ_COLLECTION_NAME,
        connection_args={
            "uri": config.ZILLIZ_URL,
            "token": config.ZILLIZ_TOKEN,
        }
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": config.K_CLOSEST})
    llm = ChatOllama(
        model=config.GEN_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=0,
        streaming=True
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=False
    )

    return chain, config_tracer


async def stream_chain(chain, query, config):
    queue = asyncio.Queue()

    def on_token(token: str):
        queue.put_nowait(token)

    async def token_generator():
        while True:
            token = await queue.get()
            if token is None:
                break
            yield f"data: {token}\n\n"

    config.callbacks[0].on_llm_new_token = on_token

    async def run_chain():
        try:
            await asyncio.to_thread(chain.invoke, {"query": query}, config=config)
        finally:
            await queue.put(None)

    asyncio.create_task(run_chain())
    return EventSourceResponse(token_generator())


# ---------- /generate (RAG with streaming) ----------

@router.post("/generate")
async def generate(request: Request):
    try:
        body = await request.json()
        prompt = body["prompt"]
        user_email = request.headers.get("email")
        user_uuid = request.headers.get("uuid")

        chain, config_tracer = get_langchain_chain(user_uuid, user_email)
        return await stream_chain(chain, prompt, config_tracer)

    except Exception as e:
        _logger.error(f"/generate error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        prompt = body["prompt"]
        user_email = request.headers.get("email")
        user_uuid = request.headers.get("uuid")

        chain, config_tracer = get_langchain_chain(user_uuid, user_email)
        return await stream_chain(chain, prompt, config_tracer)

    except Exception as e:
        _logger.error(f"/chat error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/tags")
async def list_models():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{config.OLLAMA_BASE_URL}/api/tags")
        return JSONResponse(content=res.json(), status_code=res.status_code)

@router.post("/pull")
async def pull_model(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{config.OLLAMA_BASE_URL}/api/pull", content=body)
        return JSONResponse(content=res.json(), status_code=res.status_code)

@router.delete("/delete")
async def delete_model(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        res = await client.delete(f"{config.OLLAMA_BASE_URL}/api/delete", content=body)
        return JSONResponse(content=res.json(), status_code=res.status_code)

@router.get("/show")
async def show_model(name: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{config.OLLAMA_BASE_URL}/api/show", params={"name": name})
        return JSONResponse(content=res.json(), status_code=res.status_code)
