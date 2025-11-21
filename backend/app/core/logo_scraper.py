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
        # Brandfetch API key (free tier: 100 requests/month)
        self.brandfetch_key = os.environ.get('BRANDFETCH_API_KEY', '')
    
    def get_company_logo(self, company_name: str, company_website: Optional[str] = None) -> Optional[str]:
        """
        Tries to fetch company logo using multiple methods:
        1. Brandfetch API (best database)
        2. Clearbit API (free tier)
        3. Logo.dev API
        4. Favicon extraction
        5. Direct website scraping
        6. Generate placeholder logo as fallback

        Returns: Path to downloaded logo or placeholder
        """
        # Check cache first
        cache_key = company_website or company_name
        if cache_key in self._logo_cache:
            cached_logo = self._logo_cache[cache_key]
            if cached_logo and os.path.exists(cached_logo):
                print(f"✓ Logo found in cache for: {company_name}")
                return cached_logo

        print(f"🔍 Searching logo for: {company_name} (website: {company_website})")

        logo_path = None

        # Method 1: Try Brandfetch API (best database)
        if company_website and self.brandfetch_key:
            print(f"   → Trying Brandfetch API...")
            logo_path = self._try_brandfetch(company_website)
            if logo_path and os.path.exists(logo_path):
                self._logo_cache[cache_key] = logo_path
                return logo_path

        # Method 2: Try Clearbit API (good fallback)
        if company_website:
            print(f"   → Trying Clearbit API...")
            logo_path = self._try_clearbit(company_website)
            if logo_path and os.path.exists(logo_path):
                self._logo_cache[cache_key] = logo_path
                return logo_path

        # Method 3: Try Logo.dev API
        if company_website:
            print(f"   → Trying Logo.dev API...")
            logo_path = self._try_logodev(company_website)
            if logo_path and os.path.exists(logo_path):
                self._logo_cache[cache_key] = logo_path
                return logo_path

        # Method 4: Try favicon extraction (more reliable than full scraping)
        if company_website:
            print(f"   → Trying favicon extraction...")
            logo_path = self._try_favicon(company_website)
            if logo_path and os.path.exists(logo_path):
                self._logo_cache[cache_key] = logo_path
                return logo_path

        # Method 5: Try scraping company website directly
        if company_website:
            print(f"   → Trying website scraping...")
            logo_path = self._scrape_website_logo(company_website)
            if logo_path and os.path.exists(logo_path):
                self._logo_cache[cache_key] = logo_path
                return logo_path

        # Method 6: Generate placeholder logo with company initials
        print(f"   → Generating placeholder logo for: {company_name}")
        logo_path = self._generate_placeholder_logo(company_name)
        if logo_path and os.path.exists(logo_path):
            self._logo_cache[cache_key] = logo_path
            print(f"✓ Placeholder logo created for: {company_name}")
            return logo_path

        print(f"⚠️ Could not find or create logo for {company_name}")
        self._logo_cache[cache_key] = None
        return None
    
    def _try_brandfetch(self, website: str) -> Optional[str]:
        """Use Brandfetch API - excellent logo database"""
        try:
            domain = urlparse(website).netloc or website
            domain = domain.replace('www.', '')
            
            # Brandfetch API endpoint
            api_url = f"https://api.brandfetch.io/v2/brands/{domain}"
            headers = {**self.headers, 'Authorization': f'Bearer {self.brandfetch_key}'}
            
            response = requests.get(api_url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Try to get the logo from the response
                logos = data.get('logos', [])
                if logos and len(logos) > 0:
                    logo_url = logos[0].get('formats', [{}])[0].get('src')
                    if logo_url:
                        logo_response = requests.get(logo_url, headers=self.headers, timeout=5)
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
    
    def _try_logodev(self, website: str) -> Optional[str]:
        """Use Logo.dev API - alternative to Clearbit"""
        try:
            import os
            domain = urlparse(website).netloc or website
            domain = domain.replace('www.', '')

            # Security: Get API key from environment variable
            logodev_token = os.getenv('LOGODEV_API_KEY', 'pk_X-1ZO13CRYuAq5BIwG4BQA')  # Fallback for backward compatibility
            logodev_url = f"https://img.logo.dev/{domain}?token={logodev_token}"

            response = requests.get(logodev_url, headers=self.headers, timeout=3)
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
                    response = requests.get(favicon_url, headers=self.headers, timeout=3)
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

    def _generate_placeholder_logo(self, company_name: str) -> Optional[str]:
        """Generate a placeholder logo with company initials using SVG"""
        try:
            # Create logos directory
            logos_dir = "backend/storage/logos"
            os.makedirs(logos_dir, exist_ok=True)

            # Get initials (up to 2-3 characters)
            words = company_name.split()
            if len(words) >= 2:
                initials = ''.join(word[0].upper() for word in words[:3] if word)
            else:
                initials = company_name[:3].upper()

            # Clean for filename
            safe_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')

            # Generate a color based on company name (deterministic)
            hash_value = sum(ord(c) for c in company_name)
            colors = [
                ('#1976d2', '#0d47a1'),  # Blue
                ('#388e3c', '#1b5e20'),  # Green
                ('#7b1fa2', '#4a148c'),  # Purple
                ('#d32f2f', '#b71c1c'),  # Red
                ('#f57c00', '#e65100'),  # Orange
                ('#0097a7', '#006064'),  # Teal
                ('#5d4037', '#3e2723'),  # Brown
                ('#455a64', '#263238'),  # Blue Grey
            ]
            color_pair = colors[hash_value % len(colors)]

            # Calculate font size based on initials length
            font_size = 48 if len(initials) <= 2 else 36 if len(initials) == 3 else 28

            # Create SVG placeholder
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="100" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:{color_pair[0]};stop-opacity:1" />
            <stop offset="100%" style="stop-color:{color_pair[1]};stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect width="200" height="100" rx="10" fill="url(#grad)"/>
    <text x="100" y="58" font-family="Arial, Helvetica, sans-serif" font-size="{font_size}"
          font-weight="bold" fill="white" text-anchor="middle" dominant-baseline="middle">
        {initials}
    </text>
</svg>'''

            logo_path = f"{logos_dir}/{safe_name}_placeholder.svg"

            with open(logo_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)

            return logo_path

        except Exception as e:
            print(f"Error generating placeholder logo: {str(e)}")
            return None
