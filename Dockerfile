FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system build dependencies for PyMuPDF, Pillow, and C++ extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies from backend/requirements.txt
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source files
COPY backend/ .

EXPOSE 8000

# Listen on Render's dynamic $PORT or default to 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
