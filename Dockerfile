FROM python:3.9-slim

# Set the working directory
WORKDIR /app  

# Copy project files into the container
COPY . /app  

# Install dependencies
RUN pip install -r requirements.txt  
