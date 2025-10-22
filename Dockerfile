# syntax=docker/dockerfile:1
FROM python:3.11-slim
WORKDIR /app
COPY apps/ ./apps/
COPY packages/ ./packages/
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["python", "apps/operator-runtime/main.py"]
