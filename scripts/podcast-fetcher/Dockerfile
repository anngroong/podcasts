# Use the official lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the local code to the container
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Set environment variables
ENV PORT=8080

# Expose the port Flask will run on
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]

