"""
Модуль содержит основные классы данных приложения.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class OperationType(Enum):
    """Типы финансовых операций."""
    INCOME = "Доход"
    EXPENSE = "Расход"

@dataclass
class Category:
    """Класс категории финансовой операции."""
    id: int
    name: str
    parent_id: Optional[int] = None
    
    def __str__(self):
        return self.name

@dataclass
class FinancialOperation:
    """Класс финансовой операции."""
    id: int
    amount: float
    operation_type: OperationType
    category: Category
    date: datetime
    description: str = ""
    
    def __post_init__(self):
        """Валидация данных после инициализации."""
        if self.amount <= 0:
            raise ValueError("Сумма операции должна быть положительной")
    
    @property
    def signed_amount(self) -> float:
        """Возвращает сумму со знаком."""
        return self.amount if self.operation_type == OperationType.INCOME else -self.amount
    
    def to_dict(self) -> dict:
        """Конвертирует операцию в словарь."""
        return {
            "id": self.id,
            "amount": self.amount,
            "type": self.operation_type.value,
            "category": self.category.name,
            "date": self.date.strftime("%Y-%m-%d %H:%M:%S"),
            "description": self.description
        }