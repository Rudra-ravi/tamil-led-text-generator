#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tamil LED Text Generator - Streamlit Web Application

A comprehensive web interface for generating crisp 1-bit PNG images of Tamil text
for LED display panels using HarfBuzz text shaping and FreeType rendering.

Features:
- Proper Tamil text shaping with HarfBuzz
- 1-bit monochrome rendering with FreeType
- Multiple alignment options (left, center, right)
- Margin control
- Font selection (Regular/Bold/Black/ExtraBold/Medium)
- Custom dimensions for LED panels
- Direct PNG download for HD2020 import
- Text and background color selection
"""

import streamlit as st
import io
import os
import math
import numpy as np
from PIL import Image
import tempfile
import base64

# Check for required dependencies
try:
    import freetype
    import uharfbuzz as hb
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

def load_font_bytes(path):
    """Load font file as bytes."""
    with open(path, 'rb') as f:
        return f.read()

def hb_shape(text, font_bytes, script='taml', lang='ta', direction='LTR', upem=None, px_size=16):
    """Shape Tamil text using HarfBuzz for proper glyph positioning."""
    # Create HB objects
    blob = hb.Blob(font_bytes)
    face = hb.Face(blob)
    font = hb.Font(face)

    # Let HB use OpenType funcs for metrics/placement
    hb.ot_font_set_funcs(font)

    # Scale HB font roughly to pixel size: map units/em to pixels
    upem = upem or face.upem
    font.scale = (px_size * 64, px_size * 64)

    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    buf.script = script
    buf.language = lang
    buf.direction = direction

    features = {"kern": True, "liga": True}
    hb.shape(font, buf, features)
    infos = buf.glyph_infos
    positions = buf.glyph_positions
    return infos, positions, face, font

def unpack_mono_bitmap(ft_bitmap):
    """Unpack FreeType monochrome bitmap to numpy array."""
    width, rows, pitch = ft_bitmap.width, ft_bitmap.rows, ft_bitmap.pitch
    buffer = ft_bitmap.buffer
    out = np.zeros((rows, width), dtype=np.uint8)
    for y in range(rows):
        rowstart = y * pitch
        outy = out[y]
        for byte_index in range(pitch):
            b = buffer[rowstart + byte_index]
            for bit in range(min(8, width - byte_index * 8)):
                mask = 1 << (7 - bit)
                outy[byte_index * 8 + bit] = 1 if (b & mask) else 0
    return out

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def render_1bit_png_bytes(text, font_path, width, height, px_size=16, margin=0, align='center', text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    """
    Render Tamil text as 1-bit PNG and return as bytes.
    
    Args:
        text: Tamil text to render
        font_path: Path to Tamil font file
        width: Output image width in pixels
        height: Output image height in pixels
        px_size: Font size in pixels
        margin: Left/right margin in pixels
        align: Horizontal alignment ('left', 'center', 'right')
        text_color: RGB tuple for text color
        bg_color: RGB tuple for background color
    
    Returns:
        bytes: PNG image data
    """
    if not DEPENDENCIES_AVAILABLE:
        raise ImportError("Required dependencies (uharfbuzz, freetype-py) not available")
    
    font_bytes = load_font_bytes(font_path)
    
    # FreeType face for rasterization & metrics
    ft_face = freetype.Face(font_path)
    ft_face.set_char_size(0, px_size * 64, 72, 72)

    infos, positions, hb_face, hb_font = hb_shape(
        text, font_bytes, script='taml', lang='ta', direction='LTR',
        upem=ft_face.units_per_EM, px_size=px_size
    )

    # Compute baseline using FreeType size metrics
    ascender = ft_face.size.ascender / 64.0
    descender = ft_face.size.descender / 64.0

    # Measure shaped run advance
    x_advance_total = 0.0
    for pos in positions:
        x_advance_total += pos.x_advance / 64.0

    # Initial pen position based on alignment
    if align == 'left':
        pen_x = margin
    elif align == 'right':
        pen_x = max(margin, width - margin - x_advance_total)
    else:  # center
        pen_x = (width - x_advance_total) / 2.0
        pen_x = max(margin, pen_x)

    # Vertical position: center glyphs in available height
    baseline = (height + ascender - (-descender)) / 2.0

    # Create 1-bit canvas
    canvas = np.zeros((height, width), dtype=np.uint8)

    for info, pos in zip(infos, positions):
        gid = info.codepoint
        x_advance = pos.x_advance / 64.0
        x_offset = pos.x_offset / 64.0
        y_offset = pos.y_offset / 64.0

        # Load glyph with monochrome target
        ft_face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)
        slot = ft_face.glyph
        bmp = slot.bitmap
        glyph_img = unpack_mono_bitmap(bmp)

        # Position glyph
        gx = int(round(pen_x + x_offset + slot.bitmap_left))
        gy = int(round(baseline - y_offset - slot.bitmap_top))

        # Blit with clipping
        h, w = glyph_img.shape
        if w == 0 or h == 0:
            pen_x += x_advance
            continue

        x0 = max(0, gx)
        y0 = max(0, gy)
        x1 = min(width, gx + w)
        y1 = min(height, gy + h)

        if x0 < x1 and y0 < y1:
            sub = glyph_img[(y0 - gy):(y1 - gy), (x0 - gx):(x1 - gx)]
            canvas[y0:y1, x0:x1] = np.maximum(canvas[y0:y1, x0:x1], sub)

        pen_x += x_advance

    # Convert to PIL image with specified colors
    img = Image.new('RGB', (width, height), color=bg_color)
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            if canvas[y, x] == 1:
                pixels[x, y] = text_color
    
    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return buf.getvalue()

def render_multiline_text(text_lines, font_path, width, height, px_size=16, margin=0, align='center', line_spacing=2, text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    """
    Render multiple lines of Tamil text.
    
    Args:
        text_lines: List of text lines
        font_path: Path to Tamil font file
        width: Output image width in pixels
        height: Output image height in pixels
        px_size: Font size in pixels
        margin: Left/right margin in pixels
        align: Horizontal alignment ('left', 'center', 'right')
        line_spacing: Additional spacing between lines in pixels
        text_color: RGB tuple for text color
        bg_color: RGB tuple for background color
    
    Returns:
        bytes: PNG image data
    """
    if not DEPENDENCIES_AVAILABLE:
        raise ImportError("Required dependencies (uharfbuzz, freetype-py) not available")
    
    font_bytes = load_font_bytes(font_path)
    
    # Initialize FreeType face once for metrics
    ft_face_metrics = freetype.Face(font_path)
    ft_face_metrics.set_char_size(0, px_size * 64, 72, 72)
    ascender = ft_face_metrics.size.ascender / 64.0
    descender = ft_face_metrics.size.descender / 64.0
    line_height_calc = ascender - descender + line_spacing
    
    # Create main canvas
    canvas = np.zeros((height, width), dtype=np.uint8)
    
    # Calculate total text height and starting Y to center all lines vertically
    total_text_content_height = len(text_lines) * line_height_calc - line_spacing
    start_y_overall = (height - total_text_content_height) / 2.0
    
    for i, line in enumerate(text_lines):
        if not line.strip():  # Skip empty lines
            continue
            
        # Shape each line independently
        infos, positions, hb_face_line, hb_font_line = hb_shape(
            line, font_bytes, script='taml', lang='ta', direction='LTR',
            upem=ft_face_metrics.units_per_EM, px_size=px_size
        )

        # FreeType face for rasterization for this line
        ft_face_line_render = freetype.Face(font_path)
        ft_face_line_render.set_char_size(0, px_size * 64, 72, 72)

        # Measure shaped run advance for this line
        x_advance_total_line = 0.0
        for pos in positions:
            x_advance_total_line += pos.x_advance / 64.0

        # Calculate pen position for this line based on alignment
        if align == 'left':
            pen_x = margin
        elif align == 'right':
            pen_x = max(margin, width - margin - x_advance_total_line)
        else:  # center
            pen_x = (width - x_advance_total_line) / 2.0
            pen_x = max(margin, pen_x)

        # Calculate baseline for the current line
        current_line_y_offset = start_y_overall + i * line_height_calc
        baseline = current_line_y_offset + ascender

        # Render glyphs for this line onto the main canvas
        for info, pos in zip(infos, positions):
            gid = info.codepoint
            x_advance = pos.x_advance / 64.0
            x_offset = pos.x_offset / 64.0
            y_offset = pos.y_offset / 64.0

            ft_face_line_render.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)
            slot = ft_face_line_render.glyph
            bmp = slot.bitmap
            glyph_img = unpack_mono_bitmap(bmp)

            gx = int(round(pen_x + x_offset + slot.bitmap_left))
            gy = int(round(baseline - y_offset - slot.bitmap_top))

            h, w = glyph_img.shape
            if w == 0 or h == 0:
                pen_x += x_advance
                continue

            x0 = max(0, gx)
            y0 = max(0, gy)
            x1 = min(width, gx + w)
            y1 = min(height, gy + h)

            if x0 < x1 and y0 < y1:
                sub = glyph_img[(y0 - gy):(y1 - gy), (x0 - gx):(x1 - gx)]
                canvas[y0:y1, x0:x1] = np.maximum(canvas[y0:y1, x0:x1], sub)

            pen_x += x_advance

    # Convert to PIL image with specified colors
    img = Image.new('RGB', (width, height), color=bg_color)
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            if canvas[y, x] == 1:
                pixels[x, y] = text_color
    
    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return buf.getvalue()

# Streamlit App Configuration
st.set_page_config(
    page_title="Tamil LED Text Generator",
    page_icon="🔤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown('<h1 class="main-header">🔤 Tamil LED Text Generator</h1>', unsafe_allow_html=True)

# Check dependencies
if not DEPENDENCIES_AVAILABLE:
    st.error("""
    **Missing Dependencies**: This application requires `uharfbuzz` and `freetype-py` for proper Tamil text shaping.
    
    To install dependencies:
    ```bash
    pip install uharfbuzz freetype-py pillow numpy streamlit
    ```
    
    **Note**: These dependencies may require system libraries. On Ubuntu/Debian:
    ```bash
    sudo apt-get install libharfbuzz-dev libfreetype6-dev
    ```
    """)
    st.stop()

# Description
st.markdown("""
This tool generates crisp, 1-bit PNG images of Tamil text optimized for LED display panels. 
It uses **HarfBuzz** for proper Tamil text shaping and **FreeType** for monochrome rendering, 
ensuring correct display of vowel signs, ligatures, and complex Tamil characters.

**Perfect for**: HD2020 LED control systems, P10 panels, and other LED matrix displays.
""")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Font Selection
    st.subheader("Font Settings")
    
    # Font families with their weight variants
    font_families = {
        "Noto Sans Tamil": {
            "Regular": "fonts/NotoSansTamil-Regular.ttf",
            "Medium": "fonts/NotoSansTamil-Medium.ttf", 
            "Bold": "fonts/NotoSansTamil-Bold.ttf",
            "ExtraBold": "fonts/NotoSansTamil-ExtraBold.ttf",
            "Black": "fonts/NotoSansTamil-Black.ttf"
        },
        "Catamaran": {
            "Regular": "fonts/Catamaran-Regular.ttf",
            "Bold": "fonts/Catamaran-Bold.ttf"
        },
        "Hind Madurai": {
            "Regular": "fonts/HindMadurai-Regular.ttf",
            "Bold": "fonts/HindMadurai-Bold.otf"
        },
        "Mukta Malar": {
            "Regular": "fonts/MuktaMalar-Regular.ttf",
            "Bold": "fonts/MuktaMalar-Bold.ttf",
            "ExtraBold": "fonts/MuktaMalar-ExtraBold.ttf"
        },
        "Tamil Sangam MN": {
            "Regular": "fonts/TamilSangamMN-Regular.ttf",
            "Bold": "fonts/TamilSangamMN-Bold.ttf"
        },
        "Latha": {
            "Regular": "fonts/Latha-Regular.ttf",
            "Bold": "fonts/Latha-Bold.ttf"
        },
        "Brahma": {
            "Regular": "fonts/Brahma-Regular.ttf",
            "Bold": "fonts/Brahma-Bold.ttf"
        }
    }
    
    # Check available font families
    available_families = {}
    for family_name, weights in font_families.items():
        available_weights = {}
        for weight_name, font_path in weights.items():
            if os.path.exists(font_path):
                available_weights[weight_name] = font_path
        if available_weights:
            available_families[family_name] = available_weights
    
    if not available_families:
        st.error("No Tamil font files found. Please ensure font files are in the 'fonts/' directory.")
        st.stop()
    
    # Font family selection
    family_names = list(available_families.keys())
    selected_family = st.selectbox("Font Family", family_names)
    
    # Font weight selection
    available_weights = list(available_families[selected_family].keys())
    selected_weight = st.selectbox("Font Weight", available_weights)
    
    # Get the selected font path
    selected_font_path = available_families[selected_family][selected_weight]
    
    font_size = st.slider("Font Size (pixels)", min_value=8, max_value=64, value=16, step=1)
    
    # Color Options
    st.subheader("Color Options")
    color_schemes = {
        "White": "#FFFFFF",
        "Red": "#FF0000",
        "Green": "#00FF00",
        "Blue": "#0000FF",
        "Yellow": "#FFFF00",
        "Orange": "#FFA500",
        "Purple": "#800080",
        "Cyan": "#00FFFF",
        "Magenta": "#FF00FF",
    }
    
    selected_color_scheme_name = st.selectbox("Text Color Scheme", list(color_schemes.keys()))
    text_color_hex = color_schemes[selected_color_scheme_name]
    st.color_picker("Custom Text Color (overrides scheme)", text_color_hex)

    bg_color_hex = st.color_picker("Background Color", "#000000")
    
    text_color_rgb = hex_to_rgb(text_color_hex)
    bg_color_rgb = hex_to_rgb(bg_color_hex)


    # Image Dimensions
    st.subheader("Image Dimensions")
    col1, col2 = st.columns(2)
    with col1:
        width = st.number_input("Width (px)", min_value=16, max_value=2048, value=128, step=1)
    with col2:
        height = st.number_input("Height (px)", min_value=16, max_value=512, value=32, step=1)
    
    # Layout Settings
    st.subheader("Layout Settings")
    alignment = st.selectbox("Text Alignment", ["center", "left", "right"])
    margin = st.slider("Horizontal Margin (px)", min_value=0, max_value=50, value=2, step=1)
    line_spacing = st.slider("Line Spacing (px)", min_value=0, max_value=20, value=2, step=1)
    
    # Preset Dimensions
    st.subheader("Common LED Panel Presets")
    if st.button("P10 Module (32×16)"):
        st.session_state.width = 32
        st.session_state.height = 16
    if st.button("Small Banner (128×32)"):
        st.session_state.width = 128
        st.session_state.height = 32
    if st.button("Medium Banner (256×64)"):
        st.session_state.width = 256
        st.session_state.height = 64

# Main Content Area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Text Input")
    
    # Text input modes
    input_mode = st.radio("Input Mode", ["Single Line", "Multiple Lines"])
    
    if input_mode == "Single Line":
        text_input = st.text_input(
            "Tamil Text",
            value="வணக்கம்",
            help="Enter Tamil text to render"
        )
        text_lines = [text_input] if text_input else []
    else:
        text_input = st.text_area(
            "Tamil Text (one line per line)",
            value="வணக்கம்\nதமிழ் செய்திகள்",
            height=100,
            help="Enter multiple lines of Tamil text"
        )
        text_lines = [line.strip() for line in text_input.split('\n') if line.strip()]
    
    # Preview settings
    st.subheader("Preview Settings")
    preview_scale = st.slider("Preview Scale", min_value=1, max_value=10, value=4, step=1)

with col2:
    st.header("🖼️ Generated Image")
    
    if text_lines:
        try:
            # Generate image
            if len(text_lines) == 1:
                image_bytes = render_1bit_png_bytes(
                    text_lines[0], selected_font_path, width, height,
                    px_size=font_size, margin=margin, align=alignment,
                    text_color=text_color_rgb, bg_color=bg_color_rgb
                )
            else:
                image_bytes = render_multiline_text(
                    text_lines, selected_font_path, width, height,
                    px_size=font_size, margin=margin, align=alignment,
                    line_spacing=line_spacing, text_color=text_color_rgb, bg_color=bg_color_rgb
                )
            
            # Display image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Scale for preview
            preview_img = img.resize((width * preview_scale, height * preview_scale), Image.NEAREST)
            
            st.image(
                preview_img,
                caption=f"Output: {width}×{height}px, 1-bit Monochrome (Preview scaled {preview_scale}x)",
                use_container_width=True
            )
            
            # Download button
            st.download_button(
                label="📥 Download PNG",
                data=image_bytes,
                file_name=f"tamil_led_{width}x{height}.png",
                mime="image/png",
                use_container_width=True
            )
            
            # Image info
            st.info(f"""
            **Image Details:**
            - Dimensions: {width} × {height} pixels
            - Format: PNG
            - Font: {selected_family} {selected_weight} ({font_size}px)
            - Alignment: {alignment.title()}
            - Text Color: {text_color_hex}
            - Background Color: {bg_color_hex}
            - File size: {len(image_bytes):,} bytes
            """)
            
        except Exception as e:
            st.error(f"Error generating image: {str(e)}")
    else:
        st.info("Enter Tamil text to generate an image.")

# Instructions and Help
st.markdown("""
---
## 💡 How to Use:

1.  **Enter your Tamil text** in the input box. You can choose between single or multiple lines.
2.  **Adjust Font Settings**: Select a font family and size.
3.  **Choose Colors**: Pick your desired text and background colors.
4.  **Set Dimensions**: Specify the width and height of your LED panel in pixels, or use a preset.
5.  **Configure Layout**: Adjust alignment, margin, and line spacing.
6.  **Preview**: See a scaled preview of your generated LED text.
7.  **Download**: Click the "Download PNG" button to save your 1-bit image.

## 🛠️ Technical Details:

*   **HarfBuzz**: Ensures correct rendering of complex Tamil script features like conjuncts and vowel signs.
*   **FreeType**: Used for high-quality monochrome glyph rasterization.
*   **1-bit Output**: Generates images suitable for LED matrix displays, which typically use 1-bit color depth per pixel.

""")

st.markdown("""
---
**Note**: If you encounter rendering issues, ensure your text is valid Tamil and try adjusting font size or line spacing.
""")

