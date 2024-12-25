# DECODE_Cloud_JobFetcher
Code for the workers of [DECODE OpenCloud](https://github.com/ries-lab/DECODE_Cloud_Documentation).

The local workers run this as a Docker container to process jobs, by communicating with the [DECODE OpenCloud worker-facing API](https://github.com/ries-lab/DECODE_Cloud_WorkerAPI):
 - Fetch new jobs for which they have enough resources.
 - Download the job input files.
 - Run the job's Docker container.
 - Upload the job output files.

Additionally, while processing the jobs, they send status updates (new status or keep-alive signals).  
The [cloud workers](https://github.com/ries-lab/DECODE_AWS_Infrastructure/tree/main/stack/worker/runtime/jobs_handler) use specific functions from this package to do the above steps in separate AWS Lambda functions.

## Development guide

### Prepare the development environment
We use [poetry](https://python-poetry.org/) for dependency tracking.
See online guides on how to use it, but this setup should work:
 - `conda create -n "3-11-10" python=3.11.10`
 - `conda activate 3-11-10`
 - `pip install pipx`
 - `pipx install poetry`
 - `poetry env use /path/to/conda/env/bin/python`
 - `poetry install`
Afterwards, when you need a new package, use `poetry add [--group dev] <package>` to add new dependencies.
The `--group dev` option adds the dependency only for development (e.g., pre-commit hooks, pytest, ...).

Install the pre-commit hooks: `pre-commit install`.
These currently include ruff and mypy.

### Run locally

#### Define the environment variables
Copy the `.env.example` file to a `.env` file at the root of the directory and define its fields appropriately (alternatively, these fields can be passed as environment variables to the Docker container directly, e.g., with the `-e` flag of the `docker run` command):
  - Worker-facing API connection:
    - `API_URL`: url to use to connect to the [worker-facing API](https://github.com/ries-lab/DECODE_Cloud_WorkerAPI) (or to the mock API).
    - `ACCESS_TOKEN`: access token to authenticate to the [worker-facing API](https://github.com/ries-lab/DECODE_Cloud_WorkerAPI) (note: this will typically only be valid for a short time, hence, setting `USERNAME` and `PASSWORD` instead is recommended).
    - `USERNAME`: username to authenticate to the [worker-facing API](https://github.com/ries-lab/DECODE_Cloud_WorkerAPI) (not required if `ACCESS_TOKEN` is set).
    - `PASSWORD`: password to authenticate to the [worker-facing API](https://github.com/ries-lab/DECODE_Cloud_WorkerAPI) (not required if `ACCESS_TOKEN` is set).
  - Local paths:
    - `PATH_BASE`: path to which to mount in the container (e.g., `/data`).
    - `PATH_HOST_BASE`: path to mount on the host (e.g., `/home/user/temp/decode_cloud/mount; must be absolute if running inside of a docker container).
  - Timeouts:
    - `TIMEOUT_JOB`: how often (in seconds) to look for a new job.
    - `TIMEOUT_STATUS`: how often (in seconds) to send a keep-alive signal while processing the job.

#### Start the job fetcher
`poetry run run`

#### Docker
Alternatively, you can build a Docker image.
For this, run `poetry run docker-build`:
This will create a Docker image named `api:<branch_name>`.  
To run the Docker container, use `poetry run docker-run`.  
To stop and delete all containers for this package, use `poetry run docker-stop`.
If you want to additionally remove all images for this package and prune dangling images, run `poetry run docker-cleanup`.

Note that to run GPU jobs you will need the [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

### Tests

#### Automatic tests
Run them with `poetry run pytest`.

#### Manual tests
To test without worker-facing API running:
- Start mock_api (cd to dir, create env) then `uvicorn app.app:app --host 0.0.0.0 --reload`.
- Start docker container as described above, with `API_URL=http://host.docker.internal:8000`.

Run them with `poetry run pytest`.
