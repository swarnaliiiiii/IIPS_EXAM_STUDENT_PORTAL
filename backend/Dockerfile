FROM python:3.12.3

# Install system-level dependencies for PyAudio
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Start the server
CMD ["python", "server.py"]
