FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY scripts/ ./scripts/
COPY alembic.ini ./
COPY data/ ./data/

# Set Python path
ENV PYTHONPATH=/app

# Make entrypoint executable
RUN chmod +x scripts/entrypoint.sh

# Run entrypoint
CMD ["scripts/entrypoint.sh"]