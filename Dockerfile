# Docker environment with all the dependencies and such setup to run the
# project (eliminating "it works on my machine")
#
# Build:
# > docker build -t fyp .
# Run:
# > docker run -ti --security-opt="seccomp=unconfined" -v $PWD:/fyp fyp /bin/bash

FROM ubuntu:latest

WORKDIR /fyp

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

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

