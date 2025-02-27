# Research Pod API

A Flask-based REST API service with Docker containerization support.

## Prerequisites

- Docker and Docker Compose (use [Docker Desktop](https://www.docker.com/get-started/))

#### Recommended Tools
- [Postman VSCODE extension](https://marketplace.visualstudio.com/items?itemName=Postman.postman-for-vscode) - make requests to the API by specifying the endpoint URL

## Installation

### Docker Development

1. Clone the repository:
   ```bash
   git clone https://github.com/richardr1126/research-pod-api.git
   ```

2. Create a `.env` file:
   ```bash
   cp template.env .env
   ```
   > No need to edit the `.env` file for now

3. Build and run the Docker image:
   ```bash
   docker compose up --build
   ```
   > `--build` rebuilds the image if there are changes in the code

The API will be available at `http://localhost:8888`

> Test server using `http://localhost:8888/health`

### Local Development

#### Prerequisites (If running with local python environment)
- Python 3.12.x
- Conda (optional)

1. Clone the repository:
   ```bash
   git clone https://github.com/richardr1126/research-pod-api.git
   cd research-pod-api
   ```

2. Create a virtual environment and activate it:
   ```bash
   conda create --name research-pod
   conda activate research-pod
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```bash
   cp template.env .env
   ```
   > Edit the `.env` file if needed

5. Run the development server:
   ```bash
   python app.py
   ```
   or WSGI production server:
   ```bash
   gunicorn --bind 0.0.0.0:8888 --workers 1 api:server --log-level debug
   ```
   The API will be available at `http://localhost:8888`
   
## API Endpoints

- `GET /health` - Health check endpoint
- `GET /v1/api/hello` - Example endpoint returning a greeting message

## Environment Variables

- `PORT`: Server port (default: 8888)
- `FLASK_ENV`: Flask environment setting (development/production)


## Development

The application uses Flask's development server when run locally and Gunicorn for production deployment in Docker.

## License

See the [LICENSE](LICENSE) file for details.