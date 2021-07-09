FROM ubuntu:latest

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev && \
    pip install Flask

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]
