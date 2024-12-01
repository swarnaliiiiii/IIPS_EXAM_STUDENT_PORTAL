# Base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies for sounddevice and other tools
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libasound2-dev \
    libjack-dev \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*  # Clean up apt cache to reduce image size

# Upgrade pip
RUN python -m pip install --upgrade pip

# Copy application code into the container
COPY . .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
EXPOSE 8000

# Set the command to run your application
CMD ["python", "server.py"]
