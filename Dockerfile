# installation is a bit weird due to needing to install the local neat-python:
# docker build -t neatrader:latest -f ../neatrader/Dockerfile ../

FROM python:3.8-slim
MAINTAINER Chad Bowman <chad.bowman0+github.com>

COPY ../neatrader/ /neatrader/
COPY ../neat-python/ /neat-python/
WORKDIR /neatrader/

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt update && apt install -y graphviz \
    && python3 -m pip install --upgrade pip ../neat-python/ \
    && python3 -m pip install .

ENTRYPOINT [ "python3", "-m", "neatrader" ]
