#!/bin/bash
# Update system packages
apt-get update && apt-get install -y portaudio19-dev

# Upgrade pip to the latest version
python -m pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
