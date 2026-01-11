"""
Модуль для работы с базой данных.
Поддерживает SQLite и PostgreSQL.
"""

import sqlite3
from typing import List, Optional, Tuple
from datetime import datetime, date
from contextlib import contextmanager
from models import FinancialOperation, Category, OperationType
import psycopg2
import os

class DatabaseManager:
    """Менеджер базы данных."""
    
    def __init__(self, db_type: str = "sqlite", db_name: str = "data/operations.db"):
        """
        Инициализирует менеджер базы данных.
        
        Args:
            db_type: Тип БД ('sqlite' или 'postgresql')
            db_name: Имя файла БД или строка подключения
        """
        self.db_type = db_type
        self.db_name = db_name
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Контекстный менеджер для получения соединения с БД."""
        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
        else:  # postgresql
            conn = psycopg2.connect(self.db_name)
            conn.autocommit = False
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """Инициализирует таблицы базы данных."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Создание таблицы категорий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    parent_id INTEGER,
                    FOREIGN KEY (parent_id) REFERENCES categories(id)
                )
            """)
            
            # Создание таблицы операций
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    category_id INTEGER NOT NULL,
                    date TIMESTAMP NOT NULL,
                    description TEXT,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            """)
            
            # Создание индексов для ускорения запросов
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_operations_date ON operations(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_operations_type ON operations(type)")
    
    def add_category(self, name: str, parent_id: Optional[int] = None) -> int:
        """Добавляет новую категорию."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO categories (name, parent_id) VALUES (?, ?)",
                (name, parent_id)
            )
            return cursor.lastrowid
    
    def get_all_categories(self) -> List[Category]:
        """Возвращает все категории."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, parent_id FROM categories ORDER BY name")
            return [
                Category(id=row[0], name=row[1], parent_id=row[2])
                for row in cursor.fetchall()
            ]
    
    def add_operation(self, operation: FinancialOperation) -> int:
        """Добавляет финансовую операцию."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO operations (amount, type, category_id, date, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                operation.amount,
                operation.operation_type.value,
                operation.category.id,
                operation.date,
                operation.description
            ))
            return cursor.lastrowid
    
    def get_operations(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[int] = None,
        operation_type: Optional[OperationType] = None
    ) -> List[FinancialOperation]:
        """Возвращает операции по фильтрам."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT o.id, o.amount, o.type, o.date, o.description,
                       c.id as cat_id, c.name as cat_name, c.parent_id
                FROM operations o
                JOIN categories c ON o.category_id = c.id
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND o.date >= ?"
                params.append(start_date.strftime("%Y-%m-%d"))
            
            if end_date:
                query += " AND o.date <= ?"
                params.append(end_date.strftime("%Y-%m-%d"))
            
            if category_id:
                query += " AND c.id = ?"
                params.append(category_id)
            
            if operation_type:
                query += " AND o.type = ?"
                params.append(operation_type.value)
            
            query += " ORDER BY o.date DESC"
            
            cursor.execute(query, params)
            
            operations = []
            for row in cursor.fetchall():
                category = Category(
                    id=row['cat_id'],
                    name=row['cat_name'],
                    parent_id=row['parent_id']
                )
                
                operation = FinancialOperation(
                    id=row['id'],
                    amount=row['amount'],
                    operation_type=OperationType(row['type']),
                    category=category,
                    date=datetime.strptime(row['date'], "%Y-%m-%d %H:%M:%S"),
                    description=row['description'] or ""
                )
                operations.append(operation)
            
            return operations
    
    def delete_operation(self, operation_id: int) -> bool:
        """Удаляет операцию по ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM operations WHERE id = ?", (operation_id,))
            return cursor.rowcount > 0
    
    def get_balance(self) -> float:
        """Рассчитывает текущий баланс."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN type = 'Доход' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type = 'Расход' THEN amount ELSE 0 END) as expense
                FROM operations
            """)
            row = cursor.fetchone()
            income = row[0] or 0
            expense = row[1] or 0
            return income - expense