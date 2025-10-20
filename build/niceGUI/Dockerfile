FROM python:3.11-slim

# Install the locales package
RUN apt-get update && apt-get install -y locales && \
    # Uncomment the Spanish locale in the locale generation file
    sed -i -e 's/# es_ES.UTF-8 UTF-8/es_ES.UTF-8 UTF-8/' /etc/locale.gen && \
    # Generate the locale
    dpkg-reconfigure --frontend=noninteractive locales && \
    # Clean up apt cache to reduce image size
    rm -rf /var/lib/apt/lists/*

# Set environment variables for the locale
ENV LANG=es_ES.UTF-8
ENV LANGUAGE=es_ES.UTF-8
ENV LC_ALL=es_ES.UTF-8

# Set the working directory in the container
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["python", "main.py"]