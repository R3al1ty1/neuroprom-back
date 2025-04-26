FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .

RUN uv pip install --no-cache-dir --system -e .

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]