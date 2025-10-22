"""
Database models for voice interactions
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class VoiceCall(Base):
    """Represents a voice call session"""

    __tablename__ = "voice_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    channel = Column(String(50), nullable=False)  # 'phone', 'webrtc', 'realtime'
    caller_id = Column(String(255), nullable=False, index=True)  # Phone number or user ID
    direction = Column(String(20), nullable=False)  # 'inbound', 'outbound'
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    status = Column(String(50), nullable=False, default='active')  # 'active', 'completed', 'failed', 'missed', 'abandoned'
    recording_url = Column(String(512), nullable=True)
    transcription = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    language = Column(String(10), default='en-US')
    tools_executed = Column(JSON, nullable=True)  # List of tool names used during call
    lead_id = Column(Integer, nullable=True)  # Reference to created lead
    reservation_id = Column(Integer, nullable=True)  # Reference to created reservation
    call_metadata = Column(JSON, nullable=True)  # Additional call metadata

    # Relationship to conversation turns
    conversation_turns = relationship("ConversationTurn", back_populates="call", cascade="all, delete-orphan")
    analytics = relationship("VoiceAnalytics", back_populates="call", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<VoiceCall(session_id='{self.session_id}', caller_id='{self.caller_id}', status='{self.status}')>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "channel": self.channel,
            "caller_id": self.caller_id,
            "direction": self.direction,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "recording_url": self.recording_url,
            "transcription": self.transcription,
            "sentiment_score": self.sentiment_score,
            "language": self.language,
            "tools_executed": self.tools_executed,
            "lead_id": self.lead_id,
            "reservation_id": self.reservation_id,
            "call_metadata": self.call_metadata,
        }


class ConversationTurn(Base):
    """Represents a single turn in a conversation"""

    __tablename__ = "conversation_turns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(Integer, ForeignKey('voice_calls.id'), nullable=False, index=True)
    turn_number = Column(Integer, nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    audio_url = Column(String(512), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    latency_ms = Column(Integer, nullable=True)  # Time taken to generate response
    turn_metadata = Column(JSON, nullable=True)

    # Relationship
    call = relationship("VoiceCall", back_populates="conversation_turns")

    def __repr__(self):
        return f"<ConversationTurn(turn={self.turn_number}, role='{self.role}', content='{self.content[:50]}...')>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "call_id": self.call_id,
            "turn_number": self.turn_number,
            "role": self.role,
            "content": self.content,
            "audio_url": self.audio_url,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "latency_ms": self.latency_ms,
            "turn_metadata": self.turn_metadata,
        }


class VoiceAnalytics(Base):
    """Stores analytics metrics for voice calls"""

    __tablename__ = "voice_analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(Integer, ForeignKey('voice_calls.id'), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    analytics_metadata = Column(JSON, nullable=True)

    # Relationship
    call = relationship("VoiceCall", back_populates="analytics")

    def __repr__(self):
        return f"<VoiceAnalytics(metric='{self.metric_name}', value={self.metric_value})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "call_id": self.call_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "analytics_metadata": self.analytics_metadata,
        }


# Metric name constants for consistency
class VoiceMetrics:
    """Standard metric names for voice analytics"""

    CALL_DURATION = "call_duration_seconds"
    RESPONSE_LATENCY = "response_latency_ms"
    STT_LATENCY = "stt_latency_ms"
    TTS_LATENCY = "tts_latency_ms"
    LLM_LATENCY = "llm_latency_ms"
    TOOL_EXECUTION_TIME = "tool_execution_ms"
    SENTIMENT_SCORE = "sentiment_score"
    INTERRUPTION_COUNT = "interruption_count"
    SILENCE_DURATION = "silence_duration_seconds"
    AUDIO_QUALITY = "audio_quality_score"
    TRANSCRIPTION_ACCURACY = "transcription_accuracy"
    CALL_SUCCESS = "call_success_rate"
    TOOL_SUCCESS = "tool_success_rate"
    GUEST_SATISFACTION = "guest_satisfaction_score"
