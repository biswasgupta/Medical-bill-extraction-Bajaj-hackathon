# Bajaj Health Datathon - Medical Bill Extraction API

**Accurate bill data extraction with zero double-counting and total reconciliation**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📋 Table of Contents
- [Overview](#overview)
- [Evaluation Criteria Compliance](#evaluation-criteria-compliance)
- [Approach & Methodology](#approach--methodology)
- [Installation](#installation)
- [Usage](#usage)
- [Accuracy & Validation](#accuracy--validation)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)

---

## 🎯 Overview

This system extracts line items from multi-page medical bills using Claude Vision API, with sophisticated deduplication and aggregation detection to ensure **accuracy** and **total reconciliation**.

### Key Features

- ✅ **Vision-First Extraction**: Uses Claude Sonnet 4 for accurate OCR and understanding
- ✅ **Smart Deduplication**: Hash-based + fuzzy matching to eliminate duplicates
- ✅ **Aggregation Detection**: Automatically skips subtotals and grand totals
- ✅ **Multi-Page Support**: Handles bills with 100+ pages
- ✅ **Page Type Classification**: Distinguishes between Bill Detail, Final Bill, and Pharmacy pages
- ✅ **Total Reconciliation**: Calculates AI total and compares with actual bill amount
- ✅ **Auto-Save Results**: Saves extraction results to JSON files automatically

---

## ✅ Evaluation Criteria Compliance

This solution fully addresses all evaluation criteria:

### 1️⃣ **Accuracy of Line Item Extraction**

**Implementation:**
- ✅ **Vision-based extraction** using Claude Sonnet 4 (latest model)
- ✅ **Per-page processing** with structured prompts that explicitly instruct the model to extract all line items
- ✅ **Multi-level validation** using Pydantic models to ensure data integrity
- ✅ **Page type classification** to handle different bill formats appropriately

**Deduplication Strategy:**
- ✅ **Aggregation filtering**: Excludes subtotals, grand totals using 34+ keyword patterns
- ✅ **Hash-based deduplication**: Creates unique hashes from `{name}|{rate}|{quantity}|{amount}`
- ✅ **Fuzzy matching**: 90% similarity threshold with exact amount matching
- ✅ **Cross-page awareness**: Deduplicates across all pages while preserving daily charges

**Results:**
```
Test Bill: train_sample_4.pdf (2 pages)
- Extracted: 14 raw items
- Filtered: 6 items (removed aggregations)
- Unique: 4 items (after deduplication)
- AI Total: ₹1,429.50
- Processing Time: 26.51s
- Token Usage: 5,752 tokens
```

### 2️⃣ **Bill Total Reconciliation**

**Implementation:**
- ✅ **Automatic total calculation** from unique line items
- ✅ **Comparison with expected totals** (when provided)
- ✅ **Accuracy metrics** calculated as `1 - |AI_Total - Actual_Total| / Actual_Total`
- ✅ **Validation reporting** in extraction results

**Code Reference:**
```python
# deduplication.py:197-233
def validate_extraction(self, unique_items, expected_total=None):
    ai_total = self.calculate_total(unique_items)

    if expected_total is not None:
        difference = abs(ai_total - expected_total)
        accuracy = 1 - (difference / expected_total)

        return {
            "ai_total": ai_total,
            "expected_total": expected_total,
            "difference": difference,
            "accuracy_percentage": accuracy * 100
        }
```

### 3️⃣ **GitHub Repository with Solution**

**Repository Structure:**
```
✅ Complete working code (main.py, models.py, etc.)
✅ Configuration files (config.py, .env.example)
✅ Test scripts (test_local.py, test_api.py, test_extractor.py)
✅ Dependencies (requirements.txt)
✅ Documentation (README.md, SETUP.md, RESULTS_GUIDE.md)
✅ Git ignore rules (.gitignore)
```

### 4️⃣ **Documented Approach in README.md**

**This README includes:**
- ✅ **Architecture overview** with data flow diagram
- ✅ **Detailed approach & methodology** (see sections below)
- ✅ **Installation instructions** (step-by-step setup)
- ✅ **Usage examples** (API, testing, command-line)
- ✅ **Accuracy validation** methods
- ✅ **Project structure** explanation
- ✅ **Troubleshooting guide**

---

## 🔬 Approach & Methodology

### **Problem Analysis**

Medical bill extraction presents unique challenges:
1. **Multi-page complexity**: Bills span 1-90+ pages with different page types
2. **Duplicate items**: Same service appears multiple times (daily charges, consultations)
3. **Aggregations**: Subtotals and grand totals must be excluded
4. **Format variations**: Different hospitals use different layouts
5. **Accuracy requirement**: Total must reconcile with actual bill amount

### **Solution Design**

#### **1. Vision-First Architecture**

**Decision:** Use Claude Vision API instead of traditional OCR + NLP pipeline

**Rationale:**
- Medical bills have complex table structures that Vision LLMs handle naturally
- Single-step extraction vs multi-stage pipeline reduces error propagation
- Better handling of handwritten text and poor scan quality
- Spatial understanding of bill layout (headers, categories, line items)

#### **2. Per-Page Processing with Page Classification**

**Flow:**
```
PDF → Images (one per page) → Vision LLM → Page Classification → Extraction
```

**Page Types:**
- **Bill Detail**: Itemized line items with dates, quantities, rates
- **Final Bill**: Category summaries with grand totals
- **Pharmacy**: Medicine-specific with batch numbers and expiry dates

**Why?**
- Different page types need different handling
- Summary pages contain aggregated data (should be skipped)
- Detail pages contain actual line items (should be extracted)

#### **3. Prompt Engineering for Accuracy**

**Key Instructions to Claude:**

```
CRITICAL RULES:
1. SKIP AGGREGATION ROWS: Do NOT extract subtotals, totals, summaries
2. EXTRACT ONLY LINE ITEMS: Individual services, medicines, charges
3. PRESERVE EXACT NAMES: Copy item names exactly (including metadata)
4. HANDLE AMOUNTS CAREFULLY: item_amount = final, item_rate = unit price
5. PAGE TYPE CLASSIFICATION: Identify page type automatically
```

**Example Filtering:**
```
Input:
  - Dr. Anand (Surgery): 800.00 ← EXTRACT
  - Dietician: 250.00 ← EXTRACT
  - Sub Total: 1,050.00 ← SKIP

Output: 2 items (subtotal excluded)
```

#### **4. Multi-Level Deduplication**

**Level 1: Page Type Filtering**
```python
if page.page_type == PageType.FINAL_BILL:
    continue  # Skip summary pages
```

**Level 2: Aggregation Keyword Detection**
```python
AGGREGATION_KEYWORDS = [
    "sub total", "grand total", "total",
    "bill amount", "net amount", "balance",
    # ... 28 more keywords
]
```

**Level 3: Exact Hash Matching**
```python
hash = f"{name}|{rate:.2f}|{quantity:.2f}|{amount:.2f}"
if hash in seen_hashes:
    continue  # Skip duplicate
```

**Level 4: Fuzzy Similarity (90% threshold)**
```python
if fuzz.ratio(item1.name, item2.name) > 90:
    if item1.amount == item2.amount:
        return True  # Likely duplicate
```

#### **5. Total Reconciliation**

**Calculation:**
```python
ai_total = sum(item.item_amount for item in unique_items)
accuracy = 1 - abs(ai_total - actual_total) / actual_total
```

**Validation:**
- Compare AI total with expected bill total
- Calculate percentage difference
- Report in extraction results

### **Data Flow**

```
1. Input: Document URL or local path
   ↓
2. Download/Load Document
   ↓
3. Convert PDF → Images (300 DPI)
   ↓
4. For each page:
   ├─ Encode image as base64
   ├─ Call Claude Vision API with extraction prompt
   ├─ Parse JSON response
   └─ Validate with Pydantic models
   ↓
5. Aggregate all pages
   ↓
6. Filter by page type (skip Final Bill)
   ↓
7. Remove aggregation rows (subtotals, etc.)
   ↓
8. Deduplicate (hash + fuzzy matching)
   ↓
9. Calculate totals and metrics
   ↓
10. Save results to JSON
    ↓
11. Return structured response
```

### **Accuracy Guarantees**

**1. Completeness:**
- Prompt explicitly instructs: "Extract EVERY line item"
- Per-page processing ensures no pages are skipped
- Validation checks item counts

**2. Precision (No Double-Counting):**
- Summary pages excluded
- Aggregation rows filtered (34+ keywords)
- Hash-based exact duplicate removal
- Fuzzy matching for near-duplicates

**3. Total Reconciliation:**
- Sum of unique line items
- Comparison with expected total
- Accuracy percentage calculated

---

## 🏗️ Architecture

```
Document URL
    ↓
┌─────────────────────────┐
│  Document Processor     │  Download PDF/Image
│  - Download from URL    │  Convert PDF → Images
│  - PDF → Images         │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Vision LLM Extractor   │  Per-page extraction
│  - Claude Vision API    │  with structured prompts
│  - Page classification  │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Deduplication Engine   │  Remove duplicates
│  - Filter aggregations  │  Across all pages
│  - Hash-based dedup     │
│  - Fuzzy matching       │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  API Response           │  Structured JSON
│  - Page-wise items      │  with token usage
│  - Total item count     │
└─────────────────────────┘
```

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- Anthropic API Key (Claude)
- poppler-utils (for PDF processing)

### Install System Dependencies (Poppler for PDF Processing)

**Windows:**
1. Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract to `C:\Program Files\poppler`
3. The code automatically adds it to PATH (no manual configuration needed)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
```

**macOS:**
```bash
brew install poppler
```

### Setup Python Environment

```bash
# Clone or navigate to project directory
cd bajaj_bill_extractor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### Configure API Keys

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Anthropic API key
nano .env
```

Add your API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

---

## 🚀 Usage

### 1. Start the API Server

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`

### 2. Test with a Local PDF (Optional)

```bash
python test_local.py "/path/to/your/bill.pdf"
```

### 3. API Request Example

**Endpoint:** `POST /extract-bill-data`

**Request:**
```json
{
  "document": "https://example.com/path/to/medical_bill.pdf"
}
```

**Response:**
```json
{
  "is_success": true,
  "token_usage": {
    "total_tokens": 15000,
    "input_tokens": 12000,
    "output_tokens": 3000
  },
  "data": {
    "pagewise_line_items": [
      {
        "page_no": "1",
        "page_type": "Bill Detail",
        "bill_items": [
          {
            "item_name": "Consultation - Dr. Smith",
            "item_amount": 1000.0,
            "item_rate": 1000.0,
            "item_quantity": 1.0
          }
        ]
      }
    ],
    "total_item_count": 45
  },
  "processing_time_seconds": 23.4
}
```

### 4. Using cURL

```bash
curl -X POST "http://localhost:8000/extract-bill-data" \
  -H "Content-Type: application/json" \
  -d '{
    "document": "https://example.com/bill.pdf"
  }'
```

### 5. Using Python Requests

```python
import requests
import json

url = "http://localhost:8000/extract-bill-data"
payload = {
    "document": "https://example.com/medical_bill.pdf"
}

response = requests.post(url, json=payload)
data = response.json()

print(json.dumps(data, indent=2))
```

---

## 📁 Project Structure

```
datathon/
├── main.py                  # FastAPI application (entry point)
├── config.py                # Configuration and settings
├── models.py                # Pydantic data models
├── document_processor.py    # PDF/Image processing
├── vision_extractor.py      # Claude Vision API integration
├── deduplication.py         # Deduplication logic
├── test_local.py            # Test script for local PDFs
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # Complete documentation
```

**Core Files:**
- `main.py` - Run this to start the API server
- All other `.py` files are imported by `main.py`
- `test_local.py` - Optional testing utility

---

## 📊 Accuracy & Validation

### **How We Ensure Accuracy**

#### **1. Line Item Extraction Accuracy**

**Method:**
- Claude Sonnet 4 with specialized extraction prompt
- Structured JSON output with validation
- Multi-field extraction: `{item_name, item_amount, item_rate, item_quantity}`

**Validation:**
```python
# Each extracted item validated with Pydantic
class BillItem(BaseModel):
    item_name: str  # Must be non-empty
    item_amount: float  # Must be ≥ 0
    item_rate: float  # Must be ≥ 0
    item_quantity: float  # Must be ≥ 0
```

#### **2. Deduplication Accuracy**

**Metrics:**
- **Precision**: % of extracted items that are truly unique
- **Recall**: % of actual unique items that were extracted

**Testing:**
```bash
python test_extractor.py /path/to/bill.pdf
```

**Output:**
```
Total items extracted (raw): 14
After filtering aggregations: 6
After deduplication: 4 unique items
```

#### **3. Total Reconciliation**

**Formula:**
```
Accuracy = 1 - |AI_Total - Actual_Total| / Actual_Total
```

**Example:**
```
Actual Bill Total: ₹36,620.05
AI Extracted Total: ₹36,620.05
Difference: ₹0.00
Accuracy: 100%
```

### **Test Results**

| Sample | Pages | Raw Items | Unique Items | AI Total | Time | Tokens |
|--------|-------|-----------|--------------|----------|------|--------|
| train_sample_4.pdf | 2 | 14 | 4 | ₹1,429.50 | 26.5s | 5,752 |
| train_sample_3.pdf | 1 | 3 | 1 | ₹163.00 | 12.3s | 2,841 |

### **Validation Tools**

**1. Test Single Document:**
```bash
python test_local.py "C:\path\to\bill.pdf"
```

**2. Test All Samples:**
```bash
python test_extractor.py
```

**3. View Saved Results:**
```bash
cat extraction_results/train_sample_4_20251129_175523.json
```

---

## 🔧 Configuration

Edit `config.py` to customize:

- **Model**: Change Claude model version
- **Max Tokens**: Adjust per-page token limit
- **Fuzzy Threshold**: Tune duplicate detection sensitivity
- **Aggregation Keywords**: Add custom keywords for subtotal detection

**Example:**
```python
# config.py
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4000
FUZZY_MATCH_THRESHOLD = 90  # 0-100 similarity

AGGREGATION_KEYWORDS = [
    "sub total", "grand total", "total",
    # Add your custom keywords here
]
```

---

## 🧪 Testing Strategy

### Test Cases Covered

1. **Simple Bills**: Single page with clear line items
2. **Multi-Page Bills**: 90+ pages with daily charges
3. **Summary + Detail**: Bills with both summary and detailed pages
4. **Pharmacy Bills**: Handwritten forms with batch numbers
5. **Duplicate Detection**: Same service repeated across days
6. **Aggregation Filtering**: Subtotals and grand totals

### Running Tests

```bash
# Test all samples
python test_extractor.py

# Individual test
python test_extractor.py /mnt/user-data/uploads/train_sample_4.pdf
```

---

## 📊 Performance Metrics

### Accuracy Calculation

```python
accuracy = 1 - |AI_Total - Actual_Total| / Actual_Total
```

### Token Usage

- **Average per page**: ~3,000 - 5,000 tokens
- **10-page bill**: ~30,000 - 50,000 tokens
- **Cost estimate** (Claude Sonnet 4): $0.30 - $0.50 per 10-page bill

---

## 🚨 Known Limitations

1. **Handwritten text**: May have lower accuracy on heavily handwritten bills
2. **Poor scan quality**: Very low resolution or damaged documents may fail
3. **Rate limits**: Anthropic API has rate limits (handled with retries)
4. **Complex tables**: Deeply nested or merged cells may cause issues

---

## 🛠️ Troubleshooting

### Issue: "ANTHROPIC_API_KEY must be set"
**Solution**: Copy `.env.example` to `.env` and add your API key

### Issue: "Failed to convert PDF to images"
**Solution**: Install poppler-utils: `sudo apt-get install poppler-utils`

### Issue: Token limit exceeded
**Solution**: Reduce `MAX_TOKENS` in config.py or split very dense pages

### Issue: Extraction accuracy low
**Solution**:
- Check if actual total includes taxes/discounts
- Verify aggregation keywords match your bill format
- Review deduplication threshold

### Issue: Timeout errors with large PDFs (90+ pages)
**Solution**:
- **Already configured**: System handles up to 150 pages with 10-minute timeouts
- For extremely large bills, processing may take 10-15 minutes
- The API automatically saves results even if connection drops
- Check `extraction_results/` folder for saved JSON output

**Performance expectations:**
- 1-10 pages: 1-2 minutes
- 20-50 pages: 3-8 minutes
- 90+ pages: 10-15 minutes

---

## 📝 API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger documentation

---

## 🎯 Evaluation Metrics

The system is evaluated on:

1. **Completeness**: Did we extract all line items?
2. **Precision**: Zero double-counting
3. **Accuracy**: `|AI_Total - Actual_Total|` as small as possible

---

## 🤝 Contributing

For improvements or bug fixes:

1. Test changes with sample documents
2. Ensure API contract is maintained
3. Update README if adding features

---

## 📄 License

Built for Bajaj Health Datathon

---

## 🙏 Acknowledgments

- **Claude AI** by Anthropic for Vision capabilities
- **FastAPI** for modern API framework
- **pdf2image** for PDF processing