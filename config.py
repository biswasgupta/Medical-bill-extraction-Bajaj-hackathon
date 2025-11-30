import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
    
    # Model Configuration
    CLAUDE_MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 4000
    TEMPERATURE = 0.0  # Deterministic for extraction
    
    # Processing Configuration
    MAX_PAGES_PER_DOCUMENT = 150  # Increased limit for large bills
    IMAGE_DPI = 300  # For PDF to image conversion

    # Timeout Configuration (for large PDFs)
    API_REQUEST_TIMEOUT = 600  # 10 minutes for Claude API calls
    DOWNLOAD_TIMEOUT = 120  # 2 minutes for document download

    # Deduplication Configuration
    FUZZY_MATCH_THRESHOLD = 90  # Percentage similarity for fuzzy matching
    
    # Aggregation Keywords (case-insensitive)
    AGGREGATION_KEYWORDS = [
        "sub total", "subtotal", "sub-total",
        "grand total", "total", "net total",
        "service amount", "bill amount",
        "total discount", "total payable",
        "carried forward", "balance",
        "amount after discount", "total amount",
        "bill of supply", "tax invoice",
        "net payable", "outstanding amount"
    ]
    
    # API Configuration
    HOST = os.getenv("HOST", "0.0.0.0")  # 0.0.0.0 for production, 127.0.0.1 for local
    PORT = int(os.getenv("PORT", 8000))  # Use PORT from environment (Render provides this)
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY must be set in environment variables")
        return True

# Validate configuration on import
Config.validate()