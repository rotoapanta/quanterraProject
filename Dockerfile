FROM ubuntu:latest
LABEL authors="rtoapanta"

ENTRYPOINT ["top", "-b"]