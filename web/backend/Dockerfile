FROM python:3.12-slim
WORKDIR /app
COPY web/backend/requirements.txt /app/web/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/web/backend/requirements.txt \
    && pip install --no-cache-dir PyYAML jsonschema cryptography
COPY src/uap /app/src/uap
COPY src/narna /app/src/narna
COPY specs/schemas /app/specs/schemas
COPY specs/examples /app/specs/examples
# Ensure Decision Packages are available even if cwd differs
COPY specs/examples/packages/legal-decision.yaml /app/src/uap/_packages/legal-decision.yaml
COPY specs/examples/packages/eu-ai-act.yaml /app/src/uap/_packages/eu-ai-act.yaml
COPY web/backend /app/web/backend
WORKDIR /app
ENV PYTHONPATH=/app/src:/app/web/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
