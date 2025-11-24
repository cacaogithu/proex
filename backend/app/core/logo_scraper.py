import requests
from bs4 import BeautifulSoup
import os
from typing import Optional, List
from urllib.parse import urljoin, urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import io

# Configuration constants
STORAGE_BASE_DIR = os.getenv('STORAGE_BASE_DIR', 'backend/storage')
DEFAULT_REQUEST_TIMEOUT = 8  # Increased timeout
MIN_LOGO_SIZE = 2000  # Minimum file size in bytes for quality logos
MAX_LOGO_SIZE = 5000000  # 5MB max


class LogoScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self._logo_cache = {}
        self.brandfetch_key = os.environ.get('BRANDFETCH_API_KEY', '')
        self.max_parallel_methods = 4
    
    def get_company_logo(self, company_name: str, company_website: Optional[str] = None) -> Optional[str]:
        """
        Enhanced logo fetching with multiple methods and quality checks.
        
        Methods (in parallel):
        1. Brandfetch API (best quality)
        2. Clearbit API
        3. Logo.dev API
        4. Favicon extraction (high-res)
        5. Aggressive website scraping with advanced selectors
        
        Quality targets: 2KB-5MB for better variance
        """
        cache_key = company_website or company_name
        if cache_key in self._logo_cache:
            print(f"✓ Logo found in cache for: {company_name}")
            return self._logo_cache[cache_key]

        print(f"🔍 Searching logo for: {company_name}")

        # Try to extract domain from company name if no website provided
        if not company_website:
            # Clean company name and try common TLDs
            clean_name = company_name.lower().strip()
            # Remove common Portuguese words
            clean_name = clean_name.replace(' s.a.', '').replace(' s/a', '').replace(' ltda', '').replace(' ltda.', '').strip()
            clean_name = clean_name.replace(' ', '').replace('/', '')
            
            # Try common Brazilian domains
            for tld in ['.com.br', '.com', '.br', '.co']:
                test_domain = f"{clean_name}{tld}"
                print(f"  Trying domain: {test_domain}")
                logo_path = self._try_clearbit(test_domain)
                if logo_path:
                    self._logo_cache[cache_key] = logo_path
                    return logo_path
            
            print(f"⚠️ No website provided for {company_name} and domain lookup failed")
            self._logo_cache[cache_key] = None
            return None

        methods = [
            ('Clearbit', lambda: self._try_clearbit(company_website)),
            ('Logo.dev', lambda: self._try_logodev(company_website)),
            ('Favicon', lambda: self._try_favicon(company_website)),
        ]

        if self.brandfetch_key:
            methods.insert(0, ('Brandfetch', lambda: self._try_brandfetch(company_website)))

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
                        print(f"✓ Logo found via {method_name}")
                        for f in future_to_method:
                            f.cancel()
                        break
                except Exception as exc:
                    pass

        # Aggressive website scraping if APIs fail
        if not logo_path:
            logo_path = self._scrape_website_logo_advanced(company_website)

        if logo_path:
            self._logo_cache[cache_key] = logo_path
        else:
            print(f"⚠️ Could not find logo for {company_name}")
            self._logo_cache[cache_key] = None

        return logo_path
    
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
            
            # Try common high-res favicon paths (in order of quality)
            favicon_paths = [
                f"{website}/apple-touch-icon.png",
                f"{website}/apple-touch-icon-precomposed.png",
                f"{website}/favicon-512x512.png",
                f"{website}/favicon-256x256.png",
                f"{website}/favicon-196x196.png",
                f"{website}/favicon-192x192.png",
                f"{website}/favicon-128x128.png",
                f"{website}/favicon-96x96.png",
                f"{website}/favicon.ico",
            ]
            
            for favicon_url in favicon_paths:
                try:
                    response = requests.get(favicon_url, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        size = len(response.content)
                        if MIN_LOGO_SIZE <= size <= MAX_LOGO_SIZE:
                            logo_path = self._save_logo(domain.replace('www.', ''), response.content)
                            print(f"✓ Logo found via favicon: {domain} ({size} bytes)")
                            return logo_path
                except (requests.RequestException, IOError, OSError):
                    continue
        except Exception as e:
            print(f"Favicon extraction failed: {str(e)}")
        
        return None
    
    def _scrape_website_logo(self, website: str) -> Optional[str]:
        """Scrape logo directly from company website - basic method"""
        try:
            if not website.startswith('http'):
                website = f"https://{website}"
            
            response = requests.get(website, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            
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
                    logo_response = requests.get(logo_url, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
                    if logo_response.status_code == 200 and len(logo_response.content) >= MIN_LOGO_SIZE:
                        domain = urlparse(website).netloc.replace('www.', '')
                        logo_path = self._save_logo(domain, logo_response.content)
                        print(f"✓ Logo scraped from website: {domain}")
                        return logo_path
        except Exception as e:
            print(f"Website scraping failed: {str(e)}")
        
        return None
    
    def _scrape_website_logo_advanced(self, website: str) -> Optional[str]:
        """Advanced website scraping with comprehensive selectors and heuristics"""
        try:
            if not website.startswith('http'):
                website = f"https://{website}"
            
            response = requests.get(website, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Comprehensive logo selectors
            logo_selectors = [
                # Direct logo matches
                'img[class*="logo" i]',
                'img[id*="logo" i]',
                'img[src*="logo" i]',
                'img[alt*="logo" i]',
                
                # Container-based
                'a[class*="logo" i] img',
                'div[class*="logo" i] img',
                '[class*="navbar" i] img',
                '[class*="header" i] img',
                '[class*="brand" i] img',
                
                # SVG logos
                'svg[class*="logo" i]',
                'svg[id*="logo" i]',
                
                # Header/nav images
                'header img',
                'nav img',
                '[role="banner"] img',
                
                # Links containing images (often logo placement)
                'a[href="/"] img',
                'a[href="./"] img',
                'a img[alt]',
            ]
            
            found_logos: List[tuple] = []
            
            # Collect all candidates with quality metrics
            for selector in logo_selectors:
                try:
                    elements = soup.select(selector)
                    for elem in elements:
                        if elem.name == 'img':
                            src = elem.get('src') or elem.get('data-src')
                            alt = elem.get('alt', '').lower()
                            if src and ('logo' in alt or 'brand' in alt or not alt):
                                logo_url = urljoin(website, src)
                                found_logos.append((logo_url, elem))
                        elif elem.name == 'svg':
                            found_logos.append((None, elem))  # SVG case
                except:
                    pass
            
            # Try each logo URL
            domain = urlparse(website).netloc.replace('www.', '')
            
            for logo_url, elem in found_logos:
                if not logo_url:
                    continue
                
                try:
                    logo_response = requests.get(logo_url, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
                    if logo_response.status_code == 200:
                        size = len(logo_response.content)
                        # Accept logos in 2KB-5MB range for quality variance
                        if MIN_LOGO_SIZE <= size <= MAX_LOGO_SIZE:
                            logo_path = self._save_logo(domain, logo_response.content)
                            print(f"✓ Logo scraped (advanced): {domain} ({size} bytes)")
                            return logo_path
                except:
                    pass
            
            # If no logos found with quality check, be less strict
            for logo_url, elem in found_logos:
                if not logo_url:
                    continue
                try:
                    logo_response = requests.get(logo_url, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
                    if logo_response.status_code == 200 and len(logo_response.content) > 500:
                        logo_path = self._save_logo(domain, logo_response.content)
                        print(f"✓ Logo scraped (advanced, relaxed): {domain}")
                        return logo_path
                except:
                    pass
        
        except Exception as e:
            print(f"Advanced website scraping failed: {str(e)}")
        
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
