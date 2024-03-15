# DECODE_Cloud_JobFetcher
Code for the workers of [DECODE OpenCloud](https://github.com/ries-lab/DECODE_Cloud_Documentation).

The local workers run this as a Docker container to process jobs, by communicating with the [DECODE OpenCloud worker-facing API](https://github.com/ries-lab/DECODE_Cloud_WorkerAPI):
 - Fetch new jobs for which they have enough resources.
 - Download the job input files.
 - Run the job's Docker container.
 - Upload the job output files.

Additionally, while processing the jobs, they send status updates (new status or keep-alive signals).  
The [cloud workers](https://github.com/ries-lab/DECODE_AWS_Infrastructure/tree/main/stack/worker/runtime/jobs_handler) use specific functions from this package to do the above steps in separate AWS Lambda functions.

## Run locally
#### Define the environment variables
Copy the `.env.example` file to a `.env` file at the root of the directory and define its fields appropriately (alternatively, these fields can be passed as environment variables to the Docker container directly, e.g., with the `-e` flag of the `docker run` command):
  - Worker-facing API connection:
    - `API_URL`: url to use to connect to the [worker-facing API](https://github.com/ries-lab/DECODE_Cloud_WorkerAPI) (or to the mock API).
    - `ACCESS_TOKEN`: access token to authenticate to the [worker-facing API](https://github.com/ries-lab/DECODE_Cloud_WorkerAPI) (note: this will typically only be valid for a short time, hence, setting `USERNAME` and `PASSWORD` instead is recommended).
    - `USERNAME`: username to authenticate to the [worker-facing API](https://github.com/ries-lab/DECODE_Cloud_WorkerAPI) (not required if `ACCESS_TOKEN` is set).
    - `PASSWORD`: password to authenticate to the [worker-facing API](https://github.com/ries-lab/DECODE_Cloud_WorkerAPI) (not required if `ACCESS_TOKEN` is set).
  - Local paths:
    - `PATH_BASE`: path to which to mount in the container (e.g., `/data`).
    - `PATH_HOST_BASE`: path to mount on the host (e.g., `/home/user/temp/decode_cloud/mount).
  - Timeouts:
    - `TIMEOUT_JOB`: how often (in seconds) to look for a new job.
    - `TIMOUT_STATUS`: how often (in seconds) to send a keep-alive signal while processing the job.
#### Build the Docker image
`docker build -t jobfetcher .`
#### Install the nvidia-container-toolkit
[See here](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) to run GPU jobs
#### Run the Docker container
`docker run --gpus all -v <PATH_HOST_BASE>:<PATH_BASE> -v /var/run/docker.sock:/var/run/docker.sock --add-host=host.docker.internal:host-gateway jobfetcher:latest`, where:
 - `<PATH_HOST_BASE>` and `<PATH_BASE>` are set as above.
 - `--add-host=host.docker.internal:host-gateway jobfetcher:latest` is required only when running Linux.

## Test locally
- Start mock_api (cd to dir, create env) then `uvicorn app.main:app --host 0.0.0.0 --reload`.
- Start docker container as above, with `API_URL=http://host.docker.internal:8000`.
