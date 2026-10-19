FROM python:3.11-slim

WORKDIR /app
COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt

COPY kromamed ./kromamed
COPY api ./api
COPY web ./web

# Render fournit $PORT ; Hugging Face Spaces utilise 7860 (valeur par défaut ci-dessous)
ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
