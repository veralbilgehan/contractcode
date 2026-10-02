FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (Docker cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py index.html script.js style.css ./

# Expose port (Cloud Run injects PORT env var)
EXPOSE 8080

# Run the application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
