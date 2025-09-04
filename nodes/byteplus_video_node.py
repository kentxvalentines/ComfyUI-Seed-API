from .byteplus_utils import BytePlusApiHandler, BytePlusImageUtils, BytePlusPromptBuilder


class BytePlusSeedanceTextToVideoNode:
    """BytePlus Seedance Text-to-Video Generation Node"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "resolution": (["480p", "720p", "1080p"], {"default": "720p"}),
                "ratio": (["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"], {"default": "16:9"}),
                "duration": ("INT", {"default": 5, "min": 3, "max": 12, "step": 1}),
            },
            "optional": {
                "framepersecond": ("INT", {"default": 24, "min": 24, "max": 24, "step": 1}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "camerafixed": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate_video"
    CATEGORY = "BytePlus/VideoGeneration"

    def generate_video(
        self, 
        prompt, 
        resolution, 
        ratio, 
        duration,
        framepersecond=24,
        seed=-1,
        camerafixed=False
    ):
        try:
            # Build prompt with text commands
            full_prompt = BytePlusPromptBuilder.build_prompt_with_commands(
                prompt=prompt,
                resolution=resolution,
                ratio=ratio,
                duration=duration,
                framepersecond=framepersecond,
                watermark=False,
                seed=seed,
                camerafixed=camerafixed
            )
            
            # Prepare content for API
            content = [
                {
                    "type": "text",
                    "text": full_prompt
                }
            ]
            
            # Submit to BytePlus API
            video_url = BytePlusApiHandler.submit_and_get_result(
                model="seedance-1-0-lite-t2v-250428",
                content=content
            )
            
            if video_url and video_url.strip():
                return (video_url,)
            else:
                return BytePlusApiHandler.handle_video_generation_error(
                    "BytePlus Seedance Text-to-Video", "Failed to generate video"
                )
                
        except Exception as e:
            return BytePlusApiHandler.handle_video_generation_error(
                "BytePlus Seedance Text-to-Video", str(e)
            )


class BytePlusSeedanceImageToVideoNode:
    """BytePlus Seedance Image-to-Video Generation Node (First Frame)"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "image": ("IMAGE",),
                "resolution": (["480p", "720p", "1080p"], {"default": "720p"}),
                "ratio": (["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"], {"default": "adaptive"}),
                "duration": ("INT", {"default": 5, "min": 3, "max": 12, "step": 1}),
            },
            "optional": {
                "framepersecond": ("INT", {"default": 24, "min": 24, "max": 24, "step": 1}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "camerafixed": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate_video"
    CATEGORY = "BytePlus/VideoGeneration"

    def generate_video(
        self, 
        prompt, 
        image,
        resolution, 
        ratio, 
        duration,
        framepersecond=24,
        seed=-1,
        camerafixed=False
    ):
        try:
            # Convert image to base64
            image_base64 = BytePlusImageUtils.image_to_base64(image)
            if not image_base64:
                return BytePlusApiHandler.handle_video_generation_error(
                    "BytePlus Seedance Image-to-Video", "Failed to convert image to base64"
                )
            
            # Build prompt with text commands
            full_prompt = BytePlusPromptBuilder.build_prompt_with_commands(
                prompt=prompt,
                resolution=resolution,
                ratio=ratio,
                duration=duration,
                framepersecond=framepersecond,
                watermark=False,
                seed=seed,
                camerafixed=camerafixed
            )
            
            # Prepare content for API
            content = [
                {
                    "type": "text",
                    "text": full_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_base64
                    },
                    "role": "first_frame"
                }
            ]
            
            # Submit to BytePlus API
            video_url = BytePlusApiHandler.submit_and_get_result(
                model="seedance-1-0-lite-i2v-250428",
                content=content
            )
            
            if video_url and video_url.strip():
                return (video_url,)
            else:
                return BytePlusApiHandler.handle_video_generation_error(
                    "BytePlus Seedance Image-to-Video", "Failed to generate video"
                )
                
        except Exception as e:
            return BytePlusApiHandler.handle_video_generation_error(
                "BytePlus Seedance Image-to-Video", str(e)
            )


class BytePlusSeedanceFirstLastFrameNode:
    """BytePlus Seedance First+Last Frame Video Generation Node"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "first_frame": ("IMAGE",),
                "last_frame": ("IMAGE",),
                "resolution": (["480p", "720p"], {"default": "720p"}),
                "ratio": (["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"], {"default": "adaptive"}),
                "duration": ("INT", {"default": 5, "min": 3, "max": 12, "step": 1}),
            },
            "optional": {
                "framepersecond": ("INT", {"default": 24, "min": 24, "max": 24, "step": 1}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate_video"
    CATEGORY = "BytePlus/VideoGeneration"

    def generate_video(
        self, 
        prompt, 
        first_frame,
        last_frame,
        resolution, 
        ratio, 
        duration,
        framepersecond=24,
        seed=-1
    ):
        try:
            # Convert images to base64
            first_frame_base64 = BytePlusImageUtils.image_to_base64(first_frame)
            last_frame_base64 = BytePlusImageUtils.image_to_base64(last_frame)
            
            if not first_frame_base64 or not last_frame_base64:
                return BytePlusApiHandler.handle_video_generation_error(
                    "BytePlus Seedance First+Last Frame", "Failed to convert images to base64"
                )
            
            # Build prompt with text commands (no camerafixed for this mode)
            full_prompt = BytePlusPromptBuilder.build_prompt_with_commands(
                prompt=prompt,
                resolution=resolution,
                ratio=ratio,
                duration=duration,
                framepersecond=framepersecond,
                watermark=False,
                seed=seed
            )
            
            # Prepare content for API
            content = [
                {
                    "type": "text",
                    "text": full_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": first_frame_base64
                    },
                    "role": "first_frame"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": last_frame_base64
                    },
                    "role": "last_frame"
                }
            ]
            
            # Submit to BytePlus API (only supported by seedance-1-0-lite-i2v)
            video_url = BytePlusApiHandler.submit_and_get_result(
                model="seedance-1-0-lite-i2v-250428",
                content=content
            )
            
            if video_url and video_url.strip():
                return (video_url,)
            else:
                return BytePlusApiHandler.handle_video_generation_error(
                    "BytePlus Seedance First+Last Frame", "Failed to generate video"
                )
                
        except Exception as e:
            return BytePlusApiHandler.handle_video_generation_error(
                "BytePlus Seedance First+Last Frame", str(e)
            )


class BytePlusSeedanceReferenceImagesNode:
    """BytePlus Seedance Reference Images Video Generation Node"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "reference_image_1": ("IMAGE",),
                "reference_image_2": ("IMAGE",),
                "resolution": (["480p", "720p"], {"default": "720p"}),
                "ratio": (["16:9", "4:3", "1:1", "3:4", "9:16", "21:9"], {"default": "16:9"}),
                "duration": ("INT", {"default": 5, "min": 3, "max": 12, "step": 1}),
            },
            "optional": {
                "reference_image_3": ("IMAGE",),
                "reference_image_4": ("IMAGE",),
                "framepersecond": ("INT", {"default": 24, "min": 24, "max": 24, "step": 1}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate_video"
    CATEGORY = "BytePlus/VideoGeneration"

    def generate_video(
        self, 
        prompt, 
        reference_image_1,
        reference_image_2,
        resolution, 
        ratio, 
        duration,
        reference_image_3=None,
        reference_image_4=None,
        framepersecond=24,
        seed=-1
    ):
        try:
            # Convert required images to base64
            ref_images = [reference_image_1, reference_image_2]
            if reference_image_3 is not None:
                ref_images.append(reference_image_3)
            if reference_image_4 is not None:
                ref_images.append(reference_image_4)
            
            # Build prompt with text commands (no camerafixed for reference images)
            full_prompt = BytePlusPromptBuilder.build_prompt_with_commands(
                prompt=prompt,
                resolution=resolution,
                ratio=ratio,
                duration=duration,
                framepersecond=framepersecond,
                watermark=False,
                seed=seed
            )
            
            # Prepare content for API
            content = [
                {
                    "type": "text",
                    "text": full_prompt
                }
            ]
            
            # Add reference images
            for i, ref_image in enumerate(ref_images):
                image_base64 = BytePlusImageUtils.image_to_base64(ref_image)
                if not image_base64:
                    return BytePlusApiHandler.handle_video_generation_error(
                        "BytePlus Seedance Reference Images", f"Failed to convert reference image {i+1} to base64"
                    )
                
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_base64
                    },
                    "role": "reference_image"
                })
            
            # Submit to BytePlus API (only supported by seedance-1-0-lite-i2v)
            video_url = BytePlusApiHandler.submit_and_get_result(
                model="seedance-1-0-lite-i2v-250428",
                content=content
            )
            
            if video_url and video_url.strip():
                return (video_url,)
            else:
                return BytePlusApiHandler.handle_video_generation_error(
                    "BytePlus Seedance Reference Images", "Failed to generate video"
                )
                
        except Exception as e:
            return BytePlusApiHandler.handle_video_generation_error(
                "BytePlus Seedance Reference Images", str(e)
            )


class BytePlusSeedanceProNode:
    """BytePlus Seedance Pro Video Generation Node"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "mode": (["text-to-video", "image-to-video"], {"default": "text-to-video"}),
                "resolution": (["480p", "720p", "1080p"], {"default": "1080p"}),
                "ratio": (["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"], {"default": "adaptive"}),
                "duration": ("INT", {"default": 5, "min": 3, "max": 12, "step": 1}),
            },
            "optional": {
                "image": ("IMAGE",),
                "framepersecond": ("INT", {"default": 24, "min": 24, "max": 24, "step": 1}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "camerafixed": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate_video"
    CATEGORY = "BytePlus/VideoGeneration"

    def generate_video(
        self, 
        prompt, 
        mode,
        resolution, 
        ratio, 
        duration,
        image=None,
        framepersecond=24,
        seed=-1,
        camerafixed=False
    ):
        try:
            # Build prompt with text commands
            full_prompt = BytePlusPromptBuilder.build_prompt_with_commands(
                prompt=prompt,
                resolution=resolution,
                ratio=ratio,
                duration=duration,
                framepersecond=framepersecond,
                watermark=False,
                seed=seed,
                camerafixed=camerafixed
            )
            
            # Prepare content for API
            content = [
                {
                    "type": "text",
                    "text": full_prompt
                }
            ]
            
            # Add image if in image-to-video mode
            if mode == "image-to-video":
                if image is None:
                    return BytePlusApiHandler.handle_video_generation_error(
                        "BytePlus Seedance Pro", "Image is required for image-to-video mode"
                    )
                
                image_base64 = BytePlusImageUtils.image_to_base64(image)
                if not image_base64:
                    return BytePlusApiHandler.handle_video_generation_error(
                        "BytePlus Seedance Pro", "Failed to convert image to base64"
                    )
                
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_base64
                    },
                    "role": "first_frame"
                })
            
            # Submit to BytePlus API
            video_url = BytePlusApiHandler.submit_and_get_result(
                model="seedance-1-0-pro-250528",
                content=content
            )
            
            if video_url and video_url.strip():
                return (video_url,)
            else:
                return BytePlusApiHandler.handle_video_generation_error(
                    "BytePlus Seedance Pro", "Failed to generate video"
                )
                
        except Exception as e:
            return BytePlusApiHandler.handle_video_generation_error(
                "BytePlus Seedance Pro", str(e)
            )


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "SeedanceLiteTextToVideo": BytePlusSeedanceTextToVideoNode,
    "SeedanceLiteImageToVideo": BytePlusSeedanceImageToVideoNode,
    "SeedanceLiteFirstLastFrame": BytePlusSeedanceFirstLastFrameNode,
    "SeedanceLiteReferenceImages": BytePlusSeedanceReferenceImagesNode,
    "SeedanceProTextImageToVideo": BytePlusSeedanceProNode,
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "SeedanceLiteTextToVideo": "Seedance Lite Text-to-Video",
    "SeedanceLiteImageToVideo": "Seedance Lite Image-to-Video",
    "SeedanceLiteFirstLastFrame": "Seedance Lite First+Last Frame",
    "SeedanceLiteReferenceImages": "Seedance Lite Reference Images",
    "SeedanceProTextImageToVideo": "Seedance Pro Text/Image-to-Video",
}
