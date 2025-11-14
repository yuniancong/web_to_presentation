#!/usr/bin/env node
/**
 * HTML to Images Converter
 * Converts HTML pages to high-resolution images (one image per .page element)
 */

const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');
const { glob } = require('glob');

// Load configuration
function loadConfig() {
  const configPath = path.join(__dirname, 'html-to-images-config.json');
  let customConfig = {};

  try {
    if (require('fs').existsSync(configPath)) {
      const configData = require('fs').readFileSync(configPath, 'utf-8');
      customConfig = JSON.parse(configData);
      console.log('✓ Loaded custom configuration');
    }
  } catch (error) {
    console.log('⚠ Using default configuration');
  }

  // Default configuration
  const defaultConfig = {
    outputDir: path.join(__dirname, '../output/images'),
    // Scan patterns for HTML files (will scan root directory and subdirectories)
    scanPatterns: [
      path.join(__dirname, '../*.html'),           // Root directory
      path.join(__dirname, '../**/*.html'),        // All subdirectories
    ],
    // Exclude patterns (files/folders to ignore)
    excludePatterns: [
      '**/node_modules/**',
      '**/output/**',
      '**/.git/**',
      '**/dist/**',
      '**/build/**',
      '**/frontend/**'
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

  // Merge custom config with defaults
  return {
    ...defaultConfig,
    viewport: { ...defaultConfig.viewport, ...customConfig.viewport },
    imageFormat: customConfig.imageFormat || defaultConfig.imageFormat,
    imageQuality: customConfig.imageQuality || defaultConfig.imageQuality
  };
}

const CONFIG = loadConfig();

/**
 * Scan for HTML files in the project
 * @returns {Promise<string[]>} Array of HTML file paths
 */
async function scanHtmlFiles() {
  const allFiles = [];

  for (const pattern of CONFIG.scanPatterns) {
    try {
      const files = await glob(pattern, {
        ignore: CONFIG.excludePatterns,
        absolute: true,
        nodir: true // Only match files, not directories
      });
      allFiles.push(...files);
    } catch (error) {
      console.error(`Error scanning pattern ${pattern}:`, error.message);
    }
  }

  // Remove duplicates and sort
  const uniqueFiles = [...new Set(allFiles)].sort();
  return uniqueFiles;
}

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

  // Create a new context with device scale factor
  const context = await browser.newContext({
    viewport: {
      width: CONFIG.viewport.width,
      height: CONFIG.viewport.height
    },
    deviceScaleFactor: CONFIG.viewport.deviceScaleFactor
  });

  const page = await context.newPage();

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
  await context.close();
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

  // Scan for HTML files
  console.log('\n📂 Scanning for HTML files...');
  const htmlFiles = await scanHtmlFiles();

  if (htmlFiles.length === 0) {
    console.log('⚠️  No HTML files found in the project directory.');
    console.log('   Please add HTML files to the root directory or subdirectories.');
    return;
  }

  console.log(`✓ Found ${htmlFiles.length} HTML file(s):`);
  htmlFiles.forEach((file, index) => {
    const relativePath = path.relative(path.join(__dirname, '..'), file);
    console.log(`  ${index + 1}. ${relativePath}`);
  });

  let totalPages = 0;
  let successCount = 0;
  let failCount = 0;

  for (const htmlFile of htmlFiles) {
    try {
      const pageCount = await convertHtmlToImages(htmlFile);
      totalPages += pageCount;
      successCount++;
    } catch (error) {
      console.error(`\n❌ Error processing ${htmlFile}:`, error.message);
      failCount++;
    }
  }

  console.log(`\n✅ Conversion complete!`);
  console.log(`   Processed: ${successCount} success, ${failCount} failed`);
  console.log(`   Total pages: ${totalPages}`);
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
