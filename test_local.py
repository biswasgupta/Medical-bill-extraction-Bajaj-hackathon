#!/usr/bin/env python3
"""
Quick test script for local PDF files
"""

import requests
import json
import sys
from pathlib import Path

def test_local_pdf(pdf_path: str, api_url: str = "http://127.0.0.1:8000"):
    """
    Test extraction with a local PDF file

    Args:
        pdf_path: Path to local PDF file
        api_url: API endpoint URL
    """

    # Verify file exists
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        return

    print(f"🧪 Testing with local file: {pdf_path}")
    print(f"📡 API URL: {api_url}")
    print()

    # Prepare request
    payload = {
        "document": pdf_path  # Now accepts local paths!
    }

    try:
        # Send request
        print("📤 Sending request...")
        response = requests.post(
            f"{api_url}/extract-bill-data",
            json=payload,
            timeout=300  # 5 minute timeout for large files
        )

        # Check response
        response.raise_for_status()
        data = response.json()

        # Display results
        if data.get("is_success"):
            print("\n✅ SUCCESS!\n")
            print("=" * 80)
            print("EXTRACTION RESULTS")
            print("=" * 80)

            extraction_data = data.get("data", {})
            token_usage = data.get("token_usage", {})

            print(f"\n📊 Summary:")
            print(f"  Total unique items: {extraction_data.get('total_item_count', 0)}")
            print(f"  Pages processed: {len(extraction_data.get('pagewise_line_items', []))}")
            print(f"  Processing time: {data.get('processing_time_seconds', 0):.2f}s")

            print(f"\n💰 Token Usage:")
            print(f"  Total: {token_usage.get('total_tokens', 0):,}")
            print(f"  Input: {token_usage.get('input_tokens', 0):,}")
            print(f"  Output: {token_usage.get('output_tokens', 0):,}")

            # Calculate total amount
            total_amount = 0
            print(f"\n📋 Page-wise Breakdown:")
            for page in extraction_data.get('pagewise_line_items', []):
                page_items = page['bill_items']
                page_total = sum(item['item_amount'] for item in page_items)
                total_amount += page_total
                print(f"  Page {page['page_no']} ({page['page_type']}): {len(page_items)} items → ₹{page_total:,.2f}")

            print(f"\n💵 AI Total: ₹{total_amount:,.2f}")

            # Show sample items
            all_items = []
            for page in extraction_data.get('pagewise_line_items', []):
                all_items.extend(page['bill_items'])

            if all_items:
                print(f"\n📄 Sample Items (first 5):")
                print("-" * 80)
                for i, item in enumerate(all_items[:5], 1):
                    print(f"{i}. {item['item_name'][:60]:<60} ₹{item['item_amount']:>10,.2f}")

                if len(all_items) > 5:
                    print(f"... and {len(all_items) - 5} more items")

            # Save results
            output_file = f"{Path(pdf_path).stem}_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Full results saved to: {output_file}")

        else:
            print(f"\n❌ Extraction failed: {data.get('error_message', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to API at {api_url}")
        print(f"   Make sure the server is running: uvicorn main:app --host 127.0.0.1 --port 8000")
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out (>5 minutes)")
        print(f"   The PDF might be too large or complex")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_local.py <path_to_pdf>")
        print("\nExample:")
        print("  python test_local.py C:\\Users\\user\\Documents\\bill.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    test_local_pdf(pdf_path)
