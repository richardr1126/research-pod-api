import os
from typing import Literal, Optional
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TextToSpeechClient:
    """
    A client for OpenAI's Text-to-Speech (TTS) API.
    This client allows you to generate speech from text using OpenAI's TTS models.
    It supports custom base URL configuration for OpenAI API endpoint.
    Can be used as a context manager with 'with' statement.
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TTS client.
        
        Args:
            api_key: OpenAI API key. If not provided, will use OPENAI_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', 'not-needed')
        self.base_url = os.getenv('TTS_BASE_URL')
        
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided either through constructor or OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def __enter__(self):
        """Context manager entry point."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point that ensures proper cleanup."""
        self.close()
        return False  # Re-raise any exceptions

    def generate_speech(
        self,
        text: str,
        model: str = "tts-1",
        voice: str = "alloy",
        format: Literal["mp3", "aac"] = "mp3",
        speed: float = 1.0,
        instructions: Optional[str] = None
    ) -> bytes:
        """
        Generate speech from text using OpenAI's TTS API.
        
        Args:
            text: The text to convert to speech
            model: TTS model to use (default: "tts-1")
            voice: Voice to use for speech
            format: Audio format (mp3 or aac)
            speed: Speech speed (0.25 to 4.0)
            instructions: Optional voice instructions for custom models
            
        Returns:
            Audio data as bytes
        """
        try:
            # Validate speed range
            if not 0.25 <= speed <= 4.0:
                raise ValueError("Speed must be between 0.25 and 4.0")

            # Prepare speech parameters
            params = {
                "model": model,
                "voice": voice,
                "input": text,
                "speed": speed,
                "response_format": format
            }

            # Add instructions if using a custom model that supports it
            if instructions and model == "gpt-4o-mini-tts":
                params["instructions"] = instructions

            # Generate speech synchronously
            response = self.client.audio.speech.create(**params)
            
            # Get the audio data
            audio_data = response.content
            
            return audio_data

        except Exception as e:
            raise Exception(f"Failed to generate speech: {str(e)}")

    def close(self):
        """Close the OpenAI client session."""
        if hasattr(self, 'client'):
            self.client.close()