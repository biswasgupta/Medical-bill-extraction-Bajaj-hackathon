# Testing Guide for Medical Bill Extraction API

## ⚠️ Common Issues and Solutions

### Issue 1: "Downloaded file is empty (0 bytes)"

**Cause**: The server is blocking automated requests with WAF (Web Application Firewall)

**Solution**:
- Use URLs from servers that allow programmatic access
- Avoid URLs with bot protection (Cloudflare, AWS WAF, etc.)
- Use direct download links, not preview pages

**Example of BAD URL** (has WAF):
```
https://global.oup.com/us/companion.websites/fdscontent/uscompanion/us/pdf/globalmusic/SIndiaQuizzes.pdf
```
**Response**: HTTP 202 with HTML challenge page

**Example of GOOD URLs** (direct access):
```
https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf
https://www.africau.edu/images/default/sample.pdf
https://www.clickdimensions.com/links/TestPDFfile.pdf
```

---

## 🧪 Testing Options

### Option 1: Use Publicly Accessible Medical Bill PDFs

Upload your medical bill to a public file hosting service:
- **Google Drive**: Make shareable link public → Use direct download URL
- **Dropbox**: Get public link → Change `dl=0` to `dl=1` in URL
- **GitHub**: Upload to repository → Use raw content URL
- **AWS S3**: Upload to public bucket → Use direct URL

**Google Drive URL Conversion**:
```
Original: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
Direct:   https://drive.google.com/uc?export=download&id=FILE_ID
```

**Dropbox URL Conversion**:
```
Original: https://www.dropbox.com/s/FILE_ID/filename.pdf?dl=0
Direct:   https://www.dropbox.com/s/FILE_ID/filename.pdf?dl=1
```

### Option 2: Use Local File Testing

If testing locally (not on Render):

```bash
python test_local.py "C:\path\to\your\medical_bill.pdf"
```

### Option 3: Test with Sample PDFs

For initial testing, use these sample PDF URLs (non-medical):

1. **Small PDF (1 page)**:
   ```
   https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf
   ```

2. **Medium PDF (3 pages)**:
   ```
   https://www.africau.edu/images/default/sample.pdf
   ```

3. **Test with API**:
   ```bash
   curl -X POST "https://your-app.onrender.com/extract-bill-data" \
     -H "Content-Type: application/json" \
     -d '{"document": "https://www.africau.edu/images/default/sample.pdf"}'
   ```

---

## 🔧 Updated Code Changes

The following improvements were made to handle download issues:

### 1. Added Retry Logic (3 attempts)
- Exponential backoff: 2s, 4s, 8s between retries
- Better error messages

### 2. Enhanced Headers
- Full browser-like headers to bypass WAF
- User-Agent, Accept headers, Sec-Fetch headers

### 3. WAF Detection
- Detects when server returns HTML instead of PDF
- Clear error message: "likely WAF/bot protection"

### 4. File Validation
- Checks Content-Length header
- Validates downloaded bytes
- Verifies file written to disk

---

## 📊 Testing Checklist

Before deploying to production:

- [ ] Test with direct PDF URL (no WAF)
- [ ] Test with medical bill PDF
- [ ] Test with multi-page PDF (10+ pages)
- [ ] Test with local file path
- [ ] Verify extraction accuracy
- [ ] Check token usage is reasonable
- [ ] Verify auto-save creates JSON files
- [ ] Test error handling (invalid URL)
- [ ] Test timeout handling (very large PDFs)

---

## 🚀 Deployment Steps

After fixing the code:

1. **Commit Changes**:
   ```bash
   git add document_processor.py
   git commit -m "fix: improve download with retry logic and WAF detection"
   git push origin main
   ```

2. **Render Auto-Deploy**:
   - Render will automatically detect the push
   - Wait 2-3 minutes for rebuild
   - Check deployment logs

3. **Test Again**:
   ```bash
   curl -X POST "https://your-app.onrender.com/extract-bill-data" \
     -H "Content-Type: application/json" \
     -d '{"document": "VALID_PDF_URL_HERE"}'
   ```

---

## 💡 Recommended Testing Workflow

### For Medical Bills:

1. **Upload to Google Drive**:
   - Right-click → Get link → Anyone with link can view
   - Copy the file ID from URL
   - Use: `https://drive.google.com/uc?export=download&id=FILE_ID`

2. **Test Locally First**:
   ```bash
   python test_local.py "path/to/bill.pdf"
   ```

3. **Then Test on Render**:
   ```bash
   curl -X POST "https://your-app.onrender.com/extract-bill-data" \
     -H "Content-Type: application/json" \
     -d '{"document": "GOOGLE_DRIVE_DIRECT_URL"}'
   ```

---

## 🐛 Debugging Tips

### Check Render Logs:
1. Go to Render dashboard
2. Click on your service
3. Click "Logs" tab
4. Look for:
   - `📥 Download attempt 1/3: ...`
   - `✅ Downloaded X bytes`
   - Error messages

### Common Error Messages:

| Error | Cause | Solution |
|-------|-------|----------|
| "Downloaded file is empty (0 bytes)" | WAF blocking | Use direct URL without protection |
| "Server returned HTML instead of PDF" | WAF challenge page | Use different hosting |
| "Failed to convert PDF to images" | Corrupted PDF | Verify PDF opens locally |
| "Request error: 404" | Invalid URL | Check URL is accessible |
| "Request error: timeout" | Slow server | Increase DOWNLOAD_TIMEOUT in config |

---

## ✅ Success Indicators

Your API is working correctly when you see:

```json
{
  "is_success": true,
  "token_usage": {
    "total_tokens": 5752,
    "input_tokens": 4800,
    "output_tokens": 952
  },
  "data": {
    "pagewise_line_items": [...],
    "total_item_count": 4
  },
  "processing_time_seconds": 26.51
}
```

And in Render logs:
```
📥 Download attempt 1/3: https://...
✅ Downloaded 284950 bytes
✅ Saved to temp file: 284950 bytes
✅ Document processed: 2 pages
🔍 Extracting data from 2 pages...
📄 Processing page 1/2...
   ✅ Extracted 7 items
📄 Processing page 2/2...
   ✅ Extracted 4 items
🔄 Deduplicating items...
✅ Total unique items after deduplication: 8
💰 AI Total: 1429.50
💾 Results saved to: extraction_results/...
```

---

Good luck with testing! 🎯
