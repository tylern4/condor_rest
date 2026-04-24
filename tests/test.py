from httpx import Client
from pydantic import AnyUrl
import json
import os
import time

CONDOR_URL = os.getenv("CONDOR_URL", "http://localhost:8008")
CONDOR_PASS = os.getenv("CONDOR_PASS", "password")


class CondorClient:
    def __init__(
        self,
        base_url: AnyUrl = CONDOR_URL,
    ):
        self._client = Client(
            base_url=f"{base_url}", headers={"Authorization": f"Bearer {CONDOR_PASS}"}
        )

    def submit_job(self):
        job = {
            "arguments": "20",
            "error": "/tmp/err",
            "executable": "/usr/bin/sleep",
            "log": "/tmp/log",
            "output": "/tmp/out",
            "request_cpus": "1",
            "request_disk": "1",
            "request_memory": "1",
        }
        response = self._client.post("/condor_submit", json=job)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return response.content.decode()

    def get_queue(self, job_id: int | None = None):
        url = f"/condor_q/{job_id}" if job_id else "/condor_q"
        response = self._client.get(url)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return response.content.decode()

    def get_history(self, job_id: int | None = None):
        url = f"/condor_history/{job_id}" if job_id else "/condor_history"
        response = self._client.get(url)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return response.content.decode()


def main():
    condor = CondorClient()

    job = condor.submit_job()
    print(json.dumps(job, indent=4))
    job_id = job["cluster"]
    queue = condor.get_queue()
    print(json.dumps(queue, indent=4))
    queue = condor.get_queue(job_id=job_id)
    print(json.dumps(queue, indent=4))
    for _ in range(2):
        time.sleep(20)
        history = condor.get_history()
        print(json.dumps(history, indent=4))
        history = condor.get_history(job_id=job_id)
        print(json.dumps(history, indent=4))


if __name__ == "__main__":
    main()
