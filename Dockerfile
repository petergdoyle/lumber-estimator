# Use a standard Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for matplotlib/pandas potentially)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code and web assets
COPY src/ /app/src/
COPY web/ /app/web/
COPY projects/ /app/projects/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the API port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "src.lumber_estimator.web.server:app", "--host", "0.0.0.0", "--port", "8000"]
