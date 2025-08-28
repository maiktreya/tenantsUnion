#!/bin/bash

# Pull the latest pgAdmin4 image
docker pull dpage/pgadmin4:latest

# Run pgAdmin4 container in detached mode with port mapping and auto-remove
docker run -d \
  --name pgadmin \
  -p 81:80 \
  --rm \
  -e "PGADMIN_DEFAULT_EMAIL=admin@admin.com" \
  -e "PGADMIN_DEFAULT_PASSWORD=admin" \
  dpage/pgadmin4:latest