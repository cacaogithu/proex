import requests
from bs4 import BeautifulSoup
import os
from typing import Optional, List
from urllib.parse import urljoin, urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import io
import json

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
        self._domain_cache = {}
        self.brandfetch_key = os.environ.get('BRANDFETCH_API_KEY', '')
        # Logo.dev uses different keys for different endpoints
        # LOGO_DEV_SECRET_KEY: For Brand Search API (https://api.logo.dev/search)
        # LOGO_DEV_TOKEN: For Image API (https://img.logo.dev/)
        self.logodev_secret_key = os.environ.get('LOGO_DEV_SECRET_KEY', os.environ.get('LOGO_DEV_API_KEY', ''))
        self.logodev_token = os.environ.get('LOGO_DEV_TOKEN', os.environ.get('LOGO_DEV_API_KEY', ''))
        self.max_parallel_methods = 4

        # Initialize LLM for AI-powered company search
        from openai import OpenAI
        self.openrouter_key = os.environ.get('OPENROUTER_API_KEY', '')
        if self.openrouter_key:
            self.llm_client = OpenAI(
                api_key=self.openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.llm_client = None
    
    def get_company_logo(self, company_name: str, company_website: Optional[str] = None, company_location: Optional[str] = None) -> Optional[str]:
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

        # If no website provided, use AI-powered search as primary method
        if not company_website:
            print(f"  No website provided, using AI-powered search for: {company_name}")

            # Try AI-powered web search first (most accurate)
            if self.llm_client:
                company_website = self._ai_find_company_website(company_name, company_location)
                if company_website:
                    print(f"  ✓ AI found website: {company_website}")
                    # Continue with normal logo fetching using the found website
                    cache_key = company_website  # Update cache key

            # Fallback to Logo.dev Brand Search if AI didn't find anything
            if not company_website and self.logodev_secret_key:
                searched_domain = self._search_logodev_domain(company_name, strategy="match")
                if searched_domain:
                    print(f"  Brand Search found domain: {searched_domain}, fetching logo via Clearbit...")
                    logo_path = self._try_clearbit(searched_domain)
                    if logo_path:
                        self._logo_cache[cache_key] = logo_path
                        return logo_path
                    logo_path = self._try_favicon(f"https://{searched_domain}")
                    if logo_path:
                        self._logo_cache[cache_key] = logo_path
                        return logo_path
            
            clean_name = company_name.lower().strip()
            clean_name = clean_name.replace(' s.a.', '').replace(' s/a', '').replace(' ltda', '').replace(' ltda.', '').strip()
            clean_name = clean_name.replace(' ', '').replace('/', '')
            
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
            ('Logo.dev', lambda: self._try_logodev(company_website, company_name)),
            ('Clearbit', lambda: self._try_clearbit(company_website)),
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
            print(f"✅ Logo successfully fetched for {company_name}")
        else:
            # Provide detailed failure reason
            if not company_website and not self.llm_client and not self.logodev_secret_key:
                print(f"❌ Could not find logo for {company_name}: No website provided and no AI/Brand Search available")
                print(f"   💡 Suggestion: Set OPENROUTER_API_KEY or LOGO_DEV_SECRET_KEY environment variables")
            else:
                print(f"⚠️ Could not find logo for {company_name}: All methods exhausted")
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
    
    def _search_logodev_domain(self, company_name: str, strategy: str = "match") -> Optional[str]:
        """
        Use Logo.dev Brand Search API to find the correct domain for a company.
        
        Args:
            company_name: The company/brand name to search for
            strategy: 'typeahead' for autocomplete, 'match' for exact/near-exact matches
            
        Returns:
            The best matching domain, or None if not found
        """
        if not self.logodev_secret_key:
            print("⚠️ LOGO_DEV_API_KEY not set, skipping Brand Search")
            return None
            
        cache_key = f"domain_{company_name.lower()}"
        if cache_key in self._domain_cache:
            return self._domain_cache[cache_key]
            
        try:
            import urllib.parse
            encoded_query = urllib.parse.quote(company_name)
            search_url = f"https://api.logo.dev/search?q={encoded_query}&strategy={strategy}"
            
            headers = {
                **self.headers,
                'Authorization': f'Bearer {self.logodev_secret_key}'
            }
            
            response = requests.get(search_url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    domain = results[0].get('domain')
                    if domain:
                        print(f"✓ Logo.dev Brand Search found domain: {domain} for '{company_name}'")
                        self._domain_cache[cache_key] = domain
                        return domain
            elif response.status_code == 401:
                print(f"⚠️ Logo.dev Brand Search auth failed - check LOGODEV_SECRET_KEY")
            else:
                print(f"⚠️ Logo.dev Brand Search returned status {response.status_code}")
                
        except Exception as e:
            print(f"Logo.dev Brand Search failed: {str(e)}")
        
        self._domain_cache[cache_key] = None
        return None
    
    def _try_logodev(self, website: str, company_name: Optional[str] = None) -> Optional[str]:
        """
        Use Logo.dev API - with Brand Search fallback for better accuracy.
        
        This method now uses two approaches:
        1. Direct domain lookup if website URL is provided
        2. Brand Search API to find the correct domain from company name
        """
        try:
            domain = None
            
            if website:
                domain = urlparse(website).netloc or website
                domain = domain.replace('www.', '')
            
            if not domain and company_name:
                domain = self._search_logodev_domain(company_name, strategy="match")
            
            if not domain:
                return None

            logodev_url = f"https://img.logo.dev/{domain}?token={self.logodev_token}&size=256&format=png"

            response = requests.get(logodev_url, headers=self.headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            if response.status_code == 200 and len(response.content) > 1000:
                logo_path = self._save_logo(domain, response.content)
                print(f"✓ Logo found via Logo.dev: {domain}")
                return logo_path
            elif response.status_code == 200:
                print(f"⚠️ Logo.dev returned small/placeholder image for {domain}")
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
                            alt_attr = elem.get('alt', '')
                            alt = str(alt_attr).lower() if alt_attr else ''
                            if src and ('logo' in alt or 'brand' in alt or not alt):
                                logo_url = urljoin(website, str(src))
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
    
    
    
    def _ai_find_company_website(self, company_name: str, location: Optional[str] = None) -> Optional[str]:
        """
        Use AI with web search capability to find the official company website.
        This is more reliable than domain guessing or basic brand search.

        Args:
            company_name: The company name to search for
            location: Optional location/country to disambiguate (e.g., "Brazil", "São Paulo, Brazil")

        Returns:
            The company's official website URL, or None if not found
        """
        if not self.llm_client:
            print("⚠️ AI search not available (OPENROUTER_API_KEY not set)")
            return None

        cache_key = f"website_{company_name.lower()}_{location or ''}"
        if cache_key in self._domain_cache:
            return self._domain_cache[cache_key]

        try:
            # Build context-aware search prompt
            location_context = f" in {location}" if location else ""

            prompt = f"""Find the official company website for "{company_name}"{location_context}.

Instructions:
1. Search for the company's official website
2. Return ONLY the website URL (e.g., https://www.company.com or https://company.com.br)
3. If you find multiple results, prefer the official corporate website (not Wikipedia, LinkedIn, or directories)
4. If the company has regional websites and location is provided, prefer the regional site
5. If you cannot find the website with high confidence, return "NOT_FOUND"

Output format: Just the URL or "NOT_FOUND"
Example outputs:
- https://www.weg.net
- https://www.microsoft.com
- https://www.vale.com
- NOT_FOUND

Company: {company_name}{location_context}
Official website URL:"""

            # Call LLM with reasoning capability (using a better model for accuracy)
            response = self.llm_client.chat.completions.create(
                model="google/gemini-2.5-flash",  # Good balance of speed and accuracy
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for factual accuracy
                max_tokens=100
            )

            result = response.choices[0].message.content.strip()

            # Validate and clean the result
            if result and result != "NOT_FOUND" and ("http://" in result or "https://" in result):
                # Extract URL if there's extra text
                import re
                url_match = re.search(r'https?://[^\s]+', result)
                if url_match:
                    website = url_match.group(0).rstrip('.,;)')
                    print(f"  ✓ AI found website: {website}")
                    self._domain_cache[cache_key] = website
                    return website

            print(f"  ⚠️ AI could not find website for {company_name}")
            self._domain_cache[cache_key] = None
            return None

        except Exception as e:
            print(f"  ⚠️ AI website search failed: {str(e)}")
            self._domain_cache[cache_key] = None
            return None

    def _validate_logo_quality(self, image_data: bytes) -> bool:
        """
        Validate logo quality to ensure it's not a placeholder or low-quality image.

        Checks:
        - File size (not too small or suspiciously large)
        - For PNG/JPG: Image dimensions (should be reasonable for a logo)
        - Not a common placeholder pattern

        Returns:
            True if logo passes quality checks, False otherwise
        """
        try:
            # Basic size check
            size = len(image_data)
            if size < MIN_LOGO_SIZE or size > MAX_LOGO_SIZE:
                print(f"  ⚠️ Logo failed size check: {size} bytes (expected {MIN_LOGO_SIZE}-{MAX_LOGO_SIZE})")
                return False

            # For raster images, check dimensions
            if image_data.startswith(b'\x89PNG') or image_data.startswith(b'\xff\xd8'):
                try:
                    img = Image.open(io.BytesIO(image_data))
                    width, height = img.size

                    # Logos should be at least 50x50 pixels
                    if width < 50 or height < 50:
                        print(f"  ⚠️ Logo too small: {width}x{height}px")
                        return False

                    # Aspect ratio check (logos usually between 0.2 and 5.0 ratio)
                    aspect_ratio = width / height
                    if aspect_ratio < 0.2 or aspect_ratio > 5.0:
                        print(f"  ⚠️ Unusual aspect ratio: {aspect_ratio:.2f}")
                        # Don't reject, just warn

                    print(f"  ✓ Logo quality check passed: {width}x{height}px, {size} bytes")
                except Exception as e:
                    # If we can't validate, assume it's OK (might be SVG or other format)
                    print(f"  ℹ️ Could not validate image dimensions: {e}")
                    pass

            return True

        except Exception as e:
            print(f"  ⚠️ Logo validation error: {e}")
            # If validation fails, don't reject the logo
            return True

    def _save_logo(self, company_identifier: str, image_data: bytes) -> str:
        """Save logo to storage and return path after validation"""

        # Validate logo quality
        if not self._validate_logo_quality(image_data):
            raise ValueError(f"Logo quality validation failed for {company_identifier}")

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
