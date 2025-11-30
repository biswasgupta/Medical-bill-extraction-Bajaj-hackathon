import requests
import tempfile
import os
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF
from PIL import Image
import base64
from io import BytesIO

from config import Config


class DocumentProcessor:
    """Handle document download and conversion (NO POPPLER NEEDED!)"""

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()

    def download_document(self, url: str, max_retries: int = 3) -> Tuple[str, str]:
        """
        Download document from URL with retry logic

        Returns:
            Tuple of (file_path, file_type)
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                # Add more headers to avoid being blocked
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'application/pdf,application/octet-stream,*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                }

                response = requests.get(
                    url,
                    timeout=Config.DOWNLOAD_TIMEOUT,
                    headers=headers,
                    allow_redirects=True,  # Follow redirects
                    stream=True  # Better for large files
                )
                response.raise_for_status()

                # Check if content is actually downloaded
                content_length = response.headers.get('content-length', '0')
                if len(response.content) == 0 and content_length == '0':
                    error_msg = (
                        f"Server returned empty content (0 bytes). "
                        f"Possible reasons:\n"
                        f"  1. URL requires authentication\n"
                        f"  2. Server blocking automated requests\n"
                        f"  3. Invalid or expired URL\n"
                        f"  4. Server-side error\n"
                        f"Please verify the URL is publicly accessible: {url}"
                    )
                    raise Exception(error_msg)

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
                    f.write(response.content)

                print(f"✅ Downloaded {len(response.content)} bytes from URL")
                return temp_file, file_ext

            except requests.RequestException as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"⚠️ Download attempt {attempt + 1} failed, retrying...")
                    continue  # Retry
                else:
                    raise Exception(f"Failed to download document after {max_retries} attempts. Last error: {str(e)}")

    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF to list of PIL Images using PyMuPDF (NO POPPLER NEEDED!)
        Optimized for large PDFs (100-150 pages)

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PIL Image objects
        """
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(pdf_path)
            images = []
            total_pages = len(pdf_document)

            print(f"📄 Converting {total_pages} page PDF to images...")

            # Convert each page to image
            for page_num in range(total_pages):
                page = pdf_document[page_num]

                # Render page to image (similar DPI to pdf2image)
                zoom = Config.IMAGE_DPI / 72  # 72 is the default DPI
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)  # alpha=False saves memory

                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(BytesIO(img_data))
                images.append(img)

                # Clear pixmap to free memory (important for large PDFs)
                pix = None

                # Progress indicator for large PDFs
                if total_pages > 10 and (page_num + 1) % 10 == 0:
                    print(f"   Processed {page_num + 1}/{total_pages} pages...")

            pdf_document.close()
            print(f"✅ Successfully converted {total_pages} pages")
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

        print(f"✅ Document processed: {len(images)} pages")
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
