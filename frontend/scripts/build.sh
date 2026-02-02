#!/bin/bash
# NexControl Build Script
# Builds the app for specified platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if platform is specified
if [ -z "$1" ]; then
    print_error "Please specify a platform: ios, android, or all"
    echo "Usage: ./scripts/build.sh [ios|android|all]"
    exit 1
fi

PLATFORM=$1

# Function to build for a platform
build_platform() {
    local platform=$1
    print_info "Building for $platform..."

    # Sync Capacitor
    print_info "Syncing Capacitor..."
    npx cap sync "$platform"

    # Build command based on platform
    case $platform in
        ios)
            print_info "Opening in Xcode..."
            npx cap open ios
            print_info "Complete! Use Xcode to build and run."
            ;;
        android)
            print_info "Opening in Android Studio..."
            npx cap open android
            print_info "Complete! Use Android Studio to build and run."
            ;;
        *)
            print_error "Unknown platform: $platform"
            exit 1
            ;;
    esac
}

# Build based on input
case $PLATFORM in
    ios)
        build_platform ios
        ;;
    android)
        build_platform android
        ;;
    all)
        build_platform ios
        build_platform android
        ;;
    *)
        print_error "Unknown platform: $PLATFORM"
        exit 1
        ;;
esac

print_info "Build process completed!"
