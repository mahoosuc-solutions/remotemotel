"""
Text-to-Speech (TTS) engines

Supports:
- OpenAI TTS API
- Multiple voices
- Streaming synthesis
- SSML support (basic)
"""

import os
import io
import logging
from typing import Optional, AsyncIterator, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - TTS features will be limited")


class Voice(Enum):
    """Available TTS voices"""
    ALLOY = "alloy"      # Neutral, balanced
    ECHO = "echo"        # Male, warm
    FABLE = "fable"      # British, expressive
    ONYX = "onyx"        # Male, deep
    NOVA = "nova"        # Female, energetic
    SHIMMER = "shimmer"  # Female, warm


class TTSEngine(ABC):
    """
    Base class for Text-to-Speech engines
    """

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str = "alloy"
    ) -> bytes:
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize
            voice: Voice to use

        Returns:
            Audio bytes
        """
        pass

    @abstractmethod
    async def stream_synthesize(
        self,
        text: str,
        voice: str = "alloy"
    ) -> AsyncIterator[bytes]:
        """
        Stream synthesized speech

        Args:
            text: Text to synthesize
            voice: Voice to use

        Yields:
            Audio chunks
        """
        pass


class OpenAITTS(TTSEngine):
    """
    OpenAI Text-to-Speech engine
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "tts-1",  # or "tts-1-hd" for higher quality
        default_voice: str = "alloy"
    ):
        """
        Initialize OpenAI TTS

        Args:
            api_key: OpenAI API key (uses env var if None)
            model: TTS model to use ("tts-1" or "tts-1-hd")
            default_voice: Default voice
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package is required for OpenAITTS")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.model = model
        self.default_voice = default_voice
        self.client = AsyncOpenAI(api_key=self.api_key)

        self.logger = logging.getLogger(f"{__name__}.OpenAITTS")
        self.logger.info(f"OpenAITTS initialized with model {model}, voice {default_voice}")

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> bytes:
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize (max 4096 chars)
            voice: Voice to use
            speed: Speech speed (0.25 to 4.0)

        Returns:
            Audio bytes (MP3 format)
        """
        try:
            voice = voice or self.default_voice

            # Validate speed
            speed = max(0.25, min(4.0, speed))

            # Call TTS API
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                speed=speed,
                response_format="mp3"
            )

            # Get audio bytes
            audio_data = response.content

            self.logger.info(
                f"Synthesized {len(text)} characters with voice '{voice}': "
                f"{len(audio_data)} bytes"
            )

            return audio_data

        except Exception as e:
            self.logger.error(f"Error synthesizing speech: {e}", exc_info=True)
            raise

    async def stream_synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> AsyncIterator[bytes]:
        """
        Stream synthesized speech for low latency

        Args:
            text: Text to synthesize
            voice: Voice to use
            speed: Speech speed

        Yields:
            Audio chunks
        """
        try:
            voice = voice or self.default_voice
            speed = max(0.25, min(4.0, speed))

            # Stream TTS
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                speed=speed,
                response_format="mp3"
            )

            # Stream chunks
            async for chunk in response.iter_bytes(chunk_size=1024):
                yield chunk

            self.logger.info(f"Streamed synthesis of {len(text)} characters")

        except Exception as e:
            self.logger.error(f"Error streaming speech: {e}")
            raise

    async def synthesize_opus(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> bytes:
        """
        Synthesize speech in Opus format (for WebRTC)

        Args:
            text: Text to synthesize
            voice: Voice to use
            speed: Speech speed

        Returns:
            Audio bytes (Opus format)
        """
        try:
            voice = voice or self.default_voice

            response = await self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                speed=speed,
                response_format="opus"
            )

            audio_data = response.content
            self.logger.info(f"Synthesized Opus audio: {len(audio_data)} bytes")

            return audio_data

        except Exception as e:
            self.logger.error(f"Error synthesizing Opus: {e}")
            raise

    async def synthesize_pcm(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> bytes:
        """
        Synthesize speech in PCM format (for Twilio)

        Args:
            text: Text to synthesize
            voice: Voice to use
            speed: Speech speed

        Returns:
            Audio bytes (PCM format, 16-bit, 24kHz)
        """
        try:
            voice = voice or self.default_voice

            response = await self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                speed=speed,
                response_format="pcm"
            )

            audio_data = response.content
            self.logger.info(f"Synthesized PCM audio: {len(audio_data)} bytes")

            return audio_data

        except Exception as e:
            self.logger.error(f"Error synthesizing PCM: {e}")
            raise

    def process_ssml(self, ssml_text: str) -> str:
        """
        Basic SSML processing (extract text, handle pauses)

        Args:
            ssml_text: SSML-formatted text

        Returns:
            Plain text with processed SSML
        """
        # For now, just strip SSML tags
        # TODO: Implement proper SSML parsing and conversion to OpenAI format
        import re

        # Remove XML tags
        text = re.sub(r'<[^>]+>', '', ssml_text)

        # Handle breaks (convert to commas for natural pauses)
        text = re.sub(r'<break\s+time="[^"]*"\s*/>', ',', text)

        return text


class TTSManager:
    """
    Manage TTS operations with caching and optimization
    """

    def __init__(
        self,
        engine: Optional[TTSEngine] = None,
        cache_enabled: bool = True
    ):
        """
        Initialize TTS manager

        Args:
            engine: TTS engine to use (creates OpenAITTS if None)
            cache_enabled: Enable result caching
        """
        self.engine = engine or OpenAITTS()
        self.cache_enabled = cache_enabled
        self.cache: Dict[str, bytes] = {}

        # Common hotel phrases for pre-caching
        self.common_phrases = [
            "Welcome to our hotel.",
            "Thank you for calling.",
            "How may I help you today?",
            "Let me check availability for you.",
            "Please hold while I look that up.",
            "Your reservation is confirmed.",
            "Is there anything else I can help you with?"
        ]

        self.logger = logging.getLogger(f"{__name__}.TTSManager")
        self.logger.info("TTSManager initialized")

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        session_id: Optional[str] = None
    ) -> bytes:
        """
        Synthesize speech with optional caching

        Args:
            text: Text to synthesize
            voice: Voice to use
            speed: Speech speed
            session_id: Session ID for tracking

        Returns:
            Audio bytes
        """
        # Check cache
        if self.cache_enabled:
            cache_key = f"{text}_{voice}_{speed}"
            if cache_key in self.cache:
                self.logger.debug("Cache hit for TTS")
                return self.cache[cache_key]

        # Synthesize
        audio = await self.engine.synthesize(text, voice, speed)

        # Cache result
        if self.cache_enabled:
            self.cache[cache_key] = audio

        # Log metrics
        if session_id:
            self.logger.info(
                f"Session {session_id}: Synthesized {len(text)} chars to {len(audio)} bytes"
            )

        return audio

    async def stream_synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> AsyncIterator[bytes]:
        """
        Stream synthesized speech

        Args:
            text: Text to synthesize
            voice: Voice to use
            speed: Speech speed

        Yields:
            Audio chunks
        """
        async for chunk in self.engine.stream_synthesize(text, voice, speed):
            yield chunk

    async def pre_cache_common_phrases(
        self,
        voice: Optional[str] = None
    ) -> None:
        """
        Pre-cache common hotel phrases for low latency

        Args:
            voice: Voice to use for caching
        """
        self.logger.info(f"Pre-caching {len(self.common_phrases)} common phrases...")

        for phrase in self.common_phrases:
            try:
                await self.synthesize(phrase, voice)
            except Exception as e:
                self.logger.error(f"Error caching phrase '{phrase}': {e}")

        self.logger.info("Pre-caching complete")

    def clear_cache(self) -> None:
        """Clear the TTS cache"""
        self.cache.clear()
        self.logger.info("TTS cache cleared")

    def get_cache_size(self) -> int:
        """
        Get total cache size in bytes

        Returns:
            Cache size in bytes
        """
        total_size = sum(len(audio) for audio in self.cache.values())
        return total_size


# Convenience functions
def create_openai_tts(
    api_key: Optional[str] = None,
    voice: str = "alloy"
) -> OpenAITTS:
    """
    Create an OpenAI TTS engine

    Args:
        api_key: OpenAI API key
        voice: Default voice

    Returns:
        OpenAITTS instance
    """
    return OpenAITTS(api_key=api_key, default_voice=voice)


async def synthesize_speech(
    text: str,
    voice: str = "alloy",
    speed: float = 1.0
) -> bytes:
    """
    Quick speech synthesis using OpenAI

    Args:
        text: Text to synthesize
        voice: Voice to use
        speed: Speech speed

    Returns:
        Audio bytes
    """
    engine = OpenAITTS()
    return await engine.synthesize(text, voice, speed)


# Voice recommendations for hotel use cases
HOTEL_VOICES = {
    "professional": Voice.ALLOY,   # Balanced, professional
    "friendly": Voice.NOVA,        # Energetic, friendly
    "warm": Voice.SHIMMER,         # Warm, welcoming
    "authoritative": Voice.ONYX,   # Deep, authoritative
    "expressive": Voice.FABLE      # Expressive, engaging
}
