FROM python:3.10

WORKDIR /app/src

RUN pip install --no-cache-dir poetry

COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

COPY . .

RUN mkdir -p /app/temp
RUN apt-get update && apt-get install -y ffmpeg

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]