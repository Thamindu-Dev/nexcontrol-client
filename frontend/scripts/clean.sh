#!/bin/bash
# NexControl Clean Script
# Cleans build artifacts and caches

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info "Cleaning NexControl build artifacts..."

# Clean Quasar build
print_info "Cleaning Quasar dist..."
rm -rf dist/

# Clean iOS
print_info "Cleaning iOS build..."
rm -rf ios/App/App/public/
rm -rf ios/App/DerivedData/
rm -rf ios/.gradle/

# Clean Android
print_info "Cleaning Android build..."
rm -rf android/app/src/main/assets/public/
rm -rf android/app/build/
rm -rf android/.gradle/
rm -rf android/build/

# Clean node modules (optional, requires confirmation)
if [ "$1" == "--deep" ]; then
    print_warning "Deep clean: removing node_modules..."
    rm -rf node_modules/
    rm -rf ios/Pods/
    rm -rf android/.gradle/
    print_info "Run 'npm install' to reinstall dependencies"
fi

print_info "Clean complete!"
