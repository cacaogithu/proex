import requests
from bs4 import BeautifulSoup
import os
from typing import Optional
from urllib.parse import urljoin, urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pdfplumber
import io
from PIL import Image

# Configuration constants
STORAGE_BASE_DIR = os.getenv('STORAGE_BASE_DIR', 'backend/storage')
DEFAULT_REQUEST_TIMEOUT = 5  # seconds


class LogoScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Cache logos during a single run to avoid re-fetching
        self._logo_cache = {}
        # Brandfetch API key (free tier: 100 requests/month)
        self.brandfetch_key = os.environ.get('BRANDFETCH_API_KEY', '')
        # Max concurrent logo fetching methods
        self.max_parallel_methods = 3
    
    def set_pdf_path(self, pdf_path: str) -> None:
        """Set the path to scan for logos (e.g., testimonial PDF)"""
        self.pdf_path = pdf_path
    
    def get_company_logo(self, company_name: str, company_website: Optional[str] = None, pdf_path: Optional[str] = None) -> Optional[str]:
        """
        Tries to fetch company logo using multiple methods in parallel for speed.

        Methods tried (in order of priority):
        1. Extract from PDF if provided (FASTEST - instant)
        2. Brandfetch API (if key available)
        3. Clearbit API (free tier)
        4. Logo.dev API
        5. Favicon extraction
        6. Direct website scraping

        Returns: Path to downloaded logo or None
        """
        # Check cache first
        cache_key = company_website or company_name
        if cache_key in self._logo_cache:
            print(f"✓ Logo found in cache for: {company_name}")
            return self._logo_cache[cache_key]

        print(f"🔍 Searching logo for: {company_name}")
        
        # TRY PDF EXTRACTION FIRST (fast and reliable)
        if pdf_path and os.path.exists(pdf_path):
            logo_path = self._extract_logo_from_pdf(pdf_path, company_name)
            if logo_path:
                print(f"✓ Logo extracted from PDF: {company_name}")
                self._logo_cache[cache_key] = logo_path
                return logo_path

        if not company_website:
            print(f"⚠️ No website or PDF provided for {company_name}, skipping logo fetch")
            self._logo_cache[cache_key] = None
            return None

        # Build list of methods to try
        methods = [
            ('Clearbit', lambda: self._try_clearbit(company_website)),
            ('Logo.dev', lambda: self._try_logodev(company_website)),
            ('Favicon', lambda: self._try_favicon(company_website)),
        ]

        # Add Brandfetch if API key is available
        if self.brandfetch_key:
            methods.insert(0, ('Brandfetch', lambda: self._try_brandfetch(company_website)))

        # Try all methods in parallel, return first successful result
        logo_path = None
        with ThreadPoolExecutor(max_workers=self.max_parallel_methods) as executor:
            future_to_method = {
                executor.submit(method_func): method_name
                for method_name, method_func in methods
            }

            for future in as_completed(future_to_method):
                method_name = future_to_method[future]
                try:
                    result = future.result()
                    if result:
                        logo_path = result
                        print(f"✓ Logo found via {method_name} (parallel fetch)")
                        # Cancel remaining tasks since we found a logo
                        for f in future_to_method:
                            f.cancel()
                        break
                except Exception as exc:
                    # Silent failure - let other methods try
                    pass

        # If parallel methods failed, try website scraping (slower, so do it last)
        if not logo_path:
            logo_path = self._scrape_website_logo(company_website)

        if logo_path:
            self._logo_cache[cache_key] = logo_path
        else:
            print(f"⚠️ Could not find logo for {company_name}")
            self._logo_cache[cache_key] = None

        return logo_path
    
    def _extract_logo_from_pdf(self, pdf_path: str, company_name: str) -> Optional[str]:
        """Extract logo/images directly from PDF - FAST and RELIABLE"""
        try:
            if not os.path.exists(pdf_path):
                return None
            
            with pdfplumber.open(pdf_path) as pdf:
                # Scan first 2 pages (logos usually at top)
                pages_to_scan = min(2, len(pdf.pages))
                
                for page_idx in range(pages_to_scan):
                    page = pdf.pages[page_idx]
                    
                    # Extract images from page
                    if hasattr(page, 'images') and page.images:
                        for img_idx, img in enumerate(page.images):
                            # Get image coordinates
                            x0, top, x1, bottom = img['x0'], img['top'], img['x1'], img['bottom']
                            width = x1 - x0
                            height = bottom - top
                            
                            # Prefer images in top area (headers/logos) and reasonable size
                            is_header_position = top < (page.height * 0.3)  # Top 30% of page
                            is_reasonable_size = 50 < width < 400 and 20 < height < 400
                            
                            if is_header_position and is_reasonable_size:
                                try:
                                    # Extract the image
                                    cropped_page = page.within_bbox((x0, top, x1, bottom))
                                    im = cropped_page.to_image(resolution=150)
                                    
                                    # Save extracted logo
                                    if im and im.original:
                                        image_data = io.BytesIO()
                                        im.original.save(image_data, format='PNG')
                                        image_data.seek(0)
                                        
                                        logo_path = self._save_logo(company_name, image_data.getvalue())
                                        return logo_path
                                except Exception as e:
                                    print(f"Error extracting image from PDF: {str(e)}")
                                    continue
        
        except Exception as e:
            print(f"PDF logo extraction failed: {str(e)}")
        
        return None
    
    def _try_brandfetch(self, website: str) -> Optional[str]:
        """Use Brandfetch API - excellent logo database"""
        try:
            domain = urlparse(website).netloc or website
            domain = domain.replace('www.', '')
            
            # Brandfetch API endpoint
            api_url = f"https://api.brandfetch.io/v2/brands/{domain}"
            headers = {**self.headers, 'Authorization': f'Bearer {self.brandfetch_key}'}
            
            response = requests.get(api_url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                # Try to get the logo from the response
                logos = data.get('logos', [])
                if logos and len(logos) > 0:
                    logo_url = logos[0].get('formats', [{}])[0].get('src')
                    if logo_url:
                        logo_response = requests.get(logo_url, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
                        if logo_response.status_code == 200:
                            logo_path = self._save_logo(domain, logo_response.content)
                            print(f"✓ Logo found via Brandfetch: {domain}")
                            return logo_path
        except Exception as e:
            print(f"Brandfetch failed: {str(e)}")
        
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
                
                response = requests.get(clearbit_url, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
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
    
    def _try_logodev(self, website: str) -> Optional[str]:
        """Use Logo.dev API - alternative to Clearbit"""
        try:
            import os
            domain = urlparse(website).netloc or website
            domain = domain.replace('www.', '')

            # Security: Get API key from environment variable
            logodev_token = os.getenv('LOGODEV_API_KEY', 'pk_X-1ZO13CRYuAq5BIwG4BQA')  # Fallback for backward compatibility
            logodev_url = f"https://img.logo.dev/{domain}?token={logodev_token}"

            response = requests.get(logodev_url, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            if response.status_code == 200 and len(response.content) > 1000:  # Ensure it's not an error placeholder
                logo_path = self._save_logo(domain, response.content)
                print(f"✓ Logo found via Logo.dev: {domain}")
                return logo_path
        except Exception as e:
            print(f"Logo.dev failed: {str(e)}")
        
        return None
    
    def _try_favicon(self, website: str) -> Optional[str]:
        """Extract high-quality favicon as logo fallback"""
        try:
            if not website.startswith('http'):
                website = f"https://{website}"
            
            domain = urlparse(website).netloc or website
            
            # Try common high-res favicon paths
            favicon_paths = [
                f"{website}/apple-touch-icon.png",
                f"{website}/apple-touch-icon-precomposed.png",
                f"{website}/favicon-196x196.png",
                f"{website}/favicon-128x128.png",
                f"{website}/favicon.ico",
            ]
            
            for favicon_url in favicon_paths:
                try:
                    response = requests.get(favicon_url, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
                    if response.status_code == 200 and len(response.content) > 500:
                        logo_path = self._save_logo(domain.replace('www.', ''), response.content)
                        print(f"✓ Logo found via favicon: {domain}")
                        return logo_path
                except (requests.RequestException, IOError, OSError):
                    # Try next favicon path
                    continue
        except Exception as e:
            print(f"Favicon extraction failed: {str(e)}")
        
        return None
    
    def _scrape_website_logo(self, website: str) -> Optional[str]:
        """Scrape logo directly from company website"""
        try:
            # Ensure website has protocol
            if not website.startswith('http'):
                website = f"https://{website}"
            
            response = requests.get(website, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
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
                    logo_response = requests.get(logo_url, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
                    if logo_response.status_code == 200:
                        domain = urlparse(website).netloc.replace('www.', '')
                        logo_path = self._save_logo(domain, logo_response.content)
                        print(f"✓ Logo scraped from website: {domain}")
                        return logo_path
        except Exception as e:
            print(f"Website scraping failed: {str(e)}")
        
        return None
    
    
    
    def _save_logo(self, company_identifier: str, image_data: bytes) -> str:
        """Save logo to storage and return path"""
        # Create logos directory (use centralized configuration)
        logos_dir = os.path.join(STORAGE_BASE_DIR, "logos")
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
