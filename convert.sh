#!/bin/bash

###############################################################################
# Web to Presentation Converter
#
# This script converts HTML reports to high-resolution images and PowerPoint
# presentations.
#
# Usage:
#   ./convert.sh [--images-only | --ppt-only]
#
# Options:
#   --images-only   Only convert HTML to images (skip PPT generation)
#   --ppt-only      Only convert images to PPT (skip HTML to images)
#   (no options)    Run full pipeline: HTML → Images → PPT
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Web to Presentation Converter v1.0                 ║${NC}"
echo -e "${BLUE}║        HTML → High-Res Images → PowerPoint                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Parse arguments
IMAGES_ONLY=false
PPT_ONLY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --images-only)
      IMAGES_ONLY=true
      shift
      ;;
    --ppt-only)
      PPT_ONLY=true
      shift
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Usage: ./convert.sh [--images-only | --ppt-only]"
      exit 1
      ;;
  esac
done

# Check dependencies
check_dependencies() {
    echo -e "${YELLOW}🔍 Checking dependencies...${NC}"

    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed${NC}"
        echo "   Please install Node.js from https://nodejs.org/"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Node.js $(node --version)"

    # Check npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm is not installed${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} npm $(npm --version)"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed${NC}"
        echo "   Please install Python 3 from https://www.python.org/"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Python $(python3 --version)"

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}❌ pip3 is not installed${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} pip $(pip3 --version)"

    echo ""
}

# Install Node.js dependencies
install_node_deps() {
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
        npm install
        echo ""
    fi
}

# Install Python dependencies
install_python_deps() {
    echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
    pip3 install -q -r requirements.txt
    echo -e "  ${GREEN}✓${NC} Python packages installed"
    echo ""
}

# Convert HTML to images
html_to_images() {
    echo -e "${YELLOW}🖼️  Step 1: Converting HTML to high-resolution images...${NC}"
    echo ""
    node src/html-to-images.js
    echo ""
}

# Convert images to PPT
images_to_ppt() {
    echo -e "${YELLOW}📊 Step 2: Converting images to PowerPoint...${NC}"
    echo ""
    python3 src/images-to-ppt.py
    echo ""
}

# Main execution
main() {
    check_dependencies

    if [ "$PPT_ONLY" = false ]; then
        install_node_deps
    fi

    if [ "$IMAGES_ONLY" = false ]; then
        install_python_deps
    fi

    # Run conversion pipeline
    if [ "$PPT_ONLY" = false ]; then
        html_to_images
    fi

    if [ "$IMAGES_ONLY" = false ]; then
        images_to_ppt
    fi

    # Summary
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                 ✨ Conversion Complete! ✨                 ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "📁 Output files:"
    echo -e "  ${BLUE}Images:${NC}  ./output/images/"
    echo -e "  ${BLUE}PPT:${NC}     ./output/*.pptx"
    echo ""

    # List generated files
    if [ -d "output" ]; then
        echo -e "${YELLOW}Generated files:${NC}"
        if [ -d "output/images" ]; then
            IMAGE_COUNT=$(ls -1 output/images/*.png 2>/dev/null | wc -l)
            echo -e "  ${GREEN}✓${NC} $IMAGE_COUNT images"
        fi
        if ls output/*.pptx 1> /dev/null 2>&1; then
            for pptx in output/*.pptx; do
                SIZE=$(du -h "$pptx" | cut -f1)
                echo -e "  ${GREEN}✓${NC} $(basename "$pptx") ($SIZE)"
            done
        fi
    fi
    echo ""
}

# Run main function
main
