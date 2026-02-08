#!/usr/bin/env node

/**
 * Cistercian Font Glyph Generator
 *
 * Generates SVG glyphs for all numbers 1-9999 using the Cistercian numeral system.
 * Outputs normalized SVGs suitable for font creation.
 */

const fs = require("fs");
const path = require("path");

// Import the Cistercian generator (modified for Node.js)
const {
  toCistercian,
  configure,
} = require("../cistercian-source/toCistercian.js");

// Font configuration
const FONT_CONFIG = {
  // Standard font metrics (1000 units per em)
  unitsPerEm: 1000,
  ascender: 800,
  descender: -200,
  capHeight: 700,
  xHeight: 500,

  // Glyph dimensions
  glyphWidth: 600, // Fixed width for monospace behavior
  glyphHeight: 800,

  // SVG viewBox and scaling
  svgWidth: 120,
  svgHeight: 180,

  // Stroke configuration for consistent appearance
  strokeWidth: 8,
  strokeColor: "#000",
};

/**
 * Configure the Cistercian generator for font-optimized output
 */
function setupCistercianConfig() {
  configure({
    canvas: { width: FONT_CONFIG.svgWidth },
    stroke: {
      colour: FONT_CONFIG.strokeColor,
      width: FONT_CONFIG.strokeWidth,
      cap: "square",
    },
  });
}

/**
 * Normalize SVG for font usage
 * - Remove XML declaration and DOCTYPE
 * - Set consistent viewBox
 * - Ensure proper coordinate system
 * - Add font-specific attributes
 */
function normalizeSVGForFont(svgString, number) {
  // Remove XML declaration and clean up
  let cleanSvg = svgString
    .replace(/<\?xml[^>]*\?>/, "")
    .replace(/<!DOCTYPE[^>]*>/, "")
    .trim();

  // Extract the inner content (lines)
  const lineMatches = cleanSvg.match(/<line[^>]*>/g) || [];

  // Create normalized SVG with proper viewBox and coordinate system
  const viewBox = `0 0 ${FONT_CONFIG.svgWidth} ${FONT_CONFIG.svgHeight}`;

  const normalizedSvg = `<svg viewBox="${viewBox}" xmlns="http://www.w3.org/2000/svg">
  <title>Cistercian numeral ${number}</title>
  <g id="glyph-${number}">
    ${lineMatches.join("\n    ")}
  </g>
</svg>`;

  return normalizedSvg;
}

/**
 * Generate glyph metadata for font creation
 */
function generateGlyphMetadata(number) {
  return {
    number: number,
    unicode: null, // Will be assigned during font creation
    glyphName: `cistercian_${number}`,
    width: FONT_CONFIG.glyphWidth,
    leftSideBearing: (FONT_CONFIG.glyphWidth - FONT_CONFIG.svgWidth) / 2,
    rightSideBearing: (FONT_CONFIG.glyphWidth - FONT_CONFIG.svgWidth) / 2,
  };
}

/**
 * Generate all Cistercian glyphs (1-9999)
 */
function generateAllGlyphs() {
  console.log("Setting up Cistercian configuration...");
  setupCistercianConfig();

  console.log("Creating output directories...");
  const glyphsDir = path.join(__dirname, "..", "glyphs");
  const metadataDir = path.join(__dirname, "..", "metadata");

  if (!fs.existsSync(glyphsDir)) {
    fs.mkdirSync(glyphsDir, { recursive: true });
  }
  if (!fs.existsSync(metadataDir)) {
    fs.mkdirSync(metadataDir, { recursive: true });
  }

  console.log("Generating glyphs for numbers 1-9999...");

  const glyphMetadata = [];
  const batchSize = 100;
  let processed = 0;

  for (let number = 1; number <= 9999; number++) {
    try {
      // Generate SVG using Cistercian generator
      const rawSvg = toCistercian(number);

      if (!rawSvg) {
        console.warn(`Failed to generate SVG for number ${number}`);
        continue;
      }

      // Normalize SVG for font usage
      const normalizedSvg = normalizeSVGForFont(rawSvg, number);

      // Generate metadata
      const metadata = generateGlyphMetadata(number);
      glyphMetadata.push(metadata);

      // Save SVG file
      const svgFilename = `cistercian_${number.toString().padStart(4, "0")}.svg`;
      const svgPath = path.join(glyphsDir, svgFilename);
      fs.writeFileSync(svgPath, normalizedSvg, "utf8");

      processed++;

      // Progress reporting
      if (processed % batchSize === 0) {
        console.log(
          `Generated ${processed}/9999 glyphs (${((processed / 9999) * 100).toFixed(1)}%)`,
        );
      }
    } catch (error) {
      console.error(
        `Error generating glyph for number ${number}:`,
        error.message,
      );
    }
  }

  // Save metadata
  console.log("Saving glyph metadata...");
  const metadataPath = path.join(metadataDir, "glyphs.json");
  fs.writeFileSync(
    metadataPath,
    JSON.stringify(
      {
        fontConfig: FONT_CONFIG,
        glyphs: glyphMetadata,
        totalGlyphs: glyphMetadata.length,
        generatedAt: new Date().toISOString(),
      },
      null,
      2,
    ),
    "utf8",
  );

  // Generate ligature mapping
  console.log("Generating ligature mappings...");
  generateLigatureMappings(glyphMetadata);

  console.log(`\nGeneration complete!`);
  console.log(`- Generated ${processed} SVG glyphs`);
  console.log(`- Saved to: ${glyphsDir}`);
  console.log(`- Metadata: ${metadataPath}`);
}

/**
 * Generate OpenType ligature mappings
 */
function generateLigatureMappings(glyphMetadata) {
  const mappings = [];

  // Generate substitution rules for each number
  glyphMetadata.forEach((glyph) => {
    const number = glyph.number;
    const digits = number.toString().split("");

    // Create ligature rule: digits -> cistercian glyph
    mappings.push({
      input: digits,
      output: glyph.glyphName,
      number: number,
    });
  });

  // Sort by length (longer sequences first for proper matching)
  mappings.sort((a, b) => b.input.length - a.input.length);

  const ligatureData = {
    mappings: mappings,
    totalMappings: mappings.length,
    generatedAt: new Date().toISOString(),
  };

  const ligaturePath = path.join(__dirname, "..", "metadata", "ligatures.json");
  fs.writeFileSync(ligaturePath, JSON.stringify(ligatureData, null, 2), "utf8");

  console.log(`Generated ${mappings.length} ligature mappings`);
}

// Run the generator if called directly
if (require.main === module) {
  console.log("Cistercian Font Glyph Generator");
  console.log("================================");
  generateAllGlyphs();
}

module.exports = {
  generateAllGlyphs,
  normalizeSVGForFont,
  generateGlyphMetadata,
  FONT_CONFIG,
};
