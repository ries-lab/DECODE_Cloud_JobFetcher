# Querier
Queries cloud endpoint

## Usage
- Copy and modify .env.example
- Start mock_api (cd to dir, create env) then `uvicorn app.main:app --host 0.0.0.0 --reload`
- Start docker container as below


## JobFetcher
```bash
docker run \
  --gpus all \  # needs to detect GPUs
  -e PATH_BASE=/data \  # dir in container (alternatively, set in `.env`)
  -e PATH_HOST_BASE=/home/riesgroup/temp/decode_cloud/mounts \  # dir in host (alternatively, set in `.env`)
  -v /home/riesgroup/temp/decode_cloud/mounts:/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --add-host=host.docker.internal:host-gateway \  # linux only
  jobfetcher:latest
```
