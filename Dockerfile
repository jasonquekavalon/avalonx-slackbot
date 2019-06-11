FROM python:3.7

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
#RUN rm -rf /tmp/

COPY . /app

## Run flask
ENTRYPOINT ["gunicorn", "--bind=0.0.0.0:8000", "app:__flask_wsgi__"]

