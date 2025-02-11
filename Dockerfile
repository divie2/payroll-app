# Use an official Python runtime based on Debian 10 "buster" as a parent image
FROM python:3.12.0a3-slim-buster

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Create and set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files into the container currently just three files
COPY . /app/


# Make port 8000 available to the world outside this container
EXPOSE 8888