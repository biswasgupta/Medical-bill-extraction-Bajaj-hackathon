import requests
import tempfile
import os
from pathlib import Path
from typing import List, Tuple
from pdf2image import convert_from_path
from PIL import Image
import base64
from io import BytesIO

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
            url: URL to download from
            max_retries: Maximum number of retry attempts

        Returns:
            Tuple of (file_path, file_type)
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        last_error = None
        for attempt in range(max_retries):
            try:
                print(f"📡 Download attempt {attempt + 1}/{max_retries}...")
                response = requests.get(url, timeout=Config.DOWNLOAD_TIMEOUT, headers=headers, allow_redirects=True)
                response.raise_for_status()

                # Check if content is empty
                if not response.content or len(response.content) == 0:
                    raise Exception("Downloaded file is empty (0 bytes)")

                # Log download details
                content_length = len(response.content)
                print(f"📦 Downloaded {content_length} bytes")

                # Determine file type from content-type or URL
                content_type = response.headers.get('content-type', '').lower()
                print(f"📄 Content-Type: {content_type}")

                # Check if we got HTML instead of the expected file type
                if 'html' in content_type or response.content[:15].lower().startswith(b'<!doctype html') or response.content[:6].lower().startswith(b'<html'):
                    raise Exception(f"Server returned HTML instead of a document. This could indicate: "
                                    f"1) The URL is incorrect, 2) The file requires authentication, "
                                    f"3) The server is blocking automated requests. "
                                    f"Content preview: {response.content[:200]}")

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
                    f.write(response.content)

                # Verify file was written correctly
                file_size = os.path.getsize(temp_file)
                if file_size == 0:
                    raise Exception(f"Saved file is empty (0 bytes) at {temp_file}")

                print(f"✅ File saved: {temp_file} ({file_size} bytes)")
                return temp_file, file_ext

            except requests.RequestException as e:
                last_error = f"Download failed: {str(e)}"
                print(f"⚠️ {last_error}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
            except Exception as e:
                last_error = str(e)
                print(f"⚠️ {last_error}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                continue

        raise Exception(f"Failed to download document after {max_retries} attempts. Last error: {last_error}")
    
    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF to list of PIL Images

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PIL Image objects
        """
        # Validate PDF file exists and has content
        if not os.path.exists(pdf_path):
            raise Exception(f"PDF file not found: {pdf_path}")

        file_size = os.path.getsize(pdf_path)
        if file_size == 0:
            raise Exception(f"PDF file is empty (0 bytes): {pdf_path}")

        print(f"📖 Converting PDF to images (file size: {file_size} bytes)...")

        # Validate PDF header
        try:
            with open(pdf_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    raise Exception(f"Invalid PDF file: File does not start with PDF header. Header: {header}")
        except Exception as e:
            raise Exception(f"Failed to validate PDF file: {str(e)}")

        try:
            images = convert_from_path(
                pdf_path,
                dpi=Config.IMAGE_DPI,
                fmt='png'
            )

            if not images or len(images) == 0:
                raise Exception("PDF conversion returned no images")

            print(f"✅ Converted PDF to {len(images)} images")
            return images

        except Exception as e:
            # Provide detailed error message
            error_msg = f"Failed to convert PDF to images: {str(e)}\n"
            error_msg += f"File: {pdf_path}\n"
            error_msg += f"File size: {file_size} bytes\n"

            # Check if it's a poppler issue
            if "poppler" in str(e).lower():
                error_msg += "This might be a poppler installation issue. Ensure poppler is installed on the server."

            raise Exception(error_msg)
    
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