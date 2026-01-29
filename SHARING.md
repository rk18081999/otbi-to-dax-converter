# Sharing Your Work - Git & Google Cloud Storage Guide

## 📋 Table of Contents

1. [Git/GitHub Setup](#git-github-setup)
2. [Google Cloud Storage Setup](#google-cloud-storage-setup)
3. [Best Practices](#best-practices)
4. [What to Include/Exclude](#what-to-include-exclude)

---

## 1. Git/GitHub Setup

### Option A: Push to GitHub (Recommended)

#### Step 1: Create .gitignore
```bash
cd "/Users/coher/My Pc/Rite/venv/OTBI2PWBI"

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg
*.egg-info/
dist/
build/
.venv/
venv/
ENV/

# Environment variables
.env
llm_config.py

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Logs
*.log
otbi-dax.log

# Output files
*.dax
!Demo_DAXquery.dax

# Temporary files
*.tmp
*.bak
EOF
```

#### Step 2: Initialize Git Repository
```bash
# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: LLM-powered OTBI to DAX converter"
```

#### Step 3: Create GitHub Repository

**Option 3a: Using GitHub CLI (if installed)**
```bash
# Install GitHub CLI (if not installed)
# brew install gh  # macOS

# Login to GitHub
gh auth login

# Create repository
gh repo create otbi-to-dax-converter \
  --public \
  --description "LLM-powered converter for Oracle OTBI Physical SQL to Power BI DAX" \
  --source=. \
  --remote=origin \
  --push
```

**Option 3b: Using GitHub Web Interface**
1. Go to https://github.com/new
2. Repository name: `otbi-to-dax-converter`
3. Description: `LLM-powered converter for Oracle OTBI Physical SQL to Power BI DAX`
4. Choose Public or Private
5. **DO NOT** initialize with README (you already have one)
6. Click "Create repository"

Then push your code:
```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/otbi-to-dax-converter.git

# Push to GitHub
git branch -M main
git push -u origin main
```

#### Step 4: Create llm_config.py Template
```bash
# Create a template version for GitHub
cat > llm_config.template.py << 'EOF'
"""
LLM Configuration Template
Copy this file to llm_config.py and add your API key
"""
import os

# Get Gemini API key from environment variable or set directly
# Get your API key at: https://makersuite.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Uncomment and set your API key directly (not recommended for production)
# GEMINI_API_KEY = "your-api-key-here"

if not GEMINI_API_KEY:
    print("⚠️  Warning: GEMINI_API_KEY not configured")
    print("   Set it in this file or as environment variable")
EOF

# Add template to git
git add llm_config.template.py
git commit -m "Add llm_config template"
git push
```

#### Step 5: Update README with Setup Instructions
```bash
# Add setup section to README
cat >> README.md << 'EOF'

## 🔧 Setup from GitHub

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/otbi-to-dax-converter.git
cd otbi-to-dax-converter
```

### 2. Configure API Key
```bash
# Copy template
cp llm_config.template.py llm_config.py

# Edit and add your API key
nano llm_config.py
```

### 3. Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run
```bash
# CLI
.venv/bin/python main.py Demo_SQL.sql

# Web UI
.venv/bin/python app.py
```
EOF

git add README.md
git commit -m "Add setup instructions for GitHub users"
git push
```

---

## 2. Google Cloud Storage Setup

### Option B: Share via Google Cloud Storage

#### Step 1: Install Google Cloud SDK
```bash
# macOS
brew install --cask google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

#### Step 2: Authenticate
```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

#### Step 3: Create GCS Bucket
```bash
# Create bucket (must be globally unique name)
gsutil mb -l us-central1 gs://otbi-to-dax-converter-YOUR_UNIQUE_ID/

# Or use web console: https://console.cloud.google.com/storage
```

#### Step 4: Create Archive
```bash
cd "/Users/coher/My Pc/Rite/venv"

# Create archive excluding sensitive files
tar -czf otbi-to-dax-converter.tar.gz \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='*.log' \
  --exclude='llm_config.py' \
  OTBI2PWBI/

# Verify archive contents
tar -tzf otbi-to-dax-converter.tar.gz | head -20
```

#### Step 5: Upload to GCS
```bash
# Upload archive
gsutil cp otbi-to-dax-converter.tar.gz gs://otbi-to-dax-converter-YOUR_UNIQUE_ID/

# Make it publicly accessible (optional)
gsutil acl ch -u AllUsers:R gs://otbi-to-dax-converter-YOUR_UNIQUE_ID/otbi-to-dax-converter.tar.gz

# Get public URL
echo "https://storage.googleapis.com/otbi-to-dax-converter-YOUR_UNIQUE_ID/otbi-to-dax-converter.tar.gz"
```

#### Step 6: Create README for GCS
```bash
cat > GCS_DOWNLOAD_INSTRUCTIONS.md << 'EOF'
# Download from Google Cloud Storage

## Direct Download
```bash
# Download archive
wget https://storage.googleapis.com/otbi-to-dax-converter-YOUR_UNIQUE_ID/otbi-to-dax-converter.tar.gz

# Extract
tar -xzf otbi-to-dax-converter.tar.gz
cd OTBI2PWBI
```

## Using gsutil
```bash
# Download with gsutil
gsutil cp gs://otbi-to-dax-converter-YOUR_UNIQUE_ID/otbi-to-dax-converter.tar.gz .

# Extract
tar -xzf otbi-to-dax-converter.tar.gz
cd OTBI2PWBI
```

## Setup After Download
1. Copy API key template: `cp llm_config.template.py llm_config.py`
2. Edit and add your API key: `nano llm_config.py`
3. Create virtual environment: `python3 -m venv .venv`
4. Activate: `source .venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Run: `.venv/bin/python app.py`
EOF

# Upload instructions
gsutil cp GCS_DOWNLOAD_INSTRUCTIONS.md gs://otbi-to-dax-converter-YOUR_UNIQUE_ID/
```

---

## 3. Best Practices

### Security Checklist

✅ **DO Include**:
- Source code files (`.py`)
- Documentation (`.md`)
- Configuration templates (`.template.py`, `.env.example`)
- Demo files (`Demo_SQL.sql`, `Demo_DAXquery.dax`)
- Deployment files (`Dockerfile`, `docker-compose.yml`, etc.)
- Prompt templates (`prompts/*.txt`)

❌ **DO NOT Include**:
- API keys (`llm_config.py` with real key)
- Environment files (`.env` with secrets)
- Virtual environments (`.venv/`, `venv/`)
- Cache files (`__pycache__/`, `*.pyc`)
- Log files (`*.log`)
- Personal data
- Large binary files

### .gitignore Best Practices

Your `.gitignore` should exclude:
```
# Secrets
.env
llm_config.py
*.key
*.pem

# Python
.venv/
__pycache__/
*.pyc

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Output
*.dax
!Demo_DAXquery.dax
```

---

## 4. What to Include/Exclude

### ✅ Files to Include

```
OTBI2PWBI/
├── *.py                      # All Python source files
├── prompts/*.txt             # Prompt templates
├── templates/                # Flask templates (if any)
├── static/                   # Static assets (if any)
├── *.md                      # All documentation
├── requirements.txt          # Dependencies
├── Dockerfile                # Container config
├── docker-compose.yml        # Compose config
├── Procfile                  # Cloud platform config
├── .env.example              # Environment template
├── llm_config.template.py    # Config template
├── deploy.sh                 # Deployment script
├── Demo_SQL.sql              # Example input
└── Demo_DAXquery.dax         # Example output
```

### ❌ Files to Exclude

```
OTBI2PWBI/
├── .venv/                    # Virtual environment
├── __pycache__/              # Python cache
├── *.pyc                     # Compiled Python
├── .env                      # Real environment vars
├── llm_config.py             # Real API key
├── *.log                     # Log files
├── .DS_Store                 # macOS metadata
└── *.dax (except Demo)       # Generated output
```

---

## 5. Quick Commands Reference

### Git Workflow
```bash
# Initial setup
git init
git add .
git commit -m "Initial commit"

# Create GitHub repo and push
gh repo create otbi-to-dax-converter --public --source=. --push

# Regular updates
git add .
git commit -m "Update: description of changes"
git push
```

### GCS Workflow
```bash
# Create archive
tar -czf otbi-to-dax-converter.tar.gz \
  --exclude='.venv' \
  --exclude='llm_config.py' \
  OTBI2PWBI/

# Upload
gsutil cp otbi-to-dax-converter.tar.gz gs://YOUR_BUCKET/

# Make public (optional)
gsutil acl ch -u AllUsers:R gs://YOUR_BUCKET/otbi-to-dax-converter.tar.gz
```

---

## 6. Sharing Options Comparison

| Feature | GitHub | Google Cloud Storage |
|---------|--------|---------------------|
| **Version Control** | ✅ Yes | ❌ No |
| **Collaboration** | ✅ Easy | ⚠️ Manual |
| **Free Tier** | ✅ Unlimited public repos | ⚠️ 5GB free |
| **Discovery** | ✅ Searchable | ❌ Direct link only |
| **CI/CD** | ✅ GitHub Actions | ⚠️ Requires setup |
| **Best For** | Open source, collaboration | Large files, backups |

**Recommendation**: Use **GitHub** for version control and collaboration. Use **GCS** for large file backups or private distribution.

---

## 7. Complete Setup Script

Save this as `setup_sharing.sh`:

```bash
#!/bin/bash

echo "🚀 OTBI to DAX Converter - Setup Sharing"
echo "========================================"
echo ""

# Create .gitignore
echo "📝 Creating .gitignore..."
cat > .gitignore << 'EOF'
.venv/
__pycache__/
*.pyc
.env
llm_config.py
*.log
.DS_Store
.vscode/
.idea/
*.dax
!Demo_DAXquery.dax
EOF

# Create config template
echo "📝 Creating llm_config.template.py..."
cat > llm_config.template.py << 'EOF'
import os
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# GEMINI_API_KEY = "your-api-key-here"
EOF

# Initialize git
echo "🔧 Initializing Git..."
git init
git add .
git commit -m "Initial commit: LLM-powered OTBI to DAX converter"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create GitHub repo: gh repo create otbi-to-dax-converter --public --source=. --push"
echo "2. Or manually: https://github.com/new"
echo ""
```

Make it executable:
```bash
chmod +x setup_sharing.sh
./setup_sharing.sh
```

---

## 8. Troubleshooting

### Git Issues

**Problem**: "fatal: not a git repository"
```bash
git init
```

**Problem**: "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/repo.git
```

**Problem**: "API key exposed in commit"
```bash
# Remove from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch llm_config.py" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
```

### GCS Issues

**Problem**: "gsutil: command not found"
```bash
brew install --cask google-cloud-sdk
```

**Problem**: "Access denied"
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

---

## Summary

**For Open Source/Collaboration**: Use GitHub
```bash
git init
git add .
git commit -m "Initial commit"
gh repo create otbi-to-dax-converter --public --source=. --push
```

**For Private Distribution**: Use GCS
```bash
tar -czf otbi-to-dax-converter.tar.gz --exclude='.venv' --exclude='llm_config.py' OTBI2PWBI/
gsutil cp otbi-to-dax-converter.tar.gz gs://YOUR_BUCKET/
```

**Best Practice**: Use both! GitHub for code, GCS for large files/backups.
