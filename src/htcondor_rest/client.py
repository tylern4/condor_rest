from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Union

import httpx
from loguru import logger

CONDOR_URL = os.getenv("CONDOR_URL", "http://localhost:8008")
CONDOR_PASS = os.getenv("CONDOR_PASS", "password")


class CondorClient:
    """HTTP client for the htcondor-rest API.

    Wraps every API endpoint in a typed helper method. All requests and
    responses are logged through ``loguru``. Responses are parsed as JSON
    where possible; non-JSON responses (e.g. ``/metrics``) are returned as
    text. HTTP error statuses raise ``httpx.HTTPStatusError``.
    """

    def __init__(
        self,
        base_url: str = CONDOR_URL,
        token: str = CONDOR_PASS,
        timeout: float = 60.0,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
            transport=transport,
        )
        logger.info(f"Connected to htcondor-rest API at {base_url}")

    def __enter__(self) -> "CondorClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()
        logger.debug("Closed htcondor-rest client")

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------
    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        logger.info(f"{method.upper()} {path}")
        response = self._client.request(method, path, **kwargs)
        if response.is_success:
            logger.debug(f"{method.upper()} {path} -> {response.status_code}")
        else:
            logger.error(
                f"{method.upper()} {path} -> {response.status_code} {response.text}"
            )
        response.raise_for_status()
        if "application/json" in response.headers.get("content-type", ""):
            return response.json()
        return response.text

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    def health(self) -> bool:
        return bool(self._request("GET", "/")["status"])

    # ------------------------------------------------------------------
    # Queue (condor_q)
    # ------------------------------------------------------------------
    def get_queue(
        self,
        job_id: Optional[int] = None,
        constraint: Optional[str] = None,
        projection: Optional[str] = None,
        limit: int = -1,
    ) -> Any:
        if job_id is not None:
            return self._request("GET", f"/condor_q/{job_id}")
        params: Dict[str, Any] = {"limit": limit}
        if constraint:
            params["constraint"] = constraint
        if projection:
            params["projection"] = projection
        return self._request("GET", "/condor_q", params=params)

    def get_user_ads(
        self,
        constraint: Optional[str] = None,
        projection: Optional[str] = None,
        limit: int = -1,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": limit}
        if constraint:
            params["constraint"] = constraint
        if projection:
            params["projection"] = projection
        return self._request("GET", "/condor_q_user", params=params)

    def get_project_ads(
        self,
        constraint: Optional[str] = None,
        projection: Optional[str] = None,
        limit: int = -1,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": limit}
        if constraint:
            params["constraint"] = constraint
        if projection:
            params["projection"] = projection
        return self._request("GET", "/condor_q_project", params=params)

    # ------------------------------------------------------------------
    # History (condor_history)
    # ------------------------------------------------------------------
    def get_history(
        self,
        job_id: Optional[int] = None,
        constraint: Optional[str] = None,
        projection: Optional[str] = None,
        match: int = -1,
        since: Optional[str] = None,
    ) -> Any:
        if job_id is not None:
            return self._request("GET", f"/condor_history/{job_id}")
        params: Dict[str, Any] = {"match": match}
        if constraint:
            params["constraint"] = constraint
        if projection:
            params["projection"] = projection
        if since:
            params["since"] = since
        return self._request("GET", "/condor_history", params=params)

    def get_epoch_history(
        self,
        constraint: Optional[str] = None,
        projection: Optional[str] = None,
        match: int = -1,
        since: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"match": match}
        if constraint:
            params["constraint"] = constraint
        if projection:
            params["projection"] = projection
        if since:
            params["since"] = since
        return self._request("GET", "/condor_epoch_history", params=params)

    def get_daemon_history(
        self,
        constraint: Optional[str] = None,
        projection: Optional[str] = None,
        match: int = -1,
        since: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"match": match}
        if constraint:
            params["constraint"] = constraint
        if projection:
            params["projection"] = projection
        if since:
            params["since"] = since
        return self._request("GET", "/condor_daemon_history", params=params)

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------
    def submit(self, job: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/condor_submit", json=job)

    def submit_file(self, submit_text: str, count: int = 0, spool: bool = False) -> Dict[str, Any]:
        """Submit a job described by raw condor_submit-language text."""
        return self._request(
            "POST",
            "/condor_submit_file",
            json={"submit_text": submit_text, "count": count, "spool": spool},
        )

    # ------------------------------------------------------------------
    # Job actions (condor_hold, condor_release, condor_rm, ...)
    # ------------------------------------------------------------------
    def _apply_action(
        self,
        action: str,
        job_id: Optional[int] = None,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        if job_id is not None:
            return self._request("POST", f"/{action}/{job_id}")
        body: Dict[str, Any] = {}
        if job_ids is not None:
            body["job_ids"] = job_ids
        if constraint is not None:
            body["constraint"] = constraint
        if reason is not None:
            body["reason"] = reason
        return self._request("POST", f"/{action}", json=body)

    def hold(
        self,
        job_id: Optional[int] = None,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._apply_action(
            "condor_hold", job_id=job_id, job_ids=job_ids, constraint=constraint, reason=reason
        )

    def release(
        self,
        job_id: Optional[int] = None,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._apply_action(
            "condor_release", job_id=job_id, job_ids=job_ids, constraint=constraint, reason=reason
        )

    def suspend(
        self,
        job_id: Optional[int] = None,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._apply_action(
            "condor_suspend", job_id=job_id, job_ids=job_ids, constraint=constraint, reason=reason
        )

    def resume(
        self,
        job_id: Optional[int] = None,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._apply_action(
            "condor_continue", job_id=job_id, job_ids=job_ids, constraint=constraint, reason=reason
        )

    def remove(
        self,
        job_id: Optional[int] = None,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._apply_action(
            "condor_rm", job_id=job_id, job_ids=job_ids, constraint=constraint, reason=reason
        )

    def remove_x(
        self,
        job_id: Optional[int] = None,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._apply_action(
            "condor_rmx", job_id=job_id, job_ids=job_ids, constraint=constraint, reason=reason
        )

    def vacate(
        self,
        job_id: Optional[int] = None,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._apply_action(
            "condor_vacate", job_id=job_id, job_ids=job_ids, constraint=constraint, reason=reason
        )

    def vacate_fast(
        self,
        job_id: Optional[int] = None,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._apply_action(
            "condor_vacate_fast", job_id=job_id, job_ids=job_ids, constraint=constraint, reason=reason
        )

    def delete_job(self, job_id: int) -> bool:
        return bool(self._request("DELETE", f"/condor_rm/{job_id}"))

    # ------------------------------------------------------------------
    # Schedd: file transfer (spool / retrieve)
    # ------------------------------------------------------------------
    def spool(self) -> Dict[str, Any]:
        """Upload input files of the most recent ``spool=True`` submit."""
        return self._request("POST", "/condor_spool")

    def retrieve(
        self,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
    ) -> bool:
        if job_ids is None and constraint is None:
            raise ValueError("Must provide job_ids or constraint")
        body: Dict[str, Any] = {}
        if job_ids is not None:
            body["job_ids"] = job_ids
        if constraint is not None:
            body["constraint"] = constraint
        return bool(self._request("POST", "/condor_retrieve", json=body))

    def refresh_gsi_proxy(
        self,
        cluster: int,
        proc: int,
        proxy_filename: str,
        lifetime: int = -1,
    ) -> int:
        return int(
            self._request(
                "POST",
                "/condor_refresh_gsi_proxy",
                json={
                    "cluster": cluster,
                    "proc": proc,
                    "proxy_filename": proxy_filename,
                    "lifetime": lifetime,
                },
            )
        )

    def get_claims(
        self,
        constraint: Optional[str] = None,
        projection: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if constraint:
            params["constraint"] = constraint
        if projection:
            params["projection"] = projection
        return self._request("GET", "/condor_claims", params=params)

    # ------------------------------------------------------------------
    # Schedd: one-click university (OCU) claims
    # ------------------------------------------------------------------
    def create_ocu(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/condor_create_ocu", json={"request": request})

    def remove_ocu(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/condor_remove_ocu", json={"request": request})

    def query_ocu(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/condor_query_ocu", json={"request": request})

    # ------------------------------------------------------------------
    # Schedd: user / project accounting records
    # ------------------------------------------------------------------
    def _rec_action(
        self,
        route: str,
        spec: Optional[Union[str, List[str]]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        if spec is not None and constraint is not None:
            raise ValueError("Provide either spec or constraint, not both")
        if spec is None and constraint is None:
            raise ValueError("Must provide spec or constraint")
        body: Dict[str, Any] = {}
        if spec is not None:
            body["spec"] = spec
        if constraint is not None:
            body["constraint"] = constraint
        if reason is not None:
            body["reason"] = reason
        return self._request("POST", f"/condor_{route}", json=body)

    def add_user_rec(
        self,
        spec: Optional[Union[str, List[str]]] = None,
        constraint: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._rec_action("add_user_rec", spec=spec, constraint=constraint)

    def enable_user_rec(
        self,
        spec: Optional[Union[str, List[str]]] = None,
        constraint: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._rec_action("enable_user_rec", spec=spec, constraint=constraint)

    def disable_user_rec(
        self,
        spec: Optional[Union[str, List[str]]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._rec_action(
            "disable_user_rec", spec=spec, constraint=constraint, reason=reason
        )

    def remove_user_rec(
        self,
        spec: Optional[Union[str, List[str]]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._rec_action(
            "remove_user_rec", spec=spec, constraint=constraint, reason=reason
        )

    def update_user_rec(self, ads: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._request("POST", "/condor_update_user_rec", json={"ads": ads})

    def add_project_rec(
        self,
        spec: Optional[Union[str, List[str]]] = None,
        constraint: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._rec_action("add_project_rec", spec=spec, constraint=constraint)

    def enable_project_rec(
        self,
        spec: Optional[Union[str, List[str]]] = None,
        constraint: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._rec_action("enable_project_rec", spec=spec, constraint=constraint)

    def disable_project_rec(
        self,
        spec: Optional[Union[str, List[str]]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._rec_action(
            "disable_project_rec", spec=spec, constraint=constraint, reason=reason
        )

    def remove_project_rec(
        self,
        spec: Optional[Union[str, List[str]]] = None,
        constraint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._rec_action(
            "remove_project_rec", spec=spec, constraint=constraint, reason=reason
        )

    def update_project_rec(self, ads: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._request("POST", "/condor_update_project_rec", json={"ads": ads})

    # ------------------------------------------------------------------
    # Schedd: editing and administration
    # ------------------------------------------------------------------
    def edit(
        self,
        attr: str,
        value: str,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
    ) -> int:
        if job_ids is None and constraint is None:
            raise ValueError("Must provide job_ids or constraint")
        body: Dict[str, Any] = {"attr": attr, "value": value}
        if job_ids is not None:
            body["job_ids"] = job_ids
        if constraint is not None:
            body["constraint"] = constraint
        return int(self._request("POST", "/condor_edit", json=body))

    def reschedule(self) -> bool:
        return bool(self._request("POST", "/condor_reschedule"))

    def export_jobs(
        self,
        export_dir: str,
        new_spool_dir: str,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
    ) -> Dict[str, Any]:
        if job_ids is None and constraint is None:
            raise ValueError("Must provide job_ids or constraint")
        body: Dict[str, Any] = {"export_dir": export_dir, "new_spool_dir": new_spool_dir}
        if job_ids is not None:
            body["job_ids"] = job_ids
        if constraint is not None:
            body["constraint"] = constraint
        return self._request("POST", "/condor_export_jobs", json=body)

    def import_exported_job_results(self, import_dir: str) -> Dict[str, Any]:
        return self._request(
            "POST", "/condor_import_exported_job_results", json={"import_dir": import_dir}
        )

    def unexport_jobs(
        self,
        job_ids: Optional[List[str]] = None,
        constraint: Optional[str] = None,
    ) -> Dict[str, Any]:
        if job_ids is None and constraint is None:
            raise ValueError("Must provide job_ids or constraint")
        body: Dict[str, Any] = {}
        if job_ids is not None:
            body["job_ids"] = job_ids
        if constraint is not None:
            body["constraint"] = constraint
        return self._request("POST", "/condor_unexport_jobs", json=body)

    # ------------------------------------------------------------------
    # Collector: status
    # ------------------------------------------------------------------
    def get_status(
        self,
        ad_type: str = "any",
        constraint: Optional[str] = None,
        projection: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"ad_type": ad_type}
        if constraint:
            params["constraint"] = constraint
        if projection:
            params["projection"] = projection
        return self._request("GET", "/condor_status", params=params)

    def get_status_by_name(
        self,
        name: str,
        ad_type: str = "any",
        constraint: Optional[str] = None,
        projection: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"ad_type": ad_type}
        if constraint:
            params["constraint"] = constraint
        if projection:
            params["projection"] = projection
        return self._request("GET", f"/condor_status/{name}", params=params)

    def get_nodes(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/condor_nodes")

    # ------------------------------------------------------------------
    # Collector: locate
    # ------------------------------------------------------------------
    def locate(
        self,
        daemon_type: str,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if name:
            params["name"] = name
        return self._request("GET", f"/condor_locate/{daemon_type}", params=params)

    def locate_all(self, daemon_type: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/condor_locate_all/{daemon_type}")

    def direct_query(
        self,
        daemon_type: str,
        name: Optional[str] = None,
        projection: Optional[str] = None,
        statistics: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if name:
            params["name"] = name
        if projection:
            params["projection"] = projection
        if statistics:
            params["statistics"] = statistics
        return self._request(
            "GET", f"/condor_direct_query/{daemon_type}", params=params
        )

    def advertise(
        self,
        ads: List[Dict[str, Any]],
        command: str = "UPDATE_AD_GENERIC",
        use_tcp: bool = True,
    ) -> bool:
        return bool(
            self._request(
                "POST",
                "/condor_advertise",
                json={"ads": ads, "command": command, "use_tcp": use_tcp},
            )
        )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    def get_config(self) -> Dict[str, str]:
        return self._request("GET", "/condor_config")

    def get_config_attribute(self, attribute: str) -> str:
        return self._request("GET", f"/condor_config/{attribute}")

    # ------------------------------------------------------------------
    # Negotiator: user priorities
    # ------------------------------------------------------------------
    def get_userprio(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/condor_userprio")

    def get_userprio_user(self, user: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/condor_userprio/{user}")

    # ------------------------------------------------------------------
    # Prometheus metrics
    # ------------------------------------------------------------------
    def get_metrics(self) -> str:
        return self._request("GET", "/metrics")
