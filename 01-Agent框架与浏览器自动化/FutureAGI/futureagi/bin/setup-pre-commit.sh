#!/bin/bash
# Setup script for pre-commit hooks
# This script installs and configures pre-commit for the core-backend project

set -e

echo "🔧 Setting up pre-commit hooks for core-backend..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.11+"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python version: $PYTHON_VERSION"

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
else
    echo "✓ pre-commit is already installed ($(pre-commit --version))"
fi

# Install pre-commit hooks
echo "🔨 Installing pre-commit hooks..."
pre-commit install

# Install commit-msg hook (for additional checks if needed)
pre-commit install --hook-type commit-msg

# Install pre-push hook (for heavier checks)
pre-commit install --hook-type pre-push

# Update hooks to latest versions
echo "🔄 Updating pre-commit hooks to latest versions..."
pre-commit autoupdate

# Initialize secrets baseline if it doesn't exist
if [ ! -f .secrets.baseline ]; then
    echo "🔒 Creating secrets baseline..."
    detect-secrets scan > .secrets.baseline || echo "⚠️  Warning: detect-secrets not installed yet, will be installed on first run"
fi

echo ""
echo "✅ Pre-commit setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Run 'pre-commit run --all-files' to check all files"
echo "   2. Fix any issues that are found"
echo "   3. Commit your changes - hooks will run automatically"
echo ""
echo "💡 Useful commands:"
echo "   - pre-commit run --all-files     # Run on all files"
echo "   - pre-commit run <hook-id>       # Run specific hook"
echo "   - pre-commit run --files <file>  # Run on specific file"
echo "   - SKIP=<hook-id> git commit      # Skip specific hook (emergency only)"
echo "   - make pre-commit                # Run via Makefile"
echo ""
