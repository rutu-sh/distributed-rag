import os


SERVICE_NAME = os.getenv("SERVICE_NAME", "langchain")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = os.getenv("PORT", "8000")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_TIME_FORMAT = f"%Y-%m-%d %H:%M:%S"
DATETIME_FORMAT = f"%Y-%m-%d %H:%M:%S"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("MYSQL_DATABASE")
DB_TABLE_USERS = os.getenv("DB_TABLE_USERS")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-minilm:22m")
MILVUS_URL= os.getenv("MILVUS_URL")
EMBED_URL = os.getenv("EMBED_URL")

LANGFUSE_HOST = os.getenv("LANGFUSE_HOST")

K_CLOSEST = int(os.getenv("K_CLOSEST", 2))

ZILLIZ_URL = os.getenv("ZILLIZ_URL", "https://in03-4346c77e0fa7145.serverless.gcp-us-west1.cloud.zilliz.com")
ZILLIZ_TOKEN = os.getenv("ZILLIZ_TOKEN", "zil_token")
ZILLIZ_QUERY_ENDPOINT = "v2/vectordb/entities/search"
ZILLIZ_COLLECTION_NAME = "rag_collection"

LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-b95a819a-8342-4319-92b9-026a451940d8")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-9f285103-ba98-445f-aab0-295fbc29961c")


BIND_PARAMS = {
    "service_name": SERVICE_NAME,
}
