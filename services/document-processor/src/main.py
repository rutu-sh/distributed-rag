# standard libraries
import time
import os
import json
# installed libraries

# custom imports
from controller import dp_controller
from common import common, config

_logger = common.get_logger(
    __name__, 
    bind_params=config.BIND_PARAMS, 
    handlers=[
        common.StreamHandler, 
        # common.FileHandler
    ]
)


def load_unfinished_job(job_path: str) -> dict:
    """Check for and load unfinished job from the given path."""

    try:
        os.makedirs(f"/task/{config.POD_NAME}")
        if not os.path.exists(job_path):
            return None
    except Exception as e:
        pass

    try:
        job_file = open(job_path, "r")
        job = json.load(job_file)
        job_file.close()
        _logger.info("found an unfinished job", job=job)
        return job
    except Exception as e:
        pass
    
    return None


def main():
    _logger.info("starting...")
    unifinished_job = load_unfinished_job(config.JOB_PATH)

    while True:
        try:
            job, status = dp_controller.process(unifinished_job)
            unifinished_job = None
            if status == "success":
                _logger.info("job processed")
                continue
            if job != None:
                _logger.info("job process error, continuing with next job")
            time.sleep(1)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main() 