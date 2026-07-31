import os
import secrets
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional
import json

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
from .models import (
    CondorStatus,
    CondorSubmit,
    CondorJob,
    CondorSubmitResults,
    CondorJobAction,
    CondorEdit,
    CondorExport,
    CondorImport,
    CondorUnexport,
)

import htcondor2 as htcondor
from classad2 import ClassAd, ExprTree

app = FastAPI()
security = HTTPBearer()

auth_db = ["password"]
if pass_file := os.environ.get("PASSWORDFILE"):
    pass_file_path = Path(pass_file).resolve().absolute()
    auth = pass_file_path.read_text().split("\n")
    auth_db = [a.strip() for a in auth if a != ""]
    logger.info(f"Keys in auth database {len(auth_db)}")
elif passwords := os.environ.get("PASSWORDS"):
    auth_db = passwords.split(";")
else:
    logger.warning("Using default AUTH")


def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """Extract the bearer token and verify it against the auth database.

    Raises HTTP 401 for missing or invalid credentials. Comparison is done
    in constant time to avoid leaking valid tokens via timing.
    """
    for allowed in auth_db:
        if secrets.compare_digest(credentials.credentials, allowed):
            return credentials.credentials
    raise HTTPException(status_code=401, detail="Unauthorized")


router = APIRouter(dependencies=[Depends(require_auth)])

app.include_router(router)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# Maps REST strings onto the htcondor2 AdType enumeration for collector queries.
AD_TYPES = {
    "any": htcondor.AdType.Any,
    "startd": htcondor.AdType.Startd,
    "slot": htcondor.AdType.Slot,
    "startdaemon": htcondor.AdType.StartDaemon,
    "schedd": htcondor.AdType.Schedd,
    "master": htcondor.AdType.Master,
    "submitter": htcondor.AdType.Submitter,
    "collector": htcondor.AdType.Collector,
    "negotiator": htcondor.AdType.Negotiator,
    "credd": htcondor.AdType.Credd,
    "generic": htcondor.AdType.Generic,
    "had": htcondor.AdType.HAD,
    "grid": htcondor.AdType.Grid,
    "license": htcondor.AdType.License,
    "defrag": htcondor.AdType.Defrag,
    "accounting": htcondor.AdType.Accounting,
    "placementd": htcondor.AdType.Placementd,
}

# Maps REST strings onto the htcondor2 DaemonType enumeration.
DAEMON_TYPES = {
    "any": htcondor.DaemonType.Any,
    "master": htcondor.DaemonType.Master,
    "schedd": htcondor.DaemonType.Schedd,
    "startd": htcondor.DaemonType.Startd,
    "collector": htcondor.DaemonType.Collector,
    "negotiator": htcondor.DaemonType.Negotiator,
    "credd": htcondor.DaemonType.Credd,
    "placementd": htcondor.DaemonType.Placementd,
    "had": htcondor.DaemonType.HAD,
    "generic": htcondor.DaemonType.Generic,
}

# Maps REST route names onto the htcondor2 JobAction enumeration.
JOB_ACTIONS = {
    "condor_hold": htcondor.JobAction.Hold,
    "condor_release": htcondor.JobAction.Release,
    "condor_suspend": htcondor.JobAction.Suspend,
    "condor_continue": htcondor.JobAction.Continue,
    "condor_rm": htcondor.JobAction.Remove,
    "condor_rmx": htcondor.JobAction.RemoveX,
    "condor_vacate": htcondor.JobAction.Vacate,
    "condor_vacate_fast": htcondor.JobAction.VacateFast,
}


def _projection_list(projection: Optional[str]) -> List[str]:
    if projection is None or projection == "":
        return []
    return [p.strip() for p in projection.split(",")]


def _ad_to_json(ad) -> Dict[str, Any]:
    return json.loads(ad.formatJson())


def _ads_to_json(ads) -> List[Dict[str, Any]]:
    result = []
    for ad in ads:
        try:
            result.append(_ad_to_json(ad))
        except Exception as exp:
            logger.exception(f"Could not convert ad data {exp}")
            logger.error(f"Ad data looks like: {ad}")
            raise HTTPException(status_code=500, detail=str(exp))
    return result


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@router.get("/")
async def read_root():
    logger.info("Checking Health")
    return {"status": True}


# ---------------------------------------------------------------------------
# Schedd: queue queries
# ---------------------------------------------------------------------------
@router.get("/condor_q")
async def jobs(
    constraint: str = "True",
    projection: Optional[str] = None,
    limit: int = -1,
) -> List[CondorJob]:
    logger.info("Getting condor_q")
    schedd = htcondor.Schedd()
    jobs = []
    for q in schedd.query(
        constraint=constraint, projection=_projection_list(projection), limit=limit
    ):
        try:
            job = CondorJob(**json.loads(q.formatJson()))
            jobs.append(job)
        except Exception as exp:
            logger.exception(f"Could not convert job data {exp}")
            logger.error(f"Job data looks like: {q}")
            raise HTTPException(500, f"{exp}")

    logger.info(f"Found {len(jobs)} jobs")
    return jobs


@router.get("/condor_q/{job_id}")
async def job(
    job_id: int,
) -> CondorJob:
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


@router.get("/condor_q_user")
async def user_ads(
    constraint: str = "",
    projection: Optional[str] = None,
    limit: int = -1,
) -> List[Dict[str, Any]]:
    logger.info("Getting condor_q_user")
    schedd = htcondor.Schedd()
    return _ads_to_json(
        schedd.queryUserAds(
            constraint=constraint, projection=_projection_list(projection), limit=limit
        )
    )


@router.get("/condor_q_project")
async def project_ads(
    constraint: str = "",
    projection: Optional[str] = None,
    limit: int = -1,
) -> List[Dict[str, Any]]:
    logger.info("Getting condor_q_project")
    schedd = htcondor.Schedd()
    return _ads_to_json(
        schedd.queryProjectAds(
            constraint=constraint, projection=_projection_list(projection), limit=limit
        )
    )


# ---------------------------------------------------------------------------
# Schedd: history queries
# ---------------------------------------------------------------------------
@router.get("/condor_history")
async def histories(
    constraint: Optional[str] = None,
    projection: Optional[str] = None,
    match: int = -1,
    since: Optional[str] = None,
) -> List[CondorJob]:
    logger.info("Getting condor_history")
    schedd = htcondor.Schedd()
    jobs = []
    for h in schedd.history(
        constraint=constraint, projection=_projection_list(projection), match=match, since=since
    ):
        try:
            job = CondorJob(**json.loads(h.formatJson()))
            jobs.append(job)
        except Exception as exp:
            logger.exception(f"Could not convert job data {exp}")
            logger.error(f"Job data looks like: {h}")
            raise HTTPException(500, f"{exp}")
    logger.info(f"Found {len(jobs)} jobs")
    return jobs


@router.get("/condor_history/{job_id}")
async def history(
    job_id: int,
) -> CondorJob:
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


@router.get("/condor_epoch_history")
async def epoch_history(
    constraint: Optional[str] = None,
    projection: Optional[str] = None,
    match: int = -1,
    since: Optional[str] = None,
) -> List[Dict[str, Any]]:
    logger.info("Getting condor_epoch_history")
    schedd = htcondor.Schedd()
    return _ads_to_json(
        schedd.jobEpochHistory(
            constraint=constraint, projection=_projection_list(projection), match=match, since=since
        )
    )


@router.get("/condor_daemon_history")
async def daemon_history(
    constraint: Optional[str] = None,
    projection: Optional[str] = None,
    match: int = -1,
    since: Optional[str] = None,
) -> List[Dict[str, Any]]:
    logger.info("Getting condor_daemon_history")
    schedd = htcondor.Schedd()
    since_expr = ExprTree(since) if since else None
    return _ads_to_json(
        schedd.daemonHistory(
            constraint=constraint, projection=_projection_list(projection), match=match, since=since_expr
        )
    )


# ---------------------------------------------------------------------------
# Schedd: submission
# ---------------------------------------------------------------------------
@router.post("/condor_submit")
async def submit(
    job_request: CondorSubmit,
):

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


# ---------------------------------------------------------------------------
# Schedd: job actions (condor_rm, condor_hold, condor_release, ...)
# ---------------------------------------------------------------------------
def _job_action(
    action,
    job_ids: Optional[List[str]] = None,
    constraint: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    if job_ids is None and constraint is None:
        raise HTTPException(
            status_code=400, detail="Must provide job_ids or constraint"
        )
    spec = job_ids if job_ids is not None else constraint
    try:
        result = htcondor.Schedd().act(action, spec, reason=reason)
    except Exception as exp:
        logger.exception(f"Job action {action} failed: {exp}")
        raise HTTPException(status_code=500, detail=str(exp))
    if result is None:
        return {}
    return json.loads(result.formatJson())


def _register_job_action(route: str, action) -> None:
    """Register a POST endpoint (and a ``/{job_id}`` variant) for ``action``."""

    async def condor_job_action(
        job_id: Optional[str] = None,
        body: Optional[CondorJobAction] = None,
    ) -> Dict[str, Any]:
        logger.info(f"Applying {action.name} action")
        if job_id is not None:
            job_ids = [job_id]
            constraint = None
        elif body is not None:
            job_ids = body.job_ids
            constraint = body.constraint
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide a job_id in the path or a CondorJobAction body",
            )
        reason = body.reason if body is not None else None
        return _job_action(action, job_ids=job_ids, constraint=constraint, reason=reason)

    router.add_api_route(
        f"/{route}/{{job_id}}",
        condor_job_action,
        methods=["POST"],
        name=f"{route}_by_id",
        summary=f"Apply {action.name} to a specific job",
        tags=["job actions"],
        dependencies=[Depends(require_auth)],
    )
    router.add_api_route(
        f"/{route}",
        condor_job_action,
        methods=["POST"],
        name=route,
        summary=f"Apply {action.name} to jobs by job_ids or constraint",
        tags=["job actions"],
        dependencies=[Depends(require_auth)],
    )


for _route, _action in JOB_ACTIONS.items():
    _register_job_action(_route, _action)


@router.delete("/condor_rm/{job_id}")
async def condor_rm(
    job_id: int,
):
    logger.info(f"Removing {job_id}")
    try:
        schedd = htcondor.Schedd()
        schedd.act(htcondor.JobAction.Remove, [str(job_id)])
        return True
    except Exception as exp:
        logger.debug(f"Job removal failed {exp}")
        raise HTTPException(500, f"{exp}")


# ---------------------------------------------------------------------------
# Schedd: editing and administration
# ---------------------------------------------------------------------------
@router.post("/condor_edit")
async def condor_edit(
    body: CondorEdit,
) -> int:
    if body.job_ids is None and body.constraint is None:
        raise HTTPException(
            status_code=400, detail="Must provide job_ids or constraint"
        )
    spec = body.job_ids if body.job_ids is not None else body.constraint
    logger.info(f"Editing {body.attr} on jobs matching {spec}")
    try:
        return htcondor.Schedd().edit(spec, body.attr, body.value)
    except Exception as exp:
        logger.exception(f"Could not edit job data {exp}")
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/condor_reschedule")
async def condor_reschedule(
) -> bool:
    logger.info("Requesting reschedule")
    try:
        htcondor.Schedd().reschedule()
    except Exception as exp:
        logger.exception(f"Could not reschedule {exp}")
        raise HTTPException(status_code=500, detail=str(exp))
    return True


@router.post("/condor_export_jobs")
async def condor_export_jobs(
    body: CondorExport,
) -> Dict[str, Any]:
    if body.job_ids is None and body.constraint is None:
        raise HTTPException(
            status_code=400, detail="Must provide job_ids or constraint"
        )
    spec = body.job_ids if body.job_ids is not None else body.constraint
    logger.info(f"Exporting jobs matching {spec}")
    try:
        result = htcondor.Schedd().export_jobs(spec, body.export_dir, body.new_spool_dir)
    except Exception as exp:
        logger.exception(f"Could not export jobs {exp}")
        raise HTTPException(status_code=500, detail=str(exp))
    return json.loads(result.formatJson())


@router.post("/condor_import_exported_job_results")
async def condor_import_exported_job_results(
    body: CondorImport,
) -> Dict[str, Any]:
    logger.info(f"Importing exported job results from {body.import_dir}")
    try:
        result = htcondor.Schedd().import_exported_job_results(body.import_dir)
    except Exception as exp:
        logger.exception(f"Could not import exported job results {exp}")
        raise HTTPException(status_code=500, detail=str(exp))
    return json.loads(result.formatJson())


@router.post("/condor_unexport_jobs")
async def condor_unexport_jobs(
    body: CondorUnexport,
) -> Dict[str, Any]:
    if body.job_ids is None and body.constraint is None:
        raise HTTPException(
            status_code=400, detail="Must provide job_ids or constraint"
        )
    spec = body.job_ids if body.job_ids is not None else body.constraint
    logger.info(f"Unexporting jobs matching {spec}")
    try:
        result = htcondor.Schedd().unexport_jobs(spec)
    except Exception as exp:
        logger.exception(f"Could not unexport jobs {exp}")
        raise HTTPException(status_code=500, detail=str(exp))
    return json.loads(result.formatJson())


# ---------------------------------------------------------------------------
# Collector: status
# ---------------------------------------------------------------------------
@router.get("/condor_status")
async def condor_status(
    ad_type: str = "any",
    constraint: Optional[str] = None,
    projection: Optional[str] = None,
) -> List[CondorStatus]:
    ad_type_enum = AD_TYPES.get(ad_type.lower())
    if ad_type_enum is None:
        raise HTTPException(status_code=400, detail=f"Unknown ad type: {ad_type}")
    logger.info(f"Getting condor_status for {ad_type}")
    coll = htcondor.Collector()
    nodes = []
    for n in coll.query(
        ad_type=ad_type_enum,
        constraint=constraint,
        projection=_projection_list(projection) or None,
    ):
        try:
            node = CondorStatus(**json.loads(n.formatJson()))
            nodes.append(node)
        except Exception as exp:
            logger.exception(f"Could not convert node data {exp}")
            logger.error(f"Node data looks like: {n}")
            raise HTTPException(500, f"{exp}")
    logger.info(f"Found {len(nodes)} nodes")

    return nodes


@router.get("/condor_status/{name}")
async def condor_status_by_name(
    name: str,
    ad_type: str = "any",
    constraint: Optional[str] = None,
    projection: Optional[str] = None,
) -> CondorStatus:
    ad_type_enum = AD_TYPES.get(ad_type.lower())
    if ad_type_enum is None:
        raise HTTPException(status_code=400, detail=f"Unknown ad type: {ad_type}")
    logger.info(f"Getting condor_status for {name}")
    if constraint:
        constraint = f'({constraint}) && Name == "{name}"'
    else:
        constraint = f'Name == "{name}"'
    coll = htcondor.Collector()
    ads = coll.query(
        ad_type=ad_type_enum,
        constraint=constraint,
        projection=_projection_list(projection) or None,
    )
    if len(ads) == 0:
        raise HTTPException(status_code=404, detail=f"Ad {name} not found")
    try:
        node = CondorStatus(**json.loads(ads[0].formatJson()))
    except Exception as exp:
        logger.exception(f"Could not convert node data {exp}")
        logger.error(f"Node data looks like: {ads[0]}")
        raise HTTPException(status_code=500, detail="Error converting node data")
    return node


@router.get("/condor_nodes")
async def condor_nodes() -> List[CondorStatus]:
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


# ---------------------------------------------------------------------------
# Collector: locate
# ---------------------------------------------------------------------------
@router.get("/condor_locate/{daemon_type}")
async def condor_locate(
    daemon_type: str,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    daemon_type_enum = DAEMON_TYPES.get(daemon_type.lower())
    if daemon_type_enum is None:
        raise HTTPException(
            status_code=400, detail=f"Unknown daemon type: {daemon_type}"
        )
    logger.info(f"Locating {daemon_type} {name or ''}".rstrip())
    coll = htcondor.Collector()
    ad = coll.locate(daemon_type_enum, name)
    if ad is None:
        raise HTTPException(
            status_code=404, detail=f"Daemon {name or daemon_type} not found"
        )
    return _ad_to_json(ad)


@router.get("/condor_locate_all/{daemon_type}")
async def condor_locate_all(
    daemon_type: str,
) -> List[Dict[str, Any]]:
    daemon_type_enum = DAEMON_TYPES.get(daemon_type.lower())
    if daemon_type_enum is None:
        raise HTTPException(
            status_code=400, detail=f"Unknown daemon type: {daemon_type}"
        )
    logger.info(f"Locating all {daemon_type} daemons")
    coll = htcondor.Collector()
    return _ads_to_json(coll.locateAll(daemon_type_enum))


# ---------------------------------------------------------------------------
# Configuration (htcondor.param)
# ---------------------------------------------------------------------------
@router.get("/condor_config")
async def condor_config(
) -> Dict[str, str]:
    logger.info("Getting condor_config")
    config = {}
    for key in htcondor.param:
        try:
            config[key] = htcondor.param[key]
        except Exception as exp:
            logger.debug(f"Could not get config value for {key}: {exp}")
    logger.info(f"Found {len(config)} config parameters")
    return config


@router.get("/condor_config/{attribute}")
async def condor_config_attribute(
    attribute: str,
) -> str:
    logger.info(f"Getting condor_config for {attribute}")
    try:
        return htcondor.param[attribute]
    except Exception as exp:
        logger.exception(f"Could not get config value for {attribute}: {exp}")
        raise HTTPException(
            status_code=404, detail=f"Config attribute {attribute} not found"
        )


# ---------------------------------------------------------------------------
# Negotiator: user priorities
# ---------------------------------------------------------------------------
@router.get("/condor_userprio")
async def condor_userprio(
) -> List[Dict[str, Any]]:
    logger.info("Getting condor_userprio")
    negotiator = htcondor.Negotiator()
    return _ads_to_json(negotiator.getPriorities())


@router.get("/condor_userprio/{user}")
async def condor_userprio_user(
    user: str,
) -> List[Dict[str, Any]]:
    logger.info(f"Getting condor_userprio for {user}")
    negotiator = htcondor.Negotiator()
    return _ads_to_json(negotiator.getResourceUsage(user))
