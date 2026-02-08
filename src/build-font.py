#!/usr/bin/env python3
"""
Cistercian Font Builder

Uses FontForge to create an OpenType font with ligatures for Cistercian numerals.
Requires: FontForge with Python bindings (fontforge module)

Installation:
  Ubuntu/Debian: sudo apt-get install fontforge python3-fontforge
  macOS: brew install fontforge
  Or use FontForge AppImage with built-in Python
"""

import fontforge
import json
import os
import sys
from pathlib import Path

# Font metadata
FONT_NAME = "Cistercian"
FONT_FAMILY = "Cistercian"
FONT_FULLNAME = "Cistercian Numerals"
FONT_VERSION = "1.0.0"
FONT_COPYRIGHT = "Based on Cistercian numerals (public domain)"
FONT_WEIGHT = "Regular"

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
GLYPHS_DIR = PROJECT_ROOT / "glyphs"
METADATA_DIR = PROJECT_ROOT / "metadata"
FONTS_DIR = PROJECT_ROOT / "fonts"

def load_metadata():
    """Load glyph and ligature metadata"""
    print("Loading metadata...")

    glyphs_meta_path = METADATA_DIR / "glyphs.json"
    ligatures_meta_path = METADATA_DIR / "ligatures.json"

    if not glyphs_meta_path.exists():
        print(f"Error: Glyph metadata not found at {glyphs_meta_path}")
        print("Please run generate-glyphs.js first")
        sys.exit(1)

    with open(glyphs_meta_path, 'r') as f:
        glyphs_data = json.load(f)

    with open(ligatures_meta_path, 'r') as f:
        ligatures_data = json.load(f)

    return glyphs_data, ligatures_data

def create_font(glyphs_data):
    """Create a new font with proper metrics"""
    print(f"Creating font: {FONT_FULLNAME}")

    font = fontforge.font()

    # Set font properties
    font.fontname = FONT_NAME
    font.familyname = FONT_FAMILY
    font.fullname = FONT_FULLNAME
    font.version = FONT_VERSION
    font.copyright = FONT_COPYRIGHT
    font.weight = FONT_WEIGHT

    # Set font metrics from metadata
    config = glyphs_data['fontConfig']
    font.em = config['unitsPerEm']
    font.ascent = config['ascender']
    font.descent = abs(config['descender'])

    print(f"  Em size: {font.em}")
    print(f"  Ascent: {font.ascent}")
    print(f"  Descent: {font.descent}")

    return font

def import_svg_glyph(font, svg_path, glyph_name, glyph_width):
    """Import an SVG file as a glyph"""
    try:
        # Create glyph in font
        glyph = font.createChar(-1, glyph_name)

        # Import SVG
        glyph.importOutlines(str(svg_path))

        # Set glyph width
        glyph.width = glyph_width

        # Center the glyph horizontally
        bbox = glyph.boundingBox()
        if bbox[0] != bbox[2]:  # If glyph has content
            # Calculate centering offset
            glyph_actual_width = bbox[2] - bbox[0]
            offset = (glyph_width - glyph_actual_width) / 2 - bbox[0]

            # Transform to center using psMat
            import psMat
            matrix = psMat.translate(offset, 0)
            glyph.transform(matrix)

        return True

    except Exception as e:
        print(f"  Error importing {svg_path}: {e}")
        return False

def add_glyphs(font, glyphs_data):
    """Add all Cistercian numeral glyphs to the font"""
    print("\nImporting glyphs...")

    glyphs = glyphs_data['glyphs']
    total = len(glyphs)
    imported = 0
    failed = 0

    for i, glyph_meta in enumerate(glyphs):
        number = glyph_meta['number']
        glyph_name = glyph_meta['glyphName']
        glyph_width = glyph_meta['width']

        # Construct SVG path
        svg_filename = f"cistercian_{str(number).zfill(4)}.svg"
        svg_path = GLYPHS_DIR / svg_filename

        if not svg_path.exists():
            print(f"  Warning: SVG not found for {number}")
            failed += 1
            continue

        # Import glyph
        if import_svg_glyph(font, svg_path, glyph_name, glyph_width):
            imported += 1
        else:
            failed += 1

        # Progress reporting
        if (i + 1) % 500 == 0:
            progress = (i + 1) / total * 100
            print(f"  Progress: {i + 1}/{total} ({progress:.1f}%)")

    print(f"\nGlyph import complete:")
    print(f"  Imported: {imported}")
    print(f"  Failed: {failed}")

    return imported > 0

def add_basic_glyphs(font):
    """Add basic ASCII digits (0-9) as fallback"""
    print("\nAdding basic digit glyphs...")

    # Create digit glyphs with proper names
    digit_glyph_names = {
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine"
    }

    for digit in range(10):
        digit_str = str(digit)
        glyph_name = digit_glyph_names[digit_str]
        glyph = font.createChar(ord(digit_str), glyph_name)
        glyph.width = 600

        # Add a simple representation (optional - could be left empty)
        # For now, we'll leave them empty as they'll be replaced by ligatures

    print("  Added digits 0-9 with glyph names")

def create_ligature_feature(font, ligatures_data):
    """Create OpenType ligature feature"""
    print("\nCreating ligature features...")

    # Map digit characters to their OpenType glyph names
    digit_to_glyph = {
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
    }

    mappings = ligatures_data['mappings']

    # Build ligature substitution rules
    # Format: sub digit1 digit2 digit3 digit4 by cistercian_glyph;
    # Rules must be ordered longest-first so 4-digit sequences match
    # before 3-digit, etc.

    liga_rules = []

    # Sort mappings by input length descending (4-digit first, then 3, 2, 1)
    sorted_mappings = sorted(mappings, key=lambda m: len(m['input']), reverse=True)

    for mapping in sorted_mappings:
        digits = mapping['input']
        output_glyph = mapping['output']

        # Convert digit characters to OpenType glyph names
        input_glyphs = " ".join(digit_to_glyph[d] for d in digits)

        # Create substitution rule
        rule = f"  sub {input_glyphs} by {output_glyph};"
        liga_rules.append(rule)

    # Insert 'subtable;' breaks to avoid exceeding the 16-bit offset limit
    # in OpenType lookup subtables. Each subtable can hold ~500 rules safely.
    RULES_PER_SUBTABLE = 500
    rules_with_breaks = []
    for i, rule in enumerate(liga_rules):
        rules_with_breaks.append(rule)
        if (i + 1) % RULES_PER_SUBTABLE == 0 and (i + 1) < len(liga_rules):
            rules_with_breaks.append("  subtable;")

    rules_block = chr(10).join(rules_with_breaks)

    # Create feature code
    feature_code = f"""
languagesystem DFLT dflt;
languagesystem latn dflt;

feature liga {{
{rules_block}
}} liga;

feature dlig {{
{rules_block}
}} dlig;
"""

    # Save feature file
    feature_path = METADATA_DIR / "features.fea"
    with open(feature_path, 'w') as f:
        f.write(feature_code)

    print(f"  Generated {len(liga_rules)} ligature rules")
    print(f"  Saved to: {feature_path}")

    # Apply feature to font
    try:
        font.mergeFeature(str(feature_path))
        print("  Applied ligature features to font")
        return True
    except Exception as e:
        print(f"  Warning: Could not apply features automatically: {e}")
        print("  Feature file saved for manual application")
        return False

def generate_font_files(font):
    """Generate font files in various formats"""
    print("\nGenerating font files...")

    # Ensure output directory exists
    FONTS_DIR.mkdir(exist_ok=True)

    # Step 1: Generate TTF with FontForge (the only format it reliably produces)
    ttf_path = FONTS_DIR / f"{FONT_NAME}.ttf"
    try:
        print("  Generating TTF with FontForge...")
        font.generate(str(ttf_path))
        print(f"    ✓ {ttf_path}")
    except Exception as e:
        print(f"    ✗ Error generating TTF: {e}")
        return

    # Step 2: Convert TTF to WOFF and WOFF2 using fonttools
    # FontForge does not reliably generate WOFF2 (it produces PostScript Type 1
    # instead) and its WOFF output wraps CFF rather than TrueType data.
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print("\n  Error: fonttools is not installed.")
        print("  Install it with: pip install fonttools[woff]")
        print("  (or: pip install fonttools brotli)")
        sys.exit(1)

    tt = TTFont(str(ttf_path))

    # Generate WOFF
    woff_path = FONTS_DIR / f"{FONT_NAME}.woff"
    try:
        print("  Generating WOFF with fonttools...")
        tt.flavor = 'woff'
        tt.save(str(woff_path))
        print(f"    ✓ {woff_path}")
    except Exception as e:
        print(f"    ✗ Error generating WOFF: {e}")

    # Generate WOFF2
    woff2_path = FONTS_DIR / f"{FONT_NAME}.woff2"
    try:
        print("  Generating WOFF2 with fonttools...")
        tt.flavor = 'woff2'
        tt.save(str(woff2_path))
        print(f"    ✓ {woff2_path}")
    except ImportError:
        print("    ✗ Error: brotli package is required for WOFF2 compression.")
        print("      Install it with: pip install brotli")
    except Exception as e:
        print(f"    ✗ Error generating WOFF2: {e}")

    tt.close()

    print("\nFont generation complete!")

def build_font():
    """Main font building process"""
    print("=" * 60)
    print("Cistercian Font Builder")
    print("=" * 60)

    # Check if glyphs exist
    if not GLYPHS_DIR.exists() or not any(GLYPHS_DIR.glob("*.svg")):
        print("\nError: No SVG glyphs found!")
        print("Please run generate-glyphs.js first to generate the glyphs.")
        sys.exit(1)

    # Load metadata
    glyphs_data, ligatures_data = load_metadata()

    # Create font
    font = create_font(glyphs_data)

    # Add basic digit glyphs
    add_basic_glyphs(font)

    # Import Cistercian glyphs
    if not add_glyphs(font, glyphs_data):
        print("\nError: Failed to import glyphs")
        sys.exit(1)

    # Create ligature features
    create_ligature_feature(font, ligatures_data)

    # Generate font files
    generate_font_files(font)

    print("\n" + "=" * 60)
    print("Build complete!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        build_font()
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
