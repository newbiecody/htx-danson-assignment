# Use Python 3.10 base image
FROM python:3.10

# Set working directory inside the container
WORKDIR /app

# Set Python path so modules can be found
ENV PYTHONPATH=/app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files first
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

# Copy entire project
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
