from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict
from models import Page, Post, Comment, Employee, SocialMediaUser, Wallet
from schemas import PageCreate, PostBase, CommentBase, EmployeeBase, SocialMediaUserBase
from scraper import LinkedInScraper
from datetime import datetime, timedelta, timezone
import logging
import base64
import base58
from nacl.signing import VerifyKey
from jose import jwt
from config import settings

logger = logging.getLogger(__name__)

class PageService:
    def __init__(self, db: Session):
        self.db = db
        self.scraper = LinkedInScraper()
    
    def get_page_by_id(self, page_id: str) -> Optional[Page]:
        return self.db.query(Page).filter(Page.page_id == page_id).first()
    
    def create_or_update_page(self, page_data: Dict) -> Page:
        existing_page = self.get_page_by_id(page_data['page_id'])
        
        if existing_page:
            for key, value in page_data.items():
                if key != 'page_id' and key != 'posts' and key != 'employees':
                    setattr(existing_page, key, value)
            from datetime import timezone
            existing_page.updated_at = datetime.now(timezone.utc)
            page = existing_page
        else:
            page = Page(**{k: v for k, v in page_data.items() if k not in ['posts', 'employees']})
            self.db.add(page)
            self.db.flush()
        
        if 'posts' in page_data:
            self._save_posts(page.id, page_data['posts'])
        
        if 'employees' in page_data:
            self._save_employees(page.id, page_data['employees'])
        
        self.db.commit()
        self.db.refresh(page)
        return page
    
    def _save_posts(self, page_id: int, posts_data: List[Dict]):
        for post_data in posts_data:
            existing_post = None
            if post_data.get('linkedin_post_id'):
                existing_post = self.db.query(Post).filter(
                    Post.linkedin_post_id == post_data['linkedin_post_id']
                ).first()
            
            if existing_post:
                for key, value in post_data.items():
                    if key != 'comments':
                        setattr(existing_post, key, value)
            else:
                post = Post(page_id=page_id, **{k: v for k, v in post_data.items() if k != 'comments'})
                self.db.add(post)
                self.db.flush()
                
                if 'comments' in post_data and post_data['comments']:
                    self._save_comments(post.id, post_data['comments'])
    
    def _save_comments(self, post_id: int, comments_data: List[Dict]):
        for comment_data in comments_data:
            existing_comment = None
            if comment_data.get('linkedin_comment_id'):
                existing_comment = self.db.query(Comment).filter(
                    Comment.linkedin_comment_id == comment_data['linkedin_comment_id']
                ).first()
            
            if not existing_comment:
                comment = Comment(post_id=post_id, **comment_data)
                self.db.add(comment)
    
    def _save_employees(self, page_id: int, employees_data: List[Dict]):
        for emp_data in employees_data:
            existing_emp = self.db.query(Employee).filter(
                and_(
                    Employee.page_id == page_id,
                    Employee.name == emp_data.get('name', '')
                )
            ).first()
            
            if not existing_emp:
                employee = Employee(page_id=page_id, **emp_data)
                self.db.add(employee)
    
    def scrape_and_save(self, page_id: str) -> Page:
        logger.info(f"Scraping page: {page_id}")
        scraped_data = self.scraper.scrape_page(page_id)
        return self.create_or_update_page(scraped_data)
    
    def search_pages(
        self,
        min_followers: Optional[int] = None,
        max_followers: Optional[int] = None,
        name_search: Optional[str] = None,
        industry: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Page], int]:
        query = self.db.query(Page)
        
        if min_followers is not None:
            query = query.filter(Page.total_followers >= min_followers)
        if max_followers is not None:
            query = query.filter(Page.total_followers <= max_followers)
        if name_search:
            query = query.filter(Page.name.ilike(f"%{name_search}%"))
        if industry:
            query = query.filter(Page.industry.ilike(f"%{industry}%"))
        
        total = query.count()
        pages = query.offset(skip).limit(limit).all()
        
        return pages, total
    
    def get_page_followers(self, page_id: str, skip: int = 0, limit: int = 10) -> tuple[List, int]:
        page = self.get_page_by_id(page_id)
        if not page:
            return [], 0
        
        return [{"name": "Follower data requires API access", "note": "LinkedIn API required for follower list"}], 1
    
    def get_recent_posts(self, page_id: str, limit: int = 15) -> List[Post]:
        page = self.get_page_by_id(page_id)
        if not page:
            return []
        
        return self.db.query(Post).filter(
            Post.page_id == page.id
        ).order_by(Post.posted_at.desc()).limit(limit).all()

class WalletService:
    def __init__(self, db: Session):
        self.db = db
    
    def verify_signature(self, public_key: str, message: str, signature: str) -> bool:
        """
        Verify a Solana signature using the public key, message, and signature.
        Solana uses Ed25519 signatures which are 64 bytes.
        """
        try:
            # Decode the signature from base58 (Solana signatures are base58 encoded)
            signature_bytes = base58.b58decode(signature)
            
            # Decode the public key from base58
            public_key_bytes = base58.b58decode(public_key)
            
            # Verify the public key length (Ed25519 public keys are 32 bytes)
            if len(public_key_bytes) != 32:
                logger.error(f"Invalid public key length: {len(public_key_bytes)}")
                return False
            
            # Verify the signature length (Ed25519 signatures are 64 bytes)
            if len(signature_bytes) != 64:
                logger.error(f"Invalid signature length: {len(signature_bytes)}")
                return False
            
            # Create a VerifyKey from the public key
            verify_key = VerifyKey(public_key_bytes)
            
            # The message needs to be encoded
            message_bytes = message.encode('utf-8')
            
            # For Ed25519, nacl's verify method expects the signed message format
            # which is signature + message concatenated
            signed_message = signature_bytes + message_bytes
            
            # Verify the signature
            verify_key.verify(signed_message)
            return True
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False
    
    def get_or_create_wallet(self, wallet_address: str, public_key: str) -> Wallet:
        """
        Get existing wallet or create a new one.
        """
        wallet = self.db.query(Wallet).filter(
            Wallet.wallet_address == wallet_address
        ).first()
        
        if not wallet:
            wallet = Wallet(
                wallet_address=wallet_address,
                public_key=public_key,
                is_verified=False
            )
            self.db.add(wallet)
            self.db.flush()
        else:
            # Update public key if it changed
            if wallet.public_key != public_key:
                wallet.public_key = public_key
            wallet.last_connected_at = datetime.now(timezone.utc)
        
        return wallet
    
    def verify_wallet(self, wallet_address: str, signature: str, message: str) -> Optional[Wallet]:
        """
        Verify wallet ownership by checking signature.
        """
        wallet = self.db.query(Wallet).filter(
            Wallet.wallet_address == wallet_address
        ).first()
        
        if not wallet:
            return None
        
        # Verify the signature
        if self.verify_signature(wallet.public_key, message, signature):
            wallet.is_verified = True
            wallet.last_connected_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(wallet)
            return wallet
        
        return None
    
    def connect_wallet(self, wallet_address: str, public_key: str, signature: str, message: str) -> Optional[Wallet]:
        """
        Connect a wallet by verifying signature and creating/updating wallet record.
        """
        # First verify the signature
        if not self.verify_signature(public_key, message, signature):
            return None
        
        # Get or create wallet
        wallet = self.get_or_create_wallet(wallet_address, public_key)
        wallet.is_verified = True
        wallet.last_connected_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(wallet)
        return wallet
    
    def get_wallet_by_address(self, wallet_address: str) -> Optional[Wallet]:
        """
        Get wallet by address.
        """
        return self.db.query(Wallet).filter(
            Wallet.wallet_address == wallet_address
        ).first()
    
    def generate_access_token(self, wallet_address: str) -> str:
        """
        Generate JWT access token for authenticated wallet.
        """
        expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expiration_days)
        to_encode = {
            "wallet_address": wallet_address,
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
        return encoded_jwt

