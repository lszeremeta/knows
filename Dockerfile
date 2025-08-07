FROM python:3.13.6-slim
LABEL maintainer="Łukasz Szeremeta <l.szeremeta.dev+knows@gmail.com>"
WORKDIR /app
# Copy the project files into the docker image (see .dockerignore)
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT [ "python", "-m", "knows" ]