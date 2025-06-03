#!/usr/bin/env python3

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
import httpx
from loguru import logger

from app.core.config import settings
from app.db.load import load
from app.models.user import User
from app.schema.user import CreateUser, OAuthUserCreate

router = APIRouter(prefix="/users", tags=["users"])


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
    try:        
        auth_payload = {
            "name": f"{request.first_name} {request.last_name}",
            "email": request.email,
            "password1": request.password1.get_secret_value(),
            "password2": request.password2.get_secret_value(),
            "app_name": settings.PROJECT_NAME,
            "role": "user",
        }
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
        logger.error(f"Auth service error: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Auth service response status: {e.response.status_code}")
            logger.error(f"Auth service response content: {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code if hasattr(e, "response") and e.response else 500,
            detail=e.response.json() if hasattr(e, "response") and e.response else str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error during auth service registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auth service error: {str(e)}",
        )

    try:        
        new_user = User(
            id=user_id,
            first_name=request.first_name,
            last_name=request.last_name,
        )

        db.add(new_user)
        db.commit()
        
    except Exception as e:
        logger.exception(f"Database error during user creation: {e}")
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

@router.post("/oauth-register", status_code=status.HTTP_201_CREATED)
async def oauth_register(
    request: OAuthUserCreate,
    db: Session = Depends(load),
):
    """
    Create user record after successful OAuth authentication.
    This endpoint is called by the auth service after OAuth success.

    Parameters:
    - request (OAuthUserCreate): User details from OAuth provider
    - db (Session): Database session

    Returns:
    - Dict containing user creation status
    """
    try:
        
        # Check if user already exists
        existing_user = db.query(User).filter_by(id=request.id).first()
        if existing_user:
            logger.info(f"User {request.id} already exists, updating details")
            # Update existing user details if needed
            existing_user.first_name = request.first_name
            existing_user.last_name = request.last_name
            db.commit()
            
            return {
                "id": existing_user.id,
                "first_name": existing_user.first_name,
                "last_name": existing_user.last_name,
                "message": "User updated successfully",
                "is_new_user": False
            }
        
        # Create new user
        new_user = User(
            id=request.id,
            first_name=request.first_name,
            last_name=request.last_name,
        )

        db.add(new_user)
        db.commit()
        logger.info(f"Successfully created OAuth user {request.id}")
        
        return {
            "id": new_user.id,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "message": "OAuth user created successfully",
            "is_new_user": True
        }
        
    except Exception as e:
        logger.exception(f"Database error during OAuth user creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create OAuth user record: {str(e)}",
        )