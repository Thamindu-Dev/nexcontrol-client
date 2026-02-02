#!/bin/bash
# NexControl Capacitor Sync Script
# Syncs web assets to native platforms

set -e

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Check if platform is specified
PLATFORM=${1:-"all"}

print_info "Building Quasar app..."
npm run build

print_info "Syncing to $PLATFORM..."

case $PLATFORM in
    ios)
        npx cap sync ios
        ;;
    android)
        npx cap sync android
        ;;
    all)
        npx cap sync ios
        npx cap sync android
        ;;
    *)
        echo "Usage: ./scripts/sync.sh [ios|android|all]"
        exit 1
        ;;
esac

print_info "Sync complete!"
