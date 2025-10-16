# infrastructure/mlflow/Dockerfile
FROM python:3.11-slim

# Install MLflow (and optional clients for future use)
RUN pip install --no-cache-dir mlflow==2.16.0 boto3 psycopg2-binary

# Expose MLflow UI/API
EXPOSE 5000

# Use JSON-array form; keep CMD on ONE logical line
ENTRYPOINT ["mlflow"]
CMD ["server", "--host", "0.0.0.0", "--port", "5000", "--backend-store-uri", "sqlite:////mlflow/mlflow.db", "--default-artifact-root", "/mlflow/artifacts"]

