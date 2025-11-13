# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (needed for psycopg2)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code
COPY ./app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run your application
# Uvicorn will run main.py's 'app' instance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
