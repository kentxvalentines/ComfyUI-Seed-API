import io
import requests
import torch
import numpy as np
from PIL import Image
from .byteplus_utils import BytePlusConfig, BytePlusImageUtils, LoggingUtils


class SeedResultProcessor:
    """Utility functions for processing Seed image generation results."""

    @staticmethod
    def process_image_result(result):
        """Process Seed image generation result and return tensor."""
        try:
            images = []
            # BytePlus API returns data array with url field
            for img_info in result["data"]:
                img_url = img_info["url"]
                img_response = requests.get(img_url)
                img = Image.open(io.BytesIO(img_response.content))
                img_array = np.array(img).astype(np.float32) / 255.0
                images.append(img_array)

            # Stack the images along a new first dimension
            stacked_images = np.stack(images, axis=0)

            # Convert to PyTorch tensor
            img_tensor = torch.from_numpy(stacked_images)
            return (img_tensor,)
        except Exception as e:
            print(f"Error processing Seed image result: {str(e)}")
            return SeedResultProcessor.create_blank_image()

    @staticmethod
    def create_blank_image():
        """Create a blank black image tensor."""
        blank_img = Image.new("RGB", (512, 512), color="black")
        img_array = np.array(blank_img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array)[None,]
        return (img_tensor,)


class SeedImageApiHandler:
    """Utility functions for Seed image API interactions."""

    @staticmethod
    def resolve_size(width, height):
        """Resolve size parameter from width and height dimensions."""
        return f"{width}x{height}"

    @staticmethod
    def generate_image(model, arguments):
        """Generate image using Seed API."""
        config = BytePlusConfig()
        
        headers = {
            "Authorization": f"Bearer {config.get_api_key()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            **arguments
        }
        
        print(f"Making Seed image request to: {config.get_base_url()}/images/generations")
        print(f"Model: {model}")
        print(f"Requested batch size (n): {payload.get('n', 1)}")
        LoggingUtils.safe_log_payload(payload, "Payload")
        
        try:
            response = requests.post(
                f"{config.get_base_url()}/images/generations",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                LoggingUtils.safe_log_payload(result, "Seed image generation successful")
                return result
            else:
                print(f"Seed image generation error: {response.status_code} - {response.text}")
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error in Seed image generation: {str(e)}")
            raise e

    @staticmethod
    def handle_image_generation_error(model_name, error):
        """Handle image generation errors consistently."""
        print(f"Error generating image with {model_name}: {str(error)}")
        return SeedResultProcessor.create_blank_image()


class SeedreamTextToImageNode:
    """Seedream 3 Text-to-Image Generation Node"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "size": (["1024x1024", "1152x896", "896x1152", "1216x832", "832x1216", 
                         "1344x768", "768x1344", "1536x640", "640x1536"], {"default": "1024x1024"}),
            },
            "optional": {
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image"
    CATEGORY = "Seed/ImageGeneration"

    def generate_image(self, prompt, size, seed=-1):
        try:
            arguments = {
                "prompt": prompt,
                "n": 1,
                "size": size,
                "response_format": "url",
                "watermark": False,  # Always false, not exposed in UI
            }
            
            # Only add seed if it's not -1 (random)
            if seed != -1:
                arguments["seed"] = seed
            
            result = SeedImageApiHandler.generate_image(
                "seedream-3-0-t2i-250415", 
                arguments
            )
            
            return SeedResultProcessor.process_image_result(result)
            
        except Exception as e:
            return SeedImageApiHandler.handle_image_generation_error(
                "Seedream Text-to-Image", str(e)
            )


class SeedEditImageToImageNode:
    """SeedEdit 3 Image-to-Image Generation Node"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "image": ("IMAGE",),
                "size": (["adaptive", "1024x1024", "1152x896", "896x1152", "1216x832", "832x1216", 
                         "1344x768", "768x1344", "1536x640", "640x1536"], {"default": "adaptive"}),
            },
            "optional": {
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "guidance_scale": ("FLOAT", {"default": 5.5, "min": 1.0, "max": 20.0, "step": 0.1}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image"
    CATEGORY = "Seed/ImageGeneration"

    def generate_image(self, prompt, image, size, seed=-1, guidance_scale=5.5):
        try:
            # Convert image to base64
            image_base64 = BytePlusImageUtils.image_to_base64(image)
            if not image_base64:
                return SeedImageApiHandler.handle_image_generation_error(
                    "SeedEdit Image-to-Image", "Failed to convert image to base64"
                )
            
            arguments = {
                "prompt": prompt,
                "image": image_base64,
                "n": 1,
                "size": size,
                "guidance_scale": guidance_scale,
                "response_format": "url",
                "watermark": False,  # Always false, not exposed in UI
            }
            
            # Only add seed if it's not -1 (random)
            if seed != -1:
                arguments["seed"] = seed
            
            result = SeedImageApiHandler.generate_image(
                "seededit-3-0-i2i-250628", 
                arguments
            )
            
            return SeedResultProcessor.process_image_result(result)
            
        except Exception as e:
            return SeedImageApiHandler.handle_image_generation_error(
                "SeedEdit Image-to-Image", str(e)
            )


class Seedream4TextToImageNode:
    """Seedream 4 Text-to-Image Generation Node"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "width": ("INT", {"default": 2048, "min": 64, "max": 4096, "step": 1}),
                "height": ("INT", {"default": 2048, "min": 64, "max": 4096, "step": 1}),
            },
            "optional": {
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image"
    CATEGORY = "Seed/ImageGeneration"

    def generate_image(self, prompt, width, height, seed=-1):
        try:
            size = SeedImageApiHandler.resolve_size(width, height)
            arguments = {
                "prompt": prompt,
                "size": size,
                "response_format": "url",
                "watermark": False,
            }
            
            # Only add seed if it's not -1 (random)
            if seed != -1:
                arguments["seed"] = seed
            
            result = SeedImageApiHandler.generate_image(
                "seedream-4-0-250828", 
                arguments
            )
            
            return SeedResultProcessor.process_image_result(result)
            
        except Exception as e:
            return SeedImageApiHandler.handle_image_generation_error(
                "Seedream 4 Text-to-Image", str(e)
            )


class Seedream4ImageToImageNode:
    """Seedream 4 Image-to-Image Generation Node"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "image": ("IMAGE",),
                "width": ("INT", {"default": 2048, "min": 64, "max": 4096, "step": 1}),
                "height": ("INT", {"default": 2048, "min": 64, "max": 4096, "step": 1}),
            },
            "optional": {
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image"
    CATEGORY = "Seed/ImageGeneration"

    def generate_image(self, prompt, image, width, height, seed=-1):
        try:
            # Convert image to base64
            image_base64 = BytePlusImageUtils.image_to_base64(image)
            if not image_base64:
                return SeedImageApiHandler.handle_image_generation_error(
                    "Seedream 4 Image-to-Image", "Failed to convert image to base64"
                )
            
            size = SeedImageApiHandler.resolve_size(width, height)
            arguments = {
                "prompt": prompt,
                "image": image_base64,
                "size": size,
                "response_format": "url",
                "watermark": False,
                "sequential_image_generation": "disabled",  # Single image output
            }
            
            # Only add seed if it's not -1 (random)
            if seed != -1:
                arguments["seed"] = seed
            
            result = SeedImageApiHandler.generate_image(
                "seedream-4-0-250828", 
                arguments
            )
            
            return SeedResultProcessor.process_image_result(result)
            
        except Exception as e:
            return SeedImageApiHandler.handle_image_generation_error(
                "Seedream 4 Image-to-Image", str(e)
            )


class Seedream4MultiImageBlendingNode:
    """Seedream 4 Multi-Image Blending Node"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),
                "width": ("INT", {"default": 2048, "min": 64, "max": 4096, "step": 1}),
                "height": ("INT", {"default": 2048, "min": 64, "max": 4096, "step": 1}),
            },
            "optional": {
                "image3": ("IMAGE",),
                "image4": ("IMAGE",),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image"
    CATEGORY = "Seed/ImageGeneration"

    def generate_image(self, prompt, image1, image2, width, height, image3=None, image4=None, seed=-1):
        try:
            # Convert images to base64
            images_base64 = []
            for img in [image1, image2, image3, image4]:
                if img is not None:
                    img_b64 = BytePlusImageUtils.image_to_base64(img)
                    if img_b64:
                        images_base64.append(img_b64)
            
            if len(images_base64) < 2:
                return SeedImageApiHandler.handle_image_generation_error(
                    "Seedream 4 Multi-Image Blending", "At least 2 images are required"
                )
            
            size = SeedImageApiHandler.resolve_size(width, height)
            arguments = {
                "prompt": prompt,
                "image": images_base64,
                "size": size,
                "response_format": "url",
                "watermark": False,
                "sequential_image_generation": "disabled",  # Multi-image blending to single output
            }
            
            # Only add seed if it's not -1 (random)
            if seed != -1:
                arguments["seed"] = seed
            
            result = SeedImageApiHandler.generate_image(
                "seedream-4-0-250828", 
                arguments
            )
            
            return SeedResultProcessor.process_image_result(result)
            
        except Exception as e:
            return SeedImageApiHandler.handle_image_generation_error(
                "Seedream 4 Multi-Image Blending", str(e)
            )


class Seedream4BatchGenerationNode:
    """Seedream 4 Sequential Batch Image Generation Node"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "max_images": ("INT", {"default": 3, "min": 1, "max": 10, "step": 1}),
                "width": ("INT", {"default": 2048, "min": 64, "max": 4096, "step": 1}),
                "height": ("INT", {"default": 2048, "min": 64, "max": 4096, "step": 1}),
            },
            "optional": {
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_images"
    CATEGORY = "Seed/ImageGeneration"

    def generate_images(self, prompt, max_images, width, height, image1=None, image2=None, seed=-1):
        try:
            size = SeedImageApiHandler.resolve_size(width, height)
            arguments = {
                "prompt": prompt,
                "size": size,
                "response_format": "url",
                "watermark": False,
                "sequential_image_generation": "auto",
                "sequential_image_generation_options": {
                    "max_images": max_images
                },
                "stream": False,
            }
            
            # Add images if provided
            images_base64 = []
            for img in [image1, image2]:
                if img is not None:
                    img_b64 = BytePlusImageUtils.image_to_base64(img)
                    if img_b64:
                        images_base64.append(img_b64)
            
            if images_base64:
                arguments["image"] = images_base64
            
            # Only add seed if it's not -1 (random)
            if seed != -1:
                arguments["seed"] = seed
            
            result = SeedImageApiHandler.generate_image(
                "seedream-4-0-250828", 
                arguments
            )
            
            return SeedResultProcessor.process_image_result(result)
            
        except Exception as e:
            return SeedImageApiHandler.handle_image_generation_error(
                "Seedream 4 Batch Generation", str(e)
            )


class ResolutionHelperNode:
    """Resolution Helper - Calculate width/height from resolution presets and aspect ratios"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "resolution": (["1K", "2K", "3K", "4K"], {"default": "2K"}),
                "aspect_ratio": (["1:1 (Square)", "4:3 (Standard)", "3:4 (Portrait)", "16:9 (Widescreen)", 
                                "9:16 (Vertical)", "3:2 (Photo)", "2:3 (Portrait Photo)", "21:9 (Ultrawide)"], 
                               {"default": "1:1 (Square)"}),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "calculate_resolution"
    CATEGORY = "Seed/Utilities"

    def calculate_resolution(self, resolution, aspect_ratio):
        # Base resolutions (approximate pixel counts)
        base_pixels = {
            "1K": 1024 * 1024,      # ~1M pixels
            "2K": 2048 * 2048,      # ~4M pixels  
            "3K": 3072 * 3072,      # ~9M pixels
            "4K": 4096 * 4096,      # ~16M pixels
        }
        
        # Aspect ratio calculations
        aspect_ratios = {
            "1:1 (Square)": (1, 1),
            "4:3 (Standard)": (4, 3),
            "3:4 (Portrait)": (3, 4),
            "16:9 (Widescreen)": (16, 9),
            "9:16 (Vertical)": (9, 16),
            "3:2 (Photo)": (3, 2),
            "2:3 (Portrait Photo)": (2, 3),
            "21:9 (Ultrawide)": (21, 9),
        }
        
        # Get target pixel count and aspect ratio
        target_pixels = base_pixels[resolution]
        width_ratio, height_ratio = aspect_ratios[aspect_ratio]
        
        # API maximum: 16,777,216 pixels (4096²)
        max_pixels = 16777216
        
        # If target exceeds API limit, use the maximum instead
        if target_pixels > max_pixels:
            target_pixels = max_pixels
        
        # Calculate dimensions
        # For aspect ratio w:h, if total pixels = W*H, then:
        # W = width_ratio * k, H = height_ratio * k
        # W * H = width_ratio * height_ratio * k^2 = target_pixels
        # k = sqrt(target_pixels / (width_ratio * height_ratio))
        
        import math
        k = math.sqrt(target_pixels / (width_ratio * height_ratio))
        
        width = int(width_ratio * k)
        height = int(height_ratio * k)
        
        # Ensure dimensions are above minimum and total pixels don't exceed API limit
        width = max(64, width)
        height = max(64, height)
        
        # Final safety check: if calculated pixels exceed limit, scale down proportionally
        if width * height > max_pixels:
            scale_factor = math.sqrt(max_pixels / (width * height))
            width = int(width * scale_factor)
            height = int(height * scale_factor)
        
        # Round to even numbers for better codec compatibility, but respect pixel limit
        # Check if rounding up would exceed the limit
        width_even = width if width % 2 == 0 else width + 1
        height_even = height if height % 2 == 0 else height + 1
        
        if width_even * height_even > max_pixels:
            # Rounding up would exceed limit, so round down instead
            width = width if width % 2 == 0 else width - 1
            height = height if height % 2 == 0 else height - 1
        else:
            # Safe to round up to even numbers
            width = width_even
            height = height_even
        
        return (width, height)


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "SeedreamTextToImage": SeedreamTextToImageNode,
    "SeedEditImageToImage": SeedEditImageToImageNode,
    "Seedream4TextToImage": Seedream4TextToImageNode,
    "Seedream4ImageToImage": Seedream4ImageToImageNode,
    "Seedream4MultiImageBlending": Seedream4MultiImageBlendingNode,
    "Seedream4BatchGeneration": Seedream4BatchGenerationNode,
    "ResolutionHelper": ResolutionHelperNode,
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "SeedreamTextToImage": "Seedream 3 Text-to-Image",
    "SeedEditImageToImage": "SeedEdit 3 Image-to-Image",
    "Seedream4TextToImage": "Seedream 4 Text-to-Image",
    "Seedream4ImageToImage": "Seedream 4 Image-to-Image",
    "Seedream4MultiImageBlending": "Seedream 4 Multi-Image Blending",
    "Seedream4BatchGeneration": "Seedream 4 Batch Generation",
    "ResolutionHelper": "Resolution Helper",
}
