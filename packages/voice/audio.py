"""
Audio processing pipeline for voice interactions

Handles:
- Audio codec conversion (μ-law, PCM, Opus)
- Voice Activity Detection (VAD)
- Audio buffering and chunking
- Format conversion
"""

import io
import base64
import logging
import struct
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, AsyncIterator, BinaryIO
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import optional audio libraries
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError as exc:
    raise ImportError(
        "NumPy is required for packages.voice.audio. Install it with `pip install numpy`."
    ) from exc

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError as exc:
    raise ImportError(
        "Pydub is required for audio format conversions. Install it with `pip install pydub`."
    ) from exc

try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError as exc:
    raise ImportError(
        "webrtcvad is required for Voice Activity Detection. Install it with `pip install webrtcvad`."
    ) from exc


class AudioCodec(Enum):
    """Supported audio codecs"""
    MULAW = "mulaw"  # μ-law (Twilio default)
    ALAW = "alaw"    # A-law
    PCM = "pcm"      # Linear PCM
    OPUS = "opus"    # Opus (WebRTC)
    MP3 = "mp3"      # MP3
    WAV = "wav"      # WAV container


class AudioFormat:
    """Audio format specification"""

    def __init__(
        self,
        codec: AudioCodec,
        sample_rate: int = 8000,
        channels: int = 1,
        sample_width: int = 2  # bytes per sample
    ):
        self.codec = codec
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width

    def __repr__(self):
        return f"AudioFormat({self.codec.value}, {self.sample_rate}Hz, {self.channels}ch, {self.sample_width * 8}bit)"


class AudioProcessor:
    """
    Process audio streams for voice interactions

    Handles codec conversion, buffering, and basic processing.
    """

    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(f"{__name__}.AudioProcessor")
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="audio")
        self.logger.info(f"AudioProcessor initialized with {max_workers} worker threads")

    def _mulaw_to_linear(self, mulaw_data: bytes) -> bytes:
        """
        Convert μ-law to linear PCM (replaces audioop.ulaw2lin)
        
        Args:
            mulaw_data: μ-law encoded audio bytes
            
        Returns:
            Linear PCM audio bytes (16-bit)
        """
        # μ-law to linear conversion table
        mulaw_table = [
            -32124, -31100, -30076, -29052, -28028, -27004, -25980, -24956,
            -23932, -22908, -21884, -20860, -19836, -18812, -17788, -16764,
            -15996, -15484, -14972, -14460, -13948, -13436, -12924, -12412,
            -11900, -11388, -10876, -10364, -9852, -9340, -8828, -8316,
            -7932, -7676, -7420, -7164, -6908, -6652, -6396, -6140,
            -5884, -5628, -5372, -5116, -4860, -4604, -4348, -4092,
            -3900, -3772, -3644, -3516, -3388, -3260, -3132, -3004,
            -2876, -2748, -2620, -2492, -2364, -2236, -2108, -1980,
            -1884, -1820, -1756, -1692, -1628, -1564, -1500, -1436,
            -1372, -1308, -1244, -1180, -1116, -1052, -988, -924,
            -876, -844, -812, -780, -748, -716, -684, -652,
            -620, -588, -556, -524, -492, -460, -428, -396,
            -372, -356, -340, -324, -308, -292, -276, -260,
            -244, -228, -212, -196, -180, -164, -148, -132,
            -120, -112, -104, -96, -88, -80, -72, -64,
            -56, -48, -40, -32, -24, -16, -8, 0,
            32124, 31100, 30076, 29052, 28028, 27004, 25980, 24956,
            23932, 22908, 21884, 20860, 19836, 18812, 17788, 16764,
            15996, 15484, 14972, 14460, 13948, 13436, 12924, 12412,
            11900, 11388, 10876, 10364, 9852, 9340, 8828, 8316,
            7932, 7676, 7420, 7164, 6908, 6652, 6396, 6140,
            5884, 5628, 5372, 5116, 4860, 4604, 4348, 4092,
            3900, 3772, 3644, 3516, 3388, 3260, 3132, 3004,
            2876, 2748, 2620, 2492, 2364, 2236, 2108, 1980,
            1884, 1820, 1756, 1692, 1628, 1564, 1500, 1436,
            1372, 1308, 1244, 1180, 1116, 1052, 988, 924,
            876, 844, 812, 780, 748, 716, 684, 652,
            620, 588, 556, 524, 492, 460, 428, 396,
            372, 356, 340, 324, 308, 292, 276, 260,
            244, 228, 212, 196, 180, 164, 148, 132,
            120, 112, 104, 96, 88, 80, 72, 64,
            56, 48, 40, 32, 24, 16, 8, 0
        ]
        
        pcm_data = bytearray()
        for byte in mulaw_data:
            pcm_data.extend(struct.pack('<h', mulaw_table[byte]))
        
        return bytes(pcm_data)

    def _linear_to_mulaw(self, pcm_data: bytes) -> bytes:
        """
        Convert linear PCM to μ-law (replaces audioop.lin2ulaw)
        
        Args:
            pcm_data: Linear PCM audio bytes (16-bit)
            
        Returns:
            μ-law encoded audio bytes
        """
        mulaw_data = bytearray()
        
        # Process 16-bit samples (2 bytes each)
        for i in range(0, len(pcm_data), 2):
            if i + 1 < len(pcm_data):
                # Unpack 16-bit signed integer (little-endian)
                sample = struct.unpack('<h', pcm_data[i:i+2])[0]
                
                # Convert to μ-law
                mulaw_byte = self._linear_sample_to_mulaw(sample)
                mulaw_data.append(mulaw_byte)
        
        return bytes(mulaw_data)

    def _linear_sample_to_mulaw(self, sample: int) -> int:
        """
        Convert a single linear PCM sample to μ-law
        
        Args:
            sample: 16-bit signed linear PCM sample
            
        Returns:
            μ-law byte
        """
        # Clamp to 14-bit range
        sample = max(-32768, min(32767, sample))
        
        # Get sign and magnitude
        sign = 0 if sample >= 0 else 0x80
        sample = abs(sample)
        
        # Add bias
        sample += 0x84
        
        # Find segment
        segment = 0
        if sample >= 0x1000:
            segment = 7
        elif sample >= 0x800:
            segment = 6
        elif sample >= 0x400:
            segment = 5
        elif sample >= 0x200:
            segment = 4
        elif sample >= 0x100:
            segment = 3
        elif sample >= 0x80:
            segment = 2
        elif sample >= 0x40:
            segment = 1
        
        # Quantize
        quantized = (sample >> (segment + 3)) & 0x0F
        
        # Combine sign, segment, and quantized value
        mulaw = sign | (segment << 4) | quantized
        
        return mulaw ^ 0xFF  # Invert all bits

    def _resample_audio(self, audio_data: bytes, from_rate: int, to_rate: int, sample_width: int) -> bytes:
        """
        Simple resampling (replaces audioop.ratecv)
        
        Args:
            audio_data: Input audio bytes
            from_rate: Source sample rate
            to_rate: Target sample rate
            sample_width: Bytes per sample
            
        Returns:
            Resampled audio bytes
        """
        if from_rate == to_rate:
            return audio_data
        
        # Simple linear interpolation resampling
        # This is a basic implementation - for production use, consider using a proper resampling library
        
        # Calculate the ratio
        ratio = to_rate / from_rate
        
        # Convert bytes to samples
        samples = []
        for i in range(0, len(audio_data), sample_width):
            if i + sample_width <= len(audio_data):
                if sample_width == 2:
                    sample = struct.unpack('<h', audio_data[i:i+sample_width])[0]
                elif sample_width == 4:
                    sample = struct.unpack('<i', audio_data[i:i+sample_width])[0]
                else:
                    sample = audio_data[i]
                samples.append(sample)
        
        # Resample
        resampled_samples = []
        for i in range(int(len(samples) * ratio)):
            # Linear interpolation
            src_index = i / ratio
            src_index_int = int(src_index)
            src_index_frac = src_index - src_index_int
            
            if src_index_int + 1 < len(samples):
                sample1 = samples[src_index_int]
                sample2 = samples[src_index_int + 1]
                interpolated = sample1 + (sample2 - sample1) * src_index_frac
            else:
                interpolated = samples[min(src_index_int, len(samples) - 1)]
            
            resampled_samples.append(int(interpolated))
        
        # Convert back to bytes
        resampled_data = bytearray()
        for sample in resampled_samples:
            if sample_width == 2:
                resampled_data.extend(struct.pack('<h', sample))
            elif sample_width == 4:
                resampled_data.extend(struct.pack('<i', sample))
            else:
                resampled_data.append(sample & 0xFF)
        
        return bytes(resampled_data)

    def cleanup(self):
        """Clean up thread pool executor"""
        self.logger.info("Shutting down AudioProcessor thread pool")
        self.executor.shutdown(wait=True)

    async def decode_mulaw_async(self, data: bytes, sample_rate: int = 8000) -> bytes:
        """
        Async version of decode_mulaw - offloads heavy processing to thread pool
        
        Args:
            data: μ-law encoded audio bytes
            sample_rate: Sample rate (default 8000 Hz)

        Returns:
            Linear PCM audio bytes
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.decode_mulaw, 
            data, 
            sample_rate
        )

    async def encode_mulaw_async(self, pcm_data: bytes) -> bytes:
        """
        Async version of encode_mulaw - offloads heavy processing to thread pool
        
        Args:
            pcm_data: Linear PCM audio bytes (16-bit)

        Returns:
            μ-law encoded audio bytes
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.encode_mulaw, 
            pcm_data
        )

    async def resample_async(
        self,
        audio_data: bytes,
        from_rate: int,
        to_rate: int,
        sample_width: int = 2
    ) -> bytes:
        """
        Async version of resample - offloads heavy processing to thread pool
        
        Args:
            audio_data: Input audio bytes
            from_rate: Source sample rate
            to_rate: Target sample rate
            sample_width: Bytes per sample (default 2 = 16-bit)

        Returns:
            Resampled audio bytes
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.resample, 
            audio_data, 
            from_rate, 
            to_rate, 
            sample_width
        )

    async def convert_format_async(
        self,
        audio_data: bytes,
        from_format: AudioFormat,
        to_format: AudioFormat
    ) -> bytes:
        """
        Async version of convert_format - offloads heavy processing to thread pool
        
        Args:
            audio_data: Input audio bytes
            from_format: Source format
            to_format: Target format

        Returns:
            Converted audio bytes
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.convert_format, 
            audio_data, 
            from_format, 
            to_format
        )

    def decode_mulaw(self, data: bytes, sample_rate: int = 8000) -> bytes:
        """
        Decode μ-law encoded audio to linear PCM

        Args:
            data: μ-law encoded audio bytes
            sample_rate: Sample rate (default 8000 Hz)

        Returns:
            Linear PCM audio bytes
        """
        try:
            # Custom μ-law to linear PCM conversion (replaces audioop.ulaw2lin)
            pcm_data = self._mulaw_to_linear(data)
            self.logger.debug(f"Decoded {len(data)} μ-law bytes to {len(pcm_data)} PCM bytes")
            return pcm_data
        except Exception as e:
            self.logger.error(f"Error decoding μ-law: {e}")
            raise

    def encode_mulaw(self, pcm_data: bytes) -> bytes:
        """
        Encode linear PCM to μ-law

        Args:
            pcm_data: Linear PCM audio bytes (16-bit)

        Returns:
            μ-law encoded audio bytes
        """
        try:
            # Custom linear PCM to μ-law conversion (replaces audioop.lin2ulaw)
            mulaw_data = self._linear_to_mulaw(pcm_data)
            self.logger.debug(f"Encoded {len(pcm_data)} PCM bytes to {len(mulaw_data)} μ-law bytes")
            return mulaw_data
        except Exception as e:
            self.logger.error(f"Error encoding μ-law: {e}")
            raise

    def decode_base64_mulaw(self, base64_data: str) -> bytes:
        """
        Decode base64-encoded μ-law audio (Twilio format)

        Args:
            base64_data: Base64-encoded μ-law audio

        Returns:
            Linear PCM audio bytes
        """
        try:
            # Decode base64
            mulaw_bytes = base64.b64decode(base64_data)

            # Convert μ-law to PCM
            pcm_bytes = self.decode_mulaw(mulaw_bytes)

            return pcm_bytes
        except Exception as e:
            self.logger.error(f"Error decoding base64 μ-law: {e}")
            raise

    def encode_base64_mulaw(self, pcm_data: bytes) -> str:
        """
        Encode PCM audio to base64-encoded μ-law (Twilio format)

        Args:
            pcm_data: Linear PCM audio bytes

        Returns:
            Base64-encoded μ-law string
        """
        try:
            # Convert PCM to μ-law
            mulaw_bytes = self.encode_mulaw(pcm_data)

            # Encode to base64
            base64_str = base64.b64encode(mulaw_bytes).decode('utf-8')

            return base64_str
        except Exception as e:
            self.logger.error(f"Error encoding base64 μ-law: {e}")
            raise

    def resample(
        self,
        audio_data: bytes,
        from_rate: int,
        to_rate: int,
        sample_width: int = 2
    ) -> bytes:
        """
        Resample audio to a different sample rate

        Args:
            audio_data: Input audio bytes
            from_rate: Source sample rate
            to_rate: Target sample rate
            sample_width: Bytes per sample (default 2 = 16-bit)

        Returns:
            Resampled audio bytes
        """
        try:
            if from_rate == to_rate:
                return audio_data

            # Custom resampling (replaces audioop.ratecv)
            resampled = self._resample_audio(audio_data, from_rate, to_rate, sample_width)

            self.logger.debug(f"Resampled from {from_rate}Hz to {to_rate}Hz")
            return resampled
        except Exception as e:
            self.logger.error(f"Error resampling audio: {e}")
            raise

    def convert_format(
        self,
        audio_data: bytes,
        from_format: AudioFormat,
        to_format: AudioFormat
    ) -> bytes:
        """
        Convert audio from one format to another

        Args:
            audio_data: Input audio bytes
            from_format: Source format
            to_format: Target format

        Returns:
            Converted audio bytes
        """
        if not PYDUB_AVAILABLE:
            self.logger.warning("Pydub not available - limited format conversion")
            # Fallback: just handle μ-law <-> PCM
            if from_format.codec == AudioCodec.MULAW and to_format.codec == AudioCodec.PCM:
                return self.decode_mulaw(audio_data, from_format.sample_rate)
            elif from_format.codec == AudioCodec.PCM and to_format.codec == AudioCodec.MULAW:
                return self.encode_mulaw(audio_data)
            else:
                raise NotImplementedError(f"Conversion from {from_format.codec} to {to_format.codec} requires pydub")

        try:
            # Use pydub for advanced conversions
            audio = AudioSegment(
                data=audio_data,
                sample_width=from_format.sample_width,
                frame_rate=from_format.sample_rate,
                channels=from_format.channels
            )

            # Convert sample rate if needed
            if from_format.sample_rate != to_format.sample_rate:
                audio = audio.set_frame_rate(to_format.sample_rate)

            # Convert channels if needed
            if from_format.channels != to_format.channels:
                audio = audio.set_channels(to_format.channels)

            # Export to target format
            output = io.BytesIO()
            audio.export(output, format=to_format.codec.value)

            self.logger.debug(f"Converted from {from_format} to {to_format}")
            return output.getvalue()

        except Exception as e:
            self.logger.error(f"Error converting audio format: {e}")
            raise

    def chunk_audio(
        self,
        audio_data: bytes,
        chunk_duration_ms: int = 20,
        sample_rate: int = 8000,
        sample_width: int = 2
    ) -> list[bytes]:
        """
        Split audio into chunks of fixed duration

        Args:
            audio_data: Audio bytes to chunk
            chunk_duration_ms: Chunk duration in milliseconds
            sample_rate: Audio sample rate
            sample_width: Bytes per sample

        Returns:
            List of audio chunks
        """
        # Calculate chunk size in bytes
        samples_per_chunk = int(sample_rate * chunk_duration_ms / 1000)
        bytes_per_chunk = samples_per_chunk * sample_width

        # Split into chunks
        chunks = []
        offset = 0
        while offset < len(audio_data):
            chunk = audio_data[offset:offset + bytes_per_chunk]
            if len(chunk) == bytes_per_chunk:
                chunks.append(chunk)
            offset += bytes_per_chunk

        self.logger.debug(f"Split {len(audio_data)} bytes into {len(chunks)} chunks of {chunk_duration_ms}ms")
        return chunks

    def to_numpy(self, audio_data: bytes, sample_width: int = 2) -> 'np.ndarray':
        """
        Convert audio bytes to numpy array

        Args:
            audio_data: Audio bytes
            sample_width: Bytes per sample

        Returns:
            NumPy array of audio samples
        """
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy is required for this operation")

        # Determine dtype based on sample width
        if sample_width == 1:
            dtype = np.uint8
        elif sample_width == 2:
            dtype = np.int16
        elif sample_width == 4:
            dtype = np.int32
        else:
            raise ValueError(f"Unsupported sample width: {sample_width}")

        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=dtype)
        return audio_array

    def from_numpy(self, audio_array: 'np.ndarray') -> bytes:
        """
        Convert numpy array to audio bytes

        Args:
            audio_array: NumPy array of audio samples

        Returns:
            Audio bytes
        """
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy is required for this operation")

        return audio_array.tobytes()


class VoiceActivityDetector:
    """
    Detect speech vs silence in audio using WebRTC VAD
    """

    def __init__(self, aggressiveness: int = 3):
        """
        Initialize VAD

        Args:
            aggressiveness: VAD aggressiveness (0-3, higher = more aggressive)
        """
        if not VAD_AVAILABLE:
            raise ImportError("webrtcvad is required for Voice Activity Detection")

        self.vad = webrtcvad.Vad(aggressiveness)
        self.logger = logging.getLogger(f"{__name__}.VoiceActivityDetector")
        self.logger.info(f"VAD initialized with aggressiveness={aggressiveness}")

    def is_speech(
        self,
        audio_data: bytes,
        sample_rate: int = 8000
    ) -> bool:
        """
        Detect if audio contains speech

        Args:
            audio_data: Audio bytes (PCM, 16-bit)
            sample_rate: Sample rate (must be 8000, 16000, 32000, or 48000)

        Returns:
            True if speech detected, False otherwise
        """
        if sample_rate not in [8000, 16000, 32000, 48000]:
            raise ValueError(f"Sample rate must be 8000, 16000, 32000, or 48000 (got {sample_rate})")

        # Frame duration must be 10, 20, or 30 ms
        # Calculate frame size for 30ms
        frame_duration_ms = 30
        samples_per_frame = int(sample_rate * frame_duration_ms / 1000)
        bytes_per_frame = samples_per_frame * 2  # 16-bit = 2 bytes

        # Check if we have enough data
        if len(audio_data) < bytes_per_frame:
            return False

        # Take first frame
        frame = audio_data[:bytes_per_frame]

        try:
            return self.vad.is_speech(frame, sample_rate)
        except Exception as e:
            self.logger.error(f"Error in VAD: {e}")
            return False

    def detect_speech_segments(
        self,
        audio_chunks: list[bytes],
        sample_rate: int = 8000,
        padding_chunks: int = 2
    ) -> list[tuple[int, int]]:
        """
        Detect speech segments in a list of audio chunks

        Args:
            audio_chunks: List of audio chunks
            sample_rate: Sample rate
            padding_chunks: Number of chunks to pad around speech

        Returns:
            List of (start_chunk, end_chunk) tuples for speech segments
        """
        segments = []
        in_speech = False
        speech_start = 0

        for i, chunk in enumerate(audio_chunks):
            is_speech = self.is_speech(chunk, sample_rate)

            if is_speech and not in_speech:
                # Speech started
                speech_start = max(0, i - padding_chunks)
                in_speech = True

            elif not is_speech and in_speech:
                # Speech ended
                speech_end = min(len(audio_chunks), i + padding_chunks)
                segments.append((speech_start, speech_end))
                in_speech = False

        # Handle case where speech continues to end
        if in_speech:
            segments.append((speech_start, len(audio_chunks)))

        self.logger.info(f"Detected {len(segments)} speech segments")
        return segments


class AudioBuffer:
    """
    Buffer for accumulating audio data
    """

    def __init__(self, max_size: int = 1024 * 1024):  # 1MB default
        """
        Initialize audio buffer

        Args:
            max_size: Maximum buffer size in bytes
        """
        self.buffer = io.BytesIO()
        self.max_size = max_size
        self.logger = logging.getLogger(f"{__name__}.AudioBuffer")

    def append(self, data: bytes) -> None:
        """
        Append audio data to buffer

        Args:
            data: Audio bytes to append
        """
        current_size = self.buffer.tell()
        if current_size + len(data) > self.max_size:
            self.logger.warning(f"Buffer overflow: {current_size + len(data)} > {self.max_size}")
            # Keep only the most recent data
            self.buffer.seek(len(data))
            self.buffer.truncate()
            self.buffer.write(data)
        else:
            self.buffer.write(data)

    def get_data(self) -> bytes:
        """
        Get all buffered data

        Returns:
            All buffered audio bytes
        """
        return self.buffer.getvalue()

    def clear(self) -> None:
        """Clear the buffer"""
        self.buffer = io.BytesIO()

    def size(self) -> int:
        """
        Get current buffer size

        Returns:
            Buffer size in bytes
        """
        return self.buffer.tell()


# Convenience functions
def decode_twilio_audio(base64_payload: str) -> bytes:
    """
    Decode Twilio audio payload (base64 μ-law) to PCM

    Args:
        base64_payload: Base64-encoded μ-law audio from Twilio

    Returns:
        Linear PCM audio bytes
    """
    processor = AudioProcessor()
    return processor.decode_base64_mulaw(base64_payload)


def encode_twilio_audio(pcm_data: bytes) -> str:
    """
    Encode PCM audio to Twilio format (base64 μ-law)

    Args:
        pcm_data: Linear PCM audio bytes

    Returns:
        Base64-encoded μ-law string for Twilio
    """
    processor = AudioProcessor()
    return processor.encode_base64_mulaw(pcm_data)


def detect_speech(audio_data: bytes, sample_rate: int = 8000) -> bool:
    """
    Quick speech detection

    Args:
        audio_data: Audio bytes (PCM, 16-bit)
        sample_rate: Sample rate

    Returns:
        True if speech detected
    """
    if not VAD_AVAILABLE:
        logger.warning("VAD not available - assuming speech")
        return True

    try:
        vad = VoiceActivityDetector()
        return vad.is_speech(audio_data, sample_rate)
    except Exception as e:
        logger.error(f"Error in speech detection: {e}")
        return False


# Convenience functions for relay
def mulaw_decode(mulaw_bytes: bytes) -> bytes:
    """
    Decode μ-law bytes to PCM16

    Args:
        mulaw_bytes: μ-law encoded audio

    Returns:
        PCM16 audio bytes
    """
    processor = AudioProcessor()
    return processor.decode_mulaw(mulaw_bytes)


def mulaw_encode(pcm_bytes: bytes) -> bytes:
    """
    Encode PCM16 to μ-law bytes

    Args:
        pcm_bytes: PCM16 audio bytes

    Returns:
        μ-law encoded audio
    """
    processor = AudioProcessor()
    return processor.encode_mulaw(pcm_bytes)


def resample_audio(
    audio_data: bytes,
    from_rate: int,
    to_rate: int
) -> bytes:
    """
    Resample audio between different sample rates

    Args:
        audio_data: Input PCM16 audio
        from_rate: Source sample rate (Hz)
        to_rate: Target sample rate (Hz)

    Returns:
        Resampled PCM16 audio
    """
    processor = AudioProcessor()
    return processor.resample(audio_data, from_rate, to_rate, sample_width=2)


# Async convenience functions
async def decode_twilio_audio_async(base64_payload: str) -> bytes:
    """
    Async version: Decode Twilio audio payload (base64 μ-law) to PCM

    Args:
        base64_payload: Base64-encoded μ-law audio from Twilio

    Returns:
        Linear PCM audio bytes
    """
    processor = AudioProcessor()
    mulaw_bytes = base64.b64decode(base64_payload)
    return await processor.decode_mulaw_async(mulaw_bytes)


async def encode_twilio_audio_async(pcm_data: bytes) -> str:
    """
    Async version: Encode PCM audio to Twilio format (base64 μ-law)

    Args:
        pcm_data: Linear PCM audio bytes

    Returns:
        Base64-encoded μ-law string for Twilio
    """
    processor = AudioProcessor()
    mulaw_bytes = await processor.encode_mulaw_async(pcm_data)
    return base64.b64encode(mulaw_bytes).decode('utf-8')


async def resample_audio_async(
    audio_data: bytes,
    from_rate: int,
    to_rate: int
) -> bytes:
    """
    Async version: Resample audio between different sample rates

    Args:
        audio_data: Input PCM16 audio
        from_rate: Source sample rate (Hz)
        to_rate: Target sample rate (Hz)

    Returns:
        Resampled PCM16 audio
    """
    processor = AudioProcessor()
    return await processor.resample_async(audio_data, from_rate, to_rate, sample_width=2)
