FROM python:3.13-slim

WORKDIR /opt/encounter-app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

EXPOSE 8501

COPY . .

ARG BUILD=Unknown

ENV BUILD=$BUILD

ENTRYPOINT ["./entrypoint.sh"]