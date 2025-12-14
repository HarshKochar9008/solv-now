from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PageBase(BaseModel):
    page_id: str
    name: str
    url: str
    linkedin_id: Optional[str] = None
    profile_picture: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    total_followers: int = 0
    head_count: Optional[int] = None
    specialities: Optional[str] = None

class PageCreate(PageBase):
    pass

class PageResponse(PageBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SocialMediaUserBase(BaseModel):
    linkedin_id: Optional[str] = None
    name: str
    profile_url: Optional[str] = None
    profile_picture: Optional[str] = None
    headline: Optional[str] = None

class SocialMediaUserResponse(SocialMediaUserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PostBase(BaseModel):
    linkedin_post_id: Optional[str] = None
    content: Optional[str] = None
    post_url: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    posted_at: Optional[datetime] = None

class PostResponse(PostBase):
    id: int
    page_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    linkedin_comment_id: Optional[str] = None
    content: Optional[str] = None
    likes_count: int = 0
    posted_at: Optional[datetime] = None

class CommentResponse(CommentBase):
    id: int
    post_id: int
    author_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class EmployeeBase(BaseModel):
    name: str
    profile_url: Optional[str] = None
    profile_picture: Optional[str] = None
    headline: Optional[str] = None
    position: Optional[str] = None
    linkedin_id: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: int
    page_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PageDetailResponse(PageResponse):
    posts: List[PostResponse] = []
    employees: List[EmployeeResponse] = []

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int

class WalletConnectRequest(BaseModel):
    wallet_address: str
    public_key: str
    signature: str
    message: str

class WalletVerifyRequest(BaseModel):
    wallet_address: str
    signature: str
    message: str

class WalletResponse(BaseModel):
    id: int
    wallet_address: str
    public_key: str
    is_verified: bool
    last_connected_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class WalletAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    wallet: WalletResponse

