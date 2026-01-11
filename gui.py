"""
Графический интерфейс приложения на tkinter.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
from typing import Optional, List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models import FinancialOperation, Category, OperationType
from database import DatabaseManager
from analysis import FinancialAnalyzer
from visualization import FinancialVisualizer
from storage import DataStorage
from utils import Validator, Formatter

class FinancePlannerGUI:
    """Графический интерфейс финансового планировщика."""
    
    def __init__(self, root: tk.Tk):
        """
        Инициализирует графический интерфейс.
        
        Args:
            root: Главное окно tkinter
        """
        self.root = root
        self.root.title("Финансовый Планировщик")
        self.root.geometry("1200x700")
        
        # Инициализация менеджера БД
        self.db = DatabaseManager()
        
        # Загрузка данных
        self.operations = self.db.get_operations()
        self.categories = self.db.get_all_categories()
        
        # Создание основных категорий, если их нет
        self._create_default_categories()
        
        # Стилизация
        self.setup_styles()
        
        # Создание интерфейса
        self.create_widgets()
        self.refresh_operations_list()
        
        # Запуск периодического обновления
        self.root.after(60000, self.auto_save)  # Автосохранение каждую минуту
    
    def setup_styles(self):
        """Настраивает стили виджетов."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Цветовая схема
        self.colors = {
            'income': '#2ecc71',
            'expense': '#e74c3c',
            'background': '#ecf0f1',
            'text': '#2c3e50',
            'button': '#3498db'
        }
        
        self.root.configure(bg=self.colors['background'])
    
    def _create_default_categories(self):
        """Создает стандартные категории, если их нет."""
        default_categories = [
            ("Продукты", None),
            ("Транспорт", None),
            ("Жилье", None),
            ("Здоровье", None),
            ("Развлечения", None),
            ("Одежда", None),
            ("Образование", None),
            ("Зарплата", None),
            ("Инвестиции", None),
            ("Прочее", None)
        ]
        
        existing_categories = {cat.name for cat in self.categories}
        
        for name, parent_id in default_categories:
            if name not in existing_categories:
                self.db.add_category(name, parent_id)
        
        # Обновляем список категорий
        self.categories = self.db.get_all_categories()
    
    def create_widgets(self):
        """Создает все виджеты интерфейса."""
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка сетки
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Панель добавления операции
        self.create_input_panel(main_frame)
        
        # Список операций
        self.create_operations_list(main_frame)
        
        # Панель управления
        self.create_control_panel(main_frame)
        
        # Статус бар
        self.create_status_bar()
    
    def create_input_panel(self, parent):
        """Создает панель для ввода новой операции."""
        input_frame = ttk.LabelFrame(parent, text="Добавить операцию", padding="10")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Тип операции
        ttk.Label(input_frame, text="Тип:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.type_var = tk.StringVar(value="Расход")
        type_combo = ttk.Combobox(input_frame, textvariable=self.type_var, 
                                 values=["Доход", "Расход"], width=15, state="readonly")
        type_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Сумма
        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.amount_var = tk.StringVar()
        amount_entry = ttk.Entry(input_frame, textvariable=self.amount_var, width=15)
        amount_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        # Категория
        ttk.Label(input_frame, text="Категория:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(input_frame, textvariable=self.category_var, 
                                          width=20, state="normal")
        self.category_combo.grid(row=0, column=5, sticky=tk.W, padx=(0, 20))
        self.update_category_combo()
        
        # Дата
        ttk.Label(input_frame, text="Дата:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(input_frame, textvariable=self.date_var, width=15)
        date_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # Описание
        ttk.Label(input_frame, text="Описание:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.desc_var = tk.StringVar()
        desc_entry = ttk.Entry(input_frame, textvariable=self.desc_var, width=30)
        desc_entry.grid(row=1, column=3, columnspan=3, sticky=(tk.W, tk.E), 
                       padx=(0, 10), pady=(10, 0))
        
        # Кнопка добавления
        add_button = ttk.Button(input_frame, text="Добавить", 
                               command=self.add_operation, style="Accent.TButton")
        add_button.grid(row=1, column=6, padx=(10, 0), pady=(10, 0))
        
        # Привязка события Enter
        amount_entry.bind('<Return>', lambda e: self.add_operation())
        desc_entry.bind('<Return>', lambda e: self.add_operation())
    
    def create_operations_list(self, parent):
        """Создает список операций с фильтрами."""
        list_frame = ttk.LabelFrame(parent, text="Операции", padding="10")
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)
        
        # Панель фильтров
        filter_frame = ttk.Frame(list_frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(filter_frame, text="Фильтры:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Фильтр по типу
        self.filter_type_var = tk.StringVar(value="Все")
        type_filter = ttk.Combobox(filter_frame, textvariable=self.filter_type_var,
                                  values=["Все", "Доход", "Расход"], width=10, state="readonly")
        type_filter.pack(side=tk.LEFT, padx=(0, 10))
        type_filter.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())
        
        # Фильтр по категории
        ttk.Label(filter_frame, text="Категория:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_category_var = tk.StringVar(value="Все")
        self.category_filter = ttk.Combobox(filter_frame, textvariable=self.filter_category_var,
                                           width=15, state="readonly")
        self.category_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.update_category_filter()
        
        # Фильтр по дате
        ttk.Label(filter_frame, text="С:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_from_var = tk.StringVar()
        date_from_entry = ttk.Entry(filter_frame, textvariable=self.date_from_var, width=12)
        date_from_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(filter_frame, text="По:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_to_var = tk.StringVar()
        date_to_entry = ttk.Entry(filter_frame, textvariable=self.date_to_var, width=12)
        date_to_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка применения фильтров
        filter_button = ttk.Button(filter_frame, text="Применить", 
                                  command=self.apply_filters)
        filter_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка сброса фильтров
        reset_button = ttk.Button(filter_frame, text="Сбросить", 
                                 command=self.reset_filters)
        reset_button.pack(side=tk.LEFT)
        
        # Таблица операций
        columns = ("id", "date", "type", "category", "amount", "description")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Настройка колонок
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Дата")
        self.tree.heading("type", text="Тип")
        self.tree.heading("category", text="Категория")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("description", text="Описание")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("date", width=120)
        self.tree.column("type", width=80)
        self.tree.column("category", width=120)
        self.tree.column("amount", width=100, anchor=tk.E)
        self.tree.column("description", width=200)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Привязка событий
        self.tree.bind('<Double-Button-1>', self.on_operation_double_click)
        self.tree.bind('<Delete>', self.delete_selected_operation)
    
    def create_control_panel(self, parent):
        """Создает панель управления с кнопками действий."""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Кнопки анализа
        ttk.Button(control_frame, text="Баланс", 
                  command=self.show_balance).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Анализ", 
                  command=self.show_analysis).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Графики", 
                  command=self.show_charts).pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопки импорта/экспорта
        ttk.Button(control_frame, text="Экспорт CSV", 
                  command=lambda: self.export_data('csv')).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Экспорт JSON", 
                  command=lambda: self.export_data('json')).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Импорт CSV", 
                  command=lambda: self.import_data('csv')).pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка удаления
        ttk.Button(control_frame, text="Удалить выбранное", 
                  command=self.delete_selected_operation, 
                  style="Danger.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка обновления
        ttk.Button(control_frame, text="Обновить", 
                  command=self.refresh_operations_list).pack(side=tk.LEFT)
    
    def create_status_bar(self):
        """Создает строку состояния."""
        self.status_var = tk.StringVar(value="Готово")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def update_category_combo(self):
        """Обновляет список категорий в комбобоксе."""
        category_names = [cat.name for cat in self.categories]
        self.category_combo['values'] = category_names
        if category_names:
            self.category_combo.set(category_names[0])
    
    def update_category_filter(self):
        """Обновляет список категорий в фильтре."""
        category_names = ["Все"] + [cat.name for cat in self.categories]
        self.category_filter['values'] = category_names
        self.category_filter.set("Все")
    
    def add_operation(self):
        """Добавляет новую операцию."""
        try:
            # Валидация данных
            amount_valid, amount = Validator.validate_amount(self.amount_var.get())
            if not amount_valid:
                messagebox.showerror("Ошибка", "Некорректная сумма")
                return
            
            date_valid, date_obj = Validator.validate_date(self.date_var.get())
            if not date_valid:
                messagebox.showerror("Ошибка", "Некорректная дата")
                return
            
            category_name = self.category_var.get()
            if not category_name or category_name.strip() == "":
                messagebox.showerror("Ошибка", "Выберите категорию")
                return
            
            # Поиск или создание категории
            category = next((cat for cat in self.categories if cat.name == category_name), None)
            if not category:
                category_id = self.db.add_category(category_name)
                category = Category(id=category_id, name=category_name)
                self.categories.append(category)
                self.update_category_combo()
                self.update_category_filter()
            
            # Создание операции
            operation_type = OperationType.INCOME if self.type_var.get() == "Доход" else OperationType.EXPENSE
            description_valid, description = Validator.validate_description(self.desc_var.get())
            
            operation = FinancialOperation(
                id=0,
                amount=amount,
                operation_type=operation_type,
                category=category,
                date=datetime.combine(date_obj, datetime.now().time()),
                description=description
            )
            
            # Сохранение в БД
            operation_id = self.db.add_operation(operation)
            operation.id = operation_id
            
            # Обновление интерфейса
            self.operations.append(operation)
            self.refresh_operations_list()
            
            # Очистка полей ввода
            self.amount_var.set("")
            self.desc_var.set("")
            self.status_var.set(f"Операция добавлена (ID: {operation_id})")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить операцию: {str(e)}")
    
    def refresh_operations_list(self):
        """Обновляет список операций."""
        # Сохраняем выделение
        selection = self.tree.selection()
        selected_id = None
        if selection:
            selected_id = self.tree.item(selection[0])['values'][0]
        
        # Очищаем список
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Добавляем операции
        for op in self.operations:
            amount_str = Formatter.format_amount(op.amount)
            if op.operation_type == OperationType.EXPENSE:
                amount_str = f"-{amount_str}"
            
            values = (
                op.id,
                Formatter.format_date(op.date),
                op.operation_type.value,
                op.category.name,
                amount_str,
                op.description
            )
            
            item = self.tree.insert("", tk.END, values=values)
            
            # Раскрашиваем строки
            if op.operation_type == OperationType.INCOME:
                self.tree.item(item, tags=('income',))
            else:
                self.tree.item(item, tags=('expense',))
        
        # Восстанавливаем выделение
        if selected_id:
            for child in self.tree.get_children():
                if self.tree.item(child)['values'][0] == selected_id:
                    self.tree.selection_set(child)
                    self.tree.see(child)
                    break
        
        # Обновляем баланс в заголовке
        balance = self.db.get_balance()
        balance_str = Formatter.format_amount(balance)
        self.root.title(f"Финансовый Планировщик - Баланс: {balance_str}")
        
        # Настройка тегов для цветов
        self.tree.tag_configure('income', foreground=self.colors['income'])
        self.tree.tag_configure('expense', foreground=self.colors['expense'])
    
    def apply_filters(self):
        """Применяет фильтры к списку операций."""
        try:
            # Получение параметров фильтрации
            filter_type = self.filter_type_var.get()
            filter_category = self.filter_category_var.get()
            date_from_str = self.date_from_var.get()
            date_to_str = self.date_to_var.get()
            
            # Преобразование дат
            date_from = None
            if date_from_str:
                valid, date_from_obj = Validator.validate_date(date_from_str)
                if valid:
                    date_from = date_from_obj
            
            date_to = None
            if date_to_str:
                valid, date_to_obj = Validator.validate_date(date_to_str)
                if valid:
                    date_to = date_to_obj
            
            # Фильтрация операций
            filtered_ops = []
            for op in self.operations:
                # Фильтр по типу
                if filter_type != "Все" and op.operation_type.value != filter_type:
                    continue
                
                # Фильтр по категории
                if filter_category != "Все" and op.category.name != filter_category:
                    continue
                
                # Фильтр по дате
                op_date = op.date.date()
                if date_from and op_date < date_from:
                    continue
                if date_to and op_date > date_to:
                    continue
                
                filtered_ops.append(op)
            
            # Временная замена списка операций для отображения
            original_ops = self.operations
            self.operations = filtered_ops
            self.refresh_operations_list()
            self.operations = original_ops
            
            self.status_var.set(f"Найдено {len(filtered_ops)} операций")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка фильтрации: {str(e)}")
    
    def reset_filters(self):
        """Сбрасывает все фильтры."""
        self.filter_type_var.set("Все")
        self.filter_category_var.set("Все")
        self.date_from_var.set("")
        self.date_to_var.set("")
        self.refresh_operations_list()
        self.status_var.set("Фильтры сброшены")
    
    def delete_selected_operation(self, event=None):
        """Удаляет выбранную операцию."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите операцию для удаления")
            return
        
        if not messagebox.askyesno("Подтверждение", "Удалить выбранную операцию?"):
            return
        
        try:
            item = selection[0]
            operation_id = self.tree.item(item)['values'][0]
            
            # Удаление из БД
            success = self.db.delete_operation(operation_id)
            if success:
                # Удаление из списка
                self.operations = [op for op in self.operations if op.id != operation_id]
                self.refresh_operations_list()
                self.status_var.set(f"Операция {operation_id} удалена")
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить операцию")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении: {str(e)}")
    
    def on_operation_double_click(self, event):
        """Обрабатывает двойной клик по операции."""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            operation_id = self.tree.item(item)['values'][0]
            self.show_operation_details(operation_id)
    
    def show_operation_details(self, operation_id: int):
        """Показывает детали операции."""
        operation = next((op for op in self.operations if op.id == operation_id), None)
        if not operation:
            return
        
        details = (
            f"ID: {operation.id}\n"
            f"Тип: {operation.operation_type.value}\n"
            f"Сумма: {Formatter.format_amount(operation.amount)}\n"
            f"Категория: {operation.category.name}\n"
            f"Дата: {Formatter.format_date(operation.date)}\n"
            f"Описание: {operation.description}"
        )
        
        messagebox.showinfo("Детали операции", details)
    
    def show_balance(self):
        """Показывает текущий баланс."""
        balance = self.db.get_balance()
        analyzer = FinancialAnalyzer(self.operations)
        
        # Анализ за последний месяц
        end_date = date.today()
        start_date = date(end_date.year, end_date.month, 1)
        monthly_stats = analyzer.get_balance_by_period(start_date, end_date)
        
        balance_info = (
            f"Текущий баланс: {Formatter.format_amount(balance)}\n\n"
            f"За текущий месяц:\n"
            f"  Доходы: {Formatter.format_amount(monthly_stats['income'])}\n"
            f"  Расходы: {Formatter.format_amount(monthly_stats['expense'])}\n"
            f"  Баланс: {Formatter.format_amount(monthly_stats['balance'])}"
        )
        
        messagebox.showinfo("Баланс", balance_info)
    
    def show_analysis(self):
        """Показывает анализ финансов."""
        try:
            analyzer = FinancialAnalyzer(self.operations)
            
            # Статистика по категориям расходов
            expense_stats = analyzer.get_category_stats(OperationType.EXPENSE)
            
            # Топ расходы
            top_expenses = analyzer.get_top_expenses(5)
            
            # Помесячные тренды
            monthly_trends = analyzer.get_monthly_trends(6)
            
            # Прогноз
            prediction = analyzer.predict_next_month_expense()
            
            # Формирование отчета
            report_lines = ["=== ФИНАНСОВЫЙ АНАЛИЗ ===", ""]
            
            report_lines.append("=== РАСХОДЫ ПО КАТЕГОРИЯМ ===")
            for _, row in expense_stats.iterrows():
                report_lines.append(
                    f"{row['Категория']}: {Formatter.format_amount(row['Сумма'])} "
                    f"({row['Доля']}%, {int(row['Количество'])} операций)"
                )
            
            report_lines.append("\n=== ТОП-5 РАСХОДОВ ===")
            for i, op in enumerate(top_expenses, 1):
                report_lines.append(
                    f"{i}. {op.description or 'Без описания'} - "
                    f"{Formatter.format_amount(op.amount)} ({op.category.name})"
                )
            
            report_lines.append("\n=== ПРОГНОЗ ===")
            report_lines.append(
                f"Ожидаемые расходы в следующем месяце: {Formatter.format_amount(prediction)}"
            )
            
            # Создание окна с отчетом
            report_window = tk.Toplevel(self.root)
            report_window.title("Финансовый анализ")
            report_window.geometry("600x500")
            
            text_widget = tk.Text(report_window, wrap=tk.WORD, font=("Courier", 10))
            scrollbar = ttk.Scrollbar(report_window, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Вставка отчета
            report_text = "\n".join(report_lines)
            text_widget.insert(tk.END, report_text)
            text_widget.config(state=tk.DISABLED)
            
            # Кнопка сохранения
            save_button = ttk.Button(report_window, text="Сохранить отчет",
                                    command=lambda: self.save_report(report_text))
            save_button.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка анализа: {str(e)}")
    
    def save_report(self, report_text: str):
        """Сохраняет отчет в файл."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                messagebox.showinfo("Успех", "Отчет сохранен")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {str(e)}")
    
    def show_charts(self):
        """Показывает графики."""
        try:
            analyzer = FinancialAnalyzer(self.operations)
            visualizer = FinancialVisualizer()
            
            # Создание нового окна для графиков
            chart_window = tk.Toplevel(self.root)
            chart_window.title("Графики")
            chart_window.geometry("1000x800")
            
            # Получение данных
            df = analyzer.to_dataframe()
            expense_stats = analyzer.get_category_stats(OperationType.EXPENSE)
            monthly_trends = analyzer.get_monthly_trends(6)
            
            # Создание вкладок
            notebook = ttk.Notebook(chart_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Вкладка 1: Обзор
            tab1 = ttk.Frame(notebook)
            notebook.add(tab1, text="Обзор")
            
            fig1, _ = plt.subplots(2, 2, figsize=(12, 10))
            visualizer.plot_income_vs_expense(df)
            
            canvas1 = FigureCanvasTkAgg(fig1, tab1)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Вкладка 2: Категории
            tab2 = ttk.Frame(notebook)
            notebook.add(tab2, text="Категории")
            
            fig2, _ = plt.subplots(1, 2, figsize=(12, 6))
            visualizer.plot_category_distribution(expense_stats)
            
            canvas2 = FigureCanvasTkAgg(fig2, tab2)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Вкладка 3: Тренды
            tab3 = ttk.Frame(notebook)
            notebook.add(tab3, text="Тренды")
            
            fig3, _ = plt.subplots(figsize=(12, 6))
            visualizer.plot_monthly_comparison(monthly_trends)
            
            canvas3 = FigureCanvasTkAgg(fig3, tab3)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Кнопки управления
            button_frame = ttk.Frame(chart_window)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="Сохранить все", 
                      command=lambda: self.save_all_charts(visualizer, df, expense_stats, monthly_trends)
                      ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(button_frame, text="Закрыть", 
                      command=chart_window.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка построения графиков: {str(e)}")
    
    def save_all_charts(self, visualizer, df, expense_stats, monthly_trends):
        """Сохраняет все графики в файлы."""
        try:
            import os
            from datetime import datetime
            
            # Создание папки для сохранения
            save_dir = filedialog.askdirectory(title="Выберите папку для сохранения")
            if not save_dir:
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Сохранение графиков
            visualizer.plot_income_vs_expense(
                df, 
                os.path.join(save_dir, f"overview_{timestamp}.png")
            )
            
            visualizer.plot_category_distribution(
                expense_stats,
                os.path.join(save_dir, f"categories_{timestamp}.png")
            )
            
            visualizer.plot_monthly_comparison(
                monthly_trends,
                os.path.join(save_dir, f"trends_{timestamp}.png")
            )
            
            messagebox.showinfo("Успех", f"Графики сохранены в папку:\n{save_dir}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить графики: {str(e)}")
    
    def export_data(self, format_type: str):
        """Экспортирует данные в указанном формате."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=f".{format_type}",
                filetypes=[(f"{format_type.upper()} файлы", f"*.{format_type}"), ("Все файлы", "*.*")],
                initialfile=f"operations_export_{datetime.now().strftime('%Y%m%d')}.{format_type}"
            )
            
            if not filename:
                return
            
            if format_type == 'csv':
                success = DataStorage.export_to_csv(self.operations, filename)
            elif format_type == 'json':
                success = DataStorage.export_to_json(self.operations, filename)
            else:
                messagebox.showerror("Ошибка", "Неподдерживаемый формат")
                return
            
            if success:
                messagebox.showinfo("Успех", f"Данные экспортированы в {filename}")
                self.status_var.set(f"Экспорт завершен: {filename}")
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать данные")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {str(e)}")
    
    def import_data(self, format_type: str):
        """Импортирует данные из указанного формата."""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[(f"{format_type.upper()} файлы", f"*.{format_type}"), ("Все файлы", "*.*")]
            )
            
            if not filename:
                return
            
            if format_type == 'csv':
                imported_ops = DataStorage.import_from_csv(filename)
            else:
                messagebox.showerror("Ошибка", "Неподдерживаемый формат")
                return
            
            if not imported_ops:
                messagebox.showwarning("Внимание", "Не удалось импортировать данные или файл пуст")
                return
            
            # Подтверждение импорта
            if not messagebox.askyesno("Подтверждение", 
                                      f"Импортировать {len(imported_ops)} операций?"):
                return
            
            # Импорт операций
            imported_count = 0
            for op_data in imported_ops:
                try:
                    # Поиск или создание категории
                    category_name = op_data['category'].name
                    category = next((cat for cat in self.categories if cat.name == category_name), None)
                    if not category:
                        category_id = self.db.add_category(category_name)
                        category = Category(id=category_id, name=category_name)
                        self.categories.append(category)
                    
                    # Создание операции
                    operation = FinancialOperation(
                        id=0,
                        amount=op_data['amount'],
                        operation_type=op_data['type'],
                        category=category,
                        date=op_data['date'],
                        description=op_data['description']
                    )
                    
                    # Сохранение
                    operation_id = self.db.add_operation(operation)
                    operation.id = operation_id
                    self.operations.append(operation)
                    imported_count += 1
                    
                except Exception as e:
                    print(f"Ошибка импорта операции: {e}")
                    continue
            
            # Обновление интерфейса
            self.update_category_combo()
            self.update_category_filter()
            self.refresh_operations_list()
            
            messagebox.showinfo("Успех", f"Импортировано {imported_count} операций")
            self.status_var.set(f"Импорт завершен: {imported_count} операций")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка импорта: {str(e)}")
    
    def auto_save(self):
        """Автоматическое сохранение данных."""
        try:
            # Можно добавить логику автосохранения
            self.status_var.set(f"Автосохранение: {datetime.now().strftime('%H:%M:%S')}")
        finally:
            # Планирование следующего автосохранения
            self.root.after(60000, self.auto_save)