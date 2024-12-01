# Use a full Python image as the base (instead of slim)
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies for OpenCV and other tools (pyaudio dependencies removed)
RUN apt-get update && apt-get install -y \
    curl \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    build-essential \
    && rm -rf /var/lib/apt/lists/*  # Clean up apt cache to reduce image size

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install Cloudinary directly to ensure availability
RUN pip install cloudinary

# Copy application code into the container
COPY . .

# Install Python dependencies from requirements.txt (Cloudinary will skip if already installed)
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
EXPOSE 8000

# Set the command to run your application
CMD ["python", "server.py"]
