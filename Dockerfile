# see README.md for usage
FROM python:3.10

WORKDIR .

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "cli.main"]
