import requests
import docker
import time
import os

from pathlib import Path


URL_BASE = "http://10.11.133.87:8000"

URL_JOB_GET = os.getenv("URL_JOB_GET", f"{URL_BASE}/job")
URL_JOB_FILES = os.getenv("URL_JOB_STATUS", f"{URL_BASE}/job/$job_id$/file")
URL_JOB_STATUS = os.getenv("URL_JOB_STATUS", f"{URL_BASE}/job/$job_id$/status")
URL_FILES = os.getenv("URL_FILES", f"{URL_BASE}/file/$file_id$")

TIMEOUT = os.getenv("TIMEOUT", 30)
TIMEOUT_MONITOR = os.getenv("TIMEOUT_MONITOR", 2)

client = docker.from_env()


while True:
    # Get job from API
    response = requests.get(URL_JOB_GET)
    data = response.json()

    if data:
        job_id = data['job_id']
        image = f"{data['image']}:{data['image_version']}"

        #Ensure the image is present locally, if not, pull it
        try:
            client.images.get(image)
        except docker.errors.ImageNotFound:
            client.images.pull(image)
        except docker.errors.APIError as e:
            print(f"Error checking/pulling the Docker image: {e}")
            continue

        # download files and save to common space
        paths = data["files"]
        for p, p_id in paths.items():
            p_url = requests.get(URL_FILES.replace("$file_id$", p_id))
            p_url = p_url.json()
            r = requests.get(p_url, allow_redirects=True)
            open(p, "wb").write(r.content)


        # Run the worker container
        container = client.containers.run(image, environment={"JOB_ID": job_id}, detach=True)
        print(f"Started container {container.id} for job {job_id} using {image}")

        # get and keep updating its status
        while True:
            container.reload()
            print(container.attrs["State"])

            match container.attrs["State"]:
                case {"Status": "running"}:
                    requests.put(
                        URL_JOB_STATUS.replace("$job_id$", job_id),
                        params={"status": "running"}, json={"status_body": ""}
                        )
                case {"Status": "exited", "ExitCode": 0}:
                    requests.put(
                        URL_JOB_STATUS.replace("$job_id$", job_id),
                        params={"status": "finished"}, json={"status_body": ""}
                        )
                    break
                case {"Status": "exited", "ExitCode": exit_code, "Error": err_info}:
                    requests.put(
                        URL_JOB_STATUS.replace("$job_id$", job_id),
                        params={"status": "error"}, json={"status_body": f"Exit Code: {exit_code}\n{err_info}"}
                        )
                    break
                case _:
                    raise ValueError

            time.sleep(TIMEOUT_MONITOR)

        # upload result
        path_upload = Path(data["path_upload"])
        path_upload = path_upload.glob("*")

        files = [{"file": (str(p), open(p, "rb"))} for p in path_upload]
        [requests.post(URL_JOB_FILES.replace("$job_id$", job_id), files=f) for f in files]

        # clean up

    # Sleep for a defined interval before checking for the next job
    time.sleep(TIMEOUT)
