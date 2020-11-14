FROM python:3.8-alpine as builder
RUN apk update && \
    apk add git && \
    apk add build-base

FROM builder as with-deps
WORKDIR /opt/bot/
COPY ["requirements.txt", "gitrequirements.txt",  "/opt/bot/"]
RUN pip install -r requirements.txt && \
    pip install -r gitrequirements.txt 

FROM with-deps
COPY ["bot.py", "/opt/bot/"]
COPY ["cogs", "/opt/bot/cogs"]
CMD ["python", "bot.py"]
