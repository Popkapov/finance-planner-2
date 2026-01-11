"""
Главный модуль приложения.
Точка входа в программу.
"""

import tkinter as tk
from gui import FinancePlannerGUI
import sys
import os

def setup_environment():
    """Настраивает окружение приложения."""
    # Создание необходимых директорий
    os.makedirs("data/export", exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)
    
    # Проверка зависимостей
    try:
        import pandas
        import matplotlib
        import seaborn
        import sqlite3
    except ImportError as e:
        print(f"Ошибка: Не установлена зависимость: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        sys.exit(1)

def main():
    """Главная функция приложения."""
    # Настройка окружения
    setup_environment()
    
    # Создание главного окна
    root = tk.Tk()
    
    try:
        # Запуск приложения
        app = FinancePlannerGUI(root)
        
        # Обработка закрытия окна
        def on_closing():
            if tk.messagebox.askokcancel("Выход", "Сохранить изменения и выйти?"):
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Запуск главного цикла
        root.mainloop()
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()