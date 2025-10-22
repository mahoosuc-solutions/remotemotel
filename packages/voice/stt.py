"""
Speech-to-Text (STT) engines

Supports:
- OpenAI Whisper API
- Streaming transcription
- Language detection
- Multiple languages
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
    logger.warning("OpenAI not available - STT features will be limited")


class STTEngine(ABC):
    """
    Base class for Speech-to-Text engines
    """

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio to text

        Args:
            audio_data: Audio bytes (WAV, MP3, etc.)
            language: Language code (e.g., 'en', 'es')

        Returns:
            Transcribed text
        """
        pass

    @abstractmethod
    async def detect_language(self, audio_data: bytes) -> str:
        """
        Detect the language of the audio

        Args:
            audio_data: Audio bytes

        Returns:
            Detected language code
        """
        pass


class WhisperSTT(STTEngine):
    """
    OpenAI Whisper Speech-to-Text engine
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1"
    ):
        """
        Initialize Whisper STT

        Args:
            api_key: OpenAI API key (uses env var if None)
            model: Whisper model to use
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package is required for WhisperSTT")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key)

        self.logger = logging.getLogger(f"{__name__}.WhisperSTT")
        self.logger.info(f"WhisperSTT initialized with model {model}")

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """
        Transcribe audio using Whisper API

        Args:
            audio_data: Audio bytes (supports various formats)
            language: Language code (e.g., 'en', 'es')
            prompt: Optional prompt to guide transcription

        Returns:
            Transcribed text
        """
        try:
            # Create a file-like object from audio bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"  # Whisper needs a filename

            # Call Whisper API
            params: Dict[str, Any] = {
                "model": self.model,
                "file": audio_file
            }

            if language:
                params["language"] = language

            if prompt:
                params["prompt"] = prompt

            response = await self.client.audio.transcriptions.create(**params)

            text = response.text
            self.logger.info(f"Transcribed {len(audio_data)} bytes: '{text[:50]}...'")

            return text

        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}", exc_info=True)
            raise

    async def detect_language(self, audio_data: bytes) -> str:
        """
        Detect language using Whisper API

        Args:
            audio_data: Audio bytes

        Returns:
            Detected language code
        """
        try:
            # Transcribe without specifying language
            # Whisper will auto-detect
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"

            response = await self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                response_format="verbose_json"  # Get metadata including language
            )

            # Get detected language from response
            language = getattr(response, 'language', 'en')
            self.logger.info(f"Detected language: {language}")

            return language

        except Exception as e:
            self.logger.error(f"Error detecting language: {e}")
            return "en"  # Default to English

    async def transcribe_with_timestamps(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio with word-level timestamps

        Args:
            audio_data: Audio bytes
            language: Language code

        Returns:
            Dict with text and timestamps
        """
        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"

            params: Dict[str, Any] = {
                "model": self.model,
                "file": audio_file,
                "response_format": "verbose_json",
                "timestamp_granularities": ["word"]
            }

            if language:
                params["language"] = language

            response = await self.client.audio.transcriptions.create(**params)

            result = {
                "text": response.text,
                "language": getattr(response, 'language', language or 'en'),
                "duration": getattr(response, 'duration', None),
                "words": getattr(response, 'words', [])
            }

            self.logger.info(f"Transcribed with timestamps: {len(result.get('words', []))} words")
            return result

        except Exception as e:
            self.logger.error(f"Error transcribing with timestamps: {e}")
            raise

    async def translate_to_english(self, audio_data: bytes) -> str:
        """
        Translate audio to English (Whisper translation feature)

        Args:
            audio_data: Audio bytes in any language

        Returns:
            English translation
        """
        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"

            # Use Whisper's translation endpoint
            response = await self.client.audio.translations.create(
                model=self.model,
                file=audio_file
            )

            text = response.text
            self.logger.info(f"Translated to English: '{text[:50]}...'")

            return text

        except Exception as e:
            self.logger.error(f"Error translating audio: {e}")
            raise


class STTManager:
    """
    Manage STT operations with caching and optimization
    """

    def __init__(
        self,
        engine: Optional[STTEngine] = None,
        cache_enabled: bool = False
    ):
        """
        Initialize STT manager

        Args:
            engine: STT engine to use (creates WhisperSTT if None)
            cache_enabled: Enable result caching
        """
        self.engine = engine or WhisperSTT()
        self.cache_enabled = cache_enabled
        self.cache: Dict[str, str] = {}

        self.logger = logging.getLogger(f"{__name__}.STTManager")
        self.logger.info("STTManager initialized")

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Transcribe audio with optional caching

        Args:
            audio_data: Audio bytes
            language: Language code
            session_id: Session ID for tracking

        Returns:
            Transcribed text
        """
        # Check cache
        if self.cache_enabled:
            cache_key = f"{hash(audio_data)}_{language}"
            if cache_key in self.cache:
                self.logger.debug("Cache hit for transcription")
                return self.cache[cache_key]

        # Transcribe
        text = await self.engine.transcribe(audio_data, language)

        # Cache result
        if self.cache_enabled:
            self.cache[cache_key] = text

        # Log metrics
        if session_id:
            self.logger.info(f"Session {session_id}: Transcribed {len(text)} characters")

        return text

    async def detect_language(self, audio_data: bytes) -> str:
        """
        Detect audio language

        Args:
            audio_data: Audio bytes

        Returns:
            Language code
        """
        return await self.engine.detect_language(audio_data)

    def clear_cache(self) -> None:
        """Clear the transcription cache"""
        self.cache.clear()
        self.logger.info("Transcription cache cleared")


# Convenience functions
def create_whisper_engine(api_key: Optional[str] = None) -> WhisperSTT:
    """
    Create a Whisper STT engine

    Args:
        api_key: OpenAI API key

    Returns:
        WhisperSTT instance
    """
    return WhisperSTT(api_key=api_key)


async def transcribe_audio(
    audio_data: bytes,
    language: Optional[str] = None
) -> str:
    """
    Quick transcription using Whisper

    Args:
        audio_data: Audio bytes
        language: Language code

    Returns:
        Transcribed text
    """
    engine = WhisperSTT()
    return await engine.transcribe(audio_data, language)
