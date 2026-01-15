from .byteplus_utils import BytePlusApiHandler, BytePlusImageUtils, BytePlusPromptBuilder, BytePlusConfig


class SeedanceTextToVideoNode:
    """Seedance Text-to-Video Generation Node"""
    
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
    CATEGORY = "Seed/VideoGeneration"

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
                    "Seedance Text-to-Video", "Failed to generate video"
                )
                
        except Exception as e:
            return BytePlusApiHandler.handle_video_generation_error(
                "Seedance Text-to-Video", str(e)
            )


class SeedanceImageToVideoNode:
    """Seedance Image-to-Video Generation Node (First Frame)"""
    
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
    CATEGORY = "Seed/VideoGeneration"

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
                    "Seedance Image-to-Video", "Failed to convert image to base64"
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
                    "Seedance Image-to-Video", "Failed to generate video"
                )
                
        except Exception as e:
            return BytePlusApiHandler.handle_video_generation_error(
                "Seedance Image-to-Video", str(e)
            )


class SeedanceFirstLastFrameNode:
    """Seedance First+Last Frame Video Generation Node"""
    
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
    CATEGORY = "Seed/VideoGeneration"

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
                    "Seedance First+Last Frame", "Failed to convert images to base64"
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
                    "Seedance First+Last Frame", "Failed to generate video"
                )
                
        except Exception as e:
            return BytePlusApiHandler.handle_video_generation_error(
                "Seedance First+Last Frame", str(e)
            )


class SeedanceReferenceImagesNode:
    """Seedance Reference Images Video Generation Node"""
    
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
    CATEGORY = "Seed/VideoGeneration"

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
                        "Seedance Reference Images", f"Failed to convert reference image {i+1} to base64"
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
                    "Seedance Reference Images", "Failed to generate video"
                )
                
        except Exception as e:
            return BytePlusApiHandler.handle_video_generation_error(
                "Seedance Reference Images", str(e)
            )


class SeedancePro15VideoNode:
    """Seedance Pro 1.5 Video Generation Node - Text-to-Video and Image-to-Video with optional audio and draft mode"""

    # Class variable to store the last draft task ID for auto-populate
    _last_draft_task_id = ""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "resolution": (["480p", "720p", "1080p"], {"default": "720p"}),
                "aspect_ratio": (["adaptive", "16:9", "4:3", "1:1", "3:4", "9:16", "21:9"], {"default": "adaptive"}),
                "duration": ("INT", {"default": 5, "min": 4, "max": 12, "step": 1}),
            },
            "optional": {
                "first_frame": ("IMAGE",),
                "last_frame": ("IMAGE",),
                "generate_audio": ("BOOLEAN", {"default": False}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "draft_mode": ("BOOLEAN", {"default": False}),
                "draft_task_id": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("video_url", "draft_task_id",)
    FUNCTION = "generate_video"
    CATEGORY = "Seed/VideoGeneration"
    OUTPUT_NODE = True  # Enable ui output for frontend communication

    def generate_video(
        self,
        prompt,
        resolution,
        aspect_ratio,
        duration,
        first_frame=None,
        last_frame=None,
        generate_audio=False,
        seed=-1,
        draft_mode=False,
        draft_task_id="",
    ):
        try:
            # Mode 1: Render from draft (draft_mode=False AND draft_task_id provided)
            if not draft_mode and draft_task_id and draft_task_id.strip():
                print(f"Rendering from draft task ID: {draft_task_id}")
                return self._render_from_draft(draft_task_id.strip(), resolution)

            # Mode 2: Draft mode (draft_mode=True) - generate draft preview
            if draft_mode:
                print("Generating draft preview (480p forced)")
                return self._generate_draft(
                    prompt, aspect_ratio, duration, first_frame, last_frame,
                    generate_audio, seed
                )

            # Mode 3: Standard generation (draft_mode=False AND no draft_task_id)
            print("Standard video generation")
            return self._generate_standard(
                prompt, resolution, aspect_ratio, duration, first_frame,
                last_frame, generate_audio, seed
            )

        except Exception as e:
            return (*BytePlusApiHandler.handle_video_generation_error(
                "Seedance Pro 1.5", str(e)
            ), "")

    def _generate_draft(self, prompt, aspect_ratio, duration, first_frame, last_frame, generate_audio, seed):
        """Generate a draft preview video (480p, faster, cheaper)."""
        # Validate: last_frame not supported in draft mode
        if last_frame is not None:
            print("Warning: last_frame is not supported in draft mode, ignoring")

        # Build content array
        content = [{"type": "text", "text": prompt}]

        # Add first frame if provided
        if first_frame is not None:
            first_frame_base64 = BytePlusImageUtils.image_to_base64(first_frame)
            if not first_frame_base64:
                return (*BytePlusApiHandler.handle_video_generation_error(
                    "Seedance Pro 1.5 Draft", "Failed to convert first frame to base64"
                ), "")
            content.append({
                "type": "image_url",
                "image_url": {"url": first_frame_base64},
                "role": "first_frame"
            })

        # Determine ratio - remove if first_frame provided
        ratio = None if first_frame is not None else aspect_ratio

        # Generate draft (480p forced)
        video_url, task_id = BytePlusApiHandler.submit_and_get_result_with_task_id(
            model="seedance-1-5-pro-251215",
            content=content,
            resolution="480p",  # Draft only supports 480p
            ratio=ratio,
            duration=duration,
            generate_audio=generate_audio,
            seed=seed,
            draft=True
        )

        if video_url and video_url.strip() and task_id:
            # Store task_id for potential auto-use
            SeedancePro15VideoNode._last_draft_task_id = task_id
            print(f"Draft generated successfully. Task ID: {task_id}")
            # Return with ui data for frontend to auto-populate draft_task_id
            return {"result": (video_url, task_id), "ui": {"draft_task_id": [task_id]}}
        else:
            return {"result": (*BytePlusApiHandler.handle_video_generation_error(
                "Seedance Pro 1.5 Draft", "Failed to generate draft video"
            ), ""), "ui": {"draft_task_id": [""]}}

    def _render_from_draft(self, draft_task_id, resolution):
        """Render full-resolution video from a draft task ID."""
        # Build content with draft_task reference
        content = [{
            "type": "draft_task",
            "draft_task": {"id": draft_task_id}
        }]

        # Generate from draft - API reuses all settings from draft automatically
        video_url, task_id = BytePlusApiHandler.submit_and_get_result_with_task_id(
            model="seedance-1-5-pro-251215",
            content=content,
            resolution=resolution,
            # All other params (prompt, images, seed, ratio, duration, audio) come from draft
        )

        if video_url and video_url.strip():
            # Clear the stored draft task ID after successful render
            SeedancePro15VideoNode._last_draft_task_id = ""
            print(f"Rendered from draft successfully at {resolution}")
            return {"result": (video_url, draft_task_id), "ui": {"draft_task_id": [draft_task_id]}}
        else:
            return {"result": (*BytePlusApiHandler.handle_video_generation_error(
                "Seedance Pro 1.5", f"Failed to render from draft {draft_task_id}"
            ), draft_task_id), "ui": {"draft_task_id": [draft_task_id]}}

    def _generate_standard(self, prompt, resolution, aspect_ratio, duration, first_frame, last_frame, generate_audio, seed):
        """Standard full-resolution video generation."""
        # Validate: last_frame requires first_frame
        if last_frame is not None and first_frame is None:
            return {"result": (*BytePlusApiHandler.handle_video_generation_error(
                "Seedance Pro 1.5", "Last frame provided without first frame"
            ), ""), "ui": {"draft_task_id": [""]}}

        # Build content array
        content = [{"type": "text", "text": prompt}]

        # Add first frame if provided
        if first_frame is not None:
            first_frame_base64 = BytePlusImageUtils.image_to_base64(first_frame)
            if not first_frame_base64:
                return {"result": (*BytePlusApiHandler.handle_video_generation_error(
                    "Seedance Pro 1.5", "Failed to convert first frame to base64"
                ), ""), "ui": {"draft_task_id": [""]}}
            content.append({
                "type": "image_url",
                "image_url": {"url": first_frame_base64},
                "role": "first_frame"
            })

        # Add last frame if provided
        if last_frame is not None:
            last_frame_base64 = BytePlusImageUtils.image_to_base64(last_frame)
            if not last_frame_base64:
                return {"result": (*BytePlusApiHandler.handle_video_generation_error(
                    "Seedance Pro 1.5", "Failed to convert last frame to base64"
                ), ""), "ui": {"draft_task_id": [""]}}
            content.append({
                "type": "image_url",
                "image_url": {"url": last_frame_base64},
                "role": "last_frame"
            })

        # Determine ratio - remove if first_frame provided
        ratio = None if first_frame is not None else aspect_ratio

        # Submit to BytePlus API
        video_url, task_id = BytePlusApiHandler.submit_and_get_result_with_task_id(
            model="seedance-1-5-pro-251215",
            content=content,
            resolution=resolution,
            ratio=ratio,
            duration=duration,
            generate_audio=generate_audio,
            seed=seed
        )

        if video_url and video_url.strip():
            return {"result": (video_url, task_id or ""), "ui": {"draft_task_id": [task_id or ""]}}
        else:
            return {"result": (*BytePlusApiHandler.handle_video_generation_error(
                "Seedance Pro 1.5", "Failed to generate video"
            ), ""), "ui": {"draft_task_id": [""]}}


class SeedanceProNode:
    """Seedance Pro Video Generation Node"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (["seedance-1-0-pro-250528", "seedance-1-0-pro-fast-251015 (end_frame not supported)"], {"default": "seedance-1-0-pro-250528"}),
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "mode": (["text-to-video", "image-to-video"], {"default": "text-to-video"}),
                "resolution": (["480p", "720p", "1080p"], {"default": "1080p"}),
                "ratio": (["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"], {"default": "adaptive"}),
                "duration": ("INT", {"default": 5, "min": 3, "max": 12, "step": 1}),
            },
            "optional": {
                "image": ("IMAGE",),
                "end_frame": ("IMAGE",),
                "framepersecond": ("INT", {"default": 24, "min": 24, "max": 24, "step": 1}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "camerafixed": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate_video"
    CATEGORY = "Seed/VideoGeneration"

    def generate_video(
        self,
        model,
        prompt,
        mode,
        resolution,
        ratio,
        duration,
        image=None,
        end_frame=None,
        framepersecond=24,
        seed=-1,
        camerafixed=False
    ):
        try:
            # Extract the actual model ID (remove any notes in parentheses)
            model_id = model.split(" (")[0]

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
            
            # Add image(s) if in image-to-video mode
            if mode == "image-to-video":
                if image is None:
                    return BytePlusApiHandler.handle_video_generation_error(
                        "Seedance Pro", "Image is required for image-to-video mode"
                    )

                # Convert first frame
                image_base64 = BytePlusImageUtils.image_to_base64(image)
                if not image_base64:
                    return BytePlusApiHandler.handle_video_generation_error(
                        "Seedance Pro", "Failed to convert image to base64"
                    )

                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_base64
                    },
                    "role": "first_frame"
                })

                # Check if end_frame is provided for first+last frame generation
                # Only use end_frame for regular model (fast model does not support it)
                if end_frame is not None and model_id == "seedance-1-0-pro-250528":
                    # Convert last frame
                    last_frame_base64 = BytePlusImageUtils.image_to_base64(end_frame)
                    if not last_frame_base64:
                        return BytePlusApiHandler.handle_video_generation_error(
                            "Seedance Pro", "Failed to convert end frame image to base64"
                        )

                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": last_frame_base64
                        },
                        "role": "last_frame"
                    })

            # Submit to BytePlus API
            video_url = BytePlusApiHandler.submit_and_get_result(
                model=model_id,
                content=content
            )
            
            if video_url and video_url.strip():
                return (video_url,)
            else:
                return BytePlusApiHandler.handle_video_generation_error(
                    "Seedance Pro", "Failed to generate video"
                )
                
        except Exception as e:
            return BytePlusApiHandler.handle_video_generation_error(
                "Seedance Pro", str(e)
            )


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "SeedanceLiteTextToVideo": SeedanceTextToVideoNode,
    "SeedanceLiteImageToVideo": SeedanceImageToVideoNode,
    "SeedanceLiteFirstLastFrame": SeedanceFirstLastFrameNode,
    "SeedanceLiteReferenceImages": SeedanceReferenceImagesNode,
    "SeedanceProTextImageToVideo": SeedanceProNode,
    "SeedancePro15Video": SeedancePro15VideoNode,
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "SeedanceLiteTextToVideo": "Seedance Lite Text-to-Video",
    "SeedanceLiteImageToVideo": "Seedance Lite Image-to-Video",
    "SeedanceLiteFirstLastFrame": "Seedance Lite First+Last Frame",
    "SeedanceLiteReferenceImages": "Seedance Lite Reference Images",
    "SeedanceProTextImageToVideo": "Seedance Pro Text/Image-to-Video",
    "SeedancePro15Video": "Seedance Pro 1.5 Video",
}
