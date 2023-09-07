FROM python:3.10

WORKDIR .

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "cli.main"]
# start as
# docker run --network host  -v /var/run/docker.sock:/var/run/docker.sock orchestrator:latest
