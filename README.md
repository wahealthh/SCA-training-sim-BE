# SCA Simulator Backend API

The backend API server for the SCA Simulator application, a voice-based clinical consultation simulator for GP trainees. This repository provides the server-side functionality, database management, and AI integration for the application.

## Features

- RESTful API for consultation simulations
- AI-powered patient case generation using GPT models
- Consultation transcript analysis and scoring
- PostgreSQL database integration for user data and history
- RCGP rubric-based assessment engine

## Technologies

- Python 3.9+
- FastAPI web framework
- SQLAlchemy ORM
- PostgreSQL database
- OpenAI integration for AI patients
- Pydantic for data validation

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL database
- OpenAI API key
- Vapi API key (for voice functionality)

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure environment:
   ```
   cp .env.example .env
   # Edit .env with your database URL and API keys
   ```

### Development

Run the development server:

```
python main.py
```

Or with uvicorn directly:

```
uvicorn main:app --reload --host 0.0.0.0 --port 3000
```

The API will be available at http://localhost:3000.

### Database Setup

1. Ensure PostgreSQL is running
2. Set the `DATABASE_URL` in your `.env` file
3. The database schema will be automatically created on first run

## API Documentation

Once the server is running, view the interactive API documentation at:

- http://localhost:3000/docs (Swagger UI)
- http://localhost:3000/redoc (ReDoc)

## Key Endpoints

- `GET /api/generate-case` - Generate a new patient case
- `POST /api/score` - Score a consultation based on transcript
- `GET /api/history` - Get consultation history
- Static endpoints for serving frontend files
