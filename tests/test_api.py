import sys
import types
import json
import pytest
from fastapi.testclient import TestClient

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


# Dummy JobAction to mimic htcondor.JobAction enum
class _DummyJobAction:
    Remove = "Remove"


htcondor2.Schedd = _DummySchedd
htcondor2.Collector = _DummyCollector
htcondor2.Submit = _DummySubmit
htcondor2.JobAction = _DummyJobAction
sys.modules["htcondor2"] = htcondor2

# Setup a dummy ``classad2`` module with a placeholder ``ClassAd`` class.
classad2 = types.ModuleType("classad2")


class ClassAd:
    pass


classad2.ClassAd = ClassAd
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
        submit_result: DummySubmitResult = DummySubmitResult()

        def __init__(self):
            pass

        def query(self, constraint: str | None = None):
            if constraint:
                job_id = int(constraint.split("==")[1])
                return [
                    job for job in self.jobs if job._data.get("ClusterId") == job_id
                ]
            return self.jobs

        def history(self, constraint: str | None = None):
            if constraint:
                job_id = int(constraint.split("==")[1])
                return [
                    job
                    for job in self.history_data
                    if job._data.get("ClusterId") == job_id
                ]
            return self.history_data

        def submit(self, job, count: int = 1):
            return self.submit_result

    class DummyCollector:
        nodes: list[DummyJob] = []

        def __init__(self):
            pass

        def query(self, constraint: str | None = None):
            return self.nodes

    class DummySubmit:
        def __init__(self, data):
            self.data = data

    # -------------------------------------------------------------------
    # Apply the patches to the ``htcondor`` namespace used inside the app.
    # -------------------------------------------------------------------
    import htcondor_rest.app as app_module

    monkeypatch.setattr(app_module.htcondor, "Schedd", DummySchedd)
    monkeypatch.setattr(app_module.htcondor, "Collector", DummyCollector)
    monkeypatch.setattr(app_module.htcondor, "Submit", DummySubmit)

    # Expose the dummy helpers to the test functions.
    return {
        "DummySchedd": DummySchedd,
        "DummyCollector": DummyCollector,
        "DummySubmitResult": DummySubmitResult,
        "DummyJob": DummyJob,
    }


# ---------------------------------------------------------------------------
# Test cases for each API endpoint
# ---------------------------------------------------------------------------


def test_root_endpoint(client):
    """Test the root endpoint returns a status True response"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": True}


def test_unauthorized_condor_q(client):
    """Test that accessing /condor_q without auth returns 401 Unauthorized"""
    response = client.get("/condor_q")
    assert response.status_code == 401


def test_get_queue(client, mock_htcondor):
    """Test retrieving the job queue returns a list with expected job data"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.jobs = [DummyJob({"ClusterId": 123, "JobStatus": 1})]
    response = client.get("/condor_q", headers={"Authorization": "Bearer password"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["ClusterId"] == 123


def test_get_queue_by_id(client, mock_htcondor):
    """Test retrieving a specific job by ID returns the correct job"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.jobs = [DummyJob({"ClusterId": 123, "JobStatus": 1})]
    response = client.get("/condor_q/123", headers={"Authorization": "Bearer password"})
    assert response.status_code == 200
    data = response.json()
    assert data["ClusterId"] == 123


def test_get_queue_not_found(client, mock_htcondor):
    """Test retrieving a non-existent job ID returns 404 Not Found"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummySchedd.jobs = []
    response = client.get("/condor_q/999", headers={"Authorization": "Bearer password"})
    assert response.status_code == 404


def test_get_history(client, mock_htcondor):
    """Test retrieving job history returns a list with expected job data"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.history_data = [DummyJob({"ClusterId": 123, "JobStatus": 1})]
    response = client.get(
        "/condor_history", headers={"Authorization": "Bearer password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["ClusterId"] == 123


def test_get_history_by_id(client, mock_htcondor):
    """Test retrieving job history for a specific ID returns the correct job"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]
    DummySchedd.history_data = [DummyJob({"ClusterId": 123, "JobStatus": 1})]
    response = client.get(
        "/condor_history/123", headers={"Authorization": "Bearer password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ClusterId"] == 123


def test_get_history_not_found(client, mock_htcondor):
    """Test retrieving job history for a non-existent ID returns 404 Not Found"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummySchedd.history_data = []
    response = client.get(
        "/condor_history/999", headers={"Authorization": "Bearer password"}
    )
    assert response.status_code == 404


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
    response = client.post(
        "/condor_submit", json=job_payload, headers={"Authorization": "Bearer password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cluster"] == 123
    assert data["first_proc"] == 0
    assert data["num_procs"] == 1
    assert isinstance(data["clusterad"], dict)
    assert data["clusterad"]["ClusterId"] == 123


def test_condor_status(client, mock_htcondor):
    """Test retrieving condor status returns a list of node information"""
    DummyCollector = mock_htcondor["DummyCollector"]
    DummyJob = mock_htcondor["DummyJob"]
    DummyCollector.nodes = [DummyJob({"Name": "node1"})]
    response = client.get(
        "/condor_status", headers={"Authorization": "Bearer password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["Name"] == "node1"


def test_condor_nodes(client, mock_htcondor):
    """Test retrieving condor nodes returns a list of node information"""
    DummyCollector = mock_htcondor["DummyCollector"]
    DummyJob = mock_htcondor["DummyJob"]
    DummyCollector.nodes = [DummyJob({"Name": "node2"})]
    response = client.get("/condor_nodes", headers={"Authorization": "Bearer password"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["Name"] == "node2"


def test_condor_rm(client, mock_htcondor, monkeypatch):
    """Test removing a job returns the expected job data"""
    DummySchedd = mock_htcondor["DummySchedd"]
    DummyJob = mock_htcondor["DummyJob"]

    # Define a dummy act method that returns a DummyJob with the given job_id
    def act(self, job_action, job_ids):
        job_id = int(job_ids[0])
        return DummyJob({"ClusterId": job_id, "JobStatus": 5})

    monkeypatch.setattr(DummySchedd, "act", act, raising=False)
    response = client.delete(
        "/condor_rm/123", headers={"Authorization": "Bearer password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ClusterId"] == 123


def test_unauthorized_condor_rm(client):
    """Test that accessing /condor_rm without auth returns 401 Unauthorized"""
    response = client.delete("/condor_rm/123")
    assert response.status_code == 401
