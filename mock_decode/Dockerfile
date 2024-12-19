FROM python:3.10

ARG VERSION
LABEL mock_decode.version=$VERSION

WORKDIR /app

COPY . .

CMD ["python", "-u", "app/app.py"]

# build as
# docker build --build-arg VERSION=$(cat VERSION) -t mock_decode:$(cat VERSION) .