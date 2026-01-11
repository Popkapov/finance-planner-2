"""
Модуль unit-тестов для приложения.
"""

import unittest
import tempfile
import os
from datetime import datetime, date
from decimal import Decimal

from models import FinancialOperation, Category, OperationType
from database import DatabaseManager
from analysis import FinancialAnalyzer
from utils import Validator, Formatter
from storage import DataStorage

class TestModels(unittest.TestCase):
    """Тесты для моделей данных."""
    
    def test_operation_creation(self):
        """Тест создания операции."""
        category = Category(id=1, name="Продукты")
        operation = FinancialOperation(
            id=1,
            amount=100.50,
            operation_type=OperationType.EXPENSE,
            category=category,
            date=datetime.now(),
            description="Покупки в магазине"
        )
        
        self.assertEqual(operation.id, 1)
        self.assertEqual(operation.amount, 100.50)
        self.assertEqual(operation.operation_type, OperationType.EXPENSE)
        self.assertEqual(operation.category.name, "Продукты")
        self.assertEqual(operation.signed_amount, -100.50)
    
    def test_operation_validation(self):
        """Тест валидации операции."""
        category = Category(id=1, name="Продукты")
        
        with self.assertRaises(ValueError):
            FinancialOperation(
                id=1,
                amount=-100,
                operation_type=OperationType.EXPENSE,
                category=category,
                date=datetime.now()
            )
    
    def test_operation_to_dict(self):
        """Тест конвертации операции в словарь."""
        category = Category(id=1, name="Продукты")
        operation = FinancialOperation(
            id=1,
            amount=100.50,
            operation_type=OperationType.INCOME,
            category=category,
            date=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        result = operation.to_dict()
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['amount'], 100.50)
        self.assertEqual(result['type'], "Доход")
        self.assertEqual(result['category'], "Продукты")

class TestDatabase(unittest.TestCase):
    """Тесты для базы данных."""
    
    def setUp(self):
        """Настройка тестовой базы данных."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_manager = DatabaseManager(db_type="sqlite", db_name=self.temp_db.name)
    
    def tearDown(self):
        """Очистка после тестов."""
        self.temp_db.close()
        os.unlink(self.temp_db.name)
    
    def test_add_and_get_categories(self):
        """Тест добавления и получения категорий."""
        category_id = self.db_manager.add_category("Тестовая категория")
        self.assertIsNotNone(category_id)
        
        categories = self.db_manager.get_all_categories()
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0].name, "Тестовая категория")
    
    def test_add_and_get_operations(self):
        """Тест добавления и получения операций."""
        # Добавляем категорию
        category_id = self.db_manager.add_category("Продукты")
        category = Category(id=category_id, name="Продукты")
        
        # Добавляем операцию
        operation = FinancialOperation(
            id=0,
            amount=100.50,
            operation_type=OperationType.EXPENSE,
            category=category,
            date=datetime.now(),
            description="Тестовая покупка"
        )
        
        operation_id = self.db_manager.add_operation(operation)
        self.assertIsNotNone(operation_id)
        
        # Получаем операции
        operations = self.db_manager.get_operations()
        self.assertEqual(len(operations), 1)
        self.assertEqual(operations[0].amount, 100.50)

class TestValidator(unittest.TestCase):
    """Тесты для валидатора."""
    
    def test_validate_date(self):
        """Тест валидации даты."""
        # Корректная дата
        valid, date_obj = Validator.validate_date("2024-01-15")
        self.assertTrue(valid)
        self.assertEqual(date_obj, date(2024, 1, 15))
        
        # Некорректная дата
        valid, date_obj = Validator.validate_date("15-01-2024")
        self.assertFalse(valid)
        self.assertIsNone(date_obj)
        
        # Дата в будущем
        future_date = "2030-01-01"
        valid, date_obj = Validator.validate_date(future_date)
        self.assertFalse(valid)
    
    def test_validate_amount(self):
        """Тест валидации суммы."""
        # Корректные суммы
        test_cases = [
            ("100", True, 100.0),
            ("100.50", True, 100.5),
            ("1,000.50", True, 1000.5),
            ("100,50", True, 100.5)
        ]
        
        for amount_str, expected_valid, expected_value in test_cases:
            valid, value = Validator.validate_amount(amount_str)
            self.assertEqual(valid, expected_valid)
            if expected_valid:
                self.assertEqual(value, expected_value)
        
        # Некорректные суммы
        invalid_cases = ["-100", "abc", "100.", ""]
        for amount_str in invalid_cases:
            valid, value = Validator.validate_amount(amount_str)
            self.assertFalse(valid)
    
    def test_extract_amounts_from_text(self):
        """Тест извлечения сумм из текста."""
        text = "Купил продукты на 1000 руб и заплатил за услуги 1500.50 р."
        amounts = Validator.extract_amounts_from_text(text)
        self.assertIn(1000.0, amounts)
        self.assertIn(1500.5, amounts)

class TestAnalyzer(unittest.TestCase):
    """Тесты для анализатора."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.operations = []
        category = Category(id=1, name="Тест")
        
        # Добавляем тестовые операции
        for i in range(5):
            op_type = OperationType.INCOME if i % 2 == 0 else OperationType.EXPENSE
            operation = FinancialOperation(
                id=i + 1,
                amount=100 * (i + 1),
                operation_type=op_type,
                category=category,
                date=datetime(2024, 1, i + 1),
                description=f"Тестовая операция {i + 1}"
            )
            self.operations.append(operation)
        
        self.analyzer = FinancialAnalyzer(self.operations)
    
    def test_to_dataframe(self):
        """Тест конвертации в DataFrame."""
        df = self.analyzer.to_dataframe()
        self.assertEqual(len(df), 5)
        self.assertIn('amount', df.columns)
        self.assertIn('type', df.columns)
    
    def test_category_stats(self):
        """Тест статистики по категориям."""
        stats = self.analyzer.get_category_stats(OperationType.EXPENSE)
        self.assertIsNotNone(stats)
        
        if len(stats) > 0:
            self.assertIn('Категория', stats.columns)
            self.assertIn('Сумма', stats.columns)
    
    def test_get_balance_by_period(self):
        """Тест расчета баланса за период."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)
        
        balance = self.analyzer.get_balance_by_period(start_date, end_date)
        self.assertIn('income', balance)
        self.assertIn('expense', balance)
        self.assertIn('balance', balance)

class TestStorage(unittest.TestCase):
    """Тесты для работы с файлами."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.temp_dir = tempfile.mkdtemp()
        category = Category(id=1, name="Тест")
        
        self.operations = [
            FinancialOperation(
                id=1,
                amount=100.50,
                operation_type=OperationType.INCOME,
                category=category,
                date=datetime(2024, 1, 1),
                description="Тест"
            )
        ]
    
    def test_export_import_csv(self):
        """Тест экспорта и импорта CSV."""
        # Экспорт
        csv_path = os.path.join(self.temp_dir, "test.csv")
        success = DataStorage.export_to_csv(self.operations, csv_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(csv_path))
        
        # Импорт
        imported = DataStorage.import_from_csv(csv_path)
        self.assertEqual(len(imported), 1)
        self.assertEqual(imported[0]['amount'], 100.50)
    
    def test_export_import_json(self):
        """Тест экспорта и импорта JSON."""
        # Экспорт
        json_path = os.path.join(self.temp_dir, "test.json")
        success = DataStorage.export_to_json(self.operations, json_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(json_path))
        
        # Импорт
        imported = DataStorage.import_from_json(json_path)
        self.assertEqual(len(imported), 1)
        self.assertEqual(imported[0]['amount'], 100.50)

if __name__ == '__main__':
    unittest.main()