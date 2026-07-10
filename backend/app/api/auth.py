from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import jwt
import logging

from app.config import settings
from app.database.session import get_db
from app.models.db_models import User
from app.services.supabase_storage import supabase_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

security = HTTPBearer()

# --- Pydantic Schemas ---
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: str

# --- JWT Authentication Dependency ---
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    
    # 1. Attempt to decode token locally if JWT secret is configured
    if settings.SUPABASE_JWT_SECRET:
        try:
            # Supabase tokens are signed with HS256 and typically have "authenticated" audience
            payload = jwt.decode(
                token, 
                settings.SUPABASE_JWT_SECRET, 
                algorithms=["HS256"], 
                options={"verify_aud": False}
            )
            user_id = payload.get("sub")
            email = payload.get("email")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Invalid token claims: sub missing"
                )
            return {"id": user_id, "email": email}
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Authentication token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.debug(f"Local token validation failed, falling back to SDK: {str(e)}")

    # 2. Fallback to Supabase API verification
    if supabase_client is not None:
        try:
            # This calls the Supabase API to fetch user details using the token
            res = supabase_client.auth.get_user(token)
            if res and res.user:
                return {"id": res.user.id, "email": res.user.email}
        except Exception as e:
            logger.error(f"Supabase token validation exception: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired session token: {str(e)}"
            )

    # 3. Local mock fallback (for testing/dev when Supabase variables are unset)
    if not settings.SUPABASE_URL:
        logger.warning("Supabase URL is not set. Authenticating with mock user credentials.")
        return {"id": "00000000-0000-0000-0000-000000000000", "email": "mock@example.com"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to validate authentication token"
    )

# --- Routes ---

@router.post("/signup", response_model=TokenResponse)
def signup(req: SignUpRequest, db: Session = Depends(get_db)):
    if supabase_client is None:
        # Local mock signup
        logger.warning(f"Mocking signup for {req.email}")
        
        # Check if user exists
        exists = db.query(User).filter(User.email == req.email).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        mock_id = str(uuid.uuid4()) if "uuid" in globals() else "00000000-0000-0000-0000-000000000000"
        db_user = User(id=mock_id, email=req.email, full_name=req.full_name)
        db.add(db_user)
        db.commit()
        
        return {
            "access_token": "mock-jwt-token",
            "user": {"id": mock_id, "email": req.email, "full_name": req.full_name}
        }
        
    try:
        # Register user with Supabase
        res = supabase_client.auth.sign_up({
            "email": req.email,
            "password": req.password,
            "options": {
                "data": {
                    "full_name": req.full_name
                }
            }
        })
        
        if not res.user:
            raise HTTPException(status_code=400, detail="Failed to register user in Supabase")
            
        # Supabase will trigger the insertion of User into public.users table automatically,
        # but to support cases where trigger is slow, we return the session or user.
        # Check if session exists (might require email verification first)
        session = res.session
        access_token = session.access_token if session else "verification_email_sent"
        
        return {
            "access_token": access_token,
            "user": {
                "id": res.user.id,
                "email": res.user.email,
                "full_name": req.full_name
            }
        }
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    if supabase_client is None:
        # Mock login
        logger.warning(f"Mocking login for {req.email}")
        db_user = db.query(User).filter(User.email == req.email).first()
        if not db_user:
            # Create user dynamically for easy local mockup testing
            mock_id = "00000000-0000-0000-0000-000000000000"
            db_user = User(id=mock_id, email=req.email, full_name="Mock User")
            db.add(db_user)
            db.commit()
            
        return {
            "access_token": "mock-jwt-token",
            "user": {"id": db_user.id, "email": db_user.email, "full_name": db_user.full_name}
        }
        
    try:
        res = supabase_client.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password
        })
        
        if not res.session:
            raise HTTPException(status_code=400, detail="Invalid credentials or email not verified")
            
        # Try to retrieve full_name from metadata
        user_metadata = res.user.user_metadata if res.user else {}
        full_name = user_metadata.get("full_name", "")
        
        return {
            "access_token": res.session.access_token,
            "user": {
                "id": res.user.id,
                "email": res.user.email,
                "full_name": full_name
            }
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

@router.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["id"]
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user:
        # If user is in Supabase auth but not in our public.users yet (e.g. trigger didn't run)
        # We create them on demand to prevent errors
        try:
            logger.warning(f"User {user_id} not found in public.users. Creating profile on demand.")
            db_user = User(id=user_id, email=current_user["email"], full_name="")
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        except Exception as e:
            logger.error(f"Failed to create user on demand: {str(e)}")
            raise HTTPException(status_code=404, detail="User profile not found")
            
    return {
        "id": db_user.id,
        "email": db_user.email or "",
        "full_name": db_user.full_name or "",
        "created_at": db_user.created_at.isoformat() if db_user.created_at else ""
    }
