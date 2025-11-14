#!/usr/bin/env node
/**
 * HTML to Images Converter
 * Converts HTML pages to high-resolution images (one image per .page element)
 */

const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const CONFIG = {
  outputDir: path.join(__dirname, '../output/images'),
  htmlFiles: [
    path.join(__dirname, '../版本2.html'),
    path.join(__dirname, '../理想汽车供应链报告-优化版-2025-1031-1636.html')
  ],
  // A4 landscape dimensions in pixels at 96 DPI (standard screen DPI)
  viewport: {
    width: 1122,  // 297mm at 96 DPI
    height: 794,  // 210mm at 96 DPI
    deviceScaleFactor: 3 // For high quality (effectively 288 DPI)
  },
  imageFormat: 'png',
  imageQuality: 100
};

/**
 * Ensure output directory exists
 */
async function ensureOutputDir() {
  try {
    await fs.mkdir(CONFIG.outputDir, { recursive: true });
    console.log(`✓ Output directory ready: ${CONFIG.outputDir}`);
  } catch (error) {
    console.error('Error creating output directory:', error);
    throw error;
  }
}

/**
 * Convert a single HTML file to images
 * @param {string} htmlFilePath - Path to HTML file
 */
async function convertHtmlToImages(htmlFilePath) {
  const fileName = path.basename(htmlFilePath, '.html');
  console.log(`\n📄 Processing: ${fileName}`);

  // Launch a fresh browser for each file to avoid memory issues
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-web-security',
      '--disable-gpu',
      '--single-process',
      '--no-zygote'
    ]
  });

  const page = await browser.newPage();

  // Set viewport to A4 landscape at high DPI
  await page.setViewportSize({
    width: CONFIG.viewport.width,
    height: CONFIG.viewport.height
  });

  // Load the HTML file
  const fileUrl = `file://${htmlFilePath}`;

  await page.goto(fileUrl, {
    waitUntil: 'networkidle', // Wait for network to be idle (charts loaded)
    timeout: 60000
  });

  // Wait a bit more for Chart.js to render
  await page.waitForTimeout(3000);

  // Get all page elements
  const pageElements = await page.locator('.page').all();
  console.log(`  Found ${pageElements.length} pages`);

  // Screenshot each page
  for (let i = 0; i < pageElements.length; i++) {
    const element = pageElements[i];

    // Scroll the element into view
    await element.scrollIntoViewIfNeeded();

    // Wait a moment for any lazy rendering
    await page.waitForTimeout(500);

    const outputPath = path.join(
      CONFIG.outputDir,
      `${fileName}_page_${String(i + 1).padStart(2, '0')}.png`
    );

    // Take screenshot of this specific element
    await element.screenshot({
      path: outputPath,
      type: CONFIG.imageFormat,
      omitBackground: false,
      scale: 'device' // Use device scale factor
    });

    console.log(`  ✓ Page ${i + 1}/${pageElements.length} → ${path.basename(outputPath)}`);
  }

  await page.close();
  await browser.close();
  return pageElements.length;
}

/**
 * Main conversion process
 */
async function main() {
  console.log('🚀 HTML to Images Converter Started\n');
  console.log(`Resolution: ${CONFIG.viewport.width}x${CONFIG.viewport.height} @ ${CONFIG.viewport.deviceScaleFactor}x`);
  console.log(`Effective DPI: ${300 * CONFIG.viewport.deviceScaleFactor}`);

  await ensureOutputDir();

  let totalPages = 0;

  for (const htmlFile of CONFIG.htmlFiles) {
    try {
      const pageCount = await convertHtmlToImages(htmlFile);
      totalPages += pageCount;
    } catch (error) {
      console.error(`\n❌ Error processing ${htmlFile}:`, error.message);
    }
  }

  console.log(`\n✅ Conversion complete! Total pages: ${totalPages}`);
  console.log(`📁 Output directory: ${CONFIG.outputDir}`);
}

// Run if executed directly
if (require.main === module) {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { main, convertHtmlToImages };
