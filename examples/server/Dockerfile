FROM ubuntu:latest

RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get upgrade -y
RUN apt-get install -y \
    build-essential elfutils gcc-10 gcc-10-multilib libc6-dev:i386 \
    python3 python3-pip \
    clang-format 
RUN ln -s /usr/bin/python3 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip
ENV CC gcc-10

WORKDIR /usr/src/vulnspec
COPY ./examples/server/requirements.txt ./
RUN pip install -r requirements.txt

COPY ./ ./
WORKDIR /usr/src/vulnspec/examples/server/

EXPOSE 80
CMD gunicorn "app:create_app()" -w 4 -b "0.0.0.0:80"

