# Use an official Python runtime as a parent image
FROM python:3.10-slim-bullseye

# Set the working directory in the container
WORKDIR /app

ENV DJANGO_PRODUCTION=True

# Install psycopg2-binary dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc

# Copy the current directory contents into the container at /app
COPY . /app

# Install uv and then use it to install requirements
RUN pip install uv && python -m uv pip install --system --no-cache -r requirements.txt


# Install any needed packages specified in requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 to the outside world
EXPOSE 8000

# Run Django migrations and start Gunicorn
CMD ["sh", "-c", "python manage.py migrate && gunicorn srvana.wsgi:application --bind 0.0.0.0:8000"]
