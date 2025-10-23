import requests
from bs4 import BeautifulSoup
import os
from typing import Optional
from urllib.parse import urljoin, urlparse
import time


class LogoScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Cache logos during a single run to avoid re-fetching
        self._logo_cache = {}
    
    def get_company_logo(self, company_name: str, company_website: Optional[str] = None) -> Optional[str]:
        """
        Tries to fetch company logo using multiple methods:
        1. Clearbit API (free tier)
        2. Direct website scraping
        3. Google search fallback
        
        Returns: Path to downloaded logo or None
        """
        # Check cache first
        cache_key = company_website or company_name
        if cache_key in self._logo_cache:
            print(f"✓ Logo found in cache for: {company_name}")
            return self._logo_cache[cache_key]
        
        print(f"🔍 Searching logo for: {company_name}")
        
        logo_path = None
        
        # Method 1: Try Clearbit API (best quality, free tier available)
        if company_website:
            logo_path = self._try_clearbit(company_website)
            if logo_path:
                self._logo_cache[cache_key] = logo_path
                return logo_path
        
        # Method 2: Try scraping company website directly
        if company_website:
            logo_path = self._scrape_website_logo(company_website)
            if logo_path:
                self._logo_cache[cache_key] = logo_path
                return logo_path
        
        # Method 3: Try Google Images search as fallback
        logo_path = self._google_logo_search(company_name)
        if logo_path:
            self._logo_cache[cache_key] = logo_path
            return logo_path
        
        print(f"⚠️ Could not find logo for {company_name}")
        self._logo_cache[cache_key] = None
        return None
    
    def _try_clearbit(self, website: str) -> Optional[str]:
        """Use Clearbit Logo API - free tier, no auth required"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Extract domain from website
                domain = urlparse(website).netloc or website
                domain = domain.replace('www.', '')
                
                clearbit_url = f"https://logo.clearbit.com/{domain}"
                
                response = requests.get(clearbit_url, headers=self.headers, timeout=3)
                if response.status_code == 200:
                    # Save logo
                    logo_path = self._save_logo(domain, response.content)
                    print(f"✓ Logo found via Clearbit: {domain}")
                    return logo_path
            except requests.Timeout:
                if attempt < max_retries - 1:
                    print(f"Clearbit timeout, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(0.5)
                    continue
            except Exception as e:
                print(f"Clearbit failed: {str(e)}")
                break
        
        return None
    
    def _scrape_website_logo(self, website: str) -> Optional[str]:
        """Scrape logo directly from company website"""
        try:
            # Ensure website has protocol
            if not website.startswith('http'):
                website = f"https://{website}"
            
            response = requests.get(website, headers=self.headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for common logo patterns
            logo_selectors = [
                'img[class*="logo" i]',
                'img[id*="logo" i]',
                'a[class*="logo" i] img',
                'div[class*="logo" i] img',
                'header img:first-of-type',
            ]
            
            for selector in logo_selectors:
                logo = soup.select_one(selector)
                if logo and logo.get('src'):
                    logo_url = urljoin(website, str(logo['src']))
                    
                    # Download logo
                    logo_response = requests.get(logo_url, headers=self.headers, timeout=5)
                    if logo_response.status_code == 200:
                        domain = urlparse(website).netloc.replace('www.', '')
                        logo_path = self._save_logo(domain, logo_response.content)
                        print(f"✓ Logo scraped from website: {domain}")
                        return logo_path
        except Exception as e:
            print(f"Website scraping failed: {str(e)}")
        
        return None
    
    def _google_logo_search(self, company_name: str) -> Optional[str]:
        """
        Fallback: Try to find logo via Google Images
        Note: This is a simplified version. For production, consider using Google Custom Search API
        """
        try:
            # For now, return None - would require Google API key
            # In production, implement Google Custom Search API here
            pass
        except Exception as e:
            print(f"Google search failed: {str(e)}")
        
        return None
    
    def _save_logo(self, company_identifier: str, image_data: bytes) -> str:
        """Save logo to storage and return path"""
        # Create logos directory
        logos_dir = "backend/storage/logos"
        os.makedirs(logos_dir, exist_ok=True)
        
        # Clean company name for filename
        safe_name = "".join(c for c in company_identifier if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        
        # Detect image format from content
        if image_data.startswith(b'\x89PNG'):
            ext = '.png'
        elif image_data.startswith(b'\xff\xd8'):
            ext = '.jpg'
        elif image_data.startswith(b'GIF'):
            ext = '.gif'
        elif b'<svg' in image_data[:100].lower():
            ext = '.svg'
        else:
            ext = '.png'  # default
        
        logo_path = f"{logos_dir}/{safe_name}{ext}"
        
        with open(logo_path, 'wb') as f:
            f.write(image_data)
        
        return logo_path
