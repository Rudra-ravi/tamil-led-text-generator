# Font Additions Documentation

## New Tamil Fonts Added

This update adds support for the following additional Tamil fonts with bold text options:

### New Font Families
1. **Tamil Sangam MN** (Regular, Bold)
2. **Latha** (Regular, Bold)  
3. **Brahma** (Regular, Bold)

## Enhanced Font System

### Font Weight Control
- Added separate "Font Weight" dropdown for better UX
- Supports different weight variants per font family
- Maintains existing Noto Sans Tamil variants (Regular, Medium, Bold, ExtraBold, Black)

### Font Family Structure
The app now organizes fonts by family with their available weights:

```
Font Families:
├── Noto Sans Tamil (Regular, Medium, Bold, ExtraBold, Black)
├── Catamaran (Regular, Bold)
├── Hind Madurai (Regular, Bold)
├── Mukta Malar (Regular, Bold, ExtraBold)
├── Tamil Sangam MN (Regular, Bold)
├── Latha (Regular, Bold)
└── Brahma (Regular, Bold)
```

## Implementation Notes

### Placeholder Fonts
**Important**: The Tamil Sangam MN, Latha, and Brahma font files included are placeholders based on existing Noto Sans Tamil fonts. In a production environment, these should be replaced with the actual licensed font files:

- `TamilSangamMN-Regular.ttf` → Replace with actual Tamil Sangam MN Regular
- `TamilSangamMN-Bold.ttf` → Replace with actual Tamil Sangam MN Bold  
- `Latha-Regular.ttf` → Replace with actual Latha Regular
- `Latha-Bold.ttf` → Replace with actual Latha Bold
- `Brahma-Regular.ttf` → Replace with actual Brahma Regular
- `Brahma-Bold.ttf` → Replace with actual Brahma Bold

### Code Changes
- Modified font selection system in `app.py` to use font families with weight variants
- Updated image info display to show family and weight separately
- Maintained backward compatibility with existing font infrastructure

## Usage

1. Select desired font family from "Font Family" dropdown
2. Choose weight variant from "Font Weight" dropdown  
3. Font combination will be applied to text rendering
4. Image details will show full font name (e.g., "Tamil Sangam MN Bold")

## License Considerations

Users must ensure they have proper licenses for any commercial Tamil fonts they use. The placeholder fonts are based on Noto Sans Tamil which is available under the SIL Open Font License.