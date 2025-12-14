from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedInScraper:
    def __init__(self):
        self.base_url = "https://www.linkedin.com"
        
    def scrape_page(self, page_id: str) -> Dict:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            try:
                url = f"{self.base_url}/company/{page_id}/"
                logger.info(f"Scraping page: {url}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(3)
                
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                page_data = self._extract_page_details(soup, page_id, url)
                page_data['posts'] = self._extract_posts(page, soup, page_id)
                page_data['employees'] = self._extract_employees(page, page_id)
                
                browser.close()
                return page_data
                
            except Exception as e:
                logger.error(f"Error scraping page {page_id}: {str(e)}")
                browser.close()
                raise
    
    def _extract_page_details(self, soup: BeautifulSoup, page_id: str, url: str) -> Dict:
        data = {
            'page_id': page_id,
            'url': url,
            'name': '',
            'linkedin_id': '',
            'profile_picture': '',
            'description': '',
            'website': '',
            'industry': '',
            'total_followers': 0,
            'head_count': None,
            'specialities': ''
        }
        
        try:
            name_elem = soup.find('h1', class_=re.compile(r'.*org-top-card.*'))
            if not name_elem:
                name_elem = soup.find('h1')
            if name_elem:
                data['name'] = name_elem.get_text(strip=True)
            
            img_elem = soup.find('img', class_=re.compile(r'.*org-top-card.*'))
            if not img_elem:
                img_elem = soup.find('img', {'alt': data['name']})
            if img_elem and img_elem.get('src'):
                data['profile_picture'] = img_elem['src']
            
            desc_elem = soup.find('div', class_=re.compile(r'.*org-about-us-organization-description.*'))
            if desc_elem:
                data['description'] = desc_elem.get_text(strip=True)
            
            about_section = soup.find('section', {'id': 'about'})
            if about_section:
                for dt in about_section.find_all('dt'):
                    label = dt.get_text(strip=True).lower()
                    dd = dt.find_next_sibling('dd')
                    if dd:
                        value = dd.get_text(strip=True)
                        if 'website' in label:
                            link = dd.find('a')
                            if link:
                                data['website'] = link.get('href', '')
                        elif 'industry' in label:
                            data['industry'] = value
                        elif 'company size' in label or 'headcount' in label:
                            match = re.search(r'(\d+)', value.replace(',', ''))
                            if match:
                                data['head_count'] = int(match.group(1))
                        elif 'specialties' in label or 'specialities' in label:
                            data['specialities'] = value
            
            followers_elem = soup.find(string=re.compile(r'followers', re.I))
            if followers_elem:
                parent = followers_elem.find_parent()
                if parent:
                    text = parent.get_text()
                    match = re.search(r'([\d,]+)\s*followers', text, re.I)
                    if match:
                        data['total_followers'] = int(match.group(1).replace(',', ''))
            
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    import json
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict):
                        if 'url' in json_data:
                            data['linkedin_id'] = json_data.get('url', '').split('/')[-1]
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error extracting page details: {str(e)}")
        
        return data
    
    def _extract_posts(self, page, soup: BeautifulSoup, page_id: str) -> List[Dict]:
        posts = []
        try:
            page.goto(f"https://www.linkedin.com/company/{page_id}/posts/", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            
            for _ in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            post_elements = soup.find_all('div', class_=re.compile(r'.*feed-shared-update-v2.*'), limit=25)
            
            for post_elem in post_elements[:25]:
                post_data = self._extract_post_details(post_elem)
                if post_data:
                    post_data['comments'] = []
                    posts.append(post_data)
                    
        except Exception as e:
            logger.error(f"Error extracting posts: {str(e)}")
        
        return posts
    
    def _extract_post_details(self, post_elem) -> Optional[Dict]:
        try:
            post_data = {
                'linkedin_post_id': '',
                'content': '',
                'post_url': '',
                'likes_count': 0,
                'comments_count': 0,
                'shares_count': 0,
                'posted_at': None
            }
            
            content_elem = post_elem.find('div', class_=re.compile(r'.*feed-shared-text.*'))
            if content_elem:
                post_data['content'] = content_elem.get_text(strip=True)
            
            link_elem = post_elem.find('a', href=re.compile(r'/feed/update/'))
            if link_elem:
                post_data['post_url'] = link_elem.get('href', '')
                if post_data['post_url']:
                    match = re.search(r'/feed/update/([^/?]+)', post_data['post_url'])
                    if match:
                        post_data['linkedin_post_id'] = match.group(1)
            
            reactions = post_elem.find_all(string=re.compile(r'(\d+)\s*(reaction|like)', re.I))
            for reaction in reactions:
                match = re.search(r'(\d+)', reaction)
                if match:
                    count = int(match.group(1).replace(',', ''))
                    if count > post_data['likes_count']:
                        post_data['likes_count'] = count
            
            comments = post_elem.find_all(string=re.compile(r'(\d+)\s*comment', re.I))
            for comment in comments:
                match = re.search(r'(\d+)', comment)
                if match:
                    post_data['comments_count'] = int(match.group(1).replace(',', ''))
            
            shares = post_elem.find_all(string=re.compile(r'(\d+)\s*share', re.I))
            for share in shares:
                match = re.search(r'(\d+)', share)
                if match:
                    post_data['shares_count'] = int(match.group(1).replace(',', ''))
            
            time_elem = post_elem.find('time')
            if time_elem and time_elem.get('datetime'):
                try:
                    post_data['posted_at'] = datetime.fromisoformat(time_elem['datetime'].replace('Z', '+00:00'))
                except:
                    pass
            
            return post_data if post_data['content'] or post_data['linkedin_post_id'] else None
            
        except Exception as e:
            logger.error(f"Error extracting post details: {str(e)}")
            return None
    
    def _extract_employees(self, page, page_id: str) -> List[Dict]:
        employees = []
        try:
            page.goto(f"https://www.linkedin.com/company/{page_id}/people/", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            
            for _ in range(2):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            employee_elements = soup.find_all('li', class_=re.compile(r'.*org-people-profile-card.*'), limit=50)
            
            for emp_elem in employee_elements:
                emp_data = self._extract_employee_details(emp_elem)
                if emp_data:
                    employees.append(emp_data)
                    
        except Exception as e:
            logger.error(f"Error extracting employees: {str(e)}")
        
        return employees
    
    def _extract_employee_details(self, emp_elem) -> Optional[Dict]:
        try:
            emp_data = {
                'name': '',
                'profile_url': '',
                'profile_picture': '',
                'headline': '',
                'position': '',
                'linkedin_id': ''
            }
            
            name_elem = emp_elem.find('a', class_=re.compile(r'.*app-aware-link.*'))
            if name_elem:
                emp_data['name'] = name_elem.get_text(strip=True)
                emp_data['profile_url'] = name_elem.get('href', '')
                if emp_data['profile_url']:
                    match = re.search(r'/in/([^/?]+)', emp_data['profile_url'])
                    if match:
                        emp_data['linkedin_id'] = match.group(1)
            
            img_elem = emp_elem.find('img')
            if img_elem and img_elem.get('src'):
                emp_data['profile_picture'] = img_elem['src']
            
            headline_elem = emp_elem.find('div', class_=re.compile(r'.*org-people-profile-card__profile-title.*'))
            if headline_elem:
                emp_data['headline'] = headline_elem.get_text(strip=True)
                emp_data['position'] = emp_data['headline']
            
            return emp_data if emp_data['name'] else None
            
        except Exception as e:
            logger.error(f"Error extracting employee details: {str(e)}")
            return None

