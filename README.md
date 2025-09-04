# ComfyUI BytePlus API Integration

This ComfyUI custom node provides comprehensive integration with BytePlus (ByteDance) AI APIs, including both video generation (Seedance) and image generation (Seedream/SeedEdit) models.

## Features

### Video Generation (Seedance)
- **Text-to-Video Generation**: Create videos from text descriptions
- **Image-to-Video Generation**: Generate videos using input images as first frames
- **First+Last Frame Generation**: Create videos between two specific frames
- **Reference Images Generation**: Generate videos based on multiple reference images
- **High-Quality Pro Models**: Access to BytePlus's premium Seedance Pro model

### Image Generation
- **Text-to-Image Generation**: Create high-quality images from text prompts using Seedream 3.0
- **Image-to-Image Editing**: Edit and transform existing images with text descriptions using SeedEdit 3.0
- **Frame Extraction**: Convert video URLs to individual frames for further processing

## Installation

1. Clone this repository into your ComfyUI custom_nodes directory:
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/FloyoAI/ComfyUI-BytePlus-API.git
```

2. Install requirements:
```bash
cd ComfyUI-BytePlus-API
pip install -r requirements.txt
```

3. Configure your BytePlus API key:
   - Get your API key from: https://www.byteplus.com/
   - Edit `config.ini` and replace `<your_byteplus_api_key_here>` with your actual API key
   - Or set the environment variable: `export BYTEPLUS_API_KEY="your_key_here"`

4. Restart ComfyUI

## Available Nodes

### Video Generation Nodes (BytePlus/VideoGeneration)

- **Seedance Lite Text-to-Video**: Generate videos from text prompts only
  - Input: Text prompt, resolution, ratio, duration, FPS, seed, camera settings
  - Output: Video URL (STRING)
  - Use case: Create videos from scratch using descriptive text

- **Seedance Lite Image-to-Video**: Generate videos from a starting image
  - Input: Text prompt, input image, resolution, ratio, duration, FPS, seed, camera settings
  - Output: Video URL (STRING)
  - Use case: Animate static images or create videos with specific starting frames

- **Seedance Lite First+Last Frame**: Generate videos between two keyframes
  - Input: Text prompt, first frame image, last frame image, resolution, ratio, duration
  - Output: Video URL (STRING)
  - Use case: Create smooth transitions between two specific images

- **Seedance Lite Reference Images**: Generate videos using multiple reference images
  - Input: Text prompt, 2-4 reference images, resolution, ratio, duration
  - Output: Video URL (STRING)
  - Use case: Generate videos that maintain style/appearance consistency with reference materials

- **Seedance Pro Text/Image-to-Video**: High-quality video generation
  - Input: Text prompt, mode selection, optional input image, resolution, ratio, duration
  - Output: Video URL (STRING)
  - Use case: Premium quality video generation for professional use

### Image Generation Nodes (BytePlus/ImageGeneration)

- **Seedream Text-to-Image**: Generate images from text descriptions
  - Input: Text prompt, size selection, optional seed
  - Output: Generated image (IMAGE)
  - Use case: Create high-quality images from detailed text descriptions

- **SeedEdit Image-to-Image**: Edit and transform existing images
  - Input: Text prompt, input image, size selection, guidance scale, optional seed
  - Output: Edited image (IMAGE)
  - Use case: Modify existing images based on text instructions (change colors, add/remove objects, style transfer)

### Utility Nodes (BytePlus/Video)

- **Video URL to Frames**: Extract all frames from a video URL
  - Input: Video URL (STRING)
  - Output: Frame batch (IMAGE), frame count (INT), FPS (FLOAT)
  - Use case: Convert generated videos into individual frames for further image processing

## Usage Guide

### Video Generation Workflow
1. **Choose the appropriate video node** based on your input type:
   - Text only → Seedance Lite Text-to-Video
   - Single image → Seedance Lite Image-to-Video
   - Two images → Seedance Lite First+Last Frame
   - Multiple references → Seedance Lite Reference Images
   - High quality → Seedance Pro

2. **Configure parameters**:
   - **Prompt**: Describe what you want in the video
   - **Resolution**: 480p, 720p, or 1080p
   - **Ratio**: Aspect ratio (16:9, 1:1, 9:16, etc.)
   - **Duration**: 3-12 seconds

3. **Connect the output** to other nodes:
   - Use output URL directly with video preview nodes
   - Connect to "Video URL to Frames" to extract individual frames
   - Save video using external video saving nodes

### Image Generation Workflow
1. **For new images**: Use Seedream Text-to-Image
   - Write detailed prompts for best results
   - Experiment with different sizes for various use cases
   - Use seed values for reproducible results

2. **For image editing**: Use SeedEdit Image-to-Image
   - Load your source image
   - Describe the changes you want in the prompt
   - Adjust guidance scale (higher = more prompt adherence)
   - Size can be "adaptive" to maintain original dimensions

3. **Process results**:
   - Images output as standard ComfyUI IMAGE tensors
   - Compatible with all ComfyUI image processing nodes
   - Can be saved, edited, or used as input for video generation

## Requirements

- ComfyUI
- Python 3.8+
- BytePlus API key
- Required packages (see requirements.txt)

## Key Features

- **No External Dependencies**: Base64 image conversion means no external hosting required
- **Automatic Task Polling**: Video generation waits until completion automatically
- **Comprehensive Error Handling**: Graceful degradation with detailed error messages
- **ComfyUI Integration**: 
  - Video outputs as URL strings compatible with video preview nodes
  - Image outputs as standard IMAGE tensors compatible with all image nodes
- **Flexible Sizing**: Support for various aspect ratios and resolutions
- **Seed Control**: Reproducible results with optional seed parameters

## Tips for Best Results

### Video Generation
- **Be specific in prompts**: Include details about movement, camera angles, and style
- **Use appropriate ratios**: Match your intended use case (16:9 for landscape, 9:16 for mobile, etc.)
- **Leverage reference images**: For consistent character/style appearance across videos

### Image Generation
- **Detailed prompts work better**: Include style, lighting, composition details
- **Use SeedEdit for modifications**: Better than text-to-image for specific edits
- **Guidance scale tuning**: Start with default 5.5, increase for more prompt adherence
- **Size selection**: Use "adaptive" for SeedEdit to maintain original proportions

## Troubleshooting

- **API Key Issues**: Ensure your BytePlus API key is correctly set in config.ini or environment variables
- **Empty Results**: Check ComfyUI console for detailed error messages
- **Image Quality**: Try different prompts, seeds, or guidance scale values for better results
