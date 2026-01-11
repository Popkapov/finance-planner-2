"""
Модуль для визуализации финансовых данных.
Использует matplotlib и seaborn.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import numpy as np

class FinancialVisualizer:
    """Визуализатор финансовых данных."""
    
    def __init__(self, style: str = "seaborn-v0_8"):
        """
        Инициализирует визуализатор.
        
        Args:
            style: Стиль графиков matplotlib
        """
        plt.style.use(style)
        self.figsize = (12, 8)
    
    def plot_income_vs_expense(self, df: pd.DataFrame, save_path: Optional[str] = None):
        """
        Строит график доходов и расходов по времени.
        
        Args:
            df: DataFrame с финансовыми данными
            save_path: Путь для сохранения графика
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figsize)
        
        # График 1: Динамика доходов и расходов
        df['date'] = pd.to_datetime(df['date'])
        monthly = df.groupby([df['date'].dt.to_period('M'), 'type'])['amount'].sum().unstack()
        
        ax = axes[0, 0]
        monthly.plot(kind='line', ax=ax, marker='o')
        ax.set_title('Динамика доходов и расходов')
        ax.set_xlabel('Месяц')
        ax.set_ylabel('Сумма')
        ax.legend(title='Тип')
        ax.grid(True, alpha=0.3)
        
        # График 2: Структура расходов по категориям
        ax = axes[0, 1]
        expenses = df[df['type'] == 'Расход']
        if not expenses.empty:
            category_expenses = expenses.groupby('category')['amount'].sum()
            category_expenses.plot(kind='pie', ax=ax, autopct='%1.1f%%')
            ax.set_title('Структура расходов по категориям')
            ax.set_ylabel('')
        
        # График 3: Топ-10 расходов
        ax = axes[1, 0]
        if not expenses.empty:
            top_expenses = expenses.nlargest(10, 'amount')
            bars = ax.barh(top_expenses['description'].fillna('Без описания'), 
                          top_expenses['amount'])
            ax.set_title('Топ-10 самых крупных расходов')
            ax.set_xlabel('Сумма')
            
            # Добавление значений на столбцы
            for bar in bars:
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2, 
                       f'{width:,.0f}', ha='left', va='center')
        
        # График 4: Ежемесячный баланс
        ax = axes[1, 1]
        if 'month' not in df.columns:
            df['month'] = df['date'].dt.to_period('M')
        monthly_balance = df.groupby('month')['signed_amount'].sum()
        colors = ['red' if x < 0 else 'green' for x in monthly_balance]
        
        monthly_balance.plot(kind='bar', ax=ax, color=colors)
        ax.set_title('Ежемесячный баланс')
        ax.set_xlabel('Месяц')
        ax.set_ylabel('Баланс')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"График сохранен в {save_path}")
        
        plt.show()
    
    def plot_category_distribution(self, stats_df: pd.DataFrame, save_path: Optional[str] = None):
        """
        Строит круговую диаграмму распределения по категориям.
        
        Args:
            stats_df: DataFrame со статистикой категорий
            save_path: Путь для сохранения графика
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize)
        
        # Круговая диаграмма
        ax1.pie(stats_df['Сумма'], labels=stats_df['Категория'], 
               autopct='%1.1f%%', startangle=90)
        ax1.set_title('Распределение расходов по категориям')
        
        # Столбчатая диаграмма
        bars = ax2.bar(range(len(stats_df)), stats_df['Сумма'])
        ax2.set_title('Расходы по категориям')
        ax2.set_xlabel('Категория')
        ax2.set_ylabel('Сумма')
        ax2.set_xticks(range(len(stats_df)))
        ax2.set_xticklabels(stats_df['Категория'], rotation=45, ha='right')
        
        # Добавление значений на столбцы
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:,.0f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def plot_monthly_comparison(self, monthly_df: pd.DataFrame, save_path: Optional[str] = None):
        """
        Строит график сравнения доходов и расходов по месяцам.
        
        Args:
            monthly_df: DataFrame с помесячными данными
            save_path: Путь для сохранения графика
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        x = np.arange(len(monthly_df))
        width = 0.35
        
        income_bars = ax.bar(x - width/2, monthly_df.get('Доход', 0), 
                            width, label='Доходы', color='green', alpha=0.7)
        expense_bars = ax.bar(x + width/2, monthly_df.get('Расход', 0), 
                             width, label='Расходы', color='red', alpha=0.7)
        
        ax.set_xlabel('Месяц')
        ax.set_ylabel('Сумма')
        ax.set_title('Сравнение доходов и расходов по месяцам')
        ax.set_xticks(x)
        ax.set_xticklabels([str(period) for period in monthly_df.index])
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Добавление баланса линией
        ax2 = ax.twinx()
        ax2.plot(x, monthly_df['Баланс'], 'b-', marker='o', 
                linewidth=2, label='Баланс')
        ax2.set_ylabel('Баланс')
        ax2.legend(loc='upper right')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()