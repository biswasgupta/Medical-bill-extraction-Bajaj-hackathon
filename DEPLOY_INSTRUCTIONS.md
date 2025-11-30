# Deployment Instructions - Quick Fix

## 🔧 Changes Made to Fix Download Issue

The following files were updated to fix the "Downloaded file is empty (0 bytes)" error:

### 1. [document_processor.py](document_processor.py)
- ✅ Fixed typo: `Tupl6e` → `Tuple`
- ✅ Added retry logic (3 attempts with exponential backoff)
- ✅ Added browser-like headers to bypass WAF
- ✅ Added WAF detection (detects HTML responses when expecting PDF)
- ✅ Added file size validation
- ✅ Better error messages

### 2. [TESTING_GUIDE.md](TESTING_GUIDE.md) (NEW)
- Complete testing guide
- WAF troubleshooting
- Sample URLs for testing
- Google Drive/Dropbox URL conversion tips

---

## 🚀 Push to GitHub (Do This Manually)

### Step 1: Configure Git Remote

```bash
cd /c/Users/yaswa/Downloads/datathon/datathon

# Add your GitHub repository as remote
git remote add origin https://github.com/biswasgupta/Medical-bill-extraction-Bajaj-hackathon.git

# Check remote is added
git remote -v
```

### Step 2: Stage and Commit Changes

```bash
# Check what changed
git status

# Add the modified files
git add document_processor.py TESTING_GUIDE.md DEPLOY_INSTRUCTIONS.md

# Create commit
git commit -m "fix: improve download with retry logic, WAF detection, and file validation

- Added retry logic with 3 attempts and exponential backoff
- Enhanced headers to bypass WAF (Web Application Firewall)
- Added detection for WAF challenges (HTML instead of PDF)
- Added file size validation at multiple stages
- Fixed typo in type hint (Tupl6e -> Tuple)
- Added comprehensive testing guide

Fixes issue: 'Downloaded file is empty (0 bytes)'"
```

### Step 3: Push to GitHub

```bash
# Push to prod branch
git push origin main:prod

# OR if your current branch is already 'prod':
git checkout -b prod
git push -u origin prod
```

**When prompted for credentials**:
- Username: `biswas29.jobs@gmail.com`
- Password: Use your GitHub **Personal Access Token** (NOT your password)

⚠️ **IMPORTANT**: GitHub no longer accepts passwords. You need a Personal Access Token.

---

## 🔑 Create GitHub Personal Access Token

If you don't have a token yet:

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "Render Deployment"
4. Select scopes: `repo` (full control)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)
7. Use this token as your password when pushing

---

## 🎯 Alternative: Use GitHub Desktop (Easier)

If you prefer a GUI:

1. Download GitHub Desktop: https://desktop.github.com/
2. File → Add Local Repository → Select your folder
3. Sign in with your GitHub account
4. Commit changes (write commit message)
5. Click "Push origin"

---

## 🧪 After Pushing - Test on Render

Once pushed, Render will auto-deploy (takes 2-3 minutes).

### Test with a Valid URL (No WAF):

```bash
# Test 1: Small sample PDF
curl -X POST "https://your-app.onrender.com/extract-bill-data" \
  -H "Content-Type: application/json" \
  -d '{"document": "https://www.africau.edu/images/default/sample.pdf"}'
```

### Test with Medical Bill:

Upload your medical bill to Google Drive:
1. Right-click file → Share → Anyone with link
2. Get the file ID from the URL
3. Use direct download URL:

```bash
curl -X POST "https://your-app.onrender.com/extract-bill-data" \
  -H "Content-Type: application/json" \
  -d '{"document": "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID"}'
```

---

## 📊 Expected Success Response

```json
{
  "is_success": true,
  "token_usage": {
    "total_tokens": 5752,
    "input_tokens": 4800,
    "output_tokens": 952
  },
  "data": {
    "pagewise_line_items": [
      {
        "page_no": "1",
        "page_type": "Bill Detail",
        "bill_items": [...]
      }
    ],
    "total_item_count": 8
  },
  "processing_time_seconds": 26.51
}
```

---

## 🐛 If Still Getting Errors

Check Render logs for detailed error messages:
1. Render Dashboard → Your Service → Logs
2. Look for:
   - `📥 Download attempt 1/3: ...`
   - `❌ Attempt X failed: ...`
   - Specific error messages

Common issues and solutions are in [TESTING_GUIDE.md](TESTING_GUIDE.md)

---

## ⚠️ SECURITY NOTE

**NEVER commit your `.env` file or API keys to GitHub!**

The `.env` file is already in `.gitignore`, so it won't be pushed.
Your Anthropic API key should only be set in:
- Render Dashboard → Environment Variables
- Never in code or committed files

---

Good luck! 🚀
