# standard libraries
import requests
import json

# installed libraries

# custom libraries
from common import common, config
from controller import utils


_logger = common.get_logger("controller.document-processor")


def write_new_job(job: dict):
    try:
        job_file = open(config.JOB_PATH, "w")
        json.dump(job, job_file)
        job_file.close()
        _logger.info("wrote new job to file", job=job)
    except Exception as e:
        _logger.error("failed to write new job", error=e)
        return 


def remove_job_task():
    try:
        open(config.JOB_PATH, "w").close()
        _logger.info("cleared job file")
    except Exception as e:
        _logger.error(f"Failed to clear job file: {e}")


def process(unfinished_job: dict = None):
    
    if not unfinished_job:
        job = utils.dequeue_job()
        if job == None:
            # no job, continue
            return None, "failure"
        jobJSON = json.loads(job)
        write_new_job(jobJSON)
    else:
        jobJSON = unfinished_job
    
    _logger.info("processing job...", job=jobJSON)
 
    obj_name = ""
    chunk_strat = ""

    try:
        obj_name = jobJSON["objectName"]
        chunk_strat = jobJSON["chunk"]
    except:
        _logger.info("job JSON incorrect")
        return None, "failure"
    
    _logger.info(f"obj name: {obj_name}, chunk_strat: {chunk_strat}")

    # get bytes
    pdf_bytes = utils.get_file_from_minio(obj_name)

    # get embdeddings list from pdf - tuples(text, vector)
    vector_tuples = utils.embed_pdf(pdf_bytes, chunk_strat)

    _logger.info(f"number of vectors chunked: {len(vector_tuples)}")
    _logger.info(f"length of a vector: {len(vector_tuples[0][1])}")
    # print("a chunk: ", vector_tuples[0][0])

    _logger.info("uploading to vector db")
    templist = []

    for v in vector_tuples:
        # id = random.randint(0, 2000)
        data = {
            "text": v[0],
            "vector": v[1]
        }
        templist.append(data)

    headers = {
        'Authorization': "Bearer "+config.ZILLIZ_TOKEN,
        'Accept': "application/json",
        'Content-Type': "application/json"
    }

    tl = []
    for i in range(0, len(templist), 100):
        tl.append(templist[i:i+100])
    
    for l in tl: 
        payload = {
            "collectionName": config.ZILLIZ_COLLECTION_NAME,
            "data": l
        }

        resp = requests.post(url=config.ZILLIZ_URL + config.ZILLIZ_INSERT_ENDPOINT, json=payload, headers=headers)
        _logger.info(f"ZILLIZ UPLOAD STATUS CODE: {resp.status_code}")
        # print(resp.json())

    if resp.status_code == 200:
        remove_job_task()
        return None, "success"
    return job, "failure"
    