A professional Windows application for batch processing images with customizable borders and aspect ratios. Perfect for social media content creators, photographers, and anyone needing consistent image formatting.

## Features

- Modern and intuitive graphical user interface
- Batch processing capabilities:
  - Add single or multiple images
  - Add entire folders of images
  - Thumbnail view for easy image management
- Comprehensive format support:
  - Input: PNG, JPG, JPEG, TIFF, BMP, HEIF
  - Output: JPEG (80%, 95%, 100% quality), PNG, TIFF, HEIF
- Aspect ratio presets:
  - Original
  - 1:1 (Square)
  - 4:5 (Instagram Portrait)
  - 5:4 (Instagram Landscape)
  - 9:16 (Story)
  - 2:1 (Banner)
- Border customization:
  - Adjustable border size (0-300 pixels)
  - Custom color picker
  - Live preview of changes
- Advanced options:
  - Optional metadata preservation
  - Custom output filename prefix
  - Quality settings for JPEG and HEIF formats
- Real-time preview with navigation between images

## Requirements

- Windows operating system
- Python 3.8 or higher
- Required Python packages (installed via requirements.txt):
  - PyQt5 >= 5.15.0
  - Pillow >= 9.0.0
  - piexif >= 1.1.3
  - pillow-heif >= 0.10.0

## Installation

1. Clone or download this repository
2. Ensure Python 3.8+ is installed on your system
3. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Launch the application:
```bash
python main.py
```

2. Adding Images:
   - Click "Add Images" to select multiple image files
   - Click "Add Folder" to import an entire folder of images
   - Use "Thumbnail View" to preview all imported images

3. Customize Settings:
   - Select desired aspect ratio from the dropdown
   - Adjust border size using the slider (0-300px)
   - Choose border color with the color picker
   - Select output format and quality
   - Toggle metadata preservation
   - Optional: Add custom filename prefix

4. Preview and Process:
   - Use Previous/Next buttons to navigate through images
   - Live preview shows how the final image will look
   - Click "Process Images" when satisfied with the settings
   - Select output directory when prompted

## Output

- Processed images are saved in your chosen output directory
- Naming convention: [prefix]_original_filename
- Original images remain unchanged
- Output format and quality as selected in settings

## Notes

- Images are automatically scaled to fit the selected aspect ratio while maintaining maximum quality
- GPS and location metadata can be optionally preserved
- Progress bar shows real-time processing status for batch operations
- Memory-efficient processing allows for large batches of images