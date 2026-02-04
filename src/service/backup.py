"""
Database Backup Service.

This module handles automatic database backup operations with configurable
retention policies and scheduled execution.
"""
import glob
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..utils import timer

logger = logging.getLogger(__name__)


class BackupService:
    """
    Service for managing database backups.

    This class handles automatic backup creation, retention management,
    and scheduling of backup operations.
    """

    def __init__(
        self,
        db_path: str,
        backup_dir: str = 'backup',
        max_backups: int = 10,
        backup_interval: int = 3600
    ):
        """
        Initialize backup service.

        Args:
            db_path: Path to the database file to backup
            backup_dir: Directory where backups will be stored
            max_backups: Maximum number of backups to retain
            backup_interval: Backup interval in seconds
        """
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_interval = backup_interval

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"BackupService initialized: dir={backup_dir}, "
            f"max_backups={max_backups}, interval={backup_interval}s"
        )

    def create_backup(self) -> Optional[str]:
        """
        Create a new database backup.

        Returns:
            Path to the created backup file, or None if failed
        """
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"stand_db_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename

            # Verify source database exists
            if not os.path.exists(self.db_path):
                logger.error(f"Database file not found: {self.db_path}")
                return None

            # Perform backup
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Backup created successfully: {backup_filename}")

            # Clean up old backups
            self._cleanup_old_backups()

            return str(backup_path)

        except PermissionError as e:
            logger.error(f"Permission denied during backup: {e}")
            return None
        except IOError as e:
            logger.error(f"IO error during backup: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during backup: {e}", exc_info=True)
            return None

    def _cleanup_old_backups(self) -> None:
        """Remove old backups exceeding the maximum retention count."""
        try:
            # Find all backup files
            backup_pattern = str(self.backup_dir / 'stand_db_backup_*.db')
            backup_files = glob.glob(backup_pattern)

            # Sort by modification time (oldest first)
            backup_files.sort(key=os.path.getmtime)

            # Remove excess backups
            while len(backup_files) > self.max_backups:
                oldest_backup = backup_files.pop(0)
                try:
                    os.remove(oldest_backup)
                    logger.info(f"Removed old backup: {os.path.basename(oldest_backup)}")
                except OSError as e:
                    logger.error(f"Failed to remove old backup {oldest_backup}: {e}")

        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}", exc_info=True)

    def get_all_backups(self) -> List[dict]:
        """
        Get information about all existing backups.

        Returns:
            List of dictionaries with backup information
        """
        backup_pattern = str(self.backup_dir / 'stand_db_backup_*.db')
        backup_files = glob.glob(backup_pattern)
        backup_files.sort(key=os.path.getmtime, reverse=True)

        backups = []
        for backup_path in backup_files:
            backup_info = {
                'filename': os.path.basename(backup_path),
                'path': backup_path,
                'size_bytes': os.path.getsize(backup_path),
                'modified_time': datetime.fromtimestamp(os.path.getmtime(backup_path)),
                'created_time': datetime.fromtimestamp(os.path.getctime(backup_path))
            }
            backups.append(backup_info)

        return backups

    def restore_backup(self, backup_filename: str) -> bool:
        """
        Restore database from a backup file.

        Args:
            backup_filename: Name of the backup file to restore

        Returns:
            True if restore successful, False otherwise
        """
        try:
            backup_path = self.backup_dir / backup_filename

            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_filename}")
                return False

            # Create a safety backup of current database
            safety_backup = f"{self.db_path}.before_restore"
            shutil.copy2(self.db_path, safety_backup)
            logger.info(f"Created safety backup: {safety_backup}")

            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Database restored from: {backup_filename}")

            return True

        except Exception as e:
            logger.error(f"Failed to restore backup {backup_filename}: {e}", exc_info=True)
            return False

    def schedule_next_backup(self) -> None:
        """Schedule the next automatic backup."""
        timer.timer_for_thread(self.backup_interval, "backup")
        logger.debug(f"Next backup scheduled in {self.backup_interval} seconds")


# Global backup service instance
_backup_service: Optional[BackupService] = None


def initialize_backup_service(
    db_path: Optional[str] = None,
    backup_dir: str = 'backup',
    max_backups: Optional[int] = None,
    backup_interval: Optional[int] = None
) -> BackupService:
    """
    Initialize the global backup service instance.

    Args:
        db_path: Path to database (uses SQLITE_DB_PATH env var if not provided)
        backup_dir: Backup directory path
        max_backups: Maximum backups to retain (uses MAX_BACKUPS env var if not provided)
        backup_interval: Backup interval in seconds (uses BACKUP_INTERVAL env var if not provided)

    Returns:
        Initialized BackupService instance
    """
    global _backup_service

    if db_path is None:
        db_path = os.environ.get('SQLITE_DB_PATH', 'stand.db')

    if max_backups is None:
        max_backups = int(os.environ.get('MAX_BACKUPS', '10'))

    if backup_interval is None:
        backup_interval = int(os.environ.get('BACKUP_INTERVAL', '3600'))

    _backup_service = BackupService(
        db_path=db_path,
        backup_dir=backup_dir,
        max_backups=max_backups,
        backup_interval=backup_interval
    )

    return _backup_service


def get_backup_service() -> Optional[BackupService]:
    """Get the global backup service instance."""
    return _backup_service


def backup_database_auto() -> None:
    """
    Legacy automatic backup function.

    Deprecated: This function is kept for backward compatibility.
    Use BackupService class directly for new code.
    """
    try:
        service = get_backup_service()

        if service is None:
            # Initialize with environment variables if not already initialized
            service = initialize_backup_service()

        # Create backup
        backup_path = service.create_backup()

        if backup_path:
            logger.info("Automatic backup completed successfully")
        else:
            logger.error("Automatic backup failed")

    except Exception as e:
        logger.error(f"Error in automatic backup: {e}", exc_info=True)

    finally:
        # Schedule next backup
        if service:
            service.schedule_next_backup()

        # Recursive call for continuous backup
        backup_database_auto()

