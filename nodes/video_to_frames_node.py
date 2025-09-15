import os
import torch
import requests
import tempfile
import numpy as np
import time
from PIL import Image

# Try to import opencv - if not available, provide error message
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("WARNING: opencv-python not installed. Video frame extraction will not work.")
    print("To install: pip install opencv-python>=4.5.0")



def _fetch_video(url, timeout=300):
    """Download video content from URL with streaming and proper total timeout enforcement."""
    try:
        print(f"Starting video download from: {url}")
        print(f"Total timeout: {timeout} seconds")

        # Record start time for total timeout enforcement
        start_time = time.time()

        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'video/*, */*',
            'Accept-Encoding': 'identity',  # Disable compression to avoid issues
            'Connection': 'keep-alive'
        }

        # Start streaming request with connection timeout only
        # We'll handle total timeout manually
        try:
            response = requests.get(url, stream=True, timeout=30, headers=headers)  # 30s connection timeout only
            response.raise_for_status()  # Raise exception for bad status codes
        except requests.exceptions.Timeout:
            raise Exception("Connection timeout - could not connect to server within 30 seconds")

        # Check if we've already exceeded timeout during connection
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            response.close()
            raise Exception(f"Total timeout exceeded during connection ({elapsed:.1f}s >= {timeout}s)")

        # Get file size if available
        total_size = response.headers.get('content-length')
        if total_size:
            total_size = int(total_size)
            print(f"Video size: {total_size / (1024*1024):.2f} MB")
        else:
            print("Video size: Unknown")

        print(f"Starting download, will timeout after {timeout} seconds...")

        # Download in chunks with strict total timeout enforcement
        video_content = bytearray()
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        last_progress_logged = 0
        last_timeout_check = start_time

        try:
            for chunk in response.iter_content(chunk_size=chunk_size, decode_unicode=False):
                # Check total timeout every few chunks (not every single chunk for performance)
                current_time = time.time()
                if current_time - last_timeout_check > 5:  # Check every 5 seconds
                    elapsed = current_time - start_time
                    if elapsed >= timeout:
                        response.close()
                        raise Exception(f"Download timeout exceeded: {elapsed:.1f}s >= {timeout}s (downloaded {downloaded/(1024*1024):.2f} MB)")
                    last_timeout_check = current_time

                if chunk:
                    video_content.extend(chunk)
                    downloaded += len(chunk)

                    # Log progress every 10% or every 10MB, whichever comes first
                    if total_size:
                        progress = (downloaded / total_size) * 100
                        if progress - last_progress_logged >= 10:
                            elapsed = time.time() - start_time
                            print(f"Download progress: {progress:.1f}% ({downloaded / (1024*1024):.2f} MB) - {elapsed:.1f}s elapsed")
                            last_progress_logged = progress
                    else:
                        # Log every 10MB when size is unknown
                        mb_downloaded = downloaded / (1024*1024)
                        if mb_downloaded - last_progress_logged >= 10:
                            elapsed = time.time() - start_time
                            print(f"Downloaded: {mb_downloaded:.2f} MB - {elapsed:.1f}s elapsed")
                            last_progress_logged = mb_downloaded
        finally:
            response.close()

        final_elapsed = time.time() - start_time
        print(f"Download complete: {len(video_content)} bytes in {final_elapsed:.1f} seconds")
        return bytes(video_content)

    except requests.exceptions.Timeout:
        raise Exception(f"Download timeout after {timeout}s - video may be too large or connection too slow")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Download failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error during download: {str(e)}")


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
        
        # Download video content (5 minute timeout)
        try:
            video_content = _fetch_video(video_url, timeout=300)
        except Exception as e:
            error_msg = str(e)
            print(f"Error downloading video: {error_msg}")

            # For ComfyUI services, throw error with video URL for user recovery
            # Format error message to include the video URL for easy copy/paste
            user_error = f"Video download failed: {error_msg}\n\n📋 VIDEO URL (copy to retry manually):\n{video_url}\n\n💡 Try: Download manually or check network connection"

            raise Exception(user_error)
        
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
