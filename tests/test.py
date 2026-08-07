import json

from htcondor_rest.client import CondorClient


def main():
    with CondorClient() as condor:
        job_submit = {
            "jobbatchname": "job_name",
            "iwd": "/scratch/execution",
            "+Owner": "UNDEFINED",
            "request_memory": "1",
            "request_disk": "1",
            "request_cpus": "1",
            "request_gpus": "0",
            "error": "/scratch/execution/stderr",
            "output": "/scratch/execution/stdout",
            "log_xml": "true",
            "executable": "/scratch/execution/dockerScript",
            "log": "/scratch/execution/execution.log",
            "priority": "0",
        }
        job = condor.submit(job_submit)
        # print(json.dumps(job, indent=4))
        job_id = job["cluster"]
        # queue = condor.get_queue()
        # print(json.dumps(queue, indent=4))
        queue = condor.get_queue(job_id=job_id)
        print(json.dumps(queue, indent=4))
        # for _ in range(2):
        #     time.sleep(20)
        #     history = condor.get_history()
        #     print(json.dumps(history, indent=4))
        #     history = condor.get_history(job_id=job_id)
        #     print(json.dumps(history, indent=4))


if __name__ == "__main__":
    main()
