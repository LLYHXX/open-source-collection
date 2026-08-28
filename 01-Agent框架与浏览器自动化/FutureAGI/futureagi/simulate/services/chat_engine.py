"""ChatServiceBlueprint — abstract engine contract for chat providers.

Mirrors VoiceServiceBlueprint pattern. All provider-specific implementations
(VapiChatService, FutureAGIChatService, etc.) extend this class.

Only methods that EVERY engine must implement are declared here.
Provider-specific methods live on the concrete engine classes directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import structlog

from simulate.services.types.chat import (
    CreateAssistantInput,
    CreateAssistantResult,
    CreateSessionInput,
    CreateSessionResult,
    DeleteAssistantInput,
    DeleteAssistantResult,
    GetSessionInput,
    GetSessionResult,
    SendMessageInput,
    SendMessageResult,
)

logger = structlog.get_logger(__name__)


class ChatServiceBlueprint(ABC):
    """Abstract base for chat service engines.

    To add a new provider, subclass this and implement every @abstractmethod.
    Then register the class in ChatServiceManager.ENGINE_REGISTRY.
    """

    # ------------------------------------------------------------------
    # Abstract methods — the engine contract for ChatServiceManager
    # ------------------------------------------------------------------

    @abstractmethod
    def create_assistant(self, input: CreateAssistantInput) -> CreateAssistantResult:
        """Create a chat assistant (simulator persona) with the provider.

        Args:
            input: Assistant configuration including name, system_prompt, etc.

        Returns:
            CreateAssistantResult with assistant_id on success.
        """
        ...

    @abstractmethod
    def delete_assistant(self, input: DeleteAssistantInput) -> DeleteAssistantResult:
        """Delete a chat assistant.

        Args:
            input: Contains assistant_id to delete.

        Returns:
            DeleteAssistantResult indicating success/failure.
        """
        ...

    @abstractmethod
    def create_session(self, input: CreateSessionInput) -> CreateSessionResult:
        """Create a new chat session.

        Args:
            input: Session configuration including assistant_id, name, initial_message.

        Returns:
            CreateSessionResult with session_id and initial messages on success.
        """
        ...

    @abstractmethod
    def get_session(self, input: GetSessionInput) -> GetSessionResult:
        """Retrieve an existing chat session.

        Args:
            input: Contains session_id to retrieve.

        Returns:
            GetSessionResult with session details and message history.
        """
        ...

    @abstractmethod
    def send_message(self, input: SendMessageInput) -> SendMessageResult:
        """Send message(s) to a chat session and get response.

        Args:
            input: Contains session_id and messages to send.

        Returns:
            SendMessageResult with input/output messages and has_chat_ended flag.
        """
        ...

    @abstractmethod
    async def send_message_async(self, input: SendMessageInput) -> SendMessageResult:
        """Async version of send_message.

        Args:
            input: Contains session_id and messages to send.

        Returns:
            SendMessageResult with input/output messages and has_chat_ended flag.
        """
        ...

    def validate_configuration(self) -> bool:
        """Validate the service configuration (API keys, etc.).

        Default implementation returns True. Override in subclasses that
        require explicit key validation (e.g. VapiChatService).
        """
        return True
