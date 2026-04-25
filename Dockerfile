# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the monitor script
COPY monitor.py .

# Run the python script directly (unbuffered so logs show up immediately)
CMD ["python", "-u", "monitor.py"]
