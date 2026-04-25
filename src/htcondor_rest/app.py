import os
from pathlib import Path
from typing import Annotated, List
import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
from .models import CondorSubmit, CondorJob, CondorSubmitResults

import htcondor2 as htcondor
from classad2 import ClassAd

app = FastAPI()
security = HTTPBearer()

auth_db = ["password"]
if os.environ.get("PASSWORDFILE") is not None:
    pass_file_path = Path(os.environ.get("PASSWORDFILE")).resolve().absolute()
    auth = pass_file_path.read_text().split("\n")
    auth_db = [a.rstrip("/n") for a in auth]
    logger.info(f"Keys in auth database {len(auth_db)}")
else:
    logger.warning("Using default AUTH")


@app.get("/")
def read_root():
    logger.info("Checking Health")
    return {"status": True}


@app.get("/condor_q")
def jobs(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> List[CondorJob]:
    if token.credentials not in auth_db:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("Getting condor_q")
    schedd = htcondor.Schedd()
    jobs = []
    for q in schedd.query():
        try:
            job = CondorJob(**json.loads(q.formatJson()))
            jobs.append(job)
        except Exception as exp:
            logger.exception(f"Could not convert job data {exp}")
            logger.error(f"Job data looks like: {q}")

    logger.info(f"Found {len(jobs)} jobs")
    return jobs


@app.get("/condor_q/{job_id}")
def job(
    job_id: int,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> CondorJob:
    if token.credentials not in auth_db:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info(f"Getting condor_q for {job_id}")
    schedd = htcondor.Schedd()
    try:
        q: ClassAd = schedd.query(constraint=f"ClusterId=={job_id}")
        if len(q) == 0:
            return HTTPException(
                status_code=404, detail=f"Job id {job_id} not found in queue"
            )
        logger.debug(f"{q}")
        job = CondorJob(**json.loads(q[0].formatJson()))
    except Exception as exp:
        logger.exception(f"Could not convert job data {exp}")
        logger.error(f"Job data looks like: {q}")
    return job


@app.get("/condor_history")
def histories(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    if token.credentials not in auth_db:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("Getting condor_history")
    schedd = htcondor.Schedd()
    jobs = []
    for h in schedd.history():
        try:
            job = CondorJob(**json.loads(h.formatJson()))
            jobs.append(job)
        except Exception as exp:
            logger.exception(f"Could not convert job data {exp}")
            logger.error(f"Job data looks like: {h}")
    logger.info(f"Found {len(jobs)} jobs")
    return jobs


@app.get("/condor_history/{job_id}")
def history(
    job_id: int,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    if token.credentials not in auth_db:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("Getting condor_history")
    schedd = htcondor.Schedd()
    try:
        h: ClassAd = schedd.history(constraint=f"ClusterId=={job_id}")
        if len(h) == 0:
            return HTTPException(
                status_code=404, detail=f"Job id {job_id} not found in history"
            )
        logger.debug(f"{h}")
        job = CondorJob(**json.loads(h[0].formatJson()))
    except Exception as exp:
        logger.exception(f"Could not convert job data {exp}")
        logger.error(f"Job data looks like: {h}")
        raise HTTPException(
            status_code=404, detail=f"Job id {job_id} not found in history"
        )
    return job


@app.post("/condor_submit")
def submit(
    job_request: CondorSubmit,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    if token.credentials not in auth_db:
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info("Starting new job submit")
    logger.debug(f"{job_request.model_dump_json(exclude_none=True)}")
    job = htcondor.Submit(job_request.model_dump(exclude_none=True))
    schedd = htcondor.Schedd()
    submit_result = schedd.submit(job, count=1)
    logger.info(f"Submitting new job {submit_result.cluster()}")

    return CondorSubmitResults().model_validate(
        {
            "cluster": submit_result.cluster(),
            "clusterad": CondorJob(
                **json.loads(submit_result.clusterad().formatJson())
            ),
            "first_proc": submit_result.first_proc(),
            "num_procs": submit_result.num_procs(),
            "submit_script": str(job),
        }
    )
