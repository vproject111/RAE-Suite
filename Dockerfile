FROM python:3.14-rc-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn httpx pydantic pydantic-settings pyyaml "mcp<2" sse-starlette psutil requests structlog aiosqlite && \
    pip install -e packages/rae-core
ENV PYTHONPATH=/app:/app/packages/rae-core/src
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009"]
