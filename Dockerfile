FROM python:3.12-bookworm
LABEL authors="shizamuru-dev"
# Set the working directory
WORKDIR /app
# Copy the requirements file into the container
COPY requirements.txt .
# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the application code into the container
COPY . .
# Expose the port the app runs on
EXPOSE 5000
# Set environment variables

ENTRYPOINT ["python3", "main.py"]