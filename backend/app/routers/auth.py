
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.core.config import settings, logger
from app.core.security import SecurityManager
from app.models.schemas import Token, LoginRequest

router = APIRouter(tags=["Authentication"])

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Verify password
    if not SecurityManager.verify_password(form_data.password):
        # Add delay to prevent timing attacks
        import time
        time.sleep(1)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = SecurityManager.create_access_token(
        data={"sub": "admin"}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(request: Request, login_data: LoginRequest):
    """
    JSON login endpoint
    """
    # Rate limiting check
    client_ip = request.client.host
    if not SecurityManager.check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    # Validate password
    try:
        if not SecurityManager.verify_password(login_data.password):
            SecurityManager.record_login_attempt(client_ip, success=False)
            logger.warning(f"Failed login attempt from {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )
            
        SecurityManager.record_login_attempt(client_ip, success=True)
        logger.info(f"Successful login from {client_ip}")
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = SecurityManager.create_access_token(
            data={"sub": "admin"}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError as e:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/verify")
async def verify_token(current_user: str = Depends(SecurityManager.get_current_user)):
    """
    Verify if current token is valid
    """
    return {"valid": True, "user": current_user}
