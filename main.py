from fastapi import FastAPI, Depends, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db, engine, Base
from models import Page, Post, Employee, Wallet
from schemas import (
    PageResponse, PageDetailResponse, PostResponse, EmployeeResponse,
    PaginatedResponse, WalletConnectRequest, WalletVerifyRequest,
    WalletResponse, WalletAuthResponse
)
from services import PageService, WalletService
import math
import secrets
from datetime import datetime, timezone

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LinkedIn Insights Microservice",
    description="API for scraping and analyzing LinkedIn company pages with Phantom wallet integration",
    version="1.0.0"
)

security = HTTPBearer()

# In-memory nonce store (in production, use Redis or database)
nonce_store = {}

@app.get("/")
def root():
    return {"message": "LinkedIn Insights Microservice API", "version": "1.0.0"}

@app.get("/api/pages/{page_id}", response_model=PageDetailResponse)
def get_page_by_id(page_id: str, db: Session = Depends(get_db)):
    service = PageService(db)
    page = service.get_page_by_id(page_id)
    
    if not page:
        try:
            page = service.scrape_and_save(page_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to scrape page: {str(e)}")
    
    posts = db.query(Post).filter(Post.page_id == page.id).limit(25).all()
    employees = db.query(Employee).filter(Employee.page_id == page.id).limit(50).all()
    
    return {
        **PageResponse.model_validate(page).model_dump(),
        "posts": [PostResponse.model_validate(p).model_dump() for p in posts],
        "employees": [EmployeeResponse.model_validate(e).model_dump() for e in employees]
    }

@app.get("/api/pages", response_model=PaginatedResponse)
def search_pages(
    min_followers: Optional[int] = Query(None, description="Minimum follower count"),
    max_followers: Optional[int] = Query(None, description="Maximum follower count"),
    name_search: Optional[str] = Query(None, description="Search by page name"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    service = PageService(db)
    skip = (page - 1) * page_size
    
    pages, total = service.search_pages(
        min_followers=min_followers,
        max_followers=max_followers,
        name_search=name_search,
        industry=industry,
        skip=skip,
        limit=page_size
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return {
        "items": [PageResponse.model_validate(p).model_dump() for p in pages],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@app.get("/api/pages/{page_id}/followers", response_model=PaginatedResponse)
def get_page_followers(
    page_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    service = PageService(db)
    skip = (page - 1) * page_size
    
    followers, total = service.get_page_followers(page_id, skip=skip, limit=page_size)
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return {
        "items": followers,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@app.get("/api/pages/{page_id}/posts", response_model=List[PostResponse])
def get_recent_posts(
    page_id: str,
    limit: int = Query(15, ge=1, le=25, description="Number of posts to retrieve"),
    db: Session = Depends(get_db)
):
    service = PageService(db)
    posts = service.get_recent_posts(page_id, limit=limit)
    
    if not posts:
        page = service.get_page_by_id(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
    
    return [PostResponse.model_validate(p).model_dump() for p in posts]

@app.post("/api/pages/{page_id}/scrape")
def scrape_page(page_id: str, db: Session = Depends(get_db)):
    service = PageService(db)
    try:
        page = service.scrape_and_save(page_id)
        return {
            "message": "Page scraped successfully",
            "page": PageResponse.model_validate(page).model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape page: {str(e)}")

@app.get("/api/pages/{page_id}/employees", response_model=PaginatedResponse)
def get_page_employees(
    page_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    service = PageService(db)
    db_page = service.get_page_by_id(page_id)
    
    if not db_page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    skip = (page - 1) * page_size
    employees = db.query(Employee).filter(
        Employee.page_id == db_page.id
    ).offset(skip).limit(page_size).all()
    
    total = db.query(Employee).filter(Employee.page_id == db_page.id).count()
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return {
        "items": [EmployeeResponse.model_validate(e).model_dump() for e in employees],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Wallet Endpoints

@app.get("/api/wallet/nonce")
def get_nonce(wallet_address: str = Query(..., description="Wallet address to generate nonce for")):
    """
    Generate a nonce for wallet authentication.
    The client should sign this nonce with their private key.
    """
    nonce = secrets.token_urlsafe(32)
    timestamp = datetime.now(timezone.utc).isoformat()
    message = f"Please sign this message to authenticate with Solvnow.\n\nNonce: {nonce}\nTimestamp: {timestamp}"
    
    # Store nonce with wallet address (expires in 5 minutes)
    nonce_store[wallet_address] = {
        "nonce": nonce,
        "message": message,
        "timestamp": timestamp
    }
    
    return {
        "nonce": nonce,
        "message": message,
        "timestamp": timestamp
    }

@app.post("/api/wallet/connect", response_model=WalletAuthResponse)
def connect_wallet(request: WalletConnectRequest, db: Session = Depends(get_db)):
    """
    Connect a Phantom wallet by verifying signature.
    Returns JWT token for authenticated requests.
    """
    wallet_service = WalletService(db)
    
    # Verify signature
    if not wallet_service.verify_signature(request.public_key, request.message, request.signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Connect wallet
    wallet = wallet_service.connect_wallet(
        wallet_address=request.wallet_address,
        public_key=request.public_key,
        signature=request.signature,
        message=request.message
    )
    
    if not wallet:
        raise HTTPException(status_code=400, detail="Failed to connect wallet")
    
    # Generate access token
    access_token = wallet_service.generate_access_token(request.wallet_address)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "wallet": WalletResponse.model_validate(wallet).model_dump()
    }

@app.post("/api/wallet/verify", response_model=WalletResponse)
def verify_wallet(request: WalletVerifyRequest, db: Session = Depends(get_db)):
    """
    Verify wallet ownership by checking signature.
    """
    wallet_service = WalletService(db)
    
    wallet = wallet_service.get_wallet_by_address(request.wallet_address)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    # Verify signature
    verified_wallet = wallet_service.verify_wallet(
        wallet_address=request.wallet_address,
        signature=request.signature,
        message=request.message
    )
    
    if not verified_wallet:
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return WalletResponse.model_validate(verified_wallet).model_dump()

@app.get("/api/wallet/{wallet_address}", response_model=WalletResponse)
def get_wallet_info(wallet_address: str, db: Session = Depends(get_db)):
    """
    Get wallet information by address.
    """
    wallet_service = WalletService(db)
    wallet = wallet_service.get_wallet_by_address(wallet_address)
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return WalletResponse.model_validate(wallet).model_dump()

@app.get("/api/wallet/me", response_model=WalletResponse)
def get_my_wallet(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated wallet information.
    Requires JWT token in Authorization header.
    """
    from jose import jwt, JWTError
    from config import settings
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        wallet_address = payload.get("wallet_address")
        
        if not wallet_address:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        wallet_service = WalletService(db)
        wallet = wallet_service.get_wallet_by_address(wallet_address)
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        return WalletResponse.model_validate(wallet).model_dump()
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

