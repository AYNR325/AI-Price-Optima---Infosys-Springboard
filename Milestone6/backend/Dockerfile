# Use a lightweight Python image
FROM python:3.10-slim

# Install system dependencies (fixes LightGBM's libgomp issue)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose Railway port
EXPOSE 8080

# Start the app using Gunicorn with factory pattern
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:create_app()"]
