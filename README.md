# Querier
Queries cloud endpoint

## Usage

## JobFetcher
```bash
docker run \
  --gpus all \  # needs to detect GPUs
  -e PATH_BASE=/data \
  -e PATH_HOST_BASE=/home/riesgroup/temp/decode_cloud/mounts \
  -v /home/riesgroup/temp/decode_cloud/mounts:/data \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --add-host=host.docker.internal:host-gateway \  # linux only
  jobfetcher:latest
```
