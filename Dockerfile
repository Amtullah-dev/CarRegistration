#FROM python:3.9-slim
#
#
## Set the working directory
#WORKDIR /app
#
## Copy project files into the container
#COPY . /app
#
#ENV PYTHONPATH=/app
#
## Install dependencies
#RUN pip install -r requirements.txt
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Make scripts executable
RUN chmod +x ./bin/web.sh ./bin/celery_worker.sh ./bin/celery_beat.sh ./bin/client.sh ./bin/server.sh


