# Local Development Environment Setup (dev_run)

This guide explains how to run the application on your local machine for development and testing. This setup uses artificial data to protect privacy and exposes the application directly, without the Nginx reverse proxy or SSL.

## 1. Environment Setup

Before running the application, configure your .env file for a development environment. This ensures you're using the correct database scripts and port settings.

Open your `.env` file and make sure the following variables are set:

- For development data (artificial, from a single SQL file):
  `INIT_SCRIPTS_PATH=./build/postgreSQL/init-scripts-dev`

- For direct access on <http://localhost:8081>:

- `INIT_SCRIPTS_PATH`: This points to the directory containing the artificial_data.sql script, which will populate the database with safe, fictional data.

- `DEV_MODE`: If set to true makes niceGUI bind mount "rw". If left blank the default for the folder is a more secure "ro".

## 2. Exposing ports externally

You have to force upserting `docker-compose-dev.yaml` over `docker-compose.yaml` to get ports **5432(postgreSQL)**, **3000(posgREST)** and **8081(niceGUI)** externally exposed (bear in mind nginx, UFW and the other layers of protection).

## 3. Running the Application

With the .env file configured, you can start the application using the Frontend profile. This profile includes the database, the API, and the NiceGUI application, but excludes the Nginx and Certbot services used in production.

Execute the following command from the root of the project:

```bash
 # for the standard fully dockerized dev envirmoment
 docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml up -d

 # if you have a local python enviroment with the requirements installed you could run the frontend directly from source
 docker compose up -f docker-compose.yaml -f docker-compose-dev.yaml -d && python build/niceGUI/main.py

 # for allowing an enviroment with a local postgreSQL instance with hot reload and monitor logs
 docker compose --profile Frontend -f docker-compose.yaml -f docker-compose-dev.yaml  up  -d --renew-anon-volumes && docker logs --follow tenantsunion-db-1
```

This command will:

Build the necessary Docker images if they don't exist.

Start the **db**, **server**, and **nicegui-app** services in the background (-d). exposing DB/Frontend ports.

The db service will automatically run the script specified by `INIT_SCRIPTS_PATH`, creating the schema and populating it with artificial data in case `build/postgreSQL/init-scripts-dev/artificial_data.sql` is used.

## 4. Accessing the Application layers

Once the containers are running, you can access the application directly in your web browser at:

```bash
http://localhost:8081
```

The api would be available on your local network at (example endpoint to table afiliadas):

```bash
http://localhost:3001/afiliadas
```

And aslo locally available, you would be able to access the postgreSQL instance at:

```bash
postgresql://app_user:password@localhost:5432/mydb?search_path=sindicato_inq
```

## 5. ARBC and available roles for testing

There are three three basic roles available. The user credentials are the role name itself and the password "inquidb2025":

- **admin**: Full access to all tables and functions.
- **gestor**: Access to conflicts, afiliadas_importer & views module.
- **actas**: Access limited to the conflicts module.

## 6. Forcing stop and cleaning

From your project´s root run the following to stop & remove all the containers and images afterwads:

```bash
docker compose --profile Frontend down -v && docker system prune -a --volumes -f
```
