"""
Voice session management

Handles the lifecycle of voice interactions including:
- Session creation and tracking
- Conversation state management
- Tool execution coordination
- Session persistence
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Voice session status"""
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class MessageRole(Enum):
    """Message role in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SessionDirection(Enum):
    """Direction of the voice interaction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


@dataclass
class Message:
    """Represents a message in a conversation"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    audio_url: Optional[str] = None
    latency_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "audio_url": self.audio_url,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
        }


@dataclass
class VoiceSession:
    """
    Represents a single voice interaction session

    Attributes:
        session_id: Unique identifier for the session
        channel: Communication channel ('phone', 'webrtc', 'realtime')
        caller_id: Identifier of the caller (phone number or user ID)
        start_time: When the session started
        end_time: When the session ended (None if active)
        status: Current session status
        conversation_history: List of messages exchanged
        tools_used: List of tool names executed during session
        recording_url: URL to the call recording
        language: Language code (e.g., 'en-US')
        metadata: Additional session metadata
    """
    session_id: str
    channel: str
    caller_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: SessionStatus = SessionStatus.ACTIVE
    conversation_history: List[Message] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    recording_url: Optional[str] = None
    language: str = "en-US"
    metadata: Dict[str, Any] = field(default_factory=dict)
    direction: SessionDirection = SessionDirection.INBOUND

    def add_message(self, role: str, content: str, **kwargs) -> None:
        """
        Add a message to the conversation history

        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            **kwargs: Additional message attributes (audio_url, latency_ms, etc.)
        """
        message = Message(role=role, content=content, **kwargs)
        self.conversation_history.append(message)
        logger.debug(f"Session {self.session_id}: Added {role} message: {content[:50]}...")

    def add_tool_usage(self, tool_name: str) -> None:
        """
        Record that a tool was used

        Args:
            tool_name: Name of the tool executed
        """
        if tool_name not in self.tools_used:
            self.tools_used.append(tool_name)
            logger.info(f"Session {self.session_id}: Used tool '{tool_name}'")

    def end_session(self, status: SessionStatus = SessionStatus.COMPLETED) -> None:
        """
        End the session

        Args:
            status: Final session status
        """
        self.end_time = datetime.utcnow()
        self.status = status
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"Session {self.session_id} ended with status {status.value} after {duration:.2f}s")

    def get_duration_seconds(self) -> float:
        """Get session duration in seconds"""
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()

    def get_turn_count(self) -> int:
        """Get number of conversation turns"""
        return len(self.conversation_history)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "channel": self.channel,
            "caller_id": self.caller_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value,
            "direction": self.direction.value,
            "conversation_history": [msg.to_dict() for msg in self.conversation_history],
            "tools_used": self.tools_used,
            "recording_url": self.recording_url,
            "language": self.language,
            "duration_seconds": self.get_duration_seconds(),
            "turn_count": self.get_turn_count(),
            "metadata": self.metadata,
        }


class SessionManager:
    """
    Manages voice sessions

    Provides methods to create, retrieve, update, and end sessions.
    Maintains in-memory cache of active sessions for fast access.
    """

    def __init__(self, db_session=None):
        """
        Initialize session manager

        Args:
            db_session: SQLAlchemy database session for persistence
        """
        self.db_session = db_session
        self._active_sessions: Dict[str, VoiceSession] = {}
        logger.info("SessionManager initialized")

    async def create_session(
        self,
        channel: str,
        caller_id: str,
        language: str = "en-US",
        metadata: Optional[Dict[str, Any]] = None,
        direction: Union[SessionDirection, str] = SessionDirection.INBOUND,
    ) -> VoiceSession:
        """
        Create a new voice session

        Args:
            channel: Communication channel ('phone', 'webrtc', 'realtime')
            caller_id: Identifier of the caller
            language: Language code
            metadata: Additional session metadata

        Returns:
            VoiceSession: The created session
        """
        session_id = str(uuid.uuid4())
        direction_enum = (
            direction
            if isinstance(direction, SessionDirection)
            else SessionDirection(direction)
        )

        session = VoiceSession(
            session_id=session_id,
            channel=channel,
            caller_id=caller_id,
            language=language,
            metadata=metadata or {},
            direction=direction_enum,
        )

        self._active_sessions[session_id] = session

        # Persist to database if available
        if self.db_session:
            await self._persist_session(session)

        logger.info(f"Created session {session_id} for caller {caller_id} on {channel}")
        return session

    async def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """
        Retrieve a session by ID

        Args:
            session_id: Session identifier

        Returns:
            VoiceSession or None if not found
        """
        # Check in-memory cache first
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]

        # Try loading from database
        if self.db_session:
            session = await self._load_session(session_id)
            if session:
                self._active_sessions[session_id] = session
                return session

        logger.warning(f"Session {session_id} not found")
        return None

    async def end_session(
        self,
        session_id: str,
        status: SessionStatus = SessionStatus.COMPLETED
    ) -> bool:
        """
        End a session

        Args:
            session_id: Session identifier
            status: Final session status

        Returns:
            bool: True if session was ended successfully
        """
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Cannot end session {session_id}: not found")
            return False

        session.end_session(status)

        # Persist final state
        if self.db_session:
            await self._persist_session(session)

        # Remove from active sessions
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

        logger.info(f"Ended session {session_id}")
        return True

    async def get_active_sessions(self) -> List[VoiceSession]:
        """
        Get all active sessions

        Returns:
            List of active VoiceSession objects
        """
        active = [
            session for session in self._active_sessions.values()
            if session.status == SessionStatus.ACTIVE
        ]
        logger.debug(f"Found {len(active)} active sessions")
        return active

    async def get_sessions_by_caller(self, caller_id: str) -> List[VoiceSession]:
        """
        Get all sessions for a specific caller

        Args:
            caller_id: Caller identifier

        Returns:
            List of VoiceSession objects
        """
        sessions = {
            session.session_id: session
            for session in self._active_sessions.values()
            if session.caller_id == caller_id
        }

        # Also load from database if available
        if self.db_session:
            db_sessions = await self._load_sessions_by_caller(caller_id)
            for session in db_sessions:
                sessions[session.session_id] = session

        logger.debug(f"Found {len(sessions)} sessions for caller {caller_id}")
        return list(sessions.values())

    async def update_session(self, session: VoiceSession) -> bool:
        """
        Update a session in memory and database

        Args:
            session: VoiceSession to update

        Returns:
            bool: True if update was successful
        """
        self._active_sessions[session.session_id] = session

        if self.db_session:
            success = await self._persist_session(session)
            return success

        return True

    async def _persist_session(self, session: VoiceSession) -> bool:
        """
        Persist session to database

        Args:
            session: VoiceSession to persist

        Returns:
            bool: True if successful
        """
        try:
            from packages.voice.models import ConversationTurn, VoiceCall

            call = (
                self.db_session.query(VoiceCall)
                .filter_by(session_id=session.session_id)
                .first()
            )

            if not call:
                call = VoiceCall(
                    session_id=session.session_id,
                    channel=session.channel,
                    caller_id=session.caller_id,
                    direction=session.direction.value,
                    start_time=session.start_time,
                    language=session.language,
                )
                self.db_session.add(call)
                self.db_session.flush()
            else:
                self.db_session.flush()

            call.end_time = session.end_time
            call.status = session.status.value
            call.recording_url = session.recording_url
            call.tools_executed = session.tools_used
            call.duration_seconds = int(session.get_duration_seconds())
            call.call_metadata = session.metadata
            call.direction = session.direction.value

            if call.id is not None:
                self.db_session.query(ConversationTurn).filter_by(call_id=call.id).delete(
                    synchronize_session=False
                )

            for idx, msg in enumerate(session.conversation_history):
                turn = ConversationTurn(
                    call_id=call.id,
                    turn_number=idx,
                    role=msg.role,
                    content=msg.content,
                    audio_url=msg.audio_url,
                    timestamp=msg.timestamp,
                    latency_ms=msg.latency_ms,
                    turn_metadata=msg.metadata,
                )
                self.db_session.add(turn)

            self.db_session.commit()
            logger.debug(f"Persisted session {session.session_id} to database")
            return True

        except Exception as e:
            logger.error(f"Failed to persist session {session.session_id}: {e}")
            self.db_session.rollback()
            return False

    async def _load_session(self, session_id: str) -> Optional[VoiceSession]:
        """
        Load session from database

        Args:
            session_id: Session identifier

        Returns:
            VoiceSession or None
        """
        try:
            from packages.voice.models import VoiceCall

            call = self.db_session.query(VoiceCall).filter_by(
                session_id=session_id
            ).first()

            if not call:
                return None

            return await self._build_session_from_call(call)

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    async def _load_sessions_by_caller(self, caller_id: str) -> List[VoiceSession]:
        """
        Load all sessions for a caller from database

        Args:
            caller_id: Caller identifier

        Returns:
            List of VoiceSession objects
        """
        try:
            from packages.voice.models import VoiceCall

            calls = (
                self.db_session.query(VoiceCall)
                .filter_by(caller_id=caller_id)
                .order_by(VoiceCall.start_time.desc())
                .all()
            )

            sessions: List[VoiceSession] = []
            for call in calls:
                session = await self._build_session_from_call(call)
                if session:
                    sessions.append(session)
            return sessions
        except Exception as e:
            logger.error(f"Failed to load sessions for caller {caller_id}: {e}")
            return []

    async def _build_session_from_call(self, call) -> Optional[VoiceSession]:
        """
        Helper to construct a VoiceSession from a VoiceCall ORM object.
        """
        try:
            try:
                status_value = SessionStatus(call.status)
            except ValueError:
                status_value = SessionStatus.ACTIVE

            direction_value = call.direction or SessionDirection.INBOUND.value
            session = VoiceSession(
                session_id=call.session_id,
                channel=call.channel,
                caller_id=call.caller_id,
                start_time=call.start_time,
                end_time=call.end_time,
                status=status_value,
                recording_url=call.recording_url,
                language=call.language,
                metadata=call.call_metadata or {},
                direction=SessionDirection(direction_value),
            )

            for turn in call.conversation_turns:
                session.conversation_history.append(
                    Message(
                        role=turn.role,
                        content=turn.content,
                        timestamp=turn.timestamp,
                        audio_url=turn.audio_url,
                        latency_ms=turn.latency_ms,
                        metadata=turn.turn_metadata,
                    )
                )

            if call.tools_executed:
                session.tools_used = call.tools_executed

            if call.end_time:
                session.end_time = call.end_time

            return session
        except Exception as exc:
            logger.error(f"Failed to build session from call {call.session_id}: {exc}")
            return None
