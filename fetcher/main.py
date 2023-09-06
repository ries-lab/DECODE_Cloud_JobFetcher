import requests
import docker
import time
import os

URL_JOB_GET = os.getenv("URL_JOB_GET", "http://10.11.39.126:8000/job")
URL_JOB_FILES = os.getenv("URL_JOB_STATUS", "http://10.11.39.126:8000/job/{{job_id}}/file")
URL_JOB_STATUS = os.getenv("URL_JOB_STATUS", "http://10.11.39.126:8000/job/{{job_id}}/status")
URL_FILES = os.getenv("URL_FILES", "http://10.11.39.126:8000/file/{{file_id}}")

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
            p_url = requests.get(URL_FILES.replace("{{file_id}}", p_id))
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

            # TODO: SEND KEEPALIVE

            if not container.attrs["State"]["Running"]:
                break

            time.sleep(TIMEOUT_MONITOR)

        # upload result
        files = {
            "music.mp3": {"file": ("config/music.mp3", open("config/music.mp3", "rb"))},
            "video.mp3": {"file": ("config/video.mp3", open("config/video.mp3", "rb"))},
        }
        [requests.post(URL_JOB_FILES.replace("{{job_id}}", job_id), files=f) for f in files.values()]

        # clean up

    # Sleep for a defined interval before checking for the next job
    time.sleep(TIMEOUT)
