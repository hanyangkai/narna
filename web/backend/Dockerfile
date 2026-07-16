FROM python:3.12-slim
WORKDIR /app
COPY web/backend/requirements.txt /app/web/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/web/backend/requirements.txt \
    && pip install --no-cache-dir PyYAML jsonschema cryptography
COPY src/uap /app/src/uap
COPY src/narna /app/src/narna
COPY specs/schemas /app/specs/schemas
COPY specs/examples /app/specs/examples
COPY web/backend /app/web/backend
ENV PYTHONPATH=/app/src:/app/web/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
