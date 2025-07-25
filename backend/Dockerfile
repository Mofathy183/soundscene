# Use official Python 3.13.5 slim image based on Debian Bookworm
FROM python:3.13.5-slim-bookworm

# ───── Set environment variables ─────
# PYTHONDONTWRITEBYTECODE=1 prevents Python from writing .pyc files
# PYTHONUNBUFFERED=1 ensures logs are output directly (no buffering)
# UV_SYSTEM=1 allows uv to use system-level installation for some packages
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM=1

# ───── Set working directory ─────
# This is where the app code will live inside the container
WORKDIR /app

# ───── Install system dependencies ─────
# gcc and libpq-dev are needed to build psycopg2 (PostgreSQL bindings)
# curl is used to fetch uv installer
# Clean up apt cache to keep image small
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ───── Download uv installer ─────
# This will fetch the install script from Astral's site
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# ───── Run the installer and delete the script ─────
# This installs uv (fast Python package/dependency manager)
RUN sh /uv-installer.sh && rm /uv-installer.sh

# ───── Add uv to the PATH ─────
# Ensures the shell and subprocesses can access uv from its installed location
ENV PATH="/root/.local/bin/:$PATH"

# ───── Copy project source code into the image ─────
# This copies everything from your local directory to /app inside the container
ADD . /app

# ───── Set working directory again (optional safety) ─────
WORKDIR /app

# ───── Install Python dependencies ─────
# Uses uv to install locked dependencies from uv.lock or requirements.lock
RUN uv sync --locked

# ───── Expose port (if using Django dev server) ─────
# Exposes port 8000 so you can access Django server from the host
EXPOSE 8000

# ───── Default command (update to match your project) ─────
# Runs the Django development server using uv
CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]
