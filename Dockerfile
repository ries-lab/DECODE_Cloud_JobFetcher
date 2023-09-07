FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "fetcher/main.py"]
# start as
# docker run --network host  -v /var/run/docker.sock:/var/run/docker.sock orchestrator:latest
