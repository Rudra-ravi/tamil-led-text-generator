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
- Font selection (Regular/Bold)
- Custom dimensions for LED panels
- Direct PNG download for HD2020 import
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

def render_1bit_png_bytes(text, font_path, width, height, px_size=16, margin=0, align='center'):
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
        upem=hb_face.upem, px_size=px_size
    )

    # Compute baseline using FreeType size metrics
    ascender = ft_face.size.ascender / 64.0
    descender = ft_face.size.descender / 64.0
    line_height = ft_face.size.height / 64.0

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

    # Convert to PIL 1-bit image
    img = Image.new('1', (width, height))
    img.putdata((canvas.flatten() * 255).tolist())
    
    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return buf.getvalue()

def render_multiline_text(text_lines, font_path, width, height, px_size=16, margin=0, align='center', line_spacing=2):
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
    
    Returns:
        bytes: PNG image data
    """
    if not DEPENDENCIES_AVAILABLE:
        raise ImportError("Required dependencies (uharfbuzz, freetype-py) not available")
    
    # Calculate line height
    ft_face = freetype.Face(font_path)
    ft_face.set_char_size(0, px_size * 64, 72, 72)
    ascender = ft_face.size.ascender / 64.0
    descender = ft_face.size.descender / 64.0
    line_height = ascender - descender + line_spacing
    
    # Create canvas
    canvas = np.zeros((height, width), dtype=np.uint8)
    
    # Calculate starting Y position to center all lines vertically
    total_text_height = len(text_lines) * line_height - line_spacing
    start_y = (height - total_text_height) / 2.0
    
    for i, line in enumerate(text_lines):
        if not line.strip():  # Skip empty lines
            continue
            
        # Calculate Y position for this line
        line_y = start_y + i * line_height
        
        # Render this line to a temporary canvas
        line_canvas = np.zeros((height, width), dtype=np.uint8)
        
        font_bytes = load_font_bytes(font_path)
        ft_face = freetype.Face(font_path)
        ft_face.set_char_size(0, px_size * 64, 72, 72)

        infos, positions, hb_face, hb_font = hb_shape(
            line, font_bytes, script='taml', lang='ta', direction='LTR',
            upem=hb_face.upem, px_size=px_size
        )

        # Measure line advance
        x_advance_total = 0.0
        for pos in positions:
            x_advance_total += pos.x_advance / 64.0

        # Calculate pen position for this line
        if align == 'left':
            pen_x = margin
        elif align == 'right':
            pen_x = max(margin, width - margin - x_advance_total)
        else:  # center
            pen_x = (width - x_advance_total) / 2.0
            pen_x = max(margin, pen_x)

        baseline = line_y + ascender

        # Render glyphs for this line
        for info, pos in zip(infos, positions):
            gid = info.codepoint
            x_advance = pos.x_advance / 64.0
            x_offset = pos.x_offset / 64.0
            y_offset = pos.y_offset / 64.0

            ft_face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)
            slot = ft_face.glyph
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

    # Convert to PIL image
    img = Image.new('1', (width, height))
    img.putdata((canvas.flatten() * 255).tolist())
    
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
    
    # Check for available fonts
    available_fonts = []
    font_files = {
        "Noto Sans Tamil UI Regular": "NotoSansTamilUI-Regular.ttf",
        "Noto Sans Tamil UI Bold": "NotoSansTamilUI-Bold.ttf"
    }
    
    for name, filename in font_files.items():
        if os.path.exists(filename):
            available_fonts.append((name, filename))
    
    if not available_fonts:
        st.error("No Tamil font files found. Please ensure font files are in the app directory.")
        st.stop()
    
    font_names = [name for name, _ in available_fonts]
    selected_font_name = st.selectbox("Font Family", font_names)
    selected_font_path = next(path for name, path in available_fonts if name == selected_font_name)
    
    font_size = st.slider("Font Size (pixels)", min_value=8, max_value=64, value=16, step=1)
    
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
                    px_size=font_size, margin=margin, align=alignment
                )
            else:
                image_bytes = render_multiline_text(
                    text_lines, selected_font_path, width, height,
                    px_size=font_size, margin=margin, align=alignment,
                    line_spacing=line_spacing
                )
            
            # Display image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Scale for preview
            preview_img = img.resize((width * preview_scale, height * preview_scale), Image.NEAREST)
            
            st.image(
                preview_img,
                caption=f"Output: {width}×{height}px, 1-bit Monochrome (Preview scaled {preview_scale}x)",
                use_column_width=True
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
            - Format: 1-bit Monochrome PNG
            - Font: {selected_font_name} ({font_size}px)
            - Alignment: {alignment.title()}
            - File size: {len(image_bytes):,} bytes
            """)
            
        except Exception as e:
            st.error(f"Error generating image: {str(e)}")
    else:
        st.info("Enter Tamil text to generate an image.")

# Instructions and Help
with st.expander("📖 Instructions & Help"):
    st.markdown("""
    ### How to Use
    
    1. **Enter Text**: Type Tamil text in the input field (single line or multiple lines)
    2. **Configure**: Adjust font, size, dimensions, and alignment in the sidebar
    3. **Preview**: View the generated image with scaling for better visibility
    4. **Download**: Click "Download PNG" to save the 1-bit image
    5. **Import to HD2020**: Use the downloaded PNG in an Image region (not Text region)
    
    ### HD2020 Import Steps
    
    1. Open HD2020 and create a new screen with exact dimensions
    2. Add an **Image** region (not Text region) with the same pixel dimensions
    3. Import the downloaded PNG file
    4. Avoid resizing in HD2020 to maintain 1:1 pixel mapping
    5. Configure your panel settings (scan type, mapping) before testing
    6. Send the program to your LED controller
    
    ### Font Recommendations
    
    - **Noto Sans Tamil UI Regular**: Best for general LED display use
    - **Noto Sans Tamil UI Bold**: Better visibility on larger panels or longer viewing distances
    
    ### Troubleshooting
    
    - **Broken vowel signs**: Ensure HarfBuzz dependencies are properly installed
    - **Blurry edges**: This app generates true 1-bit images to prevent LED "sparkle"
    - **Scrambled display**: Check your LED panel's scan rate and mapping settings in HD2020
    - **Text cut off**: Increase image dimensions or reduce font size/margins
    
    ### Technical Details
    
    This application uses:
    - **HarfBuzz** (via uharfbuzz) for proper Tamil text shaping
    - **FreeType** (via freetype-py) for monochrome glyph rendering
    - **1-bit PNG output** optimized for LED pixel grids
    - **Exact pixel mapping** for crisp display on LED panels
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    Tamil LED Text Generator | Optimized for HD2020 and LED Display Panels
</div>
""", unsafe_allow_html=True)

