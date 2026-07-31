import sys
import types
import json
import enum
import time
import pytest
from fastapi.testclient import TestClient

AUTH_HEADERS = {"Authorization": "Bearer password"}

# ---------------------------------------------------------------------------
# Setup a dummy ``htcondor2`` module before importing the FastAPI app.
# This prevents ImportError in environments where the real ``htcondor2``
# package is not installed. The dummy module provides placeholder classes
# that will be patched in the ``mock_htcondor`` fixture.
# ---------------------------------------------------------------------------
htcondor2 = types.ModuleType("htcondor2")


class _DummySchedd:
    pass


class _DummyCollector:
    pass


class _DummySubmit:
    pass


class _DummyNegotiator:
    pass


# Dummy enums to mimic the htcondor2 enumerations used at import time.
class _DummyJobAction(enum.IntEnum):
    Hold = 1
    Release = 2
    Remove = 3
    RemoveX = 4
    Vacate = 5
    VacateFast = 6
    Suspend = 8
    Continue = 9


class _DummyAdType(enum.IntEnum):
    Startd = 0
    Schedd = 1
    Master = 2
    StartdPrivate = 5
    Submitter = 6
    Collector = 7
    License = 8
    Any = 10
    Negotiator = 13
    HAD = 14
    Generic = 15
    Credd = 16
    Grid = 19
    Placementd = 20
    Defrag = 22
    Accounting = 23
    Slot = 24
    StartDaemon = 25


class _DummyDaemonType(enum.IntEnum):
    none = 0
    Any = 1
    Master = 2
    Schedd = 3
    Startd = 4
    Collector = 5
    Negotiator = 6
    Credd = 13
    Placementd = 15
    HAD = 17
    Generic = 18


class _DummyJobStatus(enum.IntEnum):
    IDLE = 1
    RUNNING = 2
    REMOVED = 3
    COMPLETED = 4
    HELD = 5
    TRANSFERRING_OUTPUT = 6
    SUSPENDED = 7


htcondor2.Schedd = _DummySchedd
htcondor2.Collector = _DummyCollector
htcondor2.Submit = _DummySubmit
htcondor2.Negotiator = _DummyNegotiator
htcondor2.param = None
htcondor2.JobAction = _DummyJobAction
htcondor2.AdType = _DummyAdType
htcondor2.DaemonType = _DummyDaemonType
htcondor2.JobStatus = _DummyJobStatus
sys.modules["htcondor2"] = htcondor2

# Setup a dummy ``classad2`` module with placeholder classes.
classad2 = types.ModuleType("classad2")


class _DummyClassAd:
    def __init__(self, data=None):
        self._data = dict(data) if data else {}


class _DummyExprTree:
    def __init__(self, expr):
        self.expr = expr


classad2.ClassAd = _DummyClassAd
classad2.ExprTree = _DummyExprTree
sys.modules["classad2"] = classad2

# Import the FastAPI application after the dummy module is in place.
from htcondor_rest.app import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
# Fixture providing a FastAPI TestClient instance
@pytest.fixture
def client():
    """FastAPI TestClient fixture used by all tests."""
    return TestClient(app)


# Fixture that patches htcondor symbols with dummy implementations for testing
@pytest.fixture(autouse=True)
def mock_htcondor(monkeypatch):
    """Patch the ``htcondor2`` symbols used by the application.

    The fixture creates lightweight dummy implementations that mimic the
    behaviour of the real HTCondor objects. Tests can configure the dummy
    data via the class attributes ``jobs``, ``history_data``, ``nodes`` and
    ``submit_result``.
    """

    # -------------------------------------------------------------------
    # Helper classes used by the dummy HTCondor objects
    # -------------------------------------------------------------------
    class DummyJob:
        def __init__(self, data: dict):
            self._data = data

        def formatJson(self) -> str:
            return json.dumps(self._data)

        def get(self, key: str, default=None):
            return self._data.get(key, default)

    class DummySubmitResult:
        def __init__(self, cluster_id: int = 123):
            self._cluster_id = cluster_id
            self._clusterad = DummyJob({"ClusterId": cluster_id, "JobStatus": 1})

        def cluster(self) -> int:
            return self._cluster_id

        def clusterad(self) -> DummyJob:
            return self._clusterad

        def first_proc(self) -> int:
            return 0

        def num_procs(self) -> int:
            return 1

    # -------------------------------------------------------------------
    # Dummy HTCondor objects that the FastAPI routes will interact with
    # -------------------------------------------------------------------
    class DummySchedd:
        jobs: list[DummyJob] = []
        history_data: list[DummyJob] = []
        user_ads: list[DummyJob] = []
        project_ads: list[DummyJob] = []
        epoch_history: list[DummyJob] = []
        daemon_history: list[DummyJob] = []
        submit_result: DummySubmitResult = DummySubmitResult()
        spooled: DummySubmitResult | None = None
        retrieved: object = None

        def __init__(self):
            pass

        def query(self, constraint="True", projection=None, limit=-1, opts=None):
            result = self.jobs
            if constraint and "ClusterId==" in constraint:
                job_id = int(constraint.split("ClusterId==")[1])
                result = [
                    job for job in self.jobs if job._data.get("ClusterId") == job_id
                ]
            if limit is not None and limit >= 0:
                result = result[:limit]
            return result

        def queryUserAds(self, constraint="", projection=None, limit=-1):
            return self.user_ads

        def queryProjectAds(self, constraint="", projection=None, limit=-1):
            return self.project_ads

        def history(self, constraint=None, projection=None, match=-1, since=None):
            if constraint and "ClusterId==" in constraint:
                job_id = int(constraint.split("ClusterId==")[1])
                return [
                    job
                    for job in self.history_data
                    if job._data.get("ClusterId") == job_id
                ]
            return self.history_data

        def jobEpochHistory(self, constraint=None, projection=None, match=-1, since=None):
            return self.epoch_history

        def daemonHistory(self, constraint=None, projection=None, match=-1, since=None):
            return self.daemon_history

        def submit(self, job, count=1, spool=False):
            return self.submit_result

        def act(self, action, job_spec, reason=None):
            return DummyJob(
                {
                    "TotalError": 0,
                    "TotalSuccess": 1,
                    "TotalJobAds": 1,
                    "TotalChangedAds": 1,
                }
            )

        def edit(self, job_spec, attr, value, flags=None):
            return 1

        def reschedule(self):
            return None

        def export_jobs(self, job_spec, export_dir, new_spool_dir):
            return DummyJob({"Exported": True})

        def import_exported_job_results(self, import_dir):
            return DummyJob({"Imported": True})

        def unexport_jobs(self, job_spec):
            return DummyJob({"Unexported": True})

        def spool(self, result):
            type(self).spooled = result

        def retrieve(self, job_spec):
            type(self).retrieved = job_spec
            return None

        def refreshGSIProxy(self, cluster, proc, proxy_filename, lifetime=-1):
            return lifetime

        def get_claims(self, constraint=None, projection=None):
            return [DummyJob({"ClaimId": "claim-1"})]

        def create_ocu(self, request):
            return DummyJob({"OCU": "created"})

        def remove_ocu(self, request):
            return DummyJob({"OCU": "removed"})

        def query_ocu(self, request):
            return DummyJob({"OCU": "queried"})

        def addUserRec(self, user_spec):
            return DummyJob({"UserRec": "added"})

        def enableUserRec(self, user_spec):
            return DummyJob({"UserRec": "enabled"})

        def disableUserRec(self, user_spec, reason=None):
            return DummyJob({"UserRec": "disabled"})

        def removeUserRec(self, user_spec, reason=None):
            return DummyJob({"UserRec": "removed"})

        def updateUserRec(self, user_attributes):
            return DummyJob({"UserRec": "updated"})

        def addProjectRec(self, project_spec):
            return DummyJob({"ProjectRec": "added"})

        def enableProjectRec(self, project_spec):
            return DummyJob({"ProjectRec": "enabled"})

        def disableProjectRec(self, project_spec, reason=None):
            return DummyJob({"ProjectRec": "disabled"})

        def removeProjectRec(self, project_spec, reason=None):
            return DummyJob({"ProjectRec": "removed"})

        def updateProjectRec(self, project_attributes):
            return DummyJob({"ProjectRec": "updated"})

    class DummyCollector:
        nodes: list[DummyJob] = []
        located: DummyJob | None = None
        located_all: list[DummyJob] = []
        direct_queried: DummyJob = DummyJob({"MyType": "Machine"})
        advertised: object = None

        def __init__(self):
            pass

        def query(self, ad_type=None, constraint=None, projection=None, statistics=None):
            if constraint and constraint.startswith('Name == "'):
                name = constraint.split('Name == "')[1].rstrip('"')
                return [
                    node
                    for node in self.nodes
                    if node._data.get("Name") == name
                ]
            return self.nodes

        def locate(self, daemon_type, name=None):
            return self.located

        def locateAll(self, daemon_type):
            return self.located_all

        def directQuery(self, daemon_type, name=None, projection=None, statistics=None):
            return self.direct_queried

        def advertise(self, ad_list, command="UPDATE_AD_GENERIC", use_tcp=True):
            type(self).advertised = (ad_list, command, use_tcp)

    class DummySubmit:
        def __init__(self, data):
            self.data = data

    class DummyNegotiator:
        priorities: list[DummyJob] = []
        resource_usage: list[DummyJob] = []

        def __init__(self):
            pass

        def getPriorities(self, rollup=False):
            return self.priorities

        def getResourceUsage(self, user):
            return self.resource_usage

    class DummyParam:
        def __getitem__(self, key):
            if key == "UNDEFINED":
                raise KeyError(key)
            return f"value-of-{key}"

        def __iter__(self):
            return iter(["A", "B"])

        def __len__(self):
            return 2

    # -------------------------------------------------------------------
    # Apply the patches to the ``htcondor`` namespace used inside the app.
    # -------------------------------------------------------------------
    import htcondor_rest.app as app_module

    monkeypatch.setattr(app_module.htcondor, "Schedd", DummySchedd)
    monkeypatch.setattr(app_module.htcondor, "Collector", DummyCollector)
    monkeypatch.setattr(app_module.htcondor, "Submit", DummySubmit)
    monkeypatch.setattr(app_module.htcondor, "Negotiator", DummyNegotiator)
    monkeypatch.setattr(app_module.htcondor, "param", DummyParam())

    # Reset the cached metrics so every test starts from a clean slate.
    with app_module._metrics_lock:
        app_module._metrics.update(app_module._new_metrics())

    # Reset any in-memory state carried between requests.
    app_module._spooled_submit = None

    # Expose the dummy helpers to the test functions.
    return {
        "DummySchedd": DummySchedd,
        "DummyCollector": DummyCollector,
        "DummySubmitResult": DummySubmitResult,
        "DummyNegotiator": DummyNegotiator,
        "DummyJob": DummyJob,
    }


# ---------------------------------------------------------------------------
# Test cases for each API endpoint
# ---------------------------------------------------------------------------


def test_root_endpoint(client):
    """Test the root endpoint returns a status True response"""
    response = client.get("/", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json() == {"status": True}


def test_unauthorized_condor_q(client):
    """Test that accessing /condor_q without auth returns 401 Unauthorized"""
    response = client.get("/condor_q")
    assert response.status_code == 401


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/condor_status",
        "/condor_status/node1",
        "/condor_nodes",
        "/condor_spool",
        "/condor_retrieve",
        "/condor_direct_query/schedd",
        "/condor_advertise",
    ],
)
def test_all_endpoints_require_auth(client, path):
    """Test that every route, read or write, is private without a token."""
    for method in ["get", "post", "delete"]:
        response = getattr(client, method)(path)
        if response.status_code == 405:
            continue
        assert response.status_code == 401


def test_get_queue(client, mock_htcondor):
    """Test retrieving the job queue returns a list with expected job data"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.jobs = [DummyJob({"ClusterId": 123, "JobStatus": 1})]
    response = client.get("/condor_q", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["ClusterId"] == 123


def test_get_queue_constraint(client, mock_htcondor):
    """Test retrieving the job queue with a constraint filters the results"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.jobs = [
        DummyJob({"ClusterId": 123, "JobStatus": 1}),
        DummyJob({"ClusterId": 456, "JobStatus": 1}),
    ]
    response = client.get(
        "/condor_q?constraint=ClusterId==123", headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ClusterId"] == 123


def test_get_queue_limit(client, mock_htcondor):
    """Test retrieving the job queue with a limit caps the number of jobs"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.jobs = [
        DummyJob({"ClusterId": 1, "JobStatus": 1}),
        DummyJob({"ClusterId": 2, "JobStatus": 1}),
    ]
    response = client.get("/condor_q?limit=1", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_queue_by_id(client, mock_htcondor):
    """Test retrieving a specific job by ID returns the correct job"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.jobs = [DummyJob({"ClusterId": 123, "JobStatus": 1})]
    response = client.get("/condor_q/123", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["ClusterId"] == 123


def test_get_queue_not_found(client, mock_htcondor):
    """Test retrieving a non-existent job ID returns 404 Not Found"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummySchedd.jobs = []
    response = client.get("/condor_q/999", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_get_user_ads(client, mock_htcondor):
    """Test retrieving user ads returns a list with expected data"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.user_ads = [DummyJob({"Name": "user@example.com", "TotalJobs": 1})]
    response = client.get("/condor_q_user", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["Name"] == "user@example.com"


def test_get_project_ads(client, mock_htcondor):
    """Test retrieving project ads returns a list with expected data"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.project_ads = [DummyJob({"Name": "project", "TotalJobs": 1})]
    response = client.get("/condor_q_project", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["Name"] == "project"


def test_get_history(client, mock_htcondor):
    """Test retrieving job history returns a list with expected job data"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.history_data = [DummyJob({"ClusterId": 123, "JobStatus": 1})]
    response = client.get("/condor_history", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["ClusterId"] == 123


def test_get_history_by_id(client, mock_htcondor):
    """Test retrieving job history for a specific ID returns the correct job"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.history_data = [DummyJob({"ClusterId": 123, "JobStatus": 1})]
    response = client.get("/condor_history/123", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["ClusterId"] == 123


def test_get_history_not_found(client, mock_htcondor):
    """Test retrieving job history for a non-existent ID returns 404 Not Found"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummySchedd.history_data = []
    response = client.get("/condor_history/999", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_get_epoch_history(client, mock_htcondor):
    """Test retrieving job epoch history returns a list with expected data"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.epoch_history = [DummyJob({"ClusterId": 123, "JobStatus": 4})]
    response = client.get("/condor_epoch_history", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["ClusterId"] == 123


def test_get_daemon_history(client, mock_htcondor):
    """Test retrieving daemon history returns a list with expected data"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.daemon_history = [DummyJob({"ClusterId": 123, "JobStatus": 4})]
    response = client.get("/condor_daemon_history", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["ClusterId"] == 123


def test_condor_submit(client, mock_htcondor):
    """Test submitting a job returns the expected submission details"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummySubmitResult = mock_htcondor["DummySubmitResult"]
    DummySchedd.submit_result = DummySubmitResult(cluster_id=123)
    job_payload = {
        "executable": "/usr/bin/echo",
        "arguments": "Hello",
        "request_cpus": "1",
        "request_memory": "1",
        "request_disk": "1",
    }
    response = client.post("/condor_submit", json=job_payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["cluster"] == 123
    assert data["first_proc"] == 0
    assert data["num_procs"] == 1
    assert isinstance(data["clusterad"], dict)
    assert data["clusterad"]["ClusterId"] == 123


def test_condor_submit_count_defaults_to_one(client, mock_htcondor, monkeypatch):
    """Test that omitting count submits a single process"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummySubmitResult = mock_htcondor["DummySubmitResult"]
    DummySchedd.submit_result = DummySubmitResult(cluster_id=123)
    calls = {}

    def submit(self, job, count=1, spool=False):
        calls["count"] = count
        return self.submit_result

    monkeypatch.setattr(DummySchedd, "submit", submit, raising=False)
    response = client.post(
        "/condor_submit",
        json={"executable": "/usr/bin/echo"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert calls["count"] == 1


def test_condor_submit_custom_count(client, mock_htcondor, monkeypatch):
    """Test that a provided count is passed through to the schedd"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummySubmitResult = mock_htcondor["DummySubmitResult"]
    DummySchedd.submit_result = DummySubmitResult(cluster_id=123)
    calls = {}

    def submit(self, job, count=1, spool=False):
        calls["count"] = count
        return self.submit_result

    monkeypatch.setattr(DummySchedd, "submit", submit, raising=False)
    response = client.post(
        "/condor_submit",
        json={"executable": "/usr/bin/echo", "count": 5},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert calls["count"] == 5


def test_condor_submit_file(client, mock_htcondor, monkeypatch):
    """Test submitting a raw condor_submit-language description"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummySubmitResult = mock_htcondor["DummySubmitResult"]
    DummySchedd.submit_result = DummySubmitResult(cluster_id=123)
    captured = {}

    def submit(self, job, count=0, spool=False):
        captured["submit"] = job
        captured["count"] = count
        return self.submit_result

    monkeypatch.setattr(DummySchedd, "submit", submit, raising=False)
    response = client.post(
        "/condor_submit_file",
        json={"submit_text": "executable = /bin/echo\nqueue 3\n"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cluster"] == 123
    assert data["num_procs"] == 1
    assert captured["submit"].data == "executable = /bin/echo\nqueue 3\n"
    assert captured["count"] == 0


def test_condor_submit_file_invalid_text(client, mock_htcondor, monkeypatch):
    """Test that submit text the server cannot parse returns 400"""
    DummySubmitResult = mock_htcondor["DummySubmitResult"]
    import htcondor_rest.app as app_module

    def bad_submit(self, text):
        raise ValueError("parse error")

    monkeypatch.setattr(app_module.htcondor, "Submit", bad_submit, raising=False)
    response = client.post(
        "/condor_submit_file",
        json={"submit_text": "not valid"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 400


JOB_ACTION_ENDPOINTS = [
    "condor_hold",
    "condor_release",
    "condor_suspend",
    "condor_continue",
    "condor_rm",
    "condor_rmx",
    "condor_vacate",
    "condor_vacate_fast",
]


@pytest.mark.parametrize("endpoint", JOB_ACTION_ENDPOINTS)
def test_job_action_by_id(client, mock_htcondor, endpoint):
    """Test applying a job action by job ID returns the action result"""
    response = client.post(f"/{endpoint}/123", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["TotalSuccess"] == 1


@pytest.mark.parametrize("endpoint", JOB_ACTION_ENDPOINTS)
def test_job_action_by_constraint(client, mock_htcondor, endpoint):
    """Test applying a job action by constraint returns the action result"""
    response = client.post(
        f"/{endpoint}", json={"constraint": 'Owner == "bob"'}, headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    data = response.json()
    assert data["TotalSuccess"] == 1


@pytest.mark.parametrize("endpoint", JOB_ACTION_ENDPOINTS)
def test_job_action_no_spec(client, mock_htcondor, endpoint):
    """Test applying a job action without a job ID or constraint returns 400"""
    response = client.post(f"/{endpoint}", headers=AUTH_HEADERS)
    assert response.status_code == 400


@pytest.mark.parametrize("endpoint", JOB_ACTION_ENDPOINTS)
def test_unauthorized_job_action(client, endpoint):
    """Test that job actions without auth return 401 Unauthorized"""
    response = client.post(f"/{endpoint}/123")
    assert response.status_code == 401


def test_condor_status(client, mock_htcondor):
    """Test retrieving condor status returns a list of node information"""
    DummyCollector = mock_htcondor["DummyCollector"]
    DummyJob = mock_htcondor["DummyJob"]
    DummyCollector.nodes = [DummyJob({"Name": "node1"})]
    response = client.get("/condor_status", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["Name"] == "node1"


def test_condor_status_by_name(client, mock_htcondor):
    """Test retrieving condor status for a specific name returns the ad"""
    DummyCollector = mock_htcondor["DummyCollector"]
    DummyJob = mock_htcondor["DummyJob"]
    DummyCollector.nodes = [
        DummyJob({"Name": "node1", "MyType": "Machine"}),
        DummyJob({"Name": "node2", "MyType": "Machine"}),
    ]
    response = client.get("/condor_status/node1", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["Name"] == "node1"


def test_condor_status_by_name_not_found(client, mock_htcondor):
    """Test retrieving condor status for a missing name returns 404"""
    DummyCollector = mock_htcondor["DummyCollector"]
    DummyCollector.nodes = []
    response = client.get("/condor_status/nonexistent", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_condor_status_bad_ad_type(client, mock_htcondor):
    """Test that an unknown ad type returns 400"""
    response = client.get("/condor_status?ad_type=bogus", headers=AUTH_HEADERS)
    assert response.status_code == 400


def test_condor_nodes(client, mock_htcondor):
    """Test retrieving condor nodes returns a list of node information"""
    DummyCollector = mock_htcondor["DummyCollector"]
    DummyJob = mock_htcondor["DummyJob"]
    DummyCollector.nodes = [DummyJob({"Name": "node2"})]
    response = client.get("/condor_nodes", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["Name"] == "node2"


def test_condor_locate(client, mock_htcondor):
    """Test locating a daemon returns its ad"""
    DummyCollector = mock_htcondor["DummyCollector"]
    DummyJob = mock_htcondor["DummyJob"]
    DummyCollector.located = DummyJob({"Name": "schedd@host", "MyAddress": "<...>"})
    response = client.get("/condor_locate/schedd", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["Name"] == "schedd@host"


def test_condor_locate_not_found(client, mock_htcondor):
    """Test locating a missing daemon returns 404"""
    DummyCollector = mock_htcondor["DummyCollector"]
    DummyCollector.located = None
    response = client.get("/condor_locate/schedd", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_condor_locate_bad_type(client, mock_htcondor):
    """Test that an unknown daemon type returns 400"""
    response = client.get("/condor_locate/bogus", headers=AUTH_HEADERS)
    assert response.status_code == 400


def test_condor_locate_all(client, mock_htcondor):
    """Test locating all daemons of a type returns a list of ads"""
    DummyCollector = mock_htcondor["DummyCollector"]
    DummyJob = mock_htcondor["DummyJob"]
    DummyCollector.located_all = [
        DummyJob({"Name": "schedd@host1"}),
        DummyJob({"Name": "schedd@host2"}),
    ]
    response = client.get("/condor_locate_all/schedd", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_condor_config(client, mock_htcondor):
    """Test retrieving the condor config returns all parameters"""
    response = client.get("/condor_config", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data == {"A": "value-of-A", "B": "value-of-B"}


def test_condor_config_attribute(client, mock_htcondor):
    """Test retrieving a single condor config attribute"""
    response = client.get("/condor_config/CONDOR_HOST", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json() == "value-of-CONDOR_HOST"


def test_condor_config_attribute_not_found(client, mock_htcondor):
    """Test retrieving an undefined config attribute returns 404"""
    response = client.get("/condor_config/UNDEFINED", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_condor_userprio(client, mock_htcondor):
    """Test retrieving user priorities returns a list of ads"""
    DummyNegotiator = mock_htcondor["DummyNegotiator"]
    DummyJob = mock_htcondor["DummyJob"]
    DummyNegotiator.priorities = [
        DummyJob({"User": "user@example.com", "Priority": 1.0})
    ]
    response = client.get("/condor_userprio", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["User"] == "user@example.com"


def test_condor_userprio_user(client, mock_htcondor):
    """Test retrieving resource usage for a specific user"""
    DummyNegotiator = mock_htcondor["DummyNegotiator"]
    DummyJob = mock_htcondor["DummyJob"]
    DummyNegotiator.resource_usage = [
        DummyJob({"User": "user@example.com", "WeightedResources": 10})
    ]
    response = client.get("/condor_userprio/user@example.com", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data[0]["WeightedResources"] == 10


def test_condor_edit(client, mock_htcondor):
    """Test editing a job attribute returns the number of edited jobs"""
    response = client.post(
        "/condor_edit",
        json={"job_ids": ["123"], "attr": "JobPrio", "value": "5"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == 1


def test_condor_reschedule(client, mock_htcondor):
    """Test requesting a reschedule returns True"""
    response = client.post("/condor_reschedule", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json() is True


def test_condor_export_jobs(client, mock_htcondor):
    """Test exporting jobs returns the export result"""
    response = client.post(
        "/condor_export_jobs",
        json={"job_ids": ["123"], "export_dir": "/tmp", "new_spool_dir": "/spool"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == {"Exported": True}


def test_condor_import_exported_job_results(client, mock_htcondor):
    """Test importing exported job results returns the import result"""
    response = client.post(
        "/condor_import_exported_job_results",
        json={"import_dir": "/tmp"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == {"Imported": True}


def test_condor_unexport_jobs(client, mock_htcondor):
    """Test unexporting jobs returns the unexport result"""
    response = client.post(
        "/condor_unexport_jobs",
        json={"constraint": "ClusterId==123"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == {"Unexported": True}


def test_condor_rm(client, mock_htcondor, monkeypatch):
    """Test removing a job returns the expected job data"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]

    # Define a dummy act method that returns a DummyJob with the given job_id
    def act(self, job_action, job_ids):
        job_id = int(job_ids[0])
        return DummyJob({"ClusterId": job_id, "JobStatus": 5})

    monkeypatch.setattr(DummySchedd, "act", act, raising=False)
    response = client.delete("/condor_rm/123", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data


def test_unauthorized_condor_rm(client):
    """Test that accessing /condor_rm without auth returns 401 Unauthorized"""
    response = client.delete("/condor_rm/123")
    assert response.status_code == 401


def test_metrics_endpoint_public(client, mock_htcondor):
    """Test that /metrics is public and returns empty metrics by default"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummySchedd.jobs = []
    DummySchedd.history_data = []
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    assert 'htcondor_queue_jobs{status="idle"} 0' in body
    assert 'htcondor_history_jobs{result="completed",window="all"} 0' in body
    assert 'htcondor_history_jobs{result="failed",window="all"} 0' in body
    assert "htcondor_metrics_up 1" in body


def test_metrics_queue_counts(client, mock_htcondor):
    """Test that condor_q job statuses are aggregated correctly"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.jobs = [
        DummyJob({"JobStatus": 1}),
        DummyJob({"JobStatus": 1}),
        DummyJob({"JobStatus": 2}),
        DummyJob({"JobStatus": 5}),
    ]
    DummySchedd.history_data = []
    body = client.get("/metrics").text
    assert 'htcondor_queue_jobs{status="idle"} 2' in body
    assert 'htcondor_queue_jobs{status="running"} 1' in body
    assert 'htcondor_queue_jobs{status="held"} 1' in body
    assert 'htcondor_queue_jobs{status="completed"} 0' in body


def test_metrics_history_counts(client, mock_htcondor):
    """Test that condor_history results are aggregated by result and window"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.jobs = []
    now = time.time()
    DummySchedd.history_data = [
        DummyJob({"JobStatus": 4, "ExitStatus": 0, "CompletionDate": now - 3600}),
        DummyJob({"JobStatus": 4, "ExitStatus": 0, "CompletionDate": now - 3 * 86400}),
        DummyJob({"JobStatus": 4, "ExitStatus": 1, "CompletionDate": now - 3600}),
        DummyJob({"JobStatus": 3, "ExitStatus": 0}),
        DummyJob({"JobStatus": 4, "ExitStatus": 0}),
    ]
    body = client.get("/metrics").text
    assert 'htcondor_history_jobs{result="completed",window="all"} 3' in body
    assert 'htcondor_history_jobs{result="completed",window="24h"} 1' in body
    assert 'htcondor_history_jobs{result="completed",window="7d"} 2' in body
    assert 'htcondor_history_jobs{result="failed",window="all"} 1' in body
    assert 'htcondor_history_jobs{result="failed",window="24h"} 1' in body


def test_condor_spool(client, mock_htcondor):
    """Test spooling a previously spooled submit uploads its input files"""
    DummySchedd = mock_htcondor["DummySchedd"]
    response = client.post(
        "/condor_submit",
        json={"executable": "/bin/echo", "spool": True},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    response = client.post("/condor_spool", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json() == {"cluster": 123}
    assert DummySchedd.spooled is not None


def test_condor_spool_without_prior_submit(client, mock_htcondor):
    """Test that /condor_spool without a prior spooled submit returns 400"""
    response = client.post("/condor_spool", headers=AUTH_HEADERS)
    assert response.status_code == 400


def test_condor_retrieve(client, mock_htcondor):
    """Test retrieving output files for a set of jobs"""
    DummySchedd = mock_htcondor["DummySchedd"]
    response = client.post(
        "/condor_retrieve",
        json={"job_ids": ["123.0", "123.1"]},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() is True
    assert DummySchedd.retrieved == ["123.0", "123.1"]


def test_condor_retrieve_requires_spec(client, mock_htcondor):
    """Test that /condor_retrieve without a spec returns 400"""
    response = client.post("/condor_retrieve", json={}, headers=AUTH_HEADERS)
    assert response.status_code == 400


def test_condor_refresh_gsi_proxy(client, mock_htcondor):
    """Test refreshing a job's GSI proxy returns the remaining lifetime"""
    response = client.post(
        "/condor_refresh_gsi_proxy",
        json={"cluster": 123, "proc": 0, "proxy_filename": "/tmp/proxy", "lifetime": 60},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == 60


def test_condor_claims(client, mock_htcondor):
    """Test querying the schedd for claimed-slot classads"""
    response = client.get(
        "/condor_claims", params={"constraint": "Owner == \"bob\""}, headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    assert response.json() == [{"ClaimId": "claim-1"}]


def test_condor_ocu_claims(client, mock_htcondor):
    """Test creating, querying and removing OCU claims"""
    for route, expected in [
        ("create_ocu", {"OCU": "created"}),
        ("query_ocu", {"OCU": "queried"}),
        ("remove_ocu", {"OCU": "removed"}),
    ]:
        response = client.post(
            f"/condor_{route}",
            json={"request": {"Owner": "bob", "RequestCpus": 2}},
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        assert response.json() == expected


def test_user_rec_actions(client, mock_htcondor):
    """Test acting on user accounting records by name and by constraint"""
    for route, expected in [
        ("add_user_rec", {"UserRec": "added"}),
        ("enable_user_rec", {"UserRec": "enabled"}),
    ]:
        response = client.post(
            f"/condor_{route}", json={"spec": "bob@example.com"}, headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        assert response.json() == expected
    for route, expected in [
        ("disable_user_rec", {"UserRec": "disabled"}),
        ("remove_user_rec", {"UserRec": "removed"}),
    ]:
        response = client.post(
            f"/condor_{route}",
            json={"spec": "bob@example.com", "reason": "maintenance"},
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        assert response.json() == expected
    response = client.post(
        "/condor_enable_user_rec",
        json={"constraint": 'Name == "bob@example.com"'},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == {"UserRec": "enabled"}


def test_project_rec_actions(client, mock_htcondor):
    """Test acting on project accounting records"""
    for route, expected in [
        ("add_project_rec", {"ProjectRec": "added"}),
        ("enable_project_rec", {"ProjectRec": "enabled"}),
        ("disable_project_rec", {"ProjectRec": "disabled"}),
        ("remove_project_rec", {"ProjectRec": "removed"}),
    ]:
        response = client.post(
            f"/condor_{route}", json={"spec": "project-1"}, headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        assert response.json() == expected


def test_rec_action_requires_spec(client, mock_htcondor):
    """Test that rec actions without spec or constraint return 400"""
    response = client.post("/condor_add_user_rec", json={}, headers=AUTH_HEADERS)
    assert response.status_code == 400
    response = client.post(
        "/condor_add_user_rec",
        json={"spec": "bob", "constraint": "Name == \"bob\""},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 400


def test_rec_updates(client, mock_htcondor):
    """Test updating user and project accounting records"""
    response = client.post(
        "/condor_update_user_rec",
        json={"ads": [{"User": "bob", "Usage": 10}]},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == {"UserRec": "updated"}
    response = client.post(
        "/condor_update_project_rec",
        json={"ads": [{"Name": "project-1", "Usage": 10}]},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == {"ProjectRec": "updated"}


def test_condor_direct_query(client, mock_htcondor):
    """Test directly querying a daemon (bypassing the collector)"""
    response = client.get(
        "/condor_direct_query/schedd", params={"name": "schedd@host"}, headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    assert response.json() == {"MyType": "Machine"}


def test_condor_direct_query_bad_type(client, mock_htcondor):
    """Test that an unknown daemon type returns 400"""
    response = client.get("/condor_direct_query/bogus", headers=AUTH_HEADERS)
    assert response.status_code == 400


def test_condor_advertise(client, mock_htcondor):
    """Test advertising classads to the collector"""
    DummyCollector = mock_htcondor["DummyCollector"]
    response = client.post(
        "/condor_advertise",
        json={
            "ads": [{"MyType": "Generic", "Name": "custom"}],
            "command": "UPDATE_AD_GENERIC",
            "use_tcp": True,
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() is True
    ad_list, command, use_tcp = DummyCollector.advertised
    assert command == "UPDATE_AD_GENERIC"
    assert use_tcp is True
    assert ad_list[0]._data == {"MyType": "Generic", "Name": "custom"}
