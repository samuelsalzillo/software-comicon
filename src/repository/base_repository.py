"""
Base Repository Pattern.

This module provides the base repository class and interfaces for database operations,
implementing the Repository Pattern for clean data access abstraction.
"""
import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from contextlib import contextmanager

from ..utils.database import get_lock, execute_with_retry
from ..exceptions import DatabaseError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository providing common database operations.

    This class implements the Repository Pattern, providing a clean abstraction
    over database operations with proper error handling and connection management.

    Type parameter T represents the entity type this repository manages.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize repository.

        Args:
            db_path: Path to SQLite database. Uses env var if not provided.
        """
        self.db_path = db_path or os.environ.get('SQLITE_DB_PATH', 'stand.db')
        self._lock = get_lock()
        logger.debug(f"{self.__class__.__name__} initialized with db: {self.db_path}")

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the table name this repository manages."""
        pass

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with proper cleanup.

        Yields:
            sqlite3.Connection: Database connection

        Example:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        conn = None
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row  # Enable column access by name
                yield conn
                conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error in {self.__class__.__name__}: {e}", exc_info=True)
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()

    def execute_query(
        self,
        query: str,
        params: tuple = (),
        fetch_one: bool = False,
        fetch_all: bool = True
    ) -> Optional[Any]:
        """
        Execute a query with proper error handling.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: If True, fetch only one result
            fetch_all: If True, fetch all results

        Returns:
            Query results or None

        Raises:
            DatabaseError: If query execution fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                execute_with_retry(cursor, query, params)

                if fetch_one:
                    result = cursor.fetchone()
                    return dict(result) if result else None
                elif fetch_all:
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    return cursor.lastrowid
        except Exception as e:
            logger.error(f"Query execution failed: {e}", exc_info=True)
            raise DatabaseError(f"Failed to execute query: {e}")

    # ============================================================================
    # CRUD OPERATIONS
    # ============================================================================

    def find_by_id(self, id_value: Any) -> Optional[Dict]:
        """
        Find entity by ID.

        Args:
            id_value: ID value to search for

        Returns:
            Entity dictionary or None if not found
        """
        query = f"SELECT * FROM {self.table_name} WHERE {self._get_id_column()} = ?"
        result = self.execute_query(query, (id_value,), fetch_one=True)

        if result:
            logger.debug(f"Found {self.table_name} with id={id_value}")
        else:
            logger.debug(f"No {self.table_name} found with id={id_value}")

        return result

    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """
        Find all entities with optional pagination.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entity dictionaries
        """
        query = f"SELECT * FROM {self.table_name}"

        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        results = self.execute_query(query, fetch_all=True)
        logger.debug(f"Found {len(results)} {self.table_name} records")
        return results

    def find_by_criteria(
        self,
        criteria: Dict[str, Any],
        limit: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict]:
        """
        Find entities matching criteria.

        Args:
            criteria: Dictionary of column-value pairs
            limit: Maximum number of results
            order_by: Column to order by (e.g., "created_at DESC")

        Returns:
            List of matching entity dictionaries
        """
        if not criteria:
            return self.find_all(limit=limit)

        where_clause = " AND ".join([f"{key} = ?" for key in criteria.keys()])
        query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        results = self.execute_query(query, tuple(criteria.values()), fetch_all=True)
        logger.debug(f"Found {len(results)} {self.table_name} matching criteria")
        return results

    def save(self, entity: Dict[str, Any]) -> int:
        """
        Save (insert or update) an entity.

        Args:
            entity: Entity dictionary with column-value pairs

        Returns:
            Last inserted/updated row ID
        """
        id_column = self._get_id_column()

        if id_column in entity and self.exists(entity[id_column]):
            return self.update(entity)
        else:
            return self.insert(entity)

    def insert(self, entity: Dict[str, Any]) -> int:
        """
        Insert a new entity.

        Args:
            entity: Entity dictionary

        Returns:
            Last inserted row ID
        """
        columns = ", ".join(entity.keys())
        placeholders = ", ".join(["?"] * len(entity))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"

        last_id = self.execute_query(query, tuple(entity.values()), fetch_all=False)
        logger.info(f"Inserted new {self.table_name} with id={last_id}")
        return last_id

    def update(self, entity: Dict[str, Any]) -> int:
        """
        Update an existing entity.

        Args:
            entity: Entity dictionary with ID

        Returns:
            Number of affected rows
        """
        id_column = self._get_id_column()

        if id_column not in entity:
            raise DatabaseError(f"Cannot update without {id_column}")

        id_value = entity[id_column]
        update_data = {k: v for k, v in entity.items() if k != id_column}

        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {id_column} = ?"

        params = tuple(update_data.values()) + (id_value,)
        self.execute_query(query, params, fetch_all=False)

        logger.info(f"Updated {self.table_name} with {id_column}={id_value}")
        return id_value

    def delete(self, id_value: Any) -> bool:
        """
        Delete an entity by ID.

        Args:
            id_value: ID of entity to delete

        Returns:
            True if deleted, False if not found
        """
        query = f"DELETE FROM {self.table_name} WHERE {self._get_id_column()} = ?"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_value,))
            deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted {self.table_name} with id={id_value}")
        else:
            logger.debug(f"No {self.table_name} found to delete with id={id_value}")

        return deleted

    def delete_by_criteria(self, criteria: Dict[str, Any]) -> int:
        """
        Delete entities matching criteria.

        Args:
            criteria: Dictionary of column-value pairs

        Returns:
            Number of deleted rows
        """
        if not criteria:
            raise DatabaseError("Cannot delete without criteria (safety check)")

        where_clause = " AND ".join([f"{key} = ?" for key in criteria.keys()])
        query = f"DELETE FROM {self.table_name} WHERE {where_clause}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(criteria.values()))
            deleted_count = cursor.rowcount

        logger.info(f"Deleted {deleted_count} {self.table_name} records matching criteria")
        return deleted_count

    def exists(self, id_value: Any) -> bool:
        """
        Check if entity exists by ID.

        Args:
            id_value: ID to check

        Returns:
            True if exists, False otherwise
        """
        query = f"SELECT 1 FROM {self.table_name} WHERE {self._get_id_column()} = ? LIMIT 1"
        result = self.execute_query(query, (id_value,), fetch_one=True)
        return result is not None

    def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities, optionally matching criteria.

        Args:
            criteria: Optional filter criteria

        Returns:
            Number of matching entities
        """
        if criteria:
            where_clause = " AND ".join([f"{key} = ?" for key in criteria.keys()])
            query = f"SELECT COUNT(*) as count FROM {self.table_name} WHERE {where_clause}"
            result = self.execute_query(query, tuple(criteria.values()), fetch_one=True)
        else:
            query = f"SELECT COUNT(*) as count FROM {self.table_name}"
            result = self.execute_query(query, fetch_one=True)

        return result['count'] if result else 0

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _get_id_column(self) -> str:
        """
        Get the name of the ID column.

        Override in subclasses if ID column is not 'id'.

        Returns:
            ID column name
        """
        return 'id'

    def execute_raw_query(
        self,
        query: str,
        params: tuple = ()
    ) -> List[Dict]:
        """
        Execute a raw SQL query.

        Use with caution! Prefer using the standard methods.

        Args:
            query: Raw SQL query
            params: Query parameters

        Returns:
            List of result dictionaries
        """
        logger.warning(f"Executing raw query on {self.table_name}: {query[:100]}...")
        return self.execute_query(query, params, fetch_all=True)

    def truncate(self) -> None:
        """
        Delete all records from the table.

        WARNING: This is irreversible!
        """
        query = f"DELETE FROM {self.table_name}"
        logger.warning(f"TRUNCATING table {self.table_name}")
        self.execute_query(query, fetch_all=False)

    def get_table_info(self) -> List[Dict]:
        """
        Get table schema information.

        Returns:
            List of column information dictionaries
        """
        query = f"PRAGMA table_info({self.table_name})"
        return self.execute_query(query, fetch_all=True)


class RepositoryFactory:
    """
    Factory for creating repository instances.

    Provides centralized repository creation with caching.
    """

    _repositories: Dict[str, BaseRepository] = {}

    @classmethod
    def get_repository(cls, repository_class: type, db_path: Optional[str] = None) -> BaseRepository:
        """
        Get or create a repository instance.

        Args:
            repository_class: Repository class to instantiate
            db_path: Optional database path

        Returns:
            Repository instance
        """
        key = f"{repository_class.__name__}_{db_path or 'default'}"

        if key not in cls._repositories:
            cls._repositories[key] = repository_class(db_path)
            logger.debug(f"Created new repository: {key}")

        return cls._repositories[key]

    @classmethod
    def clear_cache(cls):
        """Clear the repository cache."""
        cls._repositories.clear()
        logger.debug("Repository cache cleared")
