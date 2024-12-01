# Use an official lightweight Python image as the base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed by PyAudio, Rust, and build tools
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*  # Clean up apt cache to reduce image size

# Install Rust (needed for maturin) and ensure it's available in PATH
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    echo "export PATH=/root/.cargo/bin:$PATH" >> ~/.bashrc

# Install pip, upgrade to the latest version
RUN python -m pip install --upgrade pip

# Copy your application code into the container
COPY . .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
EXPOSE 8000

# Set the command to run your application (modify 'server.py' if necessary)
CMD ["python", "server.py"]
