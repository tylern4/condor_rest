import os
from pathlib import Path
from typing import Annotated, List
import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
from .models import (
    CondorStatus,
    CondorSubmit,
    CondorJob,
    CondorSubmitResults,
)

import htcondor2 as htcondor
from classad2 import ClassAd

app = FastAPI()
security = HTTPBearer()

auth_db = ["password"]
if pass_file := os.environ.get("PASSWORDFILE"):
    pass_file_path = Path(pass_file).resolve().absolute()
    auth = pass_file_path.read_text().split("\n")
    auth_db = [a.rstrip("/n") for a in auth if a != ""]
    logger.info(f"Keys in auth database {len(auth_db)}")
elif passwords := os.environ.get("PASSWORDS"):
    auth_db = passwords.split(";")
else:
    logger.warning("Using default AUTH")


@app.get("/")
async def read_root():
    logger.info("Checking Health")
    return {"status": True}


@app.get("/condor_q")
async def jobs(
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
            raise HTTPException(500, f"{exp}")

    logger.info(f"Found {len(jobs)} jobs")
    return jobs


@app.get("/condor_q/{job_id}")
async def job(
    job_id: int,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> CondorJob:
    if token.credentials not in auth_db:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info(f"Getting condor_q for {job_id}")
    schedd = htcondor.Schedd()
    try:
        # Query the job queue for the specific job ID.
        q: ClassAd = schedd.query(constraint=f"ClusterId=={job_id}")
    except Exception as exp:
        logger.exception(f"Could not get job data {exp}")
        raise HTTPException(status_code=500, detail="Error getting job data")
    # If no job is found, raise a 404 error.
    if len(q) == 0:
        raise HTTPException(
            status_code=404, detail=f"Job id {job_id} not found in queue"
        )

    # Attempt to convert the job data to a CondorJob model.
    try:
        logger.debug(f"{q}")
        job = CondorJob(**json.loads(q[0].formatJson()))
    except Exception as exp:
        logger.exception(f"Could not convert job data {exp}")
        logger.error(f"Job data looks like: {q}")
        raise HTTPException(status_code=500, detail="Error converting job data")
    return job


@app.get("/condor_history")
async def histories(
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
            raise HTTPException(500, f"{exp}")
    logger.info(f"Found {len(jobs)} jobs")
    return jobs


@app.get("/condor_history/{job_id}")
async def history(
    job_id: int,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    if token.credentials not in auth_db:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("Getting condor_history")
    schedd = htcondor.Schedd()
    # Query the job history for the specific job ID.
    h: ClassAd = schedd.history(constraint=f"ClusterId=={job_id}")
    # If no history entry is found, raise a 404 error.
    if len(h) == 0:
        raise HTTPException(
            status_code=404, detail=f"Job id {job_id} not found in history"
        )
    # Attempt to convert the history data to a CondorJob model.
    try:
        logger.debug(f"{h}")
        job = CondorJob(**json.loads(h[0].formatJson()))
    except Exception as exp:
        logger.exception(f"Could not convert job data {exp}")
        logger.error(f"Job data looks like: {h}")
        raise HTTPException(status_code=500, detail="Error converting job data")
    return job


@app.post("/condor_submit")
async def submit(
    job_request: CondorSubmit,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    if token.credentials not in auth_db:
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info("Starting new job submit")
    logger.debug(f"{job_request.model_dump(exclude_none=True)}")
    job = htcondor.Submit(job_request.model_dump(exclude_none=True))
    logger.debug(f"{job}")
    schedd = htcondor.Schedd()
    try:
        submit_result = schedd.submit(job, count=1)
        logger.info(f"Submitting new job {submit_result.cluster()}")
    except Exception as exp:
        logger.debug(f"Job submission failed {exp}")
        raise HTTPException(500, f"{exp}")

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


@app.delete("/condor_rm/{job_id}")
async def condor_rm(
    job_id: int,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    if token.credentials not in auth_db:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info(f"Removing {job_id}")
    try:
        schedd = htcondor.Schedd()
        schedd.act(htcondor.JobAction.Remove, [str(job_id)])
        return True
    except Exception as exp:
        logger.debug(f"Job removal failed {exp}")
        raise HTTPException(500, f"{exp}")


@app.get("/condor_status")
async def condor_status():
    coll = htcondor.Collector()
    nodes = []
    for n in coll.query():
        try:
            node = CondorStatus(**json.loads(n.formatJson()))
            nodes.append(node)
        except Exception as exp:
            logger.exception(f"Could not convert job data {exp}")
            logger.error(f"Job data looks like: {n}")
            raise HTTPException(500, f"{exp}")
    logger.info(f"Found {len(nodes)} nodes")

    return nodes


@app.get("/condor_nodes")
async def condor_nodes():
    coll = htcondor.Collector()
    nodes = []
    for n in coll.query(constraint='MyType=="Machine"'):
        try:
            node = CondorStatus(**json.loads(n.formatJson()))
            nodes.append(node)
        except Exception as exp:
            logger.exception(f"Could not convert job data {exp}")
            logger.error(f"Job data looks like: {n}")
            raise HTTPException(500, f"{exp}")
    logger.info(f"Found {len(nodes)} nodes")

    return nodes
