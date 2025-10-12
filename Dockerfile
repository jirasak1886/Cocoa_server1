# Use an official Python runtime as a parent image
FROM python:3.10-slim-bullseye

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Set environment variables for the database connection
# The database is external (XAMPP) at 10.120.1.109
ENV DB_HOST=localhost
ENV DB_PORT=3306
ENV DB_USER=s652021044
ENV DB_PASS=99999wasd
ENV DB_NAME=db652021044
ENV PORT=5044

# Install any needed packages specified in requirements.txt
    COPY requirements.txt .
    RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port the app runs on
EXPOSE 5044

# Command to run the application
# Using uvicorn to serve the Flask app (ASGI compatible)
# The server.py file contains the Flask app instance named 'app'
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5044"]
