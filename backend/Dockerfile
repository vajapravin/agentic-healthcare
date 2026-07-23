# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (useful for building certain Python packages)
RUN apt-get update && apt-get install -y build-essential gcc && rm -rf /var/lib/apt/lists/*

# Copy dependencies first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add this line to download the local NLP model for Presidio
RUN python -m spacy download en_core_web_lg

# Copy the rest of the backend code
COPY . .

# Port exposed by the container
EXPOSE 8000