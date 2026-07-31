import json

import pytest

import htcondor_rest.cli as cli


class FakeCondorClient:
    """Records calls so the CLI tests can assert on what the client sees."""

    def __init__(self, **kwargs):
        self.calls = []
        self.url = kwargs.get("base_url")
        self.token = kwargs.get("token")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def submit(self, job):
        self.calls.append(("submit", job))
        return {"cluster": 123, "num_procs": 3}

    def submit_file(self, submit_text, count=0, spool=False):
        self.calls.append(("submit_file", submit_text, count, spool))
        return {"cluster": 123, "num_procs": 3}

    def get_queue(self, job_id=None, constraint=None, projection=None, limit=-1):
        self.calls.append(("get_queue", job_id, constraint, projection, limit))
        return [{"ClusterId": 123, "JobStatus": 1}]

    def get_history(self, job_id=None, constraint=None, projection=None, match=-1, since=None):
        self.calls.append(("get_history", job_id, constraint, projection, match, since))
        return [{"ClusterId": 123, "JobStatus": 4}]

    def get_status(self, ad_type="any", constraint=None, projection=None):
        self.calls.append(("get_status", ad_type, constraint, projection))
        return [{"MyType": "Machine", "Name": "slot1@host"}]

    def get_status_by_name(self, name, ad_type="any", constraint=None, projection=None):
        self.calls.append(("get_status_by_name", name, ad_type, constraint, projection))
        return {"MyType": "Machine", "Name": name}

    def remove(self, job_ids=None, constraint=None, reason=None):
        self.calls.append(("remove", job_ids, constraint, reason))
        return {"TotalSuccess": 1}

    def hold(self, job_ids=None, constraint=None, reason=None):
        self.calls.append(("hold", job_ids, constraint, reason))
        return {"TotalSuccess": 1}

    def release(self, job_ids=None, constraint=None, reason=None):
        self.calls.append(("release", job_ids, constraint, reason))
        return {"TotalSuccess": 1}


@pytest.fixture
def fake(monkeypatch):
    fake_client = FakeCondorClient()

    def factory(**kwargs):
        fake_client.url = kwargs.get("base_url")
        fake_client.token = kwargs.get("token")
        return fake_client

    monkeypatch.setattr(cli, "CondorClient", factory)
    return fake_client


# ---------------------------------------------------------------------------
# condor_submit
# ---------------------------------------------------------------------------
def test_condor_submit_cli(tmp_path, fake, capsys):
    path = tmp_path / "submit"
    path.write_text("executable = /bin/echo\nqueue 3\n")
    cli.condor_submit_cli(path)
    assert fake.calls == [("submit_file", "executable = /bin/echo\nqueue 3\n", 0, False)]
    out = capsys.readouterr().out
    assert json.loads(out) == {"cluster": 123, "num_procs": 3}


def test_condor_submit_uses_url_and_token(tmp_path, fake):
    path = tmp_path / "submit"
    path.write_text("executable = /bin/echo\n")
    cli.condor_submit_cli(path, url="http://example:8008", token="secret")
    assert fake.url == "http://example:8008"
    assert fake.token == "secret"


# ---------------------------------------------------------------------------
# condor_q
# ---------------------------------------------------------------------------
def test_condor_q_cli(fake, capsys):
    cli.condor_q_cli(None, constraint=None, projection=None, limit=-1, )
    assert fake.calls == [("get_queue", None, None, None, -1)]
    out = capsys.readouterr().out
    assert json.loads(out) == [{"ClusterId": 123, "JobStatus": 1}]


def test_condor_q_cli_by_cluster(fake):
    cli.condor_q_cli("123", constraint=None, projection=None, limit=-1, )
    assert fake.calls == [("get_queue", 123, None, None, -1)]


def test_condor_q_cli_by_proc(fake):
    cli.condor_q_cli("123.0", constraint=None, projection=None, limit=-1, )
    assert fake.calls == [
        (
            "get_queue",
            None,
            "(ClusterId == 123 && ProcID == 0)",
            None,
            -1,
        )
    ]


def test_condor_q_cli_passes_constraint(fake):
    cli.condor_q_cli(None, constraint='Owner == "bob"', projection="ClusterId", limit=5, )
    assert fake.calls == [("get_queue", None, 'Owner == "bob"', "ClusterId", 5)]


# ---------------------------------------------------------------------------
# condor_rm
# ---------------------------------------------------------------------------
def test_condor_rm_cli(fake, capsys):
    cli.condor_rm_cli("123.0", reason=None, )
    assert fake.calls == [("remove", ["123.0"], None, None)]
    assert json.loads(capsys.readouterr().out) == {"TotalSuccess": 1}


def test_condor_rm_cli_with_reason(fake):
    cli.condor_rm_cli("123", reason="no longer needed", )
    assert fake.calls == [("remove", ["123"], None, "no longer needed")]


# ---------------------------------------------------------------------------
# condor_history / condor_status / condor_hold / condor_release
# ---------------------------------------------------------------------------
def test_condor_history_cli(fake):
    cli.condor_history_cli(None, constraint=None, projection=None, match=-1, since=None, )
    assert fake.calls == [("get_history", None, None, None, -1, None)]


def test_condor_history_cli_by_proc(fake):
    cli.condor_history_cli("123.0", constraint=None, projection=None, match=-1, since=None, )
    assert fake.calls == [
        ("get_history", None, "(ClusterId == 123 && ProcID == 0)", None, -1, None)
    ]


def test_condor_status_cli(fake, capsys):
    cli.condor_status_cli(None, ad_type="any", constraint=None, projection=None, )
    assert fake.calls == [("get_status", "any", None, None)]
    assert json.loads(capsys.readouterr().out)[0]["Name"] == "slot1@host"


def test_condor_status_cli_by_name(fake):
    cli.condor_status_cli("slot1@host", ad_type="slot", constraint=None, projection=None, )
    assert fake.calls == [
        ("get_status_by_name", "slot1@host", "slot", None, None)
    ]


def test_condor_hold_cli(fake):
    cli.condor_hold_cli("123.0", constraint=None, reason="testing", )
    assert fake.calls == [("hold", ["123.0"], None, "testing")]


def test_condor_release_cli_by_constraint(fake):
    cli.condor_release_cli(None, constraint='Owner == "bob"', reason=None, )
    assert fake.calls == [("release", None, 'Owner == "bob"', None)]


def test_condor_hold_cli_requires_spec(fake):
    with pytest.raises(Exception):
        cli.condor_hold_cli(None, constraint=None, reason=None, )
