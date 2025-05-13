import os

# MILVUS CONFIG

SERVICE_NAME = os.getenv("SERVICE_NAME", "document-processor-server")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = os.getenv("PORT", "7070")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_TIME_FORMAT = f"%Y-%m-%d %H:%M:%S"
DATETIME_FORMAT = f"%Y-%m-%d %H:%M:%S"

EMBED_URL = "http://emb-svc.emb.svc.cluster.local:11434/api/embed"
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-minilm:22m")

MILVUS_ENDPOINT = os.getenv("MILVUS_ENDPOINT","http://localhost:8080/vectors/add")

ZILLIZ_URL = os.getenv("ZILLIZ_URL", "https://in03-4346c77e0fa7145.serverless.gcp-us-west1.cloud.zilliz.com")
ZILLIZ_TOKEN = os.getenv("ZILLIZ_TOKEN", "zil_token")
ZILLIZ_INSERT_ENDPOINT = "/v2/vectordb/entities/insert"
ZILLIZ_COLLECTION_NAME = "rag_collection"

MINIO_URL = os.getenv("MINIO_API_ENDPOINT", "minio-api.rutu-sh.com")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "CnM6eavCYrzreGlYpTUF")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "89BqhWExFKPnDHMbI8ezYS1NJDlsvsfjItdIOJNM")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "doc-proc")
MINIO_PREFIX = os.getenv("MINO_PREFIX", "/files/")

REDIS_HOST = os.getenv("REDIS_HOST","localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD","password")
REDIS_QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME", "doc_proc_queue")

SPLITTER_PARAM_LINE = "line"
SPLITTER_PARAM_PAR = "paragraph"

POD_NAME = os.getenv("POD_NAME", "default")
JOB_PATH = os.getenv("JOB_PATH", f"/task/{POD_NAME}/job.json")

# MILVUS_COLLECTION_NAME = "rag_collection"
# MILVUS_DIMENSION = 384

# LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")
# DB_USER = os.getenv("MYSQL_USER")
# DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
# DB_HOST = os.getenv("DB_HOST")
# DB_NAME = os.getenv("MYSQL_DATABASE")
# DB_TABLE_USERS = os.getenv("DB_TABLE_USERS")

BIND_PARAMS = {
    "service_name": SERVICE_NAME,
}
