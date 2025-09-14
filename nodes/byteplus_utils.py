import base64
import configparser
import io
import json
import os
import time
import tempfile
from typing import Optional, Dict, Any
import copy

import numpy as np
import requests
import torch
from PIL import Image


class LoggingUtils:
    """Utility functions for safe logging that truncates base64 strings."""

    @staticmethod
    def truncate_base64_in_dict(data, max_length=50):
        """Recursively truncate base64 strings in a dictionary for logging."""
        if isinstance(data, dict):
            truncated = {}
            for key, value in data.items():
                truncated[key] = LoggingUtils.truncate_base64_in_dict(value, max_length)
            return truncated
        elif isinstance(data, list):
            return [LoggingUtils.truncate_base64_in_dict(item, max_length) for item in data]
        elif isinstance(data, str):
            # Check if string looks like base64 data URI
            if data.startswith('data:image/') and 'base64,' in data and len(data) > 100:
                # Find the base64 part
                base64_start = data.find('base64,') + 7
                prefix = data[:base64_start]
                base64_part = data[base64_start:]
                if len(base64_part) > max_length:
                    truncated_b64 = base64_part[:max_length] + f"...[{len(base64_part)-max_length} chars truncated]"
                    return prefix + truncated_b64
            return data
        else:
            return data

    @staticmethod
    def safe_log_payload(payload, description="Payload"):
        """Safely log a payload by truncating base64 strings."""
        safe_payload = LoggingUtils.truncate_base64_in_dict(copy.deepcopy(payload))
        print(f"{description}: {safe_payload}")


class BytePlusConfig:
    """Singleton class to handle BytePlus configuration and client setup."""

    _instance = None
    _api_key = None
    _base_url = "https://ark.ap-southeast.bytepluses.com/api/v3"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BytePlusConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize configuration and API key."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        config_path = os.path.join(parent_dir, "config.ini")

        config = configparser.ConfigParser()
        config.read(config_path)

        try:
            if os.environ.get("BYTEPLUS_API_KEY") is not None:
                print("BYTEPLUS_API_KEY found in environment variables")
                self._api_key = os.environ["BYTEPLUS_API_KEY"]
            else:
                print("BYTEPLUS_API_KEY not found in environment variables")
                self._api_key = config["API"]["BYTEPLUS_API_KEY"]
                print("BYTEPLUS_API_KEY found in config.ini")
                os.environ["BYTEPLUS_API_KEY"] = self._api_key
                print("BYTEPLUS_API_KEY set in environment variables")

            # Check if BytePlus key is the default placeholder
            if self._api_key == "<your_byteplus_api_key_here>":
                print("WARNING: You are using the default BytePlus API key placeholder!")
                print("Please set your actual BytePlus API key in either:")
                print("1. The config.ini file under [API] section")
                print("2. Or as an environment variable named BYTEPLUS_API_KEY")
                print("Get your API key from: https://console.volcengine.com/ark/region:ap-southeast-1/apiKey")
        except KeyError:
            print("Error: BYTEPLUS_API_KEY not found in config.ini or environment variables")

    def get_api_key(self):
        """Get the BytePlus API key."""
        return self._api_key

    def get_base_url(self):
        """Get the BytePlus API base URL."""
        return self._base_url


class BytePlusImageUtils:
    """Utility functions for image processing specific to BytePlus API."""

    @staticmethod
    def tensor_to_pil(image):
        """Convert image tensor to PIL Image."""
        try:
            # Convert the image tensor to a numpy array
            if isinstance(image, torch.Tensor):
                image_np = image.cpu().numpy()
            else:
                image_np = np.array(image)

            # Ensure the image is in the correct format (H, W, C)
            if image_np.ndim == 4:
                image_np = image_np.squeeze(0)  # Remove batch dimension if present
            if image_np.ndim == 2:
                image_np = np.stack([image_np] * 3, axis=-1)  # Convert grayscale to RGB
            elif image_np.shape[0] == 3:
                image_np = np.transpose(
                    image_np, (1, 2, 0)
                )  # Change from (C, H, W) to (H, W, C)

            # Normalize the image data to 0-255 range
            if image_np.dtype == np.float32 or image_np.dtype == np.float64:
                image_np = (image_np * 255).astype(np.uint8)

            # Convert to PIL Image
            return Image.fromarray(image_np)
        except Exception as e:
            print(f"Error converting tensor to PIL: {str(e)}")
            return None

    @staticmethod
    def image_to_base64(image):
        """Convert image tensor to base64 string format for BytePlus API."""
        try:
            pil_image = BytePlusImageUtils.tensor_to_pil(image)
            if not pil_image:
                return None

            # Convert to base64
            buffered = io.BytesIO()
            pil_image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Format for BytePlus API
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            print(f"Error converting image to base64: {str(e)}")
            return None


class BytePlusApiHandler:
    """Utility functions for BytePlus API interactions."""

    @staticmethod
    def create_video_generation_task(model: str, content: list, callback_url: Optional[str] = None) -> Optional[str]:
        """Create a video generation task and return task ID."""
        config = BytePlusConfig()
        
        headers = {
            "Authorization": f"Bearer {config.get_api_key()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "content": content
        }
        
        print(f"Making request to: {config.get_base_url()}/contents/generations/tasks")
        print(f"Model: {model}")
        print(f"API Key length: {len(config.get_api_key()) if config.get_api_key() else 0}")
        print(f"API Key starts with: {config.get_api_key()[:10] if config.get_api_key() else 'None'}...")
        print(f"Headers: {headers}")
        LoggingUtils.safe_log_payload(payload, "Payload")
        
        if callback_url:
            payload["callback_url"] = callback_url
        
        try:
            response = requests.post(
                f"{config.get_base_url()}/contents/generations/tasks",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("id")
            else:
                print(f"Error creating task: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating video generation task: {str(e)}")
            return None

    @staticmethod
    def query_task_status(task_id: str) -> Optional[Dict[str, Any]]:
        """Query the status of a video generation task."""
        config = BytePlusConfig()
        
        headers = {
            "Authorization": f"Bearer {config.get_api_key()}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{config.get_base_url()}/contents/generations/tasks/{task_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error querying task: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error querying task status: {str(e)}")
            return None

    @staticmethod
    def wait_for_completion(task_id: str, max_wait_time: int = 300, poll_interval: int = 5) -> Optional[str]:
        """Wait for task completion and return video URL."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            result = BytePlusApiHandler.query_task_status(task_id)
            
            if not result:
                print(f"Failed to query task status for {task_id}")
                return None
            
            status = result.get("status")
            print(f"Task {task_id} status: {status}")
            
            if status == "succeeded":
                # Debug: Print the full response to understand the structure (with base64 truncation)
                LoggingUtils.safe_log_payload(result, "Full successful response")
                
                # Look for video URL in the result - try multiple possible paths
                if "content" in result and "video_url" in result["content"]:
                    print(f"Found video_url in content: {result['content']['video_url']}")
                    return result["content"]["video_url"]
                elif "video_url" in result:
                    print(f"Found video_url at root level: {result['video_url']}")
                    return result["video_url"]
                elif "result" in result and "video_url" in result["result"]:
                    print(f"Found video_url in result: {result['result']['video_url']}")
                    return result["result"]["video_url"]
                elif "data" in result and "video_url" in result["data"]:
                    print(f"Found video_url in data: {result['data']['video_url']}")
                    return result["data"]["video_url"]
                elif "output" in result and "video_url" in result["output"]:
                    print(f"Found video_url in output: {result['output']['video_url']}")
                    return result["output"]["video_url"]
                elif "video" in result and "url" in result["video"]:
                    print(f"Found url in video: {result['video']['url']}")
                    return result["video"]["url"]
                else:
                    print("Task succeeded but no video URL found")
                    print(f"Available keys: {list(result.keys())}")
                    return None
                    
            elif status == "failed":
                print(f"Task {task_id} failed: {result.get('error', 'Unknown error')}")
                return None
                
            elif status in ["queued", "running"]:
                time.sleep(poll_interval)
            else:
                print(f"Unknown task status: {status}")
                return None
        
        print(f"Task {task_id} timed out after {max_wait_time} seconds")
        return None

    @staticmethod
    def submit_and_get_result(model: str, content: list, callback_url: Optional[str] = None) -> Optional[str]:
        """Submit task and wait for completion, return video URL."""
        task_id = BytePlusApiHandler.create_video_generation_task(model, content, callback_url)
        
        if not task_id:
            return None
            
        print(f"Created BytePlus task: {task_id}")
        return BytePlusApiHandler.wait_for_completion(task_id)

    @staticmethod
    def handle_video_generation_error(model_name: str, error: str) -> tuple:
        """Handle video generation errors consistently."""
        print(f"Error generating video with {model_name}: {str(error)}")
        # Return empty string instead of None to avoid URL errors
        return ("",)


class BytePlusChatApiHandler:
    """Utility functions for BytePlus Chat API interactions."""

    @staticmethod
    def create_chat_completion(
        model: str,
        messages: list,
        stream: bool = False,
        thinking_type: str = "enabled",
        reasoning_effort: str = "medium"
    ) -> Optional[Dict[str, Any]]:
        """Create a chat completion and return the response."""
        config = BytePlusConfig()
        
        headers = {
            "Authorization": f"Bearer {config.get_api_key()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "thinking": {"type": thinking_type},
            "reasoning_effort": reasoning_effort
        }
        
        print(f"Making chat request to: {config.get_base_url()}/chat/completions")
        print(f"Model: {model}")
        print(f"Messages count: {len(messages)}")
        print(f"Stream: {stream}")
        print(f"Thinking: {thinking_type}")
        print(f"Reasoning effort: {reasoning_effort}")
        
        try:
            response = requests.post(
                f"{config.get_base_url()}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120  # Longer timeout for chat responses
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Chat completion successful")
                return result
            else:
                print(f"Chat completion error: {response.status_code} - {response.text}")
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error in chat completion: {str(e)}")
            raise e

    @staticmethod
    def handle_chat_error(model_name: str, error: str) -> tuple:
        """Handle chat errors consistently."""
        error_message = f"Error with {model_name}: {str(error)}"
        print(error_message)
        return (error_message,)


class BytePlusChatUtils:
    """Utility functions for chat message formatting."""

    @staticmethod
    def format_text_message(role: str, content: str) -> Dict[str, Any]:
        """Format a text message for the chat API."""
        return {
            "role": role,
            "content": content
        }

    @staticmethod
    def format_multimodal_message(role: str, text: str, images: list = None, detail: str = "auto") -> Dict[str, Any]:
        """Format a multimodal message with text and images."""
        content = []
        
        # Add text content
        if text:
            content.append({
                "type": "text",
                "text": text
            })
        
        # Add image content
        if images:
            for image in images:
                if image is not None:
                    image_base64 = BytePlusImageUtils.image_to_base64(image)
                    if image_base64:
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": image_base64,
                                "detail": detail
                            }
                        })
        
        return {
            "role": role,
            "content": content
        }

    @staticmethod
    def extract_response_text(response: Dict[str, Any]) -> str:
        """Extract text content from chat completion response."""
        try:
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
            return "No response content found"
        except Exception as e:
            return f"Error extracting response: {str(e)}"


class BytePlusPromptBuilder:
    """Utility class for building BytePlus prompts with text commands."""
    
    @staticmethod
    def build_prompt_with_commands(
        prompt: str,
        resolution: str = None,
        ratio: str = None,
        duration: int = None,
        framepersecond: int = None,
        watermark: bool = None,
        seed: int = None,
        camerafixed: bool = None
    ) -> str:
        """Build prompt with text commands appended."""
        commands = []
        
        if resolution:
            commands.append(f"--rs {resolution}")
        if ratio:
            commands.append(f"--rt {ratio}")
        if duration is not None:
            commands.append(f"--dur {duration}")
        if framepersecond is not None:
            commands.append(f"--fps {framepersecond}")
        if watermark is not None:
            commands.append(f"--wm {str(watermark).lower()}")
        if seed is not None and seed != -1:
            commands.append(f"--seed {seed}")
        if camerafixed is not None:
            commands.append(f"--cf {str(camerafixed).lower()}")
        
        if commands:
            return f"{prompt} {' '.join(commands)}"
        return prompt
