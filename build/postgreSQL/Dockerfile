FROM postgres:15

# Install the pg_cron extension
RUN apt-get update \
    && apt-get install -y postgresql-15-cron \
    && rm -rf /var/lib/apt/lists/*