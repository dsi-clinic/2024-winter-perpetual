# Pull base image
FROM quay.io/jupyter/minimal-notebook:python-3.11

# Switch to root user to update package manager and install Python dev tools
USER root

# Perform installations
RUN apt update && apt install -y --no-install-recommends \
  build-essential \
  libatlas-base-dev \
  libgdal-dev \
  gfortran \
  python3-pip \
  python3-dev

# Switch to NB_UID user to install additional packages
USER $NB_UID

# Create working directory
WORKDIR /perpetual

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt