
FROM python:3.9

# Set envs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the workdir in the container
WORKDIR /app

# Copy the requirements to the container
COPY requirements.txt .

# Install  dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the files to the workdir
COPY . .

# Expose the app port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
