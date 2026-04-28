ARG VERSION=25.7.2-el9
FROM htcondor/mini:$VERSION

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY htcondor_configs/pre-exec.sh /root/config/pre-exec.sh
COPY htcondor_configs/submit_rest.sh /usr/local/bin/submit_rest.sh
COPY htcondor_configs/supervisord.conf /etc/supervisord.conf

WORKDIR /app
RUN chown -R submituser:submituser /app

USER submituser
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project

COPY --chown=submituser:submituser src /app/
RUN uv sync --frozen
