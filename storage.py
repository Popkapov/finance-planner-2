"""
Модуль для импорта и экспорта данных в различные форматы.
"""

import csv
import json
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from models import FinancialOperation, Category, OperationType

class DataStorage:
    """Класс для работы с файлами данных."""
    
    @staticmethod
    def export_to_csv(operations: List[FinancialOperation], filepath: str) -> bool:
        """
        Экспортирует операции в CSV файл.
        
        Args:
            operations: Список операций
            filepath: Путь к файлу
            
        Returns:
            True если успешно, False в противном случае
        """
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'id', 'amount', 'type', 'category', 'date', 'description'
                ])
                writer.writeheader()
                
                for op in operations:
                    writer.writerow({
                        'id': op.id,
                        'amount': op.amount,
                        'type': op.operation_type.value,
                        'category': op.category.name,
                        'date': op.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'description': op.description
                    })
            
            print(f"Данные экспортированы в {filepath}")
            return True
            
        except Exception as e:
            print(f"Ошибка при экспорте в CSV: {e}")
            return False
    
    @staticmethod
    def import_from_csv(filepath: str) -> List[Dict[str, Any]]:
        """
        Импортирует операции из CSV файла.
        
        Args:
            filepath: Путь к файлу
            
        Returns:
            Список словарей с данными операций
        """
        try:
            operations = []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        operations.append({
                            'amount': float(row['amount']),
                            'type': OperationType(row['type']),
                            'category': Category(id=0, name=row['category']),
                            'date': datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S'),
                            'description': row['description']
                        })
                    except (ValueError, KeyError) as e:
                        print(f"Ошибка при чтении строки: {e}")
                        continue
            
            print(f"Импортировано {len(operations)} операций из {filepath}")
            return operations
            
        except Exception as e:
            print(f"Ошибка при импорте из CSV: {e}")
            return []
    
    @staticmethod
    def export_to_json(operations: List[FinancialOperation], filepath: str) -> bool:
        """
        Экспортирует операции в JSON файл.
        
        Args:
            operations: Список операций
            filepath: Путь к файлу
        """
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'export_date': datetime.now().isoformat(),
                'total_operations': len(operations),
                'operations': [op.to_dict() for op in operations]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"Данные экспортированы в {filepath}")
            return True
            
        except Exception as e:
            print(f"Ошибка при экспорте в JSON: {e}")
            return False
    
    @staticmethod
    def import_from_json(filepath: str) -> List[Dict[str, Any]]:
        """
        Импортирует операции из JSON файла.
        
        Args:
            filepath: Путь к файлу
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            operations = []
            for op_data in data.get('operations', []):
                try:
                    operations.append({
                        'amount': float(op_data['amount']),
                        'type': OperationType(op_data['type']),
                        'category': Category(id=0, name=op_data['category']),
                        'date': datetime.strptime(op_data['date'], '%Y-%m-%d %H:%M:%S'),
                        'description': op_data.get('description', '')
                    })
                except (ValueError, KeyError) as e:
                    print(f"Ошибка при чтении операции: {e}")
                    continue
            
            print(f"Импортировано {len(operations)} операций из {filepath}")
            return operations
            
        except Exception as e:
            print(f"Ошибка при импорте из JSON: {e}")
            return []