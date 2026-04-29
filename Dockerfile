ARG VERSION=25.7.2-el9
FROM htcondor/mini:$VERSION


USER root
RUN mkdir -p /logs/condor && chmod -R a+rwx /logs/condor
RUN mkdir -p /scratch && chmod -R a+rwx /scratch

COPY htcondor_configs/95-NERSC.conf /data/htcondorlogs/95-NERSC.conf
ENV CONDOR_CONFIG=/data/htcondorlogs/95-NERSC.conf
ENV CONDOR_PORT=9000
COPY htcondor_configs/start.sh /start.sh
RUN ln -s /usr/libexec/condor/* /usr/libexec


COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project
COPY htcondor_configs/start.sh /app/start.sh
COPY src /app/
RUN uv sync --frozen
RUN chmod -R a+rwx /app/.venv /root/.local
