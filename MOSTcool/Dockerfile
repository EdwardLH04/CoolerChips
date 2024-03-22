FROM --platform=linux/x86_64 ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

ENV ENERGYPLUS_LINK=https://github.com/NREL/EnergyPlus/releases/download/v23.2.0/EnergyPlus-23.2.0-7636e6b3e9-Linux-Ubuntu22.04-x86_64.tar.gz

# Install system dependencies
RUN  apt-get update && apt-get install -y \
    wget=1.21.*\
    unzip=6.0-* \
#    cmake \
#    git \
    python3=3.10.* \
    python3-pip=22.0.* \
    python-is-python3

# Install system dependencies
RUN  apt-get update && apt-get install -y \
    python3-tk=3.10.* 

# Download and install EnergyPlus    
RUN wget $ENERGYPLUS_LINK \
    && tar -xzf EnergyPlus-23.2.0-7636e6b3e9-Linux-Ubuntu22.04-x86_64.tar.gz \
    && mv EnergyPlus-23.2.0-7636e6b3e9-Linux-Ubuntu22.04-x86_64 EnergyPlus

# Copy requirements.txt to the docker image
COPY requirements.txt /app/requirements.txt

# Install Python dependencies from requirements.txt file
RUN pip install --no-cache-dir -r /app/requirements.txt

RUN ln -s /EnergyPlus/energyplus /usr/local/bin/energyplus

WORKDIR /app

CMD ["python", "main.py"]