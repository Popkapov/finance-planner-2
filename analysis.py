"""
Модуль для анализа финансовых данных.
Использует pandas для агрегации и вычислений.
"""

import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple
from models import FinancialOperation, OperationType
from collections import defaultdict

class FinancialAnalyzer:
    """Анализатор финансовых данных."""
    
    def __init__(self, operations: List[FinancialOperation]):
        """
        Инициализирует анализатор с операциями.
        
        Args:
            operations: Список финансовых операций
        """
        self.operations = operations
    
    def to_dataframe(self) -> pd.DataFrame:
        """Конвертирует операции в DataFrame."""
        data = []
        for op in self.operations:
            data.append({
                'id': op.id,
                'amount': op.amount,
                'type': op.operation_type.value,
                'category': op.category.name,
                'date': op.date,
                'description': op.description,
                'signed_amount': op.signed_amount
            })
        return pd.DataFrame(data)
    
    def get_balance_by_period(
        self, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, float]:
        """
        Возвращает баланс за период.
        
        Returns:
            Словарь с доходами, расходами и балансом
        """
        df = self.to_dataframe()
        period_df = df[(df['date'].dt.date >= start_date) & 
                      (df['date'].dt.date <= end_date)]
        
        income = period_df[period_df['type'] == 'Доход']['amount'].sum()
        expense = period_df[period_df['type'] == 'Расход']['amount'].sum()
        balance = income - expense
        
        return {
            'income': float(income),
            'expense': float(expense),
            'balance': float(balance)
        }
    
    def get_category_stats(
        self, 
        operation_type: OperationType = OperationType.EXPENSE
    ) -> pd.DataFrame:
        """
        Возвращает статистику по категориям.
        
        Args:
            operation_type: Тип операций для анализа
            
        Returns:
            DataFrame с категориями и суммами
        """
        df = self.to_dataframe()
        type_df = df[df['type'] == operation_type.value]
        
        stats = type_df.groupby('category')['amount'].agg(['sum', 'count']).reset_index()
        stats.columns = ['Категория', 'Сумма', 'Количество']
        stats['Доля'] = (stats['Сумма'] / stats['Сумма'].sum() * 100).round(2)
        
        return stats.sort_values('Сумма', ascending=False)
    
    def get_monthly_trends(self, months: int = 6) -> pd.DataFrame:
        """
        Возвращает месячные тренды доходов и расходов.
        
        Args:
            months: Количество месяцев для анализа
            
        Returns:
            DataFrame с помесячной статистикой
        """
        df = self.to_dataframe()
        df['month'] = df['date'].dt.to_period('M')
        
        monthly = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
        monthly = monthly.resample('M').sum().tail(months)
        
        monthly['Баланс'] = monthly.get('Доход', 0) - monthly.get('Расход', 0)
        return monthly
    
    def get_top_expenses(self, limit: int = 10) -> List[FinancialOperation]:
        """Возвращает самые крупные расходы."""
        expenses = [op for op in self.operations 
                   if op.operation_type == OperationType.EXPENSE]
        return sorted(expenses, key=lambda x: x.amount, reverse=True)[:limit]
    
    def predict_next_month_expense(self) -> float:
        """Прогнозирует расходы на следующий месяц."""
        df = self.to_dataframe()
        expenses = df[df['type'] == 'Расход']
        
        if len(expenses) == 0:
            return 0.0
        
        # Средние расходы за последние 3 месяца
        recent = expenses[expenses['date'] > datetime.now() - timedelta(days=90)]
        if len(recent) > 0:
            monthly_avg = recent.groupby(recent['date'].dt.to_period('M'))['amount'].sum().mean()
            return float(monthly_avg)
        
        return float(expenses['amount'].mean())