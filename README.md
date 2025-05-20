# SCA Training Simulator Backend

This is the backend API for the SCA Training Simulator application.

## Features

- FastAPI REST API
- PostgreSQL database with SQLAlchemy ORM
- JWT authentication
- User management
- OpenAI integration

## Project Structure

```
.
├── app                  # Application package
│   ├── api              # API-related modules
│   │   └── deps.py      # Dependencies (JWT, auth)
│   ├── core             # Core modules
│   │   └── config.py    # Application settings
│   ├── db               # Database modules
│   │   ├── engine.py    # DB connection
│   │   └── init_db.py   # DB initialization
│   ├── models           # SQLAlchemy models
│   │   └── user.py      # User model
│   ├── routers          # API endpoints
│   │   ├── __init__.py  # Router registration
│   │   ├── auth.py      # Auth endpoints
│   │   └── users.py     # User endpoints
│   ├── schemas          # Pydantic schemas
│   │   └── user.py      # User schemas
│   └── utils            # Utility functions
│       ├── openai.py    # OpenAI utilities
│       └── users.py     # User utilities
├── scripts              # Scripts
│   └── init_db.py       # Initialize DB
├── .env                 # Environment variables
├── .env.example         # Example env vars
├── main.py              # Application entry point
├── pyproject.toml       # Python dependencies
└── README.md            # This file
```

## Getting Started

1. Clone the repository
2. Create a virtual environment
3. Install dependencies:

```bash
pip install .
```

4. Create a `.env` file based on `.env.example` and configure environment variables
5. Run database migrations:

```bash
python scripts/init_db.py
```

6. Start the development server:

```bash
uvicorn main:app --reload
```

7. Visit the API documentation at http://localhost:8000/docs

## API Routes

- `GET /api/v1/users/` - List all users
- `POST /api/v1/users/` - Create a new user
- `GET /api/v1/users/{user_id}` - Get a user by ID
- `PUT /api/v1/users/{user_id}` - Update a user
- `DELETE /api/v1/users/{user_id}` - Delete a user
- `POST /api/v1/auth/login` - Login and get JWT token
