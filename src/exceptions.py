"""
Custom Exceptions.

This module defines custom exception classes for the application,
providing better error handling and more informative error messages.
"""
from typing import Optional


class ComIconBaseException(Exception):
    """Base exception for all ComIcon application errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize exception.

        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation of the exception."""
        if self.details:
            details_str = ', '.join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class DatabaseError(ComIconBaseException):
    """Exception raised for database-related errors."""
    pass


class QueueError(ComIconBaseException):
    """Exception raised for queue-related errors."""
    pass


class TrackError(ComIconBaseException):
    """Exception raised for track-related errors."""
    pass


class PlayerNotFoundError(ComIconBaseException):
    """Exception raised when a player is not found."""

    def __init__(self, player_id: str, context: Optional[str] = None):
        """
        Initialize exception.

        Args:
            player_id: ID of the player that was not found
            context: Optional context where the player was being searched
        """
        message = f"Player '{player_id}' not found"
        if context:
            message += f" in {context}"
        super().__init__(message, {'player_id': player_id, 'context': context})
        self.player_id = player_id


class TrackOccupiedError(TrackError):
    """Exception raised when trying to use an occupied track."""

    def __init__(self, track_name: str, current_player_id: str):
        """
        Initialize exception.

        Args:
            track_name: Name of the occupied track
            current_player_id: ID of the player currently on the track
        """
        message = f"Track '{track_name}' is occupied by player '{current_player_id}'"
        super().__init__(message, {
            'track_name': track_name,
            'current_player_id': current_player_id
        })
        self.track_name = track_name
        self.current_player_id = current_player_id


class InvalidPlayerTypeError(ComIconBaseException):
    """Exception raised for invalid player type."""

    def __init__(self, player_type: str, valid_types: Optional[list] = None):
        """
        Initialize exception.

        Args:
            player_type: The invalid player type
            valid_types: Optional list of valid player types
        """
        message = f"Invalid player type: '{player_type}'"
        if valid_types:
            message += f". Valid types: {', '.join(valid_types)}"
        super().__init__(message, {
            'player_type': player_type,
            'valid_types': valid_types
        })
        self.player_type = player_type


class QualificationError(ComIconBaseException):
    """Exception raised for qualification-related errors."""
    pass


class BackupError(ComIconBaseException):
    """Exception raised for backup-related errors."""
    pass


class ConfigurationError(ComIconBaseException):
    """Exception raised for configuration errors."""
    pass


class ValidationError(ComIconBaseException):
    """Exception raised for data validation errors."""

    def __init__(self, field: str, message: str, value: Optional[any] = None):
        """
        Initialize exception.

        Args:
            field: Name of the field that failed validation
            message: Validation error message
            value: Optional value that failed validation
        """
        full_message = f"Validation error for '{field}': {message}"
        super().__init__(full_message, {
            'field': field,
            'value': value
        })
        self.field = field
        self.value = value


class TimingError(ComIconBaseException):
    """Exception raised for timing-related errors."""
    pass


class SchedulingError(ComIconBaseException):
    """Exception raised for scheduling-related errors."""
    pass
