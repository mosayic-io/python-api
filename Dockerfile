# Use Python 3.12 (slim) as the base image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Log straight to stdout so Cloud Run captures output immediately
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container to /code
WORKDIR /code

# Copy the dependency manifests into the container
COPY ./pyproject.toml ./uv.lock* /code/

# Install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin:$PATH"

# Install the dependencies
RUN uv sync --locked --no-dev

# Copy the rest of the application code into the container
COPY ./app /code/app

EXPOSE 8080

# Set the command to run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
