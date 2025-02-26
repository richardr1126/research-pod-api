# Research Pod API

A Flask-based REST API service with Docker containerization support.

## Prerequisites

- Docker and Docker Compose
- Python >3.12.x
- Conda (optional)

## Installation

### Docker Development

1. Build and run using Docker Compose:
   ```bash
   docker compose up --build
   ```

The API will be available at `http://localhost:8888`

### Local Development

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

## Project Structure

```
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose configuration
└── README.md         # Project documentation
```

## Development

The application uses Flask's development server when run locally and Gunicorn for production deployment in Docker.

## License

See the [LICENSE](LICENSE) file for details.