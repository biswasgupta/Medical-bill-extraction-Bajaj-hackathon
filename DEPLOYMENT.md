# Deployment Guide - Bajaj Health Datathon API

## 🚀 Deploy to Render

### Prerequisites
- GitHub account
- Render account (free tier available)
- Anthropic API key

---

## Step 1: Push to GitHub

```bash
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Medical bill extraction API for Bajaj Health Datathon"

# Add remote repository (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/bajaj-health-datathon.git

# Push to GitHub
git push -u origin main
```

---

## Step 2: Deploy on Render

### Option A: Using render.yaml (Recommended)

1. **Go to [Render Dashboard](https://dashboard.render.com/)**
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml`
5. Set environment variables:
   - `ANTHROPIC_API_KEY`: Your Claude API key
6. Click **"Apply"**
7. Wait for deployment (5-10 minutes)

### Option B: Manual Setup

1. **Go to [Render Dashboard](https://dashboard.render.com/)**
2. Click **"New"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `bajaj-health-datathon`
   - **Environment**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && apt-get update && apt-get install -y poppler-utils
     ```
   - **Start Command**:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
5. Add environment variables:
   - `ANTHROPIC_API_KEY`: Your Claude API key
6. Click **"Create Web Service"**
7. Wait for deployment

---

## Step 3: Verify Deployment

Once deployed, your API will be available at:
```
https://YOUR_APP_NAME.onrender.com
```

### Test Endpoints

1. **Health Check**:
   ```bash
   curl https://YOUR_APP_NAME.onrender.com/
   ```

2. **API Documentation**:
   Visit: `https://YOUR_APP_NAME.onrender.com/docs`

3. **Test Extraction**:
   ```bash
   curl -X POST https://YOUR_APP_NAME.onrender.com/extract-bill-data \
     -H "Content-Type: application/json" \
     -d '{"document": "https://example.com/bill.pdf"}'
   ```

---

## Important Notes

### ⚠️ Render Free Tier Limitations

- **Spin down after inactivity**: Free tier services sleep after 15 minutes of inactivity
- **Cold start**: First request after sleep takes 30-60 seconds
- **750 hours/month**: Free tier limit (enough for development/testing)

### 💡 Production Considerations

For production deployment:

1. **Upgrade to Paid Plan** ($7/month):
   - No sleep/spin down
   - Faster performance
   - More memory (512MB → 2GB+)

2. **Add Poppler System Dependency**:
   - Already configured in build command
   - Required for PDF processing

3. **Set Environment Variables**:
   ```
   ANTHROPIC_API_KEY=<your-key>
   HOST=0.0.0.0
   PORT=$PORT (automatically set by Render)
   ```

4. **Monitor Logs**:
   - Check Render dashboard for real-time logs
   - Monitor token usage and costs

---

## Troubleshooting

### Issue: Build fails with "poppler not found"
**Solution**: Ensure build command includes:
```bash
apt-get update && apt-get install -y poppler-utils
```

### Issue: API returns 500 error
**Solution**:
- Check Render logs for detailed error
- Verify `ANTHROPIC_API_KEY` is set correctly
- Ensure PDF URL is publicly accessible

### Issue: Timeout on large PDFs
**Solution**:
- Already configured with 10-minute timeout
- For 90+ page bills, consider upgrading Render plan
- API auto-saves results even if connection drops

### Issue: Service takes long to respond
**Solution**:
- First request after sleep (free tier) takes 30-60s
- Subsequent requests are fast
- Consider paid plan to eliminate spin down

---

## Local Testing Before Deployment

```bash
# Set environment variable
export ANTHROPIC_API_KEY="your-key-here"

# Test locally
uvicorn main:app --host 0.0.0.0 --port 8000

# Visit: http://localhost:8000/docs
```

---

## Post-Deployment Checklist

- [ ] API is accessible at Render URL
- [ ] `/docs` endpoint shows Swagger UI
- [ ] Test with sample PDF (train_sample_3.pdf)
- [ ] Verify extraction accuracy
- [ ] Check logs for errors
- [ ] Monitor token usage
- [ ] Test with large multi-page bill (90+ pages)
- [ ] Verify auto-save functionality

---

## Support

For issues or questions:
- Check Render logs first
- Review README.md for troubleshooting
- Verify environment variables are set
- Test locally before reporting deployment issues

---

## Security Notes

🔒 **Never commit `.env` file to GitHub!**
- `.env` is already in `.gitignore`
- Set `ANTHROPIC_API_KEY` in Render dashboard
- Rotate API keys periodically

---

## Cost Estimation

**Render Costs:**
- Free tier: $0/month (with limitations)
- Starter: $7/month (recommended for production)

**Claude API Costs:**
- Based on test results: ~5,000-10,000 tokens per 3-page bill
- Estimate ~$0.01-0.02 per bill extraction
- Monitor usage in Anthropic console

---

Good luck with your deployment! 🚀
