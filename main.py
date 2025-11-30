from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
import traceback
import json
import os
from pathlib import Path
from datetime import datetime

from models import (
    ExtractionRequest,
    ExtractionResponse,
    ExtractionData,
    PageWiseLineItems,
    BillItem,
    TokenUsage,
    PageType
)
from document_processor import DocumentProcessor
from vision_extractor import VisionLLMExtractor
from deduplication import DeduplicationEngine
from config import Config


# Initialize FastAPI app
app = FastAPI(
    title="Bajaj Health Datathon - Bill Extraction API",
    description="Extract line items from medical bills with zero double-counting",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Bill Extraction API",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "anthropic_api_configured": bool(Config.ANTHROPIC_API_KEY),
        "model": Config.CLAUDE_MODEL
    }


@app.post("/extract-bill-data", response_model=ExtractionResponse)
async def extract_bill_data(request: ExtractionRequest):
    """
    Extract bill data from document URL
    
    Args:
        request: ExtractionRequest with document URL
        
    Returns:
        ExtractionResponse with extracted data
    """
    start_time = time.time()
    
    # Initialize components
    doc_processor = DocumentProcessor()
    extractor = VisionLLMExtractor()
    dedup_engine = DeduplicationEngine()
    
    try:
        # Step 1: Download and process document
        print(f"📥 Downloading document from: {request.document}")
        images = doc_processor.process_document(request.document)
        print(f"✅ Document processed: {len(images)} pages")
        
        # Step 2: Extract from each page using Vision LLM
        print(f"🔍 Extracting data from {len(images)} pages...")
        raw_extractions = extractor.extract_from_all_pages(images)
        
        # Step 3: Convert to validated models
        pagewise_items = []
        for extraction in raw_extractions:
            try:
                # Validate and convert bill items
                validated_items = []
                for item_dict in extraction.bill_items:
                    try:
                        bill_item = BillItem(**item_dict)
                        validated_items.append(bill_item)
                    except Exception as e:
                        print(f"⚠️ Skipping invalid item on page {extraction.page_no}: {e}")
                        continue
                
                # Map page type
                try:
                    page_type = PageType(extraction.page_type)
                except ValueError:
                    page_type = PageType.BILL_DETAIL  # Default
                
                page_data = PageWiseLineItems(
                    page_no=extraction.page_no,
                    page_type=page_type,
                    bill_items=validated_items
                )
                pagewise_items.append(page_data)
                
            except Exception as e:
                print(f"⚠️ Error processing page {extraction.page_no}: {e}")
                continue
        
        # Step 4: Deduplication and aggregation filtering
        print(f"🔄 Deduplicating items...")
        unique_items = dedup_engine.process_pagewise_items(pagewise_items)
        
        # Step 5: Calculate metrics
        ai_total = dedup_engine.calculate_total(unique_items)
        print(f"💰 AI Total: {ai_total}")
        print(f"📊 Unique Items: {len(unique_items)}")
        
        # Step 6: Build response
        extraction_data = ExtractionData(
            pagewise_line_items=pagewise_items,
            total_item_count=len(unique_items)  # Count of unique items
        )
        
        token_usage = extractor.get_token_usage()
        
        processing_time = time.time() - start_time
        
        response = ExtractionResponse(
            is_success=True,
            token_usage=token_usage,
            data=extraction_data,
            processing_time_seconds=round(processing_time, 2)
        )
        
        print(f"✅ Extraction complete in {processing_time:.2f}s")
        print(f"💰 Token Usage: {token_usage.total_tokens} tokens")

        # Step 7: Save results to JSON file
        try:
            # Create output directory if it doesn't exist
            output_dir = Path("extraction_results")
            output_dir.mkdir(exist_ok=True)

            # Generate filename from document path/URL
            if request.document.startswith(('http://', 'https://')):
                # Extract filename from URL
                doc_name = Path(request.document).stem
            else:
                # Use local filename
                doc_name = Path(request.document).stem

            # Add timestamp to avoid overwrites
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{doc_name}_{timestamp}.json"
            output_path = output_dir / output_filename

            # Save response to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(response.dict(), f, indent=2, ensure_ascii=False)

            print(f"💾 Results saved to: {output_path}")

        except Exception as save_error:
            print(f"⚠️ Warning: Failed to save results to file: {save_error}")
            # Don't fail the request if saving fails

        return response
        
    except Exception as e:
        # Log error
        print(f"❌ Error during extraction: {e}")
        traceback.print_exc()
        
        # Return error response
        error_response = ExtractionResponse(
            is_success=False,
            token_usage=extractor.get_token_usage() if extractor else TokenUsage(),
            data=ExtractionData(
                pagewise_line_items=[],
                total_item_count=0
            ),
            error_message=str(e),
            processing_time_seconds=round(time.time() - start_time, 2)
        )
        
        return error_response
        
    finally:
        # Cleanup
        doc_processor.cleanup()


@app.get("/debug/config")
def debug_config():
    """Debug endpoint to check configuration (remove in production)"""
    return {
        "model": Config.CLAUDE_MODEL,
        "max_tokens": Config.MAX_TOKENS,
        "temperature": Config.TEMPERATURE,
        "api_key_configured": bool(Config.ANTHROPIC_API_KEY),
        "fuzzy_threshold": Config.FUZZY_MATCH_THRESHOLD
    }


# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True
    )