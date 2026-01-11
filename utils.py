"""
Вспомогательные функции и валидация данных.
Использует регулярные выражения для проверки корректности данных.
"""

import re
from datetime import datetime, date
from typing import Optional, Tuple
from decimal import Decimal, InvalidOperation

class Validator:
    """Класс для валидации данных."""
    
    # Регулярные выражения для валидации
    DATE_PATTERN = r'^\d{4}-\d{2}-\d{2}$'
    TIME_PATTERN = r'^\d{2}:\d{2}$'
    AMOUNT_PATTERN = r'^\d+(\.\d{1,2})?$'
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, Optional[date]]:
        """
        Валидирует дату в формате YYYY-MM-DD.
        
        Args:
            date_str: Строка с датой
            
        Returns:
            Кортеж (валидна ли дата, объект date или None)
        """
        if not re.match(Validator.DATE_PATTERN, date_str):
            return False, None
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            if date_obj > datetime.now().date():
                return False, None
            return True, date_obj
        except ValueError:
            return False, None
    
    @staticmethod
    def validate_amount(amount_str: str) -> Tuple[bool, Optional[float]]:
        """
        Валидирует денежную сумму.
        
        Args:
            amount_str: Строка с суммой
            
        Returns:
            Кортеж (валидна ли сумма, число или None)
        """
        # Убираем пробелы и заменяем запятые на точки
        amount_str = amount_str.replace(' ', '').replace(',', '.')
        
        if not re.match(Validator.AMOUNT_PATTERN, amount_str):
            return False, None
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                return False, None
            return True, round(amount, 2)
        except ValueError:
            return False, None
    
    @staticmethod
    def validate_category_name(name: str) -> bool:
        """
        Валидирует название категории.
        
        Args:
            name: Название категории
            
        Returns:
            True если валидно, False в противном случае
        """
        if not name or len(name.strip()) == 0:
            return False
        if len(name) > 50:
            return False
        # Проверяем, что название содержит только буквы, цифры и пробелы
        if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-_]+$', name):
            return False
        return True
    
    @staticmethod
    def validate_description(description: str) -> Tuple[bool, str]:
        """
        Валидирует и очищает описание.
        
        Args:
            description: Описание операции
            
        Returns:
            Кортеж (валидно ли описание, очищенное описание)
        """
        if not description:
            return True, ""
        
        # Очищаем от лишних пробелов
        cleaned = ' '.join(description.strip().split())
        
        # Проверяем длину
        if len(cleaned) > 200:
            return False, ""
        
        # Убираем потенциально опасные символы
        cleaned = re.sub(r'[<>{}]', '', cleaned)
        
        return True, cleaned
    
    @staticmethod
    def extract_amounts_from_text(text: str) -> List[float]:
        """
        Извлекает денежные суммы из текста.
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список найденных сумм
        """
        # Паттерн для поиска сумм в тексте
        pattern = r'\d+(?:[.,]\d{1,2})?(?=\s*(?:руб|р|USD|EUR|₽|\$|€))'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        amounts = []
        for match in matches:
            # Нормализуем формат числа
            normalized = match.replace(',', '.')
            try:
                amount = float(normalized)
                amounts.append(amount)
            except ValueError:
                continue
        
        return amounts

class Formatter:
    """Класс для форматирования данных."""
    
    @staticmethod
    def format_amount(amount: float) -> str:
        """
        Форматирует денежную сумму.
        
        Args:
            amount: Сумма
            
        Returns:
            Отформатированная строка
        """
        return f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
    
    @staticmethod
    def format_date(date_obj: datetime) -> str:
        """
        Форматирует дату.
        
        Args:
            date_obj: Объект datetime
            
        Returns:
            Отформатированная строка
        """
        return date_obj.strftime('%d.%m.%Y %H:%M')
    
    @staticmethod
    def format_period(start_date: date, end_date: date) -> str:
        """
        Форматирует период.
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            
        Returns:
            Отформатированная строка периода
        """
        return f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"