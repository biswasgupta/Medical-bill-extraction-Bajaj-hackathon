#!/usr/bin/env python3
"""
Test script to diagnose URL download issues
Run this to test if a specific URL can be downloaded
"""

import sys
from document_processor import DocumentProcessor

def test_url(url: str):
    """Test downloading a specific URL"""
    print("=" * 80)
    print(f"Testing URL: {url}")
    print("=" * 80)

    processor = DocumentProcessor()

    try:
        file_path, file_type = processor.download_document(url)
        print(f"\n✅ SUCCESS!")
        print(f"   File saved to: {file_path}")
        print(f"   File type: {file_type}")

        # If it's a PDF, try to convert it
        if file_type == 'pdf':
            print(f"\n🔄 Testing PDF conversion...")
            images = processor.pdf_to_images(file_path)
            print(f"✅ Successfully converted to {len(images)} images")

    except Exception as e:
        print(f"\n❌ FAILED!")
        print(f"   Error: {str(e)}")
        return False
    finally:
        processor.cleanup()

    return True


if __name__ == "__main__":
    # Test URLs
    test_urls = [
        # Replace with your actual test URLs
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",  # Public test PDF
    ]

    # If URL provided as command line argument, use that
    if len(sys.argv) > 1:
        test_urls = [sys.argv[1]]

    print("\n" + "=" * 80)
    print("URL Download Test Suite")
    print("=" * 80 + "\n")

    results = {}
    for url in test_urls:
        success = test_url(url)
        results[url] = success
        print("\n")

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for url, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {url}")
