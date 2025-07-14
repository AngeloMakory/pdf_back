FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip 
RUN python -m pip install --no-cache-dir flask==2.3.2
RUN python -m pip install --no-cache-dir flask-cors==3.0.10
RUN python -m pip install --no-cache-dir python-dotenv==1.0.0
RUN python -m pip install --no-cache-dir gunicorn==20.1.0
RUN python -m pip install --no-cache-dir mysql-connector-python==8.2.0
#RUN python -m pip install -r requirements.txt

# Copy app code
COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
