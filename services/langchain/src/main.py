# standard libraries


# installed libraries
import uvicorn
from fastapi import FastAPI

# custom imports
from controller import health_check_controller, langchain_controller
from common import common, config

_logger = common.get_logger(
    __name__, 
    bind_params=config.BIND_PARAMS, 
    handlers=[
        common.StreamHandler, 
        # common.FileHandler
    ]
)

from langfuse import Langfuse

langfuse = Langfuse(
  secret_key="sk-lf-dade317b-1737-4983-b8c2-efa1b53579f7",
  public_key="pk-lf-6c758b89-339c-494f-a556-d1b813589f3c",
  host=config.LANGFUSE_HOST
)


def main():
    app = FastAPI()
    app.include_router(langchain_controller.router)
    app.include_router(health_check_controller.router)
    _logger.info("Starting the server")
    uvicorn.run(app, host=config.HOST, port=int(config.PORT))


if __name__ == '__main__':
    main() 