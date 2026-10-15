# Backend API image: FastAPI on uvicorn, non-root, read-only friendly. Model features off.
# Base pinned by digest (python:3.13-slim-bookworm as of 2026-10-06).
FROM python@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641 AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

FROM base AS build
RUN python -m venv /opt/venv
COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install -r /tmp/requirements.txt

FROM base AS runtime
LABEL org.opencontainers.image.title="rih-backend" \
      org.opencontainers.image.description="RIH Care Insight Assistant API (independent student prototype; synthetic data only)"
RUN groupadd --system --gid 10001 rih \
 && useradd --system --uid 10001 --gid rih --home-dir /app --no-create-home --shell /usr/sbin/nologin rih \
 && mkdir -p /data /app \
 && chown 10001:10001 /data
COPY --from=build /opt/venv /opt/venv
# pip is not needed at runtime; removing it also removes its vendored copies of urllib3,
# msgpack and setuptools that the container scan flagged (Phase 8 finding).
RUN /opt/venv/bin/python -m pip uninstall -y pip \
 && python -m pip uninstall -y pip
WORKDIR /app
COPY app/ app/
COPY kb/ kb/
COPY policy/ policy/
COPY governance/ governance/
COPY safety/ safety/
COPY security/ security/
COPY scripts/manage_users.py scripts/redteam.py scripts/
COPY docs/evidence/ docs/evidence/
ENV PATH="/opt/venv/bin:$PATH" \
    RIH_DB_PATH=/data/rih.sqlite3 \
    RIH_ENV=production \
    STRANDS_ENABLED=false \
    RIH_PLANNER=RULE \
    RIH_LOG_FORMAT=json
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=2).status == 200 else 1)"]
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
