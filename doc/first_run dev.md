# Local Development Environment Setup (dev_run)

This guide explains how to run the application on your local machine for development and testing. This setup uses artificial data to protect privacy and exposes the application directly, without the Nginx reverse proxy or SSL.

## 1. Environment Setup
Before running the application, configure your .env file for a development environment. This ensures you're using the correct database scripts and port settings.

Open your  `.env ` file and make sure the following variables are set:

* For development data (artificial, from a single SQL file):
`INIT_SCRIPTS_PATH=./build/postgreSQL/init-scripts-dev`

* For direct access on http://localhost:8081:

* `INIT_SCRIPTS_PATH`: This points to the directory containing the artificial_data.sql script, which will populate the database with safe, fictional data.

## 2. Running the Application
With the .env file configured, you can start the application using the Frontend profile. This profile includes the database, the API, and the NiceGUI application, but excludes the Nginx and Certbot services used in production.

Execute the following command from the root of the project:

```bash
 docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml up -d
```

This command will:

Build the necessary Docker images if they don't exist.

Start the db, server, and nicegui-app services in the background (-d). exposing DB/Frontend portz

The db service will automatically run the script specified by  `INIT_SCRIPTS_PATH `, creating the schema and populating it with artificial data.

## 3. Accessing the Application
Once the containers are running, you can access the application directly in your web browser at:

```bash
http://localhost:8081
```

## 4. Common Development Operations
View Logs:
To see the real-time logs from all running services (useful for debugging):

```bash
docker compose logs -f
```

To view logs for a specific service (e.g., nicegui-app):

```bash
docker compose logs -f nicegui-app
```


Key Differences from Production (first_run)
No Nginx or SSL: The development setup runs without the Nginx reverse proxy and does not use