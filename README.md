# Tamil LED Text Generator

A comprehensive web application for generating crisp, 1-bit PNG images of Tamil text optimized for LED display panels. Built with Streamlit and powered by HarfBuzz text shaping and FreeType rendering.

![Tamil LED Generator](https://img.shields.io/badge/Tamil-LED%20Generator-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![Python](https://img.shields.io/badge/Python-3.8+-green)

## Features

- **Proper Tamil Text Shaping**: Uses HarfBuzz for correct rendering of vowel signs, ligatures, and complex Tamil characters
- **1-bit Monochrome Output**: Generates crisp, aliasing-free images perfect for LED matrices
- **Multiple Alignment Options**: Left, center, and right text alignment
- **Margin Control**: Adjustable horizontal margins for better layout
- **Font Selection**: Choose between Regular and Bold Noto Sans Tamil fonts
- **Custom Dimensions**: Set exact pixel dimensions for your LED panel
- **Multi-line Support**: Render multiple lines of text with adjustable line spacing
- **LED Panel Presets**: Quick dimension presets for common LED panel sizes
- **Real-time Preview**: See your text rendered with adjustable preview scaling
- **Direct Download**: Download PNG files ready for HD2020 import

## Perfect For

- HD2020 LED control systems
- P10 LED panels
- LED matrix displays
- Digital signage
- Tamil text on LED boards

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/your-username/tamil-led-generator.git
cd tamil-led-generator
```

2. Install system dependencies (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install libharfbuzz-dev libfreetype6-dev
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

### Cloud Deployment

#### Streamlit Community Cloud

1. Fork this repository to your GitHub account
2. Sign up at [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Deploy your forked repository
5. Your app will be live in minutes!

#### Vercel Deployment

This app can also be deployed on Vercel with some configuration:

1. Fork the repository
2. Connect to Vercel
3. Add build configuration for Python/Streamlit
4. Deploy

## Usage

### Basic Usage

1. **Enter Text**: Type Tamil text in the input field
2. **Configure Settings**: Adjust font, size, and dimensions in the sidebar
3. **Preview**: View the generated image with scaling
4. **Download**: Click "Download PNG" to save the image
5. **Import to HD2020**: Use the PNG in an Image region (not Text region)

### HD2020 Integration

1. Open HD2020 and create a new screen with exact dimensions
2. Add an **Image** region (not Text region) with matching pixel dimensions
3. Import the downloaded PNG file
4. Avoid resizing in HD2020 to maintain 1:1 pixel mapping
5. Configure panel settings (scan type, mapping)
6. Send program to LED controller

### Advanced Features

- **Multi-line Text**: Use the "Multiple Lines" input mode for complex layouts
- **Alignment Control**: Choose left, center, or right alignment
- **Margin Adjustment**: Add horizontal margins for better spacing
- **Line Spacing**: Control spacing between multiple lines
- **Preview Scaling**: Adjust preview scale for better visibility

## Technical Details

### Dependencies

- **uharfbuzz**: HarfBuzz Python bindings for text shaping
- **freetype-py**: FreeType Python bindings for font rendering
- **Pillow**: Image processing and manipulation
- **NumPy**: Numerical operations for bitmap handling
- **Streamlit**: Web application framework

### Text Rendering Pipeline

1. **Text Shaping**: HarfBuzz processes Tamil text, handling complex script features
2. **Glyph Positioning**: Calculates exact positions for each glyph
3. **Monochrome Rendering**: FreeType renders glyphs as 1-bit bitmaps
4. **Canvas Composition**: Combines glyphs on a pixel-perfect canvas
5. **PNG Export**: Saves as optimized 1-bit PNG

### Font Support

The application includes Noto Sans Tamil fonts:
- **NotoSansTamilUI-Regular.ttf**: Optimized for UI and LED displays
- **NotoSansTamilUI-Bold.ttf**: Bold variant for better visibility

## Troubleshooting

### Common Issues

**Broken vowel signs or incorrect text rendering:**
- Ensure HarfBuzz dependencies are properly installed
- Check that `uharfbuzz` is available in your Python environment

**Blurry or pixelated output:**
- This app generates true 1-bit images to prevent LED "sparkle"
- Ensure you're using the downloaded PNG without modification

**Text appears scrambled on LED panel:**
- Check LED panel scan rate and mapping settings in HD2020
- Verify panel type configuration matches your hardware

**Text gets cut off:**
- Increase image dimensions
- Reduce font size or margins
- Check text length vs. available space

### System Requirements

- Python 3.8 or higher
- System libraries: libharfbuzz-dev, libfreetype6-dev
- Memory: Minimal (suitable for cloud deployment)
- Storage: ~100MB including dependencies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Areas for Contribution

- Additional Tamil font support
- More LED panel presets
- Export format options
- UI/UX improvements
- Performance optimizations

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- **Google Fonts** for Noto Sans Tamil fonts
- **HarfBuzz** team for text shaping engine
- **FreeType** team for font rendering library
- **Streamlit** team for the web framework

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with detailed information

---

**Made with ❤️ for the Tamil community and LED display enthusiasts**

