FROM python:3.14-rc-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn httpx pydantic pydantic-settings pyyaml "mcp<2" sse-starlette psutil requests structlog aiosqlite PyJWT GitPython && \
    pip install -e packages/rae-core
ENV PYTHONPATH=/app/src:/app:/app/packages/rae-core/src:/app/packages/rae-quality:/app/packages/rae-agentic-memory/rae-core:/app/packages/rae-agentic-memory
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009"]

