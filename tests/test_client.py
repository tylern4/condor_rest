import json

import httpx
import pytest

from htcondor_rest.client import CondorClient


@pytest.fixture
def condor_client():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        path = request.url.path
        if request.method == "GET" and path == "/":
            return httpx.Response(200, json={"status": True})
        if request.method == "GET" and path == "/condor_q":
            return httpx.Response(200, json=[{"ClusterId": 123, "JobStatus": 1}])
        if request.method == "GET" and path.startswith("/condor_q/"):
            return httpx.Response(200, json={"ClusterId": 123, "JobStatus": 1})
        if request.method == "POST" and path == "/condor_submit":
            return httpx.Response(200, json={"cluster": 123, "num_procs": 1})
        if request.method == "POST" and path == "/condor_submit_file":
            return httpx.Response(200, json={"cluster": 123, "num_procs": 3})
        if request.method == "POST" and path == "/condor_edit":
            return httpx.Response(200, json=1)
        if request.method == "POST" and path == "/condor_spool":
            return httpx.Response(200, json={"cluster": 123})
        if request.method == "POST" and path == "/condor_refresh_gsi_proxy":
            return httpx.Response(200, json=60)
        if request.method == "POST" and path.startswith("/condor_"):
            return httpx.Response(200, json={"TotalSuccess": 1})
        if request.method == "GET" and path == "/condor_claims":
            return httpx.Response(200, json=[{"ClaimId": "claim-1"}])
        if request.method == "GET" and path.startswith("/condor_direct_query/"):
            return httpx.Response(200, json={"MyType": "Machine"})
        if request.method == "DELETE" and path == "/condor_rm/9":
            return httpx.Response(200, json=True)
        if path == "/metrics":
            return httpx.Response(
                200,
                text="# HELP test metric\n# TYPE test gauge\ntest 1\n",
                headers={"content-type": "text/plain"},
            )
        return httpx.Response(404, json={"detail": "not found"})

    client = CondorClient(
        base_url="http://test",
        token="password",
        transport=httpx.MockTransport(handler),
    )
    return client, calls


def test_health(condor_client):
    client, calls = condor_client
    assert client.health() is True
    assert calls[-1].url.path == "/"


def test_submit_sends_bearer_and_json(condor_client):
    client, calls = condor_client
    result = client.submit({"executable": "/usr/bin/echo", "count": 2})
    assert result["cluster"] == 123
    request = calls[-1]
    assert request.method == "POST"
    assert request.url.path == "/condor_submit"
    assert request.headers["Authorization"] == "Bearer password"
    assert json.loads(request.content) == {"executable": "/usr/bin/echo", "count": 2}


def test_submit_file(condor_client):
    client, calls = condor_client
    result = client.submit_file("executable = /bin/echo\nqueue 3\n", count=3)
    assert result["cluster"] == 123
    assert result["num_procs"] == 3
    request = calls[-1]
    assert request.url.path == "/condor_submit_file"
    assert json.loads(request.content) == {
        "submit_text": "executable = /bin/echo\nqueue 3\n",
        "count": 3,
        "spool": False,
    }


def test_get_queue_builds_query_params(condor_client):
    client, calls = condor_client
    client.get_queue(constraint='Owner == "bob"', projection="ClusterId,JobStatus", limit=10)
    request = calls[-1]
    assert request.url.path == "/condor_q"
    assert request.url.params["constraint"] == 'Owner == "bob"'
    assert request.url.params["projection"] == "ClusterId,JobStatus"
    assert request.url.params["limit"] == "10"


def test_get_queue_by_id(condor_client):
    client, calls = condor_client
    client.get_queue(job_id=42)
    assert calls[-1].url.path == "/condor_q/42"


def test_hold_by_id(condor_client):
    client, calls = condor_client
    result = client.hold(job_id=123)
    assert result == {"TotalSuccess": 1}
    request = calls[-1]
    assert request.method == "POST"
    assert request.url.path == "/condor_hold/123"
    assert request.content == b""


def test_hold_by_constraint(condor_client):
    client, calls = condor_client
    client.hold(constraint='Owner == "bob"', reason="maintenance")
    request = calls[-1]
    assert request.url.path == "/condor_hold"
    assert json.loads(request.content) == {
        "constraint": 'Owner == "bob"',
        "reason": "maintenance",
    }


def test_remove_by_job_ids(condor_client):
    client, calls = condor_client
    client.remove(job_ids=["123.0", "123.1"])
    request = calls[-1]
    assert request.url.path == "/condor_rm"
    assert json.loads(request.content) == {"job_ids": ["123.0", "123.1"]}


def test_delete_job(condor_client):
    client, calls = condor_client
    assert client.delete_job(9) is True
    assert calls[-1].method == "DELETE"
    assert calls[-1].url.path == "/condor_rm/9"


def test_edit_requires_spec(condor_client):
    client, _ = condor_client
    with pytest.raises(ValueError):
        client.edit(attr="JobPriority", value="10")


def test_edit(condor_client):
    client, calls = condor_client
    result = client.edit(attr="JobPriority", value="10", job_ids=["1.0"])
    assert result == 1
    assert json.loads(calls[-1].content) == {"attr": "JobPriority", "value": "10", "job_ids": ["1.0"]}


def test_metrics_returns_text(condor_client):
    client, calls = condor_client
    body = client.get_metrics()
    assert body.startswith("# HELP test")
    assert calls[-1].url.path == "/metrics"


def test_error_status_raises(condor_client):
    client, _ = condor_client
    with pytest.raises(httpx.HTTPStatusError):
        client.get_config()


def test_spool(condor_client):
    client, calls = condor_client
    assert client.spool() == {"cluster": 123}
    assert calls[-1].url.path == "/condor_spool"


def test_retrieve(condor_client):
    client, calls = condor_client
    assert client.retrieve(job_ids=["123.0"]) is True
    assert json.loads(calls[-1].content) == {"job_ids": ["123.0"]}
    with pytest.raises(ValueError):
        client.retrieve()


def test_refresh_gsi_proxy(condor_client):
    client, calls = condor_client
    assert client.refresh_gsi_proxy(123, 0, "/tmp/proxy", lifetime=60) == 60
    assert json.loads(calls[-1].content) == {
        "cluster": 123,
        "proc": 0,
        "proxy_filename": "/tmp/proxy",
        "lifetime": 60,
    }


def test_get_claims(condor_client):
    client, calls = condor_client
    result = client.get_claims(constraint='Owner == "bob"', projection="ClaimId")
    assert result == [{"ClaimId": "claim-1"}]
    assert calls[-1].url.path == "/condor_claims"
    assert calls[-1].url.params["constraint"] == 'Owner == "bob"'


def test_ocu_actions(condor_client):
    client, calls = condor_client
    request = {"Owner": "bob", "RequestCpus": 2}
    for method in [client.create_ocu, client.remove_ocu, client.query_ocu]:
        assert method(request) == {"TotalSuccess": 1}
    assert json.loads(calls[-1].content) == {"request": request}
    assert calls[-1].url.path == "/condor_query_ocu"


def test_user_rec_actions(condor_client):
    client, calls = condor_client
    assert client.add_user_rec(spec=["a@h", "b@h"]) == {"TotalSuccess": 1}
    assert calls[-1].url.path == "/condor_add_user_rec"
    assert json.loads(calls[-1].content) == {"spec": ["a@h", "b@h"]}
    client.disable_user_rec(constraint='Name == "a@h"', reason="gone")
    assert json.loads(calls[-1].content) == {
        "constraint": 'Name == "a@h"',
        "reason": "gone",
    }
    with pytest.raises(ValueError):
        client.enable_user_rec()


def test_update_recs(condor_client):
    client, calls = condor_client
    client.update_user_rec([{"User": "bob", "Usage": 10}])
    assert json.loads(calls[-1].content) == {"ads": [{"User": "bob", "Usage": 10}]}
    assert calls[-1].url.path == "/condor_update_user_rec"
    client.update_project_rec([{"Name": "p1"}])
    assert calls[-1].url.path == "/condor_update_project_rec"


def test_project_rec_actions(condor_client):
    client, calls = condor_client
    client.add_project_rec(spec="project-1")
    assert calls[-1].url.path == "/condor_add_project_rec"
    assert json.loads(calls[-1].content) == {"spec": "project-1"}


def test_direct_query(condor_client):
    client, calls = condor_client
    result = client.direct_query("schedd", name="schedd@host", projection="MyType")
    assert result == {"MyType": "Machine"}
    assert calls[-1].url.path == "/condor_direct_query/schedd"
    assert calls[-1].url.params["name"] == "schedd@host"


def test_advertise(condor_client):
    client, calls = condor_client
    assert client.advertise([{"MyType": "Generic"}]) is True
    assert json.loads(calls[-1].content) == {
        "ads": [{"MyType": "Generic"}],
        "command": "UPDATE_AD_GENERIC",
        "use_tcp": True,
    }
