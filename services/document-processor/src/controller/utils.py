import fitz
from typing import List
import requests
from common import config, common
from minio import Minio
import redis
import re

_logger = common.get_logger("controller.utils")

minio_client = Minio(endpoint=config.MINIO_URL, access_key=config.MINIO_ACCESS_KEY, secret_key=config.MINIO_SECRET_KEY)
redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD)

def split_string_multiple_delimiters(text, delimiters):
    pattern = '|'.join(map(re.escape, delimiters))
    return re.split(pattern, text)


def get_chunks_from_bytes(pdf_bytes, chunk_strat: str) -> List[str]:
    text = ""
    with fitz.open(stream=pdf_bytes, filename="pdf") as doc:
        for page in doc:
            text += page.get_text()

    res = []
    if chunk_strat == config.SPLITTER_PARAM_LINE:
        _logger.info("using line splitter")
        res = split_string_multiple_delimiters(text, [". ", ".\n", "\n\n"])
    else:
        _logger.info("using par splitter")
        res = split_string_multiple_delimiters(text, [".\n", "\n\n"])
    _logger.info(f"number of chunks: {len(res)}")
    return res

# add chunking strategy and actual embedding fn here
def embed_pdf(pdf_bytes, chunk_strat: str) :
    url = config.EMBED_URL
    headers = {
        "Content-Type": "application/json"
    }
    chunks = get_chunks_from_bytes(pdf_bytes, chunk_strat)

    _logger.info(f"embedding {len(chunks)} chunks ...")

    emb_list = []
    for x in range(0, len(chunks), 500):
        data = {
            "model": config.EMBED_MODEL,
            "input": chunks[x:x+500]
        }
        response = requests.post(url, headers=headers, json=data)
        _logger.info(f"embedder code: {response.status_code}")
        data = response.json()
        embeddings = data["embeddings"]
        emb_list.extend(list(zip(chunks, embeddings)))

    _logger.info("done embedding")
    return emb_list

# pop from the right side of the queue
'''
example job JSON
{
    "chunk": "line",
    "bucket": "bucket_name",
    "objectName": "uuid"
}
'''
def dequeue_job():
    job = redis_client.rpop(name=config.REDIS_QUEUE_NAME)
    return job

def get_file_from_minio(id: str):
    obj = minio_client.get_object(bucket_name=config.MINIO_BUCKET_NAME, object_name=id)
    return obj.read()

def requeue_job(job):
    redis_client.lpush(name=config.REDIS_QUEUE_NAME, values=job.read())