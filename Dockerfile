FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MEDMLOPS_ROOT=/app/runtime
WORKDIR /app
COPY requirements-target.lock .
RUN --mount=type=cache,target=/root/.cache/pip pip install pip==26.2.1 && pip install --require-hashes -r requirements-target.lock && useradd --uid 10001 --create-home medmlops
COPY medmlops ./medmlops
COPY configs ./configs
COPY scripts ./scripts
RUN mkdir -p runtime/mlartifacts runtime/serving && chown -R medmlops:medmlops /app
USER medmlops
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "medmlops.serving:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
