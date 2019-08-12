FROM python:3.7

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
#RUN rm -rf /tmp/

COPY . /app

RUN ["make", "lint"]

EXPOSE 8000

ENTRYPOINT ["gunicorn", "--bind=0.0.0.0:8000", "app:app"]

