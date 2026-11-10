"""Abstract repository contract for storage operations."""

from abc import ABC, abstractmethod
from typing import Any


class BaseStorage(ABC):
    """Storage contract matching API and client function names."""

    @abstractmethod
    def session_submit(self, uid: int, data: dict[str, Any]) -> dict[str, Any]:
        """Creates a new session record."""

    @abstractmethod
    def session_pop(self, uid: int) -> bool:
        """Removes a session by uid."""

    @abstractmethod
    def session_search(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Filters sessions by query parameters."""

    @abstractmethod
    def session_adjust(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Updates session attributes."""

    @abstractmethod
    def instruction_submit(
        self, uid: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Creates instruction record."""

    @abstractmethod
    def instruction_pop(self, uid: int) -> bool:
        """Removes instruction record."""

    @abstractmethod
    def instruction_search(
        self, session_id: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Finds instructions belonging to a session."""

    @abstractmethod
    def instruction_adjust(
        self, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Updates instruction attributes."""

    @abstractmethod
    def response_search(
        self, instruction_id: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Finds responses associated with an instruction."""

    @abstractmethod
    def report_search(self) -> list[dict[str, Any]]:
        """Constructs relational report by formula 2."""
