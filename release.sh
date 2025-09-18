#!/bin/bash

# Android TV Box HACS Release Script
# This script helps prepare the repository for HACS release

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "hacs.json" ] || [ ! -d "custom_components/android_tv_box" ]; then
    print_error "Please run this script from the repository root directory"
    exit 1
fi

print_header "Android TV Box HACS Release Preparation"
echo "=============================================="

# Get current version from manifest.json
VERSION=$(python3 -c "
import json
with open('custom_components/android_tv_box/manifest.json', 'r') as f:
    manifest = json.load(f)
print(manifest['version'])
")

print_status "Current version: $VERSION"

# Validate files
print_status "Validating files..."

# Check manifest.json
if ! python3 -c "
import json
with open('custom_components/android_tv_box/manifest.json', 'r') as f:
    manifest = json.load(f)
required_fields = ['domain', 'name', 'documentation', 'requirements', 'version']
for field in required_fields:
    if field not in manifest:
        print(f'Missing required field: {field}')
        exit(1)
print('manifest.json validation passed')
"; then
    print_error "manifest.json validation failed"
    exit 1
fi

# Check hacs.json
if ! python3 -c "
import json
with open('hacs.json', 'r') as f:
    hacs_config = json.load(f)
required_fields = ['name', 'content_in_root', 'filename', 'homeassistant']
for field in required_fields:
    if field not in hacs_config:
        print(f'Missing required field: {field}')
        exit(1)
print('hacs.json validation passed')
"; then
    print_error "hacs.json validation failed"
    exit 1
fi

# Check required files
REQUIRED_FILES=(
    "custom_components/android_tv_box/__init__.py"
    "custom_components/android_tv_box/manifest.json"
    "custom_components/android_tv_box/config.py"
    "custom_components/android_tv_box/config_flow.py"
    "README.md"
    "HACS_INSTALLATION.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Missing required file: $file"
        exit 1
    fi
done

print_status "All required files present"

# Check for placeholder URLs
print_status "Checking for placeholder URLs..."

if grep -r "your-username" . --exclude-dir=.git --exclude="release.sh" > /dev/null; then
    print_warning "Found placeholder 'your-username' in files"
    print_warning "Please replace with your actual GitHub username before release"
fi

if grep -r "your-repo" . --exclude-dir=.git --exclude="release.sh" > /dev/null; then
    print_warning "Found placeholder 'your-repo' in files"
    print_warning "Please replace with your actual repository name before release"
fi

# Create release notes
print_status "Creating release notes..."

RELEASE_NOTES="## Release v$VERSION

### Features
- Android TV Box control via ADB
- Media player integration
- Switch controls (power, WiFi)
- Camera entity for screenshots
- Sensor entities for monitoring
- Remote control entity
- Application selector
- iSG monitoring with auto-wake
- Web management interface (port 3003)

### Installation
- Install via HACS: Add custom repository \`https://github.com/your-username/android-tv-box\`
- Or download manually and place in \`custom_components/\` directory

### Configuration
- Add integration through Home Assistant UI
- Configure ADB connection settings
- Set up applications for selector
- Enable iSG monitoring if needed

### Requirements
- Home Assistant >= 2023.1.0
- Android device with root access
- Termux application
- ADB enabled on Android device

### Support
- GitHub Issues: https://github.com/your-username/android-tv-box/issues
- Documentation: https://github.com/your-username/android-tv-box/blob/main/README.md"

echo "$RELEASE_NOTES" > RELEASE_NOTES.md
print_status "Release notes created: RELEASE_NOTES.md"

# Check git status
if command -v git > /dev/null; then
    print_status "Checking git status..."
    
    if [ -d ".git" ]; then
        if ! git diff --quiet; then
            print_warning "You have uncommitted changes"
            print_warning "Please commit your changes before creating a release"
        else
            print_status "Git working directory is clean"
        fi
        
        # Check if we're on main/master branch
        CURRENT_BRANCH=$(git branch --show-current)
        if [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
            print_warning "You're not on main/master branch (current: $CURRENT_BRANCH)"
            print_warning "Consider switching to main branch for release"
        fi
    else
        print_warning "Not a git repository"
        print_warning "Initialize git repository for version control"
    fi
else
    print_warning "Git not available"
fi

print_header "Release Preparation Complete!"
echo "================================"

print_status "Next steps:"
echo "1. Replace placeholder URLs with your actual GitHub information"
echo "2. Commit all changes to git"
echo "3. Create a release tag: git tag v$VERSION"
echo "4. Push to GitHub: git push origin main --tags"
echo "5. Create a GitHub release with the notes from RELEASE_NOTES.md"
echo "6. Add the repository to HACS custom repositories"

print_status "Files ready for HACS:"
echo "- ✅ hacs.json"
echo "- ✅ custom_components/android_tv_box/manifest.json"
echo "- ✅ custom_components/android_tv_box/ (all files)"
echo "- ✅ README.md"
echo "- ✅ HACS_INSTALLATION.md"

print_warning "Remember to:"
echo "- Update version number in manifest.json for new releases"
echo "- Test the integration before releasing"
echo "- Update documentation if needed"

print_status "Release preparation completed successfully! 🎉"
