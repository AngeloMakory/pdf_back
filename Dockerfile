# Use an official Python runtime as base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory in container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy app code into container
COPY . /app/

# Create uploads folder
RUN mkdir -p /app/uploads

# Expose port (Flask runs on 5000)
EXPOSE 5000

# Start app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
