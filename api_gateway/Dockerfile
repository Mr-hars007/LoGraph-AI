# Use a full Python image to avoid build-essential issues with grpcio
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the requirements file from the root
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to allow absolute imports
COPY . .

# Set the working directory to the service root
WORKDIR /app/api_gateway

# Set PYTHONPATH to /app so internal modules can be found
ENV PYTHONPATH=/app

# Expose the gateway port
EXPOSE 5005

# Run the application
CMD ["python", "app.py"]
