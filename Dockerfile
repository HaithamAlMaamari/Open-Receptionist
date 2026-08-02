FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml README.md ./
COPY agent ./agent
COPY config ./config

# Install dependencies + the package (prompts ship as package data).
RUN pip install --no-cache-dir . \
    && mkdir -p /app/logs \
    && useradd --create-home --uid 1000 receptionist \
    && chown -R receptionist:receptionist /app

USER receptionist

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 7860), timeout=4).close()" || exit 1

# Run as a module from /app so the source tree (with prompts/) is imported
# directly; --host 0.0.0.0 makes the dev runner reachable from outside the
# container (verified flag of pipecat.runner.run.main).
CMD ["python", "-m", "agent.bot", "--host", "0.0.0.0"]
