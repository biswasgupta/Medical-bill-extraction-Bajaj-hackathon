import anthropic
import json
from typing import List, Dict, Any
from PIL import Image

from config import Config
from models import InternalPageExtraction, TokenUsage
from document_processor import DocumentProcessor


class VisionLLMExtractor:
    """Extract bill data using Claude Vision API"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
    
    def build_extraction_prompt(self) -> str:
        """Build the extraction prompt for Claude"""
        
        prompt = """You are an expert medical bill data extraction system. Your task is to extract line items from this medical bill page.

**CRITICAL RULES:**

1. **SKIP AGGREGATION ROWS**: Do NOT extract rows that are subtotals, totals, or summaries
   - Skip if item name contains: "sub total", "total", "grand total", "bill amount", "net amount", "balance", "discount"
   - Skip if it's a category header with only an amount (e.g., "Consultation    2,650.00")

2. **EXTRACT ONLY LINE ITEMS**: Extract individual services, procedures, medicines, charges
   - Each row should have: item name, amount, rate, quantity
   - If quantity is missing, use 1.0
   - If rate is missing, use the amount value

3. **PRESERVE EXACT NAMES**: Copy item names exactly as written in the bill
   - Include doctor names, medication names, batch numbers if present
   - Do not summarize or abbreviate

4. **HANDLE AMOUNTS CAREFULLY**:
   - item_amount = final amount for that line (after any row-level discount)
   - item_rate = unit price or rate per item
   - item_quantity = how many units

5. **PAGE TYPE CLASSIFICATION**:
   - "Bill Detail" = Has itemized line items with FROM DATE/TO DATE columns, quantities, individual rates
   - "Final Bill" = Only shows final totals, discount, net amount (NO line items, just summary numbers)
   - "Pharmacy" = Has batch numbers, expiry dates, medicine-focused

   IMPORTANT: If a page has "FINAL BILL" header BUT contains itemized line items with dates/quantities,
   classify it as "Bill Detail", NOT "Final Bill"

**OUTPUT FORMAT (JSON ONLY):**

```json
{
  "page_no": "1",
  "page_type": "Bill Detail",
  "bill_items": [
    {
      "item_name": "Consultation with Dr. Smith",
      "item_amount": 800.0,
      "item_rate": 800.0,
      "item_quantity": 1.0
    }
  ]
}
```

**EXAMPLE - WHAT TO EXTRACT:**

If you see:
```
Consultation
1. Dr. Nishchal Anand (Surgery)    8/11/25   1.0   800.00   800.00
2. Dietician Consultation           8/11/25   1.0   250.00   250.00
Sub Total :                                                 1,050.00

Drugs
5. DOLENTIA 75MG INJ                8/11/25   2.0   38.44    76.88
```

Extract:
```json
{
  "page_no": "1",
  "page_type": "Bill Detail",
  "bill_items": [
    {
      "item_name": "Dr. Nishchal Anand (Surgery)",
      "item_amount": 800.0,
      "item_rate": 800.0,
      "item_quantity": 1.0
    },
    {
      "item_name": "Dietician Consultation",
      "item_amount": 250.0,
      "item_rate": 250.0,
      "item_quantity": 1.0
    },
    {
      "item_name": "DOLENTIA 75MG INJ",
      "item_amount": 76.88,
      "item_rate": 38.44,
      "item_quantity": 2.0
    }
  ]
}
```

**DO NOT EXTRACT**: "Sub Total : 1,050.00" or "Consultation" header row

**IMPORTANT**: 
- Output ONLY valid JSON, no markdown, no explanation
- If page has NO extractable items (only totals), return empty bill_items array
- Be precise with decimal numbers

Now extract from the provided image:"""
        
        return prompt
    
    def extract_from_page(
        self, 
        image: Image.Image, 
        page_number: int
    ) -> InternalPageExtraction:
        """
        Extract bill items from a single page image
        
        Args:
            image: PIL Image of the page
            page_number: Page number (1-indexed)
            
        Returns:
            InternalPageExtraction with extracted data
        """
        # Convert image to base64
        image_base64 = DocumentProcessor.image_to_base64(image)
        media_type = DocumentProcessor.get_image_media_type(image)
        
        # Build message
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": self.build_extraction_prompt()
                    }
                ]
            }
        ]
        
        try:
            # Call Claude API with timeout for large documents
            response = self.client.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE,
                messages=messages,
                timeout=Config.API_REQUEST_TIMEOUT
            )
            
            # Track token usage
            usage = response.usage
            self.input_tokens += usage.input_tokens
            self.output_tokens += usage.output_tokens
            self.total_tokens += usage.input_tokens + usage.output_tokens
            
            # Extract text response
            response_text = response.content[0].text
            
            # Clean response (remove markdown code blocks if present)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()
            
            # Parse JSON
            extraction_data = json.loads(response_text)

            # Override page_no with actual page number (Claude might return wrong page number)
            extraction_data['page_no'] = str(page_number)

            # Validate and create model
            return InternalPageExtraction(**extraction_data)
            
        except json.JSONDecodeError as e:
            # Return empty extraction if JSON parsing fails
            print(f"⚠️ JSON parsing failed for page {page_number}: {e}")
            print(f"Response was: {response_text[:200]}...")
            return InternalPageExtraction(
                page_no=str(page_number),
                page_type="Bill Detail",
                bill_items=[]
            )
        except Exception as e:
            print(f"❌ Error extracting from page {page_number}: {e}")
            return InternalPageExtraction(
                page_no=str(page_number),
                page_type="Bill Detail",
                bill_items=[]
            )
    
    def extract_from_all_pages(
        self, 
        images: List[Image.Image]
    ) -> List[InternalPageExtraction]:
        """
        Extract bill items from all pages
        
        Args:
            images: List of PIL Images
            
        Returns:
            List of InternalPageExtraction objects
        """
        extractions = []
        
        for idx, image in enumerate(images, start=1):
            print(f"📄 Processing page {idx}/{len(images)}...")
            extraction = self.extract_from_page(image, idx)
            extractions.append(extraction)
            print(f"   ✅ Extracted {len(extraction.bill_items)} items")
        
        return extractions
    
    def get_token_usage(self) -> TokenUsage:
        """Get cumulative token usage"""
        return TokenUsage(
            total_tokens=self.total_tokens,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens
        )


# Test function
def test_extractor():
    """Test the extractor with a sample image"""
    from pathlib import Path
    
    extractor = VisionLLMExtractor()
    
    # Test with uploaded sample
    test_image_path = "/mnt/user-data/uploads/1764415249801_train_sample_4.pdf"
    
    if Path(test_image_path).exists():
        processor = DocumentProcessor()
        images = processor.process_document(f"file://{test_image_path}")
        
        extraction = extractor.extract_from_page(images[0], 1)
        print(json.dumps(extraction.dict(), indent=2))
        print(f"\n💰 Token Usage: {extractor.get_token_usage()}")


if __name__ == "__main__":
    test_extractor()