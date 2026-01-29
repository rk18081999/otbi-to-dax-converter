#!/bin/bash

# OTBI to DAX Converter - Setup for Sharing
# This script prepares your project for Git/GitHub

set -e

echo "🚀 OTBI to DAX Converter - Setup for Sharing"
echo "============================================="
echo ""

cd "/Users/coher/My Pc/Rite/venv/OTBI2PWBI"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install Git first."
    exit 1
fi

echo "✅ Git found: $(git --version)"
echo ""

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Check if .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo "❌ .gitignore not found (should have been created)"
    exit 1
fi

# Check if llm_config.template.py exists
if [ ! -f "llm_config.template.py" ]; then
    echo "❌ llm_config.template.py not found (should have been created)"
    exit 1
fi

# Add all files
echo ""
echo "📝 Adding files to Git..."
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "ℹ️  No changes to commit"
else
    echo "💾 Creating initial commit..."
    git commit -m "Initial commit: LLM-powered OTBI to DAX converter

Features:
- Multi-stage LLM reasoning engine
- Semantic analysis of OTBI SQL
- Join reasoning and cardinality detection
- DAX generation with SELECTCOLUMNS + LOOKUPVALUE pattern
- CLI and Web UI interfaces
- Comprehensive documentation
- Docker and cloud deployment support"
    echo "✅ Initial commit created"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📤 Next Steps - Choose One:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Option 1: Push to GitHub (using GitHub CLI)"
echo "  gh auth login"
echo "  gh repo create otbi-to-dax-converter --public --source=. --push"
echo ""
echo "Option 2: Push to GitHub (manual)"
echo "  1. Create repo at: https://github.com/new"
echo "  2. Run: git remote add origin https://github.com/YOUR_USERNAME/otbi-to-dax-converter.git"
echo "  3. Run: git branch -M main"
echo "  4. Run: git push -u origin main"
echo ""
echo "Option 3: Create archive for Google Cloud Storage"
echo "  cd .."
echo "  tar -czf otbi-to-dax-converter.tar.gz --exclude='.venv' --exclude='llm_config.py' OTBI2PWBI/"
echo "  gsutil cp otbi-to-dax-converter.tar.gz gs://YOUR_BUCKET/"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 For detailed instructions, see: SHARING.md"
echo ""
