"""
Call recording and storage

Handles:
- Recording voice calls
- Saving to local storage or S3
- Retrieving recordings
- Audio file management
"""

import os
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, BinaryIO
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import optional libraries
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("Pydub not available - recording features will be limited")

try:
    import boto3
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    logger.warning("boto3 not available - S3 storage disabled")


class StorageBackend(Enum):
    """Storage backend types"""
    LOCAL = "local"
    S3 = "s3"


class AudioRecorder:
    """
    Record and manage voice call audio
    """

    def __init__(
        self,
        session_id: str,
        sample_rate: int = 8000,
        channels: int = 1
    ):
        """
        Initialize audio recorder

        Args:
            session_id: Voice session identifier
            sample_rate: Audio sample rate
            channels: Number of audio channels
        """
        self.session_id = session_id
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer = io.BytesIO()
        self.is_recording = False
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        self.logger = logging.getLogger(f"{__name__}.AudioRecorder")
        self.logger.info(f"AudioRecorder initialized for session {session_id}")

    def start(self) -> None:
        """Start recording"""
        if self.is_recording:
            self.logger.warning("Recording already in progress")
            return

        self.is_recording = True
        self.start_time = datetime.utcnow()
        self.buffer = io.BytesIO()
        self.logger.info(f"Recording started for session {self.session_id}")

    def append(self, audio_data: bytes) -> None:
        """
        Append audio data to recording

        Args:
            audio_data: Audio bytes to append
        """
        if not self.is_recording:
            self.logger.warning("Not recording - call start() first")
            return

        self.buffer.write(audio_data)

    def stop(self) -> bytes:
        """
        Stop recording and return audio data

        Returns:
            Recorded audio bytes
        """
        if not self.is_recording:
            self.logger.warning("Not recording")
            return b""

        self.is_recording = False
        self.end_time = datetime.utcnow()

        audio_data = self.buffer.getvalue()
        duration = (self.end_time - self.start_time).total_seconds()

        self.logger.info(
            f"Recording stopped for session {self.session_id}. "
            f"Duration: {duration:.2f}s, Size: {len(audio_data)} bytes"
        )

        return audio_data

    def get_duration(self) -> float:
        """
        Get recording duration in seconds

        Returns:
            Duration in seconds
        """
        if not self.start_time:
            return 0.0

        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()

    def get_size(self) -> int:
        """
        Get current recording size in bytes

        Returns:
            Size in bytes
        """
        return self.buffer.tell()


class RecordingManager:
    """
    Manage call recordings with storage backends
    """

    def __init__(
        self,
        storage_backend: StorageBackend = StorageBackend.LOCAL,
        local_path: Optional[str] = None,
        s3_bucket: Optional[str] = None
    ):
        """
        Initialize recording manager

        Args:
            storage_backend: Storage backend to use
            local_path: Path for local storage
            s3_bucket: S3 bucket name for cloud storage
        """
        self.storage_backend = storage_backend
        self.local_path = local_path or os.getenv("RECORDING_LOCAL_PATH", "./recordings")
        self.s3_bucket = s3_bucket or os.getenv("S3_RECORDINGS_BUCKET")

        # Create local directory if using local storage
        if self.storage_backend == StorageBackend.LOCAL:
            Path(self.local_path).mkdir(parents=True, exist_ok=True)

        # Initialize S3 client if using S3
        if self.storage_backend == StorageBackend.S3:
            if not S3_AVAILABLE:
                raise ImportError("boto3 is required for S3 storage")
            if not self.s3_bucket:
                raise ValueError("S3_RECORDINGS_BUCKET must be set for S3 storage")

            self.s3_client = boto3.client('s3')

        self.logger = logging.getLogger(f"{__name__}.RecordingManager")
        self.logger.info(f"RecordingManager initialized with {storage_backend.value} backend")

    def save_recording(
        self,
        session_id: str,
        audio_data: bytes,
        format: str = "wav"
    ) -> str:
        """
        Save recording to storage

        Args:
            session_id: Voice session identifier
            audio_data: Audio bytes to save
            format: Audio format (wav, mp3, etc.)

        Returns:
            URL or path to saved recording
        """
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_id}_{timestamp}.{format}"

        if self.storage_backend == StorageBackend.LOCAL:
            return self._save_local(filename, audio_data)
        elif self.storage_backend == StorageBackend.S3:
            return self._save_s3(filename, audio_data)
        else:
            raise ValueError(f"Unsupported storage backend: {self.storage_backend}")

    def _save_local(self, filename: str, audio_data: bytes) -> str:
        """
        Save recording to local filesystem

        Args:
            filename: Filename
            audio_data: Audio bytes

        Returns:
            Local file path
        """
        filepath = Path(self.local_path) / filename

        with open(filepath, 'wb') as f:
            f.write(audio_data)

        self.logger.info(f"Recording saved locally: {filepath}")
        return str(filepath)

    def _save_s3(self, filename: str, audio_data: bytes) -> str:
        """
        Save recording to S3

        Args:
            filename: Filename (S3 key)
            audio_data: Audio bytes

        Returns:
            S3 URL
        """
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=f"recordings/{filename}",
                Body=audio_data,
                ContentType="audio/wav"
            )

            url = f"s3://{self.s3_bucket}/recordings/{filename}"
            self.logger.info(f"Recording saved to S3: {url}")
            return url

        except Exception as e:
            self.logger.error(f"Error saving to S3: {e}")
            raise

    def get_recording(self, url: str) -> Optional[bytes]:
        """
        Retrieve recording from storage

        Args:
            url: Recording URL or path

        Returns:
            Audio bytes or None if not found
        """
        if url.startswith("s3://"):
            return self._get_s3(url)
        else:
            return self._get_local(url)

    def _get_local(self, filepath: str) -> Optional[bytes]:
        """
        Get recording from local filesystem

        Args:
            filepath: Local file path

        Returns:
            Audio bytes or None
        """
        try:
            with open(filepath, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.warning(f"Recording not found: {filepath}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading local recording: {e}")
            return None

    def _get_s3(self, url: str) -> Optional[bytes]:
        """
        Get recording from S3

        Args:
            url: S3 URL (s3://bucket/key)

        Returns:
            Audio bytes or None
        """
        try:
            # Parse S3 URL
            parts = url.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1]

            # Get object
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()

        except Exception as e:
            self.logger.error(f"Error reading from S3: {e}")
            return None

    def delete_recording(self, url: str) -> bool:
        """
        Delete recording from storage

        Args:
            url: Recording URL or path

        Returns:
            True if deleted successfully
        """
        if url.startswith("s3://"):
            return self._delete_s3(url)
        else:
            return self._delete_local(url)

    def _delete_local(self, filepath: str) -> bool:
        """
        Delete recording from local filesystem

        Args:
            filepath: Local file path

        Returns:
            True if deleted
        """
        try:
            Path(filepath).unlink()
            self.logger.info(f"Deleted local recording: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting local recording: {e}")
            return False

    def _delete_s3(self, url: str) -> bool:
        """
        Delete recording from S3

        Args:
            url: S3 URL

        Returns:
            True if deleted
        """
        try:
            # Parse S3 URL
            parts = url.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1]

            # Delete object
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            self.logger.info(f"Deleted S3 recording: {url}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting from S3: {e}")
            return False

    def convert_to_mp3(
        self,
        audio_data: bytes,
        sample_rate: int = 8000,
        channels: int = 1
    ) -> bytes:
        """
        Convert audio to MP3 format (compressed)

        Args:
            audio_data: Input audio bytes (PCM)
            sample_rate: Sample rate
            channels: Number of channels

        Returns:
            MP3 audio bytes
        """
        if not PYDUB_AVAILABLE:
            raise ImportError("pydub is required for MP3 conversion")

        # Create AudioSegment from raw PCM data
        audio = AudioSegment(
            data=audio_data,
            sample_width=2,  # 16-bit
            frame_rate=sample_rate,
            channels=channels
        )

        # Export to MP3
        output = io.BytesIO()
        audio.export(output, format="mp3", bitrate="64k")

        return output.getvalue()

    def convert_to_wav(
        self,
        audio_data: bytes,
        sample_rate: int = 8000,
        channels: int = 1
    ) -> bytes:
        """
        Convert audio to WAV format

        Args:
            audio_data: Input audio bytes (PCM)
            sample_rate: Sample rate
            channels: Number of channels

        Returns:
            WAV audio bytes
        """
        if not PYDUB_AVAILABLE:
            raise ImportError("pydub is required for WAV conversion")

        # Create AudioSegment from raw PCM data
        audio = AudioSegment(
            data=audio_data,
            sample_width=2,  # 16-bit
            frame_rate=sample_rate,
            channels=channels
        )

        # Export to WAV
        output = io.BytesIO()
        audio.export(output, format="wav")

        return output.getvalue()


# Convenience functions
def create_recorder(session_id: str) -> AudioRecorder:
    """
    Create an audio recorder for a session

    Args:
        session_id: Voice session identifier

    Returns:
        AudioRecorder instance
    """
    return AudioRecorder(session_id)


def save_call_recording(
    session_id: str,
    audio_data: bytes,
    format: str = "wav"
) -> str:
    """
    Save call recording using configured storage backend

    Args:
        session_id: Voice session identifier
        audio_data: Audio bytes
        format: Audio format

    Returns:
        Recording URL
    """
    # Determine storage backend from environment
    storage_type = os.getenv("RECORDING_STORAGE", "local")
    backend = StorageBackend.S3 if storage_type == "s3" else StorageBackend.LOCAL

    manager = RecordingManager(storage_backend=backend)
    return manager.save_recording(session_id, audio_data, format)
