import requests
import tempfile
import os
from pathlib import Path
from typing import List, Tuple
from pdf2image import convert_from_path
from PIL import Image
import base64
from io import BytesIO
import time

from config import Config

# Add poppler to PATH if on Windows
if os.name == 'nt':  # Windows
    poppler_path = r"C:\Program Files\poppler\Library\bin"
    if os.path.exists(poppler_path) and poppler_path not in os.environ['PATH']:
        os.environ['PATH'] += os.pathsep + poppler_path


class DocumentProcessor:
    """Handle document download and conversion"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def download_document(self, url: str, max_retries: int = 3) -> Tuple[str, str]:
        """
        Download document from URL with retry logic

        Args:
            url: Document URL
            max_retries: Maximum number of retry attempts

        Returns:
            Tuple of (file_path, file_type)
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                print(f"📥 Download attempt {attempt}/{max_retries}: {url}")

                # Add headers to mimic browser request and bypass WAF
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/pdf,application/octet-stream,image/*,*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }

                response = requests.get(
                    url,
                    timeout=Config.DOWNLOAD_TIMEOUT,
                    headers=headers,
                    allow_redirects=True,
                    stream=True,  # Stream download for large files
                    verify=True   # Verify SSL certificates
                )
                response.raise_for_status()

                # Download content
                content = response.content

                # Check if response has content
                content_length = response.headers.get('content-length')
                response_content_type = response.headers.get('content-type', '').lower()

                # Detect WAF challenges or HTML responses when expecting PDF
                if 'html' in response_content_type and url.lower().endswith('.pdf'):
                    raise Exception(
                        f"Server returned HTML instead of PDF (likely WAF/bot protection). "
                        f"Content-Type: {response_content_type}. "
                        f"This URL may require browser authentication or may be blocking automated requests."
                    )

                if content_length and int(content_length) == 0:
                    raise Exception("Server returned empty file (Content-Length: 0)")

                # Validate downloaded content
                if not content or len(content) == 0:
                    raise Exception(f"Downloaded file is empty (0 bytes)")

                print(f"✅ Downloaded {len(content)} bytes")

                # Determine file type from content-type or URL
                content_type = response.headers.get('content-type', '').lower()

                if 'pdf' in content_type or url.lower().endswith('.pdf'):
                    file_ext = 'pdf'
                elif any(img_type in content_type for img_type in ['png', 'jpeg', 'jpg']):
                    file_ext = content_type.split('/')[-1]
                else:
                    # Default to pdf if unclear
                    file_ext = 'pdf'

                # Save to temp file
                temp_file = os.path.join(self.temp_dir, f"document.{file_ext}")
                with open(temp_file, 'wb') as f:
                    f.write(content)

                # Verify file was written correctly
                file_size = os.path.getsize(temp_file)
                if file_size == 0:
                    raise Exception("Failed to write file to disk (0 bytes)")

                print(f"✅ Saved to temp file: {file_size} bytes")
                return temp_file, file_ext

            except requests.RequestException as e:
                last_error = f"Request error: {str(e)}"
                print(f"❌ Attempt {attempt} failed: {last_error}")

                # Wait before retry (exponential backoff)
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # 2, 4, 8 seconds
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)

            except Exception as e:
                last_error = str(e)
                print(f"❌ Attempt {attempt} failed: {last_error}")

                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)

        # All attempts failed
        raise Exception(f"Failed to download document after {max_retries} attempts. Last error: {last_error}")
    
    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF to list of PIL Images
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of PIL Image objects
        """
        try:
            images = convert_from_path(
                pdf_path,
                dpi=Config.IMAGE_DPI,
                fmt='png'
            )
            return images
        except Exception as e:
            raise Exception(f"Failed to convert PDF to images: {str(e)}")
    
    def load_image(self, image_path: str) -> Image.Image:
        """Load single image file"""
        try:
            return Image.open(image_path)
        except Exception as e:
            raise Exception(f"Failed to load image: {str(e)}")
    
    def process_document(self, document_path: str) -> List[Image.Image]:
        """
        Download and convert document to images

        Args:
            document_path: Document URL or local file path

        Returns:
            List of PIL Images (one per page)
        """
        # Check if it's a local file path
        if os.path.isfile(document_path):
            file_path = document_path
            # Determine file type from extension
            file_ext = Path(document_path).suffix.lower().lstrip('.')
            if file_ext not in ['pdf', 'png', 'jpg', 'jpeg']:
                file_ext = 'pdf'  # Default
            file_type = file_ext
        else:
            # It's a URL - download it
            file_path, file_type = self.download_document(document_path)

        # Convert to images
        if file_type == 'pdf':
            images = self.pdf_to_images(file_path)
        else:
            images = [self.load_image(file_path)]

        if len(images) > Config.MAX_PAGES_PER_DOCUMENT:
            raise Exception(
                f"Document has {len(images)} pages, "
                f"exceeds maximum of {Config.MAX_PAGES_PER_DOCUMENT}"
            )

        return images
    
    @staticmethod
    def image_to_base64(image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')
    
    @staticmethod
    def get_image_media_type(image: Image.Image) -> str:
        """Get media type for image"""
        format_map = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'JPG': 'image/jpeg',
            'WEBP': 'image/webp'
        }
        return format_map.get(image.format, 'image/png')
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass


# Utility function for quick testing
def test_processor():
    """Test document processor with a sample URL"""
    processor = DocumentProcessor()
    
    # Test URL (replace with actual test URL)
    test_url = "https://example.com/sample.pdf"
    
    try:
        images = processor.process_document(test_url)
        print(f"✅ Successfully processed document: {len(images)} pages")
        return images
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        processor.cleanup()


if __name__ == "__main__":
    test_processor()