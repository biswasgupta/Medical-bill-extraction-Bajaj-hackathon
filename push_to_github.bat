@echo off
REM Quick deployment script for pushing fixes to GitHub (Windows)

echo.
echo 🚀 Deploying fixes to GitHub...
echo.

REM Navigate to project directory
cd /d "%~dp0"

REM Check if git is initialized
if not exist ".git" (
    echo 📦 Initializing git repository...
    git init
)

REM Add remote if not exists
git remote | findstr /C:"origin" >nul
if errorlevel 1 (
    echo 🔗 Adding GitHub remote...
    git remote add origin https://github.com/biswasgupta/Medical-bill-extraction-Bajaj-hackathon.git
)

REM Show what changed
echo 📝 Files changed:
git status --short

echo.
echo 📦 Staging changes...
git add document_processor.py TESTING_GUIDE.md DEPLOY_INSTRUCTIONS.md push_to_github.bat push_to_github.sh

echo.
echo 💬 Creating commit...
git commit -m "fix: improve download with retry logic, WAF detection, and file validation" -m "- Added retry logic with 3 attempts and exponential backoff" -m "- Enhanced headers to bypass WAF (Web Application Firewall)" -m "- Added detection for WAF challenges (HTML instead of PDF)" -m "- Added file size validation at multiple stages" -m "- Fixed typo in type hint (Tupl6e -> Tuple)" -m "- Added comprehensive testing guide" -m "" -m "Fixes issue: 'Downloaded file is empty (0 bytes)'"

echo.
echo 🌿 Checking out/creating prod branch...
git checkout prod 2>nul || git checkout -b prod

echo.
echo ⬆️  Pushing to GitHub (prod branch)...
echo.
echo ⚠️  IMPORTANT: When prompted for password, use your GitHub Personal Access Token
echo    (NOT your GitHub password - GitHub no longer accepts passwords)
echo.
echo    Username: biswas29.jobs@gmail.com
echo    Password: [Enter your Personal Access Token]
echo.
echo    Don't have a token? Create one at: https://github.com/settings/tokens
echo.
pause

git push -u origin prod

if %errorlevel% equ 0 (
    echo.
    echo ✅ Successfully pushed to GitHub!
    echo.
    echo 🎯 Next steps:
    echo    1. Wait 2-3 minutes for Render to auto-deploy
    echo    2. Check deployment logs in Render dashboard
    echo    3. Test the API with a valid PDF URL
    echo.
    echo 📖 See TESTING_GUIDE.md for testing instructions
) else (
    echo.
    echo ❌ Push failed!
    echo.
    echo Common issues:
    echo    - Using password instead of Personal Access Token
    echo    - Token doesn't have 'repo' permissions
    echo    - Network/connection issues
    echo.
    echo Try using GitHub Desktop instead: https://desktop.github.com/
)

echo.
pause
