#!/bin/bash
# Quick deployment script for pushing fixes to GitHub

echo "🚀 Deploying fixes to GitHub..."
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
fi

# Add remote if not exists
if ! git remote | grep -q origin; then
    echo "🔗 Adding GitHub remote..."
    git remote add origin https://github.com/biswasgupta/Medical-bill-extraction-Bajaj-hackathon.git
fi

# Show what changed
echo "📝 Files changed:"
git status --short

echo ""
echo "📦 Staging changes..."
git add document_processor.py TESTING_GUIDE.md DEPLOY_INSTRUCTIONS.md

echo ""
echo "💬 Creating commit..."
git commit -m "fix: improve download with retry logic, WAF detection, and file validation

- Added retry logic with 3 attempts and exponential backoff
- Enhanced headers to bypass WAF (Web Application Firewall)
- Added detection for WAF challenges (HTML instead of PDF)
- Added file size validation at multiple stages
- Fixed typo in type hint (Tupl6e -> Tuple)
- Added comprehensive testing guide

Fixes issue: 'Downloaded file is empty (0 bytes)'"

echo ""
echo "🌿 Checking out/creating prod branch..."
git checkout -b prod 2>/dev/null || git checkout prod

echo ""
echo "⬆️  Pushing to GitHub (prod branch)..."
echo ""
echo "⚠️  IMPORTANT: When prompted for password, use your GitHub Personal Access Token"
echo "   (NOT your GitHub password - GitHub no longer accepts passwords)"
echo ""
echo "   Username: biswas29.jobs@gmail.com"
echo "   Password: [Enter your Personal Access Token]"
echo ""
echo "   Don't have a token? Create one at: https://github.com/settings/tokens"
echo ""

git push -u origin prod

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Wait 2-3 minutes for Render to auto-deploy"
    echo "   2. Check deployment logs in Render dashboard"
    echo "   3. Test the API with a valid PDF URL"
    echo ""
    echo "📖 See TESTING_GUIDE.md for testing instructions"
else
    echo ""
    echo "❌ Push failed!"
    echo ""
    echo "Common issues:"
    echo "   - Using password instead of Personal Access Token"
    echo "   - Token doesn't have 'repo' permissions"
    echo "   - Network/connection issues"
    echo ""
    echo "Try using GitHub Desktop instead: https://desktop.github.com/"
fi
