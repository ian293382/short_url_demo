# Set image version
FROM python:3.10-slim

# Set environment variables is mean 
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . . 

# Update & Install package 
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt 

# Expose the application port
EXPOSE 8000

# Run the application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]