import os
import torch
import requests
import tempfile
import numpy as np
from PIL import Image

# Try to import opencv - if not available, provide error message
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("WARNING: opencv-python not installed. Video frame extraction will not work.")
    print("To install: pip install opencv-python>=4.5.0")


def _fetch_video(url, stream=True):
    """Download video content from URL."""
    return requests.get(url, stream=stream).content


class VideoToFrames:
    """
    Simple node that extracts all frames from a video URL as a tensor batch.
    Clean and focused approach without file saving complexity.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_url": ("STRING", {"forceInput": True}),
            }
        }

    FUNCTION = "extract_frames"
    CATEGORY = "Seed/Video"

    RETURN_TYPES = ("IMAGE", "INT", "FLOAT")
    RETURN_NAMES = ("frames", "frame_count", "fps")

    def extract_frames(self, video_url):
        """
        Simple function that downloads video and extracts all frames.
        
        Args:
            video_url: URL of the video to download
            
        Returns:
            frames: Extracted frames as IMAGE tensor batch
            frame_count: Number of extracted frames
            fps: FPS of the video
        """
        
        # Handle case where video_url might be a list
        if isinstance(video_url, list):
            video_url = video_url[0]
        
        # Initialize return values
        frames_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)  # Default empty frames
        frame_count = 0
        video_fps = 0.0
        
        # Download video content
        try:
            print(f"Downloading video from: {video_url}")
            video_content = _fetch_video(video_url)
            print(f"Downloaded {len(video_content)} bytes")
        except Exception as e:
            print(f"Error downloading video: {str(e)}")
            return (frames_tensor, frame_count, video_fps)
        
        # Extract frames
        if video_content:
            try:
                frames_tensor, frame_count, video_fps = self._extract_frames(video_content)
                print(f"Extracted {frame_count} frames at {video_fps:.2f} fps")
            except Exception as e:
                print(f"Error extracting frames: {str(e)}")
                frames_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
                frame_count = 0
                video_fps = 0.0
        
        return (frames_tensor, frame_count, video_fps)
    
    def _extract_frames(self, video_content):
        """Extract all frames from video content as tensor batch."""
        if not OPENCV_AVAILABLE:
            print("Cannot extract frames: opencv-python not installed")
            return torch.zeros((1, 64, 64, 3), dtype=torch.float32), 0, 0.0
        
        # Create temporary file for OpenCV
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(video_content)
            temp_path = temp_file.name
        
        try:
            # Open video with OpenCV
            cap = cv2.VideoCapture(temp_path)
            
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            frames = []
            frame_count = 0
            
            print(f"Video info: {total_frames} total frames at {fps:.2f} fps")
            print(f"Extracting all frames...")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image then to tensor
                pil_image = Image.fromarray(frame_rgb)
                frame_array = np.array(pil_image).astype(np.float32) / 255.0
                
                frames.append(frame_array)
                frame_count += 1
            
            cap.release()
            
            if frames:
                # Stack frames into tensor batch
                frames_tensor = torch.from_numpy(np.stack(frames, axis=0))
                print(f"Created tensor with shape: {frames_tensor.shape}")
            else:
                # Return empty tensor if no frames extracted
                frames_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
                frame_count = 0
                fps = 0.0
            
            return frames_tensor, frame_count, fps
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "VideoToFrames": VideoToFrames,
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoToFrames": "Video URL to Frames",
}
