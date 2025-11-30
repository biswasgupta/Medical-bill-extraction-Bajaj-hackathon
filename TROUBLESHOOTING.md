# Troubleshooting Guide - PDF Download Issues

## Overview
This guide helps you diagnose and fix PDF download issues in your Render deployment.

## Recent Improvements

### Enhanced Download System
The download system now includes:

1. **Session-based downloads** with proper cookie handling
2. **Comprehensive browser headers** to avoid being blocked
3. **Retry logic** with exponential backoff (3 attempts)
4. **Streaming downloads** for large files
5. **Content validation** at every step
6. **Detailed logging** for debugging

### What Gets Checked

#### Before Download:
- URL validity

#### During Download:
- HTTP status codes
- Content-Length headers
- Content-Type headers
- Redirect chains

#### After Download:
- File size validation
- PDF header validation
- Content type verification (HTML vs PDF)

## Common Issues and Solutions

### Issue 1: "Downloaded file is empty (0 bytes)"

**Possible Causes:**
- The URL doesn't point to an actual file
- The server requires authentication
- The server is blocking automated requests
- The file has been moved/deleted

**How to Diagnose:**

1. **Test the URL in a browser** - Can you download it manually?
2. **Check the server logs** - Look for detailed error messages
3. **Use the debug endpoint**:

```bash
curl -X POST https://your-app.onrender.com/debug/test-url \
  -H "Content-Type: application/json" \
  -d '{"url": "YOUR_PDF_URL_HERE"}'
```

This will show you:
- What HTTP status code was returned
- What Content-Type header was sent
- Whether the file is actually a PDF or HTML
- How many bytes were downloaded
- Content preview if it's not a PDF

### Issue 2: "Server returned HTML instead of a document"

**Possible Causes:**
- The URL points to a webpage, not a direct file link
- The server requires login/authentication
- The file is behind a paywall
- The URL has expired

**Solution:**
- Check if the URL is a direct link to the PDF (should end in `.pdf`)
- Try accessing the URL in an incognito browser window
- Look for "Download" buttons that generate temporary URLs

### Issue 3: "Invalid PDF file: File does not start with PDF header"

**Possible Causes:**
- Downloaded content is not actually a PDF
- File is corrupted
- Server sent an error page disguised as a PDF

**Solution:**
The error message will show you the actual file header. Look for:
- `%PDF-` = Valid PDF
- `<!DOC` or `<html` = HTML page
- Other content = Corrupted or wrong file type

### Issue 4: Poppler conversion errors

**Error:** "Unable to get page count" or poppler-related errors

**Solution:**
This is usually already fixed in the `render.yaml` build command, but verify:

```yaml
buildCommand: "apt-get update && apt-get install -y poppler-utils && pip install --no-cache-dir -r requirements.txt"
```

## Testing Locally

### Method 1: Test Script

Run the provided test script:

```bash
python test_url_download.py "https://your-pdf-url-here.pdf"
```

This will:
- Attempt to download the URL
- Show all diagnostic information
- Test PDF conversion
- Report success/failure

### Method 2: Python Interactive

```python
from document_processor import DocumentProcessor

processor = DocumentProcessor()
file_path, file_type = processor.download_document("YOUR_URL_HERE")
print(f"Downloaded to: {file_path}, Type: {file_type}")
```

## Production Debugging

### Check Render Logs

1. Go to your Render dashboard
2. Select your service
3. Click "Logs"
4. Look for the detailed download messages:

```
📡 Download attempt 1/3...
🔗 URL: https://...
📊 Status Code: 200
🔄 Final URL after redirects: https://...
📏 Content-Length header: 12345 bytes
📄 Content-Type: application/pdf
📦 Downloaded 12345 bytes
✅ File saved: /tmp/xyz/document.pdf (12345 bytes)
```

### Common Log Patterns

**Empty file:**
```
📏 Content-Length header: 0 bytes
❌ Error: Server reports content-length is 0 bytes
```
→ The server is not serving the file

**HTML instead of PDF:**
```
📄 Content-Type: text/html
❌ Error: Server returned HTML instead of a document
```
→ URL is incorrect or requires authentication

**Download succeeded but PDF invalid:**
```
✅ File saved: /tmp/xyz/document.pdf (1234 bytes)
📖 Converting PDF to images (file size: 1234 bytes)...
❌ Invalid PDF file: File does not start with PDF header
```
→ File is corrupted or not actually a PDF

## API Endpoint Testing

### Test URL Download (Production)

```bash
curl -X POST https://your-app.onrender.com/debug/test-url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
  }'
```

**Successful Response:**
```json
{
  "success": true,
  "url": "https://...",
  "file_type": "pdf",
  "file_size_bytes": 12345,
  "pdf_info": {
    "page_count": 5,
    "conversion_successful": true
  }
}
```

**Failed Response:**
```json
{
  "success": false,
  "url": "https://...",
  "error": "Downloaded file is empty (0 bytes)"
}
```

## Specific URL Issues

### The URL: `https://global.oup.com/us/companion.websites/fdscontent/uscompanion/us/pdf/globalmusic/SIndiaQuizzes.pdf`

This specific URL is failing with "Downloaded file is empty (0 bytes)".

**Possible reasons:**
1. The file may have been moved or deleted from the server
2. The Oxford University Press website may require cookies/session
3. The URL may have restrictions on automated access
4. The file path may be incorrect

**What to try:**
1. Verify the URL works in a browser
2. Check if there's an updated URL for the resource
3. Contact the content provider for API access
4. Use a publicly accessible test PDF first to verify the system works

## Valid Test URLs

Use these to verify your system is working:

```
https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf
https://www.africau.edu/images/default/sample.pdf
```

## Getting Help

When reporting issues, include:

1. The full URL you're trying to download
2. The complete error message from the logs
3. The response from `/debug/test-url`
4. Whether the URL works in a browser
5. The full traceback from Render logs

## Environment Variables

Make sure these are set in Render:

```
ANTHROPIC_API_KEY=your_key_here
PORT=8000  # Usually auto-set by Render
HOST=0.0.0.0
```

## Next Steps

1. Test with known-working URLs first
2. If those work, the system is fine - issue is with specific URLs
3. If those fail, check poppler installation in render.yaml
4. Review Render build logs for any installation errors
