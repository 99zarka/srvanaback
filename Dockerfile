# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app

# Collect static files (if your project uses them)
# RUN python manage.py collectstatic --noinput

# Expose the port that Gunicorn will listen on
EXPOSE 8000

# Run the Django application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "sevana.wsgi:application"]
