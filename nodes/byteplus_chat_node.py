from .byteplus_utils import (
    BytePlusChatApiHandler,
    BytePlusChatUtils,
    BytePlusImageUtils
)


class SeedChatNode:
    """Unified Seed 1.6 Chat Node with Vision Support and Session Memory"""
    
    # Class-level conversation memory storage
    conversation_sessions = {}
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (["seed-1-6-250615", "seed-1-6-flash-250715"], {"default": "seed-1-6-flash-250715"}),
                "user_message": ("STRING", {"default": "", "multiline": True}),
                "session_id": ("STRING", {"default": "default", "tooltip": "Unique identifier for conversation session"}),
                "use_session_memory": ("BOOLEAN", {"default": False, "tooltip": "Keep conversation context in memory"}),
            },
            "optional": {
                "system_message": ("STRING", {"default": "", "multiline": True}),
                "image_1": ("IMAGE",),
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
                "image_detail": (["auto", "high", "low"], {"default": "auto"}),
                "thinking_mode": (["enabled", "disabled"], {"default": "enabled"}),
                "reasoning_effort": (["low", "medium", "high"], {"default": "medium"}),
                "clear_session": ("BOOLEAN", {"default": False, "tooltip": "Clear conversation memory for this session"}),
                "external_history": ("STRING", {"default": "", "multiline": True, "tooltip": "Import external conversation history"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("response", "full_conversation", "session_status")
    FUNCTION = "chat_completion"
    CATEGORY = "Seed/Chat"

    def chat_completion(
        self,
        model,
        user_message,
        session_id,
        use_session_memory,
        system_message="",
        image_1=None,
        image_2=None,
        image_3=None,
        image_4=None,
        image_detail="auto",
        thinking_mode="enabled",
        reasoning_effort="medium",
        clear_session=False,
        external_history=""
    ):
        try:
            # Handle session clearing
            if clear_session and session_id in self.conversation_sessions:
                del self.conversation_sessions[session_id]
                print(f"Cleared conversation session: {session_id}")
            
            # Initialize session if not exists
            if session_id not in self.conversation_sessions:
                self.conversation_sessions[session_id] = {
                    "messages": [],
                    "system_message": "",
                }
            
            session = self.conversation_sessions[session_id]
            
            # Handle system message changes
            if system_message.strip() and system_message != session["system_message"]:
                # Clear previous system message and update
                session["messages"] = [msg for msg in session["messages"] if msg["role"] != "system"]
                session["system_message"] = system_message
                session["messages"].insert(0, BytePlusChatUtils.format_text_message("system", system_message))
            elif system_message.strip() and not session["system_message"]:
                # Add initial system message
                session["system_message"] = system_message
                session["messages"].insert(0, BytePlusChatUtils.format_text_message("system", system_message))
            
            # Handle external history import (overwrites session memory)
            if external_history.strip():
                imported_messages = self._parse_conversation_history(external_history)
                if use_session_memory:
                    session["messages"] = imported_messages.copy()
                messages = imported_messages.copy()
            else:
                # Use session memory if enabled
                if use_session_memory:
                    messages = session["messages"].copy()
                else:
                    messages = []
                    # Add system message if provided and not using session memory
                    if system_message.strip():
                        messages.append(BytePlusChatUtils.format_text_message("system", system_message))
            
            # Collect images for multimodal support
            images = []
            for img in [image_1, image_2, image_3, image_4]:
                if img is not None:
                    images.append(img)
            
            # Add current user message (multimodal if images are present)
            if images:
                user_msg = BytePlusChatUtils.format_multimodal_message(
                    "user", user_message, images, image_detail
                )
            else:
                user_msg = BytePlusChatUtils.format_text_message("user", user_message)
            
            messages.append(user_msg)
            
            # Make API call
            response = BytePlusChatApiHandler.create_chat_completion(
                model=model,
                messages=messages,
                thinking_type=thinking_mode,
                reasoning_effort=reasoning_effort
            )
            
            if not response:
                return BytePlusChatApiHandler.handle_chat_error(model, "No response received")
            
            # Extract response text
            response_text = BytePlusChatUtils.extract_response_text(response)
            
            # Update session memory if enabled
            if use_session_memory and not external_history.strip():
                session["messages"].append(user_msg)
                session["messages"].append(BytePlusChatUtils.format_text_message("assistant", response_text))
                
                # Trim session memory if it gets too long (keep last 20 messages + system)
                system_msgs = [msg for msg in session["messages"] if msg["role"] == "system"]
                other_msgs = [msg for msg in session["messages"] if msg["role"] != "system"]
                if len(other_msgs) > 20:
                    other_msgs = other_msgs[-20:]
                session["messages"] = system_msgs + other_msgs
            
            # Build full conversation for output
            full_conversation = self._build_conversation_output(messages, response_text)
            
            # Create session status message
            session_status = self._create_session_status(session_id, use_session_memory, len(session["messages"]))
            
            return (response_text, full_conversation, session_status)
            
        except Exception as e:
            error_msg = f"Error with {model}: {str(e)}"
            return (error_msg, error_msg, f"Session {session_id}: Error occurred")

    def _parse_conversation_history(self, history_text):
        """Parse conversation history from text format."""
        messages = []
        lines = history_text.strip().split('\n')
        current_role = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for role indicators
            if line.startswith("User:") or line.startswith("user:"):
                if current_role and current_content:
                    messages.append(BytePlusChatUtils.format_text_message(current_role, '\n'.join(current_content)))
                current_role = "user"
                current_content = [line[5:].strip()]
            elif line.startswith("Assistant:") or line.startswith("assistant:"):
                if current_role and current_content:
                    messages.append(BytePlusChatUtils.format_text_message(current_role, '\n'.join(current_content)))
                current_role = "assistant"
                current_content = [line[10:].strip()]
            elif line.startswith("System:") or line.startswith("system:"):
                if current_role and current_content:
                    messages.append(BytePlusChatUtils.format_text_message(current_role, '\n'.join(current_content)))
                current_role = "system"
                current_content = [line[7:].strip()]
            else:
                # Continue current message
                if current_role:
                    current_content.append(line)
        
        # Add the last message
        if current_role and current_content:
            messages.append(BytePlusChatUtils.format_text_message(current_role, '\n'.join(current_content)))
        
        return messages

    def _build_conversation_output(self, messages, response_text):
        """Build a formatted conversation output."""
        conversation_parts = []
        
        for msg in messages:
            role = msg["role"].title()
            if isinstance(msg["content"], str):
                content = msg["content"]
            elif isinstance(msg["content"], list):
                # Extract text from multimodal content
                text_parts = []
                image_count = 0
                for item in msg["content"]:
                    if item["type"] == "text":
                        text_parts.append(item["text"])
                    elif item["type"] == "image_url":
                        image_count += 1
                
                content = '\n'.join(text_parts)
                if image_count > 0:
                    content += f"\n[{image_count} image(s) attached]"
            else:
                content = str(msg["content"])
            
            conversation_parts.append(f"{role}: {content}")
        
        # Add the response
        conversation_parts.append(f"Assistant: {response_text}")
        
        return '\n\n'.join(conversation_parts)
    
    def _create_session_status(self, session_id, use_memory, message_count):
        """Create status message about the session."""
        if use_memory:
            return f"Session '{session_id}': Memory enabled, {message_count} messages stored"
        else:
            return f"Session '{session_id}': Memory disabled, one-shot conversation"
    
    @classmethod
    def clear_all_sessions(cls):
        """Utility method to clear all conversation sessions."""
        cls.conversation_sessions.clear()
        print("All conversation sessions cleared")


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "SeedChat": SeedChatNode,
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "SeedChat": "Seed 1.6 Chat",
}
