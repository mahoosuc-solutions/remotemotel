"""
Unit tests for call recording
"""

import pytest
import os
import tempfile
from pathlib import Path
from packages.voice.recording import (
    AudioRecorder,
    RecordingManager,
    StorageBackend,
    create_recorder,
    save_call_recording
)


def test_audio_recorder_creation():
    """Test creating an AudioRecorder"""
    recorder = AudioRecorder(session_id="test-session-123")

    assert recorder.session_id == "test-session-123"
    assert recorder.sample_rate == 8000
    assert recorder.channels == 1
    assert recorder.is_recording is False


def test_audio_recorder_start():
    """Test starting a recording"""
    recorder = AudioRecorder("test-session")

    recorder.start()

    assert recorder.is_recording is True
    assert recorder.start_time is not None
    assert recorder.end_time is None


def test_audio_recorder_append():
    """Test appending audio data"""
    recorder = AudioRecorder("test-session")
    recorder.start()

    # Append some audio
    audio_data = b'\x00\x00' * 1000
    recorder.append(audio_data)

    assert recorder.get_size() == len(audio_data)


def test_audio_recorder_stop():
    """Test stopping a recording"""
    recorder = AudioRecorder("test-session")
    recorder.start()

    # Add some audio
    audio_data = b'\x00\x00' * 1000
    recorder.append(audio_data)

    # Stop recording
    recorded = recorder.stop()

    assert recorder.is_recording is False
    assert recorder.end_time is not None
    assert len(recorded) == len(audio_data)


def test_audio_recorder_duration():
    """Test recording duration calculation"""
    recorder = AudioRecorder("test-session")

    # Initially zero
    assert recorder.get_duration() == 0.0

    # Start recording
    recorder.start()

    # Duration should be small but non-zero
    import time
    time.sleep(0.1)

    duration = recorder.get_duration()
    assert duration > 0.0
    assert duration < 1.0  # Should be fraction of a second


def test_audio_recorder_without_start():
    """Test appending without starting"""
    recorder = AudioRecorder("test-session")

    # Should not append if not recording
    recorder.append(b'\x00\x00' * 100)

    assert recorder.get_size() == 0


def test_audio_recorder_multiple_append():
    """Test multiple append operations"""
    recorder = AudioRecorder("test-session")
    recorder.start()

    # Append multiple chunks
    chunk1 = b'\x00\x00' * 100
    chunk2 = b'\xFF\xFF' * 100
    chunk3 = b'\xAA\xAA' * 100

    recorder.append(chunk1)
    recorder.append(chunk2)
    recorder.append(chunk3)

    # Stop and check
    recorded = recorder.stop()

    assert len(recorded) == len(chunk1) + len(chunk2) + len(chunk3)


def test_recording_manager_local_storage():
    """Test RecordingManager with local storage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = RecordingManager(
            storage_backend=StorageBackend.LOCAL,
            local_path=tmpdir
        )

        assert manager.storage_backend == StorageBackend.LOCAL
        assert manager.local_path == tmpdir


def test_recording_manager_save_local():
    """Test saving recording to local storage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = RecordingManager(
            storage_backend=StorageBackend.LOCAL,
            local_path=tmpdir
        )

        # Create audio data
        audio_data = b'\x00\x00' * 1000

        # Save recording
        url = manager.save_recording(
            session_id="test-123",
            audio_data=audio_data,
            format="wav"
        )

        # Verify file exists
        assert Path(url).exists()
        assert Path(url).stat().st_size > 0


def test_recording_manager_retrieve_local():
    """Test retrieving recording from local storage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = RecordingManager(
            storage_backend=StorageBackend.LOCAL,
            local_path=tmpdir
        )

        # Save audio
        audio_data = b'\x00\x00\xFF\xFF' * 500
        url = manager.save_recording("test-456", audio_data)

        # Retrieve audio
        retrieved = manager.get_recording(url)

        assert retrieved is not None
        assert len(retrieved) == len(audio_data)


def test_recording_manager_delete_local():
    """Test deleting recording from local storage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = RecordingManager(
            storage_backend=StorageBackend.LOCAL,
            local_path=tmpdir
        )

        # Save audio
        audio_data = b'\x00\x00' * 1000
        url = manager.save_recording("test-delete", audio_data)

        # Verify exists
        assert Path(url).exists()

        # Delete
        success = manager.delete_recording(url)

        assert success is True
        assert not Path(url).exists()


def test_recording_manager_get_nonexistent():
    """Test retrieving nonexistent recording"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = RecordingManager(
            storage_backend=StorageBackend.LOCAL,
            local_path=tmpdir
        )

        # Try to get nonexistent file
        result = manager.get_recording("/nonexistent/file.wav")

        assert result is None


def test_create_recorder_helper():
    """Test create_recorder convenience function"""
    recorder = create_recorder("helper-test")

    assert recorder is not None
    assert recorder.session_id == "helper-test"


def test_save_call_recording_helper():
    """Test save_call_recording convenience function"""
    # Set local storage
    os.environ["RECORDING_STORAGE"] = "local"

    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["RECORDING_LOCAL_PATH"] = tmpdir

        audio_data = b'\x00\x00' * 1000
        url = save_call_recording("helper-session", audio_data)

        assert url is not None
        assert Path(url).exists()


def test_storage_backend_enum():
    """Test StorageBackend enum"""
    assert StorageBackend.LOCAL.value == "local"
    assert StorageBackend.S3.value == "s3"


def test_complete_recording_workflow():
    """Test complete recording workflow"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Create recorder
        recorder = AudioRecorder("workflow-test")

        # 2. Start recording
        recorder.start()
        assert recorder.is_recording

        # 3. Record audio chunks
        for i in range(10):
            chunk = b'\x00\x00' * 100
            recorder.append(chunk)

        # 4. Stop recording
        audio_data = recorder.stop()
        assert len(audio_data) == 2000  # 10 chunks * 100 samples * 2 bytes

        # 5. Save to storage
        manager = RecordingManager(
            storage_backend=StorageBackend.LOCAL,
            local_path=tmpdir
        )

        url = manager.save_recording("workflow-test", audio_data, format="wav")

        # 6. Verify saved
        assert Path(url).exists()

        # 7. Retrieve
        retrieved = manager.get_recording(url)
        assert len(retrieved) == len(audio_data)

        # 8. Get duration
        duration = recorder.get_duration()
        assert duration > 0


@pytest.mark.skipif(
    not hasattr(__import__('packages.voice.recording', fromlist=['PYDUB_AVAILABLE']), 'PYDUB_AVAILABLE') or
    not __import__('packages.voice.recording', fromlist=['PYDUB_AVAILABLE']).PYDUB_AVAILABLE,
    reason="Pydub not available"
)
def test_convert_to_mp3():
    """Test converting audio to MP3"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = RecordingManager(
            storage_backend=StorageBackend.LOCAL,
            local_path=tmpdir
        )

        # Create PCM audio
        pcm_audio = b'\x00\x00' * 8000  # 1 second at 8kHz

        # Convert to MP3
        mp3_audio = manager.convert_to_mp3(pcm_audio, sample_rate=8000, channels=1)

        assert mp3_audio is not None
        assert len(mp3_audio) > 0
        # MP3 should be compressed (smaller than PCM)
        assert len(mp3_audio) < len(pcm_audio)


@pytest.mark.skipif(
    not hasattr(__import__('packages.voice.recording', fromlist=['PYDUB_AVAILABLE']), 'PYDUB_AVAILABLE') or
    not __import__('packages.voice.recording', fromlist=['PYDUB_AVAILABLE']).PYDUB_AVAILABLE,
    reason="Pydub not available"
)
def test_convert_to_wav():
    """Test converting audio to WAV"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = RecordingManager(
            storage_backend=StorageBackend.LOCAL,
            local_path=tmpdir
        )

        # Create PCM audio
        pcm_audio = b'\x00\x00' * 8000

        # Convert to WAV
        wav_audio = manager.convert_to_wav(pcm_audio, sample_rate=8000, channels=1)

        assert wav_audio is not None
        assert len(wav_audio) > 0
        # WAV has header, so should be larger than raw PCM
        assert len(wav_audio) > len(pcm_audio)


def test_recorder_stop_without_start():
    """Test stopping recorder without starting"""
    recorder = AudioRecorder("no-start-test")

    # Stop without starting
    audio = recorder.stop()

    assert audio == b""
    assert not recorder.is_recording


def test_recorder_size_tracking():
    """Test recording size tracking"""
    recorder = AudioRecorder("size-test")
    recorder.start()

    # Initially zero
    assert recorder.get_size() == 0

    # Append and check
    recorder.append(b'\x00\x00' * 100)
    assert recorder.get_size() == 200

    recorder.append(b'\xFF\xFF' * 100)
    assert recorder.get_size() == 400
