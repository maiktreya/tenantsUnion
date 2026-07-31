# USe postgreSQL 17 as base

FROM postgres:17

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # install postgis 3 for postgreSQL 17
    postgresql-17-postgis-3 \
    postgresql-17-postgis-3-scripts && \
    rm -rf /var/lib/apt/lists/*