"""
Base repository class providing common CRUD operations.
"""

import sqlite3
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from abc import ABC, abstractmethod
from datetime import datetime

from .connection import get_db_session, RecordNotFoundError, ValidationError

logger = logging.getLogger(__name__)

# Type variable for the model type
ModelType = TypeVar('ModelType')


class BaseRepository(Generic[ModelType], ABC):
    """
    Base repository class providing common CRUD operations.
    
    This class provides a template for database operations that can be
    inherited by specific entity repositories.
    """
    
    def __init__(self, table_name: str, model_class: Type[ModelType]):
        """
        Initialize the repository.
        
        Args:
            table_name: Name of the database table
            model_class: Pydantic model class for this entity
        """
        self.table_name = table_name
        self.model_class = model_class
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def _row_to_model(self, row: sqlite3.Row) -> ModelType:
        """
        Convert a database row to a model instance.
        
        Args:
            row: SQLite row object
            
        Returns:
            Model instance
        """
        pass
    
    @abstractmethod
    def _model_to_dict(self, model: ModelType, include_id: bool = True) -> Dict[str, Any]:
        """
        Convert a model instance to a dictionary for database insertion.
        
        Args:
            model: Model instance
            include_id: Whether to include the ID field
            
        Returns:
            Dictionary representation suitable for database operations
        """
        pass
    
    def create(self, model_data: Dict[str, Any]) -> int:
        """
        Create a new record in the database.
        
        Args:
            model_data: Data for the new record
            
        Returns:
            ID of the created record
            
        Raises:
            ValidationError: If data validation fails
            DatabaseError: If database operation fails
        """
        try:
            # Add timestamp
            if 'created_at' not in model_data:
                model_data['created_at'] = datetime.now()
            model_data['updated_at'] = datetime.now()
            
            # Build INSERT query
            columns = list(model_data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = list(model_data.values())
            
            query = f"""
                INSERT INTO {self.table_name} ({', '.join(columns)})
                VALUES ({placeholders})
            """
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                record_id = cursor.lastrowid
                
                self.logger.info(f"Created {self.table_name} record with ID: {record_id}")
                return record_id
                
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Integrity error creating {self.table_name}: {e}")
            raise ValidationError(f"Data validation failed: {e}")
        except sqlite3.Error as e:
            self.logger.error(f"Database error creating {self.table_name}: {e}")
            raise
    
    def get_by_id(self, record_id: int) -> Optional[ModelType]:
        """
        Get a record by its ID.
        
        Args:
            record_id: ID of the record to retrieve
            
        Returns:
            Model instance if found, None otherwise
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = ?"
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (record_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_model(row)
                return None
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting {self.table_name} by ID {record_id}: {e}")
            raise
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ModelType]:
        """
        Get all records from the table.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of model instances
        """
        try:
            query = f"SELECT * FROM {self.table_name} ORDER BY id"
            params = []
            
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                
                if offset > 0:
                    query += " OFFSET ?"
                    params.append(offset)
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_model(row) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting all {self.table_name}: {e}")
            raise
    
    def update(self, record_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update a record by its ID.
        
        Args:
            record_id: ID of the record to update
            update_data: Data to update
            
        Returns:
            True if record was updated, False if not found
            
        Raises:
            ValidationError: If data validation fails
        """
        try:
            # Add timestamp
            update_data['updated_at'] = datetime.now()
            
            # Build UPDATE query
            set_clauses = [f"{column} = ?" for column in update_data.keys()]
            values = list(update_data.values()) + [record_id]
            
            query = f"""
                UPDATE {self.table_name}
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Updated {self.table_name} record ID: {record_id}")
                    return True
                else:
                    self.logger.warning(f"{self.table_name} record not found for update: {record_id}")
                    return False
                    
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Integrity error updating {self.table_name}: {e}")
            raise ValidationError(f"Data validation failed: {e}")
        except sqlite3.Error as e:
            self.logger.error(f"Database error updating {self.table_name}: {e}")
            raise
    
    def delete(self, record_id: int) -> bool:
        """
        Delete a record by its ID.
        
        Args:
            record_id: ID of the record to delete
            
        Returns:
            True if record was deleted, False if not found
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE id = ?"
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (record_id,))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Deleted {self.table_name} record ID: {record_id}")
                    return True
                else:
                    self.logger.warning(f"{self.table_name} record not found for deletion: {record_id}")
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error(f"Database error deleting {self.table_name}: {e}")
            raise
    
    def exists(self, record_id: int) -> bool:
        """
        Check if a record exists by its ID.
        
        Args:
            record_id: ID of the record to check
            
        Returns:
            True if record exists, False otherwise
        """
        try:
            query = f"SELECT 1 FROM {self.table_name} WHERE id = ?"
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (record_id,))
                return cursor.fetchone() is not None
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error checking existence of {self.table_name}: {e}")
            raise
    
    def count(self, where_clause: str = "", params: List[Any] = None) -> int:
        """
        Count records in the table.
        
        Args:
            where_clause: Optional WHERE clause (without 'WHERE' keyword)
            params: Parameters for the WHERE clause
            
        Returns:
            Number of records
        """
        try:
            if params is None:
                params = []
                
            query = f"SELECT COUNT(*) FROM {self.table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error counting {self.table_name}: {e}")
            raise
    
    def find_by_criteria(self, criteria: Dict[str, Any], limit: Optional[int] = None) -> List[ModelType]:
        """
        Find records matching the given criteria.
        
        Args:
            criteria: Dictionary of column: value pairs
            limit: Maximum number of records to return
            
        Returns:
            List of matching model instances
        """
        try:
            if not criteria:
                return self.get_all(limit=limit)
            
            # Build WHERE clause
            where_clauses = [f"{column} = ?" for column in criteria.keys()]
            values = list(criteria.values())
            
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE {' AND '.join(where_clauses)}
                ORDER BY id
            """
            
            if limit is not None:
                query += " LIMIT ?"
                values.append(limit)
            
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                rows = cursor.fetchall()
                
                return [self._row_to_model(row) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error finding {self.table_name} by criteria: {e}")
            raise 