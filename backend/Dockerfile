# Use an official lightweight Python image as the base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed by PyAudio
RUN apt-get update && apt-get install -y portaudio19-dev

# Copy your application code into the container
COPY . .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the command to run your application (modify 'app.py' if necessary)
CMD ["python", "app.py"]
