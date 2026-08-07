FROM python:3.15.0b3-slim
LABEL maintainer="Łukasz Szeremeta <l.szeremeta.dev+knows@gmail.com>"
WORKDIR /app
# Copy the project files into the docker image (see .dockerignore)
COPY . .
RUN pip install --no-cache-dir .[draw]
# Marker for install source detection in knows --version
ENV KNOWS_CONTAINER=1
ENTRYPOINT [ "python", "-m", "knows" ]