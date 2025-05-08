#!/usr/bin/env python3

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
import httpx

from app.core.config import settings
from app.db.load import load
from app.models.user import User
from app.schema.user import CreateUser

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    response: Response,
    request: CreateUser,
    db: Session = Depends(load),
):
    """
    Two-step registration process:
    1. Register with auth service to create user credentials
    2. Create user record in local database with additional details

    Parameters:
    - request (CreateUser): An object containing user details
    - db (Session): Database session

    Returns:
    - Dict containing user details and registration status
    """
    auth_payload = {
        "name": f"{request.first_name} {request.last_name}",
        "email": request.email,
        "password1": request.password1.get_secret_value(),
        "password2": request.password2.get_secret_value(),
        "app_name": settings.PROJECT_NAME,
        "role": "user",
    }

    try:
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(
                f"{settings.AUTH_SERVICE_URL}{settings.AUTH_REGISTER_URL}", json=auth_payload
            )
            auth_response.raise_for_status()
            auth_data = auth_response.json()
            user_id = auth_data["id"]
            
            # Forward the cookie from auth service if it exists
            if "set-cookie" in auth_response.headers:
                response.headers["set-cookie"] = auth_response.headers["set-cookie"]
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code if hasattr(e, "response") else 500,
            detail=e.response.json() if hasattr(e, "response") else str(e),
        )

    new_user = User(
        id=user_id,
        first_name=request.first_name,
        last_name=request.last_name,
    )

    try:
        db.add(new_user)
    except Exception as e:
        # If local user creation fails, we should ideally delete the auth user
        # This would require an additional endpoint in the auth service
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"msg": f"Failed to create user record: {str(e)}"}],
        )

    return {
        "id": user_id,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "email": request.email,
        "message": "User registration successful",
        "access_token": auth_data["access_token"],
        "token_type": "bearer",
    }
