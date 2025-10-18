# Use Python 3.12 as the base image
FROM python:3.12

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container to /code
WORKDIR /code

# Copy the requirements file into the container
COPY ./pyproject.toml ./poetry.lock* /code/

# Install poetry
RUN pip install poetry

# Disable the creation of a virtual environment by poetry
RUN poetry config virtualenvs.create false

# Install the dependencies
RUN poetry install --only main

# Copy the rest of the application code into the container
COPY ./app /code/app

COPY ./admin_config.json /code/
COPY ./admin_config.dev.json /code/

EXPOSE 8080

# Set the command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
