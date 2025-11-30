from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from enum import Enum


class PageType(str, Enum):
    """Enum for page types"""
    BILL_DETAIL = "Bill Detail"
    FINAL_BILL = "Final Bill"
    PHARMACY = "Pharmacy"


class BillItem(BaseModel):
    """Individual line item from bill"""
    item_name: str = Field(..., description="Exactly as mentioned in the bill")
    item_amount: float = Field(..., description="Net amount post discounts")
    item_rate: float = Field(..., description="Unit price/rate")
    item_quantity: float = Field(..., description="Quantity")
    
    @validator('item_amount', 'item_rate', 'item_quantity')
    def validate_positive(cls, v):
        """Ensure numeric fields are non-negative"""
        if v < 0:
            raise ValueError(f"Value must be non-negative, got {v}")
        return v


class PageWiseLineItems(BaseModel):
    """Line items extracted from a single page"""
    page_no: str = Field(..., description="Page number as string")
    page_type: PageType = Field(..., description="Type of page")
    bill_items: List[BillItem] = Field(default_factory=list, description="List of bill items")


class ExtractionData(BaseModel):
    """Complete extraction data"""
    pagewise_line_items: List[PageWiseLineItems]
    total_item_count: int = Field(..., description="Total count of items across all pages")
    
    @validator('total_item_count')
    def validate_item_count(cls, v, values):
        """Ensure total_item_count matches actual count"""
        if 'pagewise_line_items' in values:
            actual_count = sum(
                len(page.bill_items) 
                for page in values['pagewise_line_items']
            )
            if v != actual_count:
                # Auto-correct if mismatch
                return actual_count
        return v


class TokenUsage(BaseModel):
    """Token usage tracking"""
    total_tokens: int = Field(0, description="Cumulative tokens from all LLM calls")
    input_tokens: int = Field(0, description="Cumulative input tokens")
    output_tokens: int = Field(0, description="Cumulative output tokens")


class ExtractionRequest(BaseModel):
    """API Request schema"""
    document: str = Field(..., description="URL or local file path to document (PDF/Image)")

    @validator('document')
    def validate_document(cls, v):
        """Validate document path or URL"""
        import os

        # Check if it's a URL
        if v.startswith(('http://', 'https://')):
            return v

        # Check if it's a local file path
        if os.path.isfile(v):
            return v

        # If neither, raise error
        raise ValueError(
            "Document must be either:\n"
            "  - A valid HTTP/HTTPS URL\n"
            "  - A valid local file path"
        )


class ExtractionResponse(BaseModel):
    """API Response schema"""
    is_success: bool = Field(..., description="True if status 200 and valid schema")
    token_usage: TokenUsage
    data: ExtractionData
    
    # Optional fields for debugging/metadata
    error_message: Optional[str] = Field(None, description="Error message if any")
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time")


class InternalPageExtraction(BaseModel):
    """Internal model for per-page extraction from LLM"""
    page_no: str
    page_type: str
    bill_items: List[dict]  # Raw dict before validation
    
    class Config:
        extra = "allow"  # Allow extra fields from LLM response