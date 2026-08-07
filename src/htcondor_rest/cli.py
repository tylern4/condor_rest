from __future__ import annotations

import json
from pathlib import Path

import typer

from .client import CONDOR_PASS, CONDOR_URL, CondorClient


# ---------------------------------------------------------------------------
# condor_submit
# ---------------------------------------------------------------------------
def condor_submit_cli(
    submitfile: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the HTCondor submit file.",
    ),
    url: str = typer.Option(
        CONDOR_URL, "--url", envvar="CONDOR_URL", help="htcondor-rest base URL."
    ),
    token: str = typer.Option(
        CONDOR_PASS, "--token", envvar="CONDOR_PASS", help="htcondor-rest bearer token."
    ),
) -> None:
    """Submit a job described by a submit file to the htcondor-rest API.

    The submit file is sent verbatim; the server parses it with the full
    condor_submit language. The submit result is printed as JSON.
    """
    submit_text = submitfile.read_text()
    with CondorClient(base_url=url, token=token) as condor:
        result = condor.submit_file(submit_text)
    typer.echo(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# condor_q
# ---------------------------------------------------------------------------
def condor_q_cli(
    job_id: str | None = typer.Argument(
        None, help="Job ID to query: a cluster ID or 'cluster.proc'."
    ),
    constraint: str | None = typer.Option(
        None, "--constraint", "-c", help="ClassAd expression selecting jobs."
    ),
    projection: str | None = typer.Option(
        None, "--projection", help="Comma-separated list of attributes to return."
    ),
    limit: int = typer.Option(
        -1, "--limit", "-n", help="Maximum number of jobs to return (-1 = all)."
    ),
    url: str = typer.Option(
        CONDOR_URL, "--url", envvar="CONDOR_URL", help="htcondor-rest base URL."
    ),
    token: str = typer.Option(
        CONDOR_PASS, "--token", envvar="CONDOR_PASS", help="htcondor-rest bearer token."
    ),
) -> None:
    """Query the job queue and print the matching job ads as JSON."""
    with CondorClient(base_url=url, token=token) as condor:
        if job_id is not None:
            if "." in job_id:
                cluster, proc = job_id.split(".", 1)
                jobs = condor.get_queue(
                    constraint=f"(ClusterId == {cluster} && ProcID == {proc})"
                )
            else:
                jobs = condor.get_queue(job_id=int(job_id))
        else:
            jobs = condor.get_queue(
                constraint=constraint, projection=projection, limit=limit
            )
    typer.echo(json.dumps(jobs, indent=2))


# ---------------------------------------------------------------------------
# condor_rm
# ---------------------------------------------------------------------------
def condor_rm_cli(
    job_id: str = typer.Argument(
        ..., help="Job ID to remove: a cluster ID or 'cluster.proc'."
    ),
    reason: str | None = typer.Option(
        None, "--reason", "-r", help="Free-form justification for the removal."
    ),
    url: str = typer.Option(
        CONDOR_URL, "--url", envvar="CONDOR_URL", help="htcondor-rest base URL."
    ),
    token: str = typer.Option(
        CONDOR_PASS, "--token", envvar="CONDOR_PASS", help="htcondor-rest bearer token."
    ),
) -> None:
    """Remove a job (or a specific job process) from the queue."""
    with CondorClient(base_url=url, token=token) as condor:
        result = condor.remove(job_ids=[job_id], reason=reason)
    typer.echo(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# condor_history
# ---------------------------------------------------------------------------
def condor_history_cli(
    job_id: str | None = typer.Argument(
        None, help="Job ID to look up: a cluster ID or 'cluster.proc'."
    ),
    constraint: str | None = typer.Option(
        None, "--constraint", "-c", help="ClassAd expression selecting jobs."
    ),
    projection: str | None = typer.Option(
        None, "--projection", help="Comma-separated list of attributes to return."
    ),
    match: int = typer.Option(
        -1, "--match", "-n", help="Maximum number of jobs to return (-1 = all)."
    ),
    since: str | None = typer.Option(
        None, "--since", help="Only return jobs matching since this time."
    ),
    url: str = typer.Option(
        CONDOR_URL, "--url", envvar="CONDOR_URL", help="htcondor-rest base URL."
    ),
    token: str = typer.Option(
        CONDOR_PASS, "--token", envvar="CONDOR_PASS", help="htcondor-rest bearer token."
    ),
) -> None:
    """Query the job history and print the matching job ads as JSON."""
    with CondorClient(base_url=url, token=token) as condor:
        if job_id is not None:
            if "." in job_id:
                cluster, proc = job_id.split(".", 1)
                jobs = condor.get_history(
                    constraint=f"(ClusterId == {cluster} && ProcID == {proc})",
                    match=match,
                    since=since,
                )
            else:
                jobs = condor.get_history(job_id=int(job_id))
        else:
            jobs = condor.get_history(
                constraint=constraint, projection=projection, match=match, since=since
            )
    typer.echo(json.dumps(jobs, indent=2))


# ---------------------------------------------------------------------------
# condor_status
# ---------------------------------------------------------------------------
def condor_status_cli(
    name: str | None = typer.Argument(
        None, help="Name of a specific ad to query (e.g. a slot or daemon name)."
    ),
    ad_type: str = typer.Option(
        "any", "--ad-type", help="Ad type to query (any, startd, schedd, ...)."
    ),
    constraint: str | None = typer.Option(
        None, "--constraint", "-c", help="ClassAd expression selecting ads."
    ),
    projection: str | None = typer.Option(
        None, "--projection", help="Comma-separated list of attributes to return."
    ),
    url: str = typer.Option(
        CONDOR_URL, "--url", envvar="CONDOR_URL", help="htcondor-rest base URL."
    ),
    token: str = typer.Option(
        CONDOR_PASS, "--token", envvar="CONDOR_PASS", help="htcondor-rest bearer token."
    ),
) -> None:
    """Query the collector and print the matching ads as JSON."""
    with CondorClient(base_url=url, token=token) as condor:
        if name is not None:
            ads = condor.get_status_by_name(
                name, ad_type=ad_type, constraint=constraint, projection=projection
            )
        else:
            ads = condor.get_status(
                ad_type=ad_type, constraint=constraint, projection=projection
            )
    typer.echo(json.dumps(ads, indent=2))


# ---------------------------------------------------------------------------
# condor_hold / condor_release
# ---------------------------------------------------------------------------
def condor_hold_cli(
    job_id: str | None = typer.Argument(
        None, help="Job ID to hold: a cluster ID or 'cluster.proc'."
    ),
    constraint: str | None = typer.Option(
        None, "--constraint", "-c", help="ClassAd expression selecting jobs."
    ),
    reason: str | None = typer.Option(
        None, "--reason", "-r", help="Free-form justification for the hold."
    ),
    url: str = typer.Option(
        CONDOR_URL, "--url", envvar="CONDOR_URL", help="htcondor-rest base URL."
    ),
    token: str = typer.Option(
        CONDOR_PASS, "--token", envvar="CONDOR_PASS", help="htcondor-rest bearer token."
    ),
) -> None:
    """Place a job on hold."""
    if job_id is None and constraint is None:
        raise typer.BadParameter("provide a JOB_ID or --constraint")
    with CondorClient(base_url=url, token=token) as condor:
        result = condor.hold(
            job_ids=[job_id] if job_id is not None else None,
            constraint=constraint,
            reason=reason,
        )
    typer.echo(json.dumps(result, indent=2))


def condor_release_cli(
    job_id: str | None = typer.Argument(
        None, help="Job ID to release: a cluster ID or 'cluster.proc'."
    ),
    constraint: str | None = typer.Option(
        None, "--constraint", "-c", help="ClassAd expression selecting jobs."
    ),
    reason: str | None = typer.Option(
        None, "--reason", "-r", help="Free-form justification for the release."
    ),
    url: str = typer.Option(
        CONDOR_URL, "--url", envvar="CONDOR_URL", help="htcondor-rest base URL."
    ),
    token: str = typer.Option(
        CONDOR_PASS, "--token", envvar="CONDOR_PASS", help="htcondor-rest bearer token."
    ),
) -> None:
    """Release a job from hold."""
    if job_id is None and constraint is None:
        raise typer.BadParameter("provide a JOB_ID or --constraint")
    with CondorClient(base_url=url, token=token) as condor:
        result = condor.release(
            job_ids=[job_id] if job_id is not None else None,
            constraint=constraint,
            reason=reason,
        )
    typer.echo(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# Console script entry points
# ---------------------------------------------------------------------------
def submit_main() -> None:
    typer.run(condor_submit_cli)


def q_main() -> None:
    typer.run(condor_q_cli)


def rm_main() -> None:
    typer.run(condor_rm_cli)


def history_main() -> None:
    typer.run(condor_history_cli)


def status_main() -> None:
    typer.run(condor_status_cli)


def hold_main() -> None:
    typer.run(condor_hold_cli)


def release_main() -> None:
    typer.run(condor_release_cli)
