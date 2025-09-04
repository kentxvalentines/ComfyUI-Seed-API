import io
import requests
import torch
import numpy as np
from PIL import Image
from .byteplus_utils import BytePlusConfig, BytePlusImageUtils


class BytePlusResultProcessor:
    """Utility functions for processing BytePlus image generation results."""

    @staticmethod
    def process_image_result(result):
        """Process BytePlus image generation result and return tensor."""
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
            print(f"Error processing BytePlus image result: {str(e)}")
            return BytePlusResultProcessor.create_blank_image()

    @staticmethod
    def create_blank_image():
        """Create a blank black image tensor."""
        blank_img = Image.new("RGB", (512, 512), color="black")
        img_array = np.array(blank_img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array)[None,]
        return (img_tensor,)


class BytePlusImageApiHandler:
    """Utility functions for BytePlus image API interactions."""

    @staticmethod
    def generate_image(model, arguments):
        """Generate image using BytePlus API."""
        config = BytePlusConfig()
        
        headers = {
            "Authorization": f"Bearer {config.get_api_key()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            **arguments
        }
        
        print(f"Making BytePlus image request to: {config.get_base_url()}/images/generations")
        print(f"Model: {model}")
        print(f"Requested batch size (n): {payload.get('n', 1)}")
        print(f"Payload: {payload}")
        
        try:
            response = requests.post(
                f"{config.get_base_url()}/images/generations",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"BytePlus image generation successful: {result}")
                return result
            else:
                print(f"BytePlus image generation error: {response.status_code} - {response.text}")
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error in BytePlus image generation: {str(e)}")
            raise e

    @staticmethod
    def handle_image_generation_error(model_name, error):
        """Handle image generation errors consistently."""
        print(f"Error generating image with {model_name}: {str(error)}")
        return BytePlusResultProcessor.create_blank_image()


class BytePlusSeedreamTextToImageNode:
    """BytePlus Seedream Text-to-Image Generation Node"""
    
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
    CATEGORY = "BytePlus/ImageGeneration"

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
            
            result = BytePlusImageApiHandler.generate_image(
                "seedream-3-0-t2i-250415", 
                arguments
            )
            
            return BytePlusResultProcessor.process_image_result(result)
            
        except Exception as e:
            return BytePlusImageApiHandler.handle_image_generation_error(
                "BytePlus Seedream Text-to-Image", str(e)
            )


class BytePlusSeedEditImageToImageNode:
    """BytePlus SeedEdit Image-to-Image Generation Node"""
    
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
    CATEGORY = "BytePlus/ImageGeneration"

    def generate_image(self, prompt, image, size, seed=-1, guidance_scale=5.5):
        try:
            # Convert image to base64
            image_base64 = BytePlusImageUtils.image_to_base64(image)
            if not image_base64:
                return BytePlusImageApiHandler.handle_image_generation_error(
                    "BytePlus SeedEdit Image-to-Image", "Failed to convert image to base64"
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
            
            result = BytePlusImageApiHandler.generate_image(
                "seededit-3-0-i2i-250628", 
                arguments
            )
            
            return BytePlusResultProcessor.process_image_result(result)
            
        except Exception as e:
            return BytePlusImageApiHandler.handle_image_generation_error(
                "BytePlus SeedEdit Image-to-Image", str(e)
            )


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "BytePlusSeedreamTextToImage": BytePlusSeedreamTextToImageNode,
    "BytePlusSeedEditImageToImage": BytePlusSeedEditImageToImageNode,
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "BytePlusSeedreamTextToImage": "Seedream Text-to-Image",
    "BytePlusSeedEditImageToImage": "SeedEdit Image-to-Image",
}
