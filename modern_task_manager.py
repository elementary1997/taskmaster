#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modern Task Manager - Легковесный полупрозрачный менеджер задач
Минималистичный дизайн с glassmorphism эффектом
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QScrollArea,
    QFrame, QSizeGrip, QGraphicsDropShadowEffect, QDialog, QTextEdit, QSizePolicy,
    QCalendarWidget, QDateEdit, QSystemTrayIcon, QTableView, QAbstractItemView, QLayout
)
from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, Property, QStandardPaths, QDate, QSize, QTimer, QByteArray
from PySide6.QtGui import (
    QIcon, QFont, QColor, QPalette, QLinearGradient, QGradient, 
    QPainter, QPen, QBrush, QCursor, QAction, QPixmap, QDrag
)
from PySide6.QtCore import QMimeData


# Глобальный стиль для отключения focus rect и выделений
GLOBAL_STYLE = """
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
        outline: none;
    }
    QLineEdit, QTextEdit, QComboBox {
        outline: none;
    }
    QLineEdit:focus {
        border: 1px solid rgba(107, 207, 127, 0.6);
    }
    QTextEdit:focus {
        border: 0px;
    }
    QComboBox:focus {
        border: 1px solid rgba(107, 207, 127, 0.6);
    }
    QLineEdit::selection, QTextEdit::selection {
        background-color: #6bcf7f !important;
        color: #ffffff !important;
    }
    QLineEdit::selected-text, QTextEdit::selected-text {
        background-color: #6bcf7f !important;
        color: #ffffff !important;
    }
    QLabel {
        selection-background-color: transparent !important;
        selection-color: inherit !important;
    }
    QLabel::selection {
        background-color: transparent !important;
        color: inherit !important;
    }
    * {
        selection-background-color: transparent !important;
        selection-color: inherit !important;
    }
"""


# Константы
# Определение пути к файлу данных
def get_data_file():
    """Получить путь к файлу данных в папке пользователя"""
    # Windows: C:/Users/<User>/AppData/Local/ModernTaskManager/tasks.json
    # Linux: ~/.local/share/ModernTaskManager/tasks.json
    base_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    app_dir = Path(base_path) / "ModernTaskManager"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / "tasks.json"

TASKS_FILE = get_data_file()

# Файл настроек
def get_settings_file():
    """Получить путь к файлу настроек"""
    base_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    app_dir = Path(base_path) / "ModernTaskManager"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / "settings.json"

SETTINGS_FILE = get_settings_file()

# === Вспомогательные функции ===

def pluralize(number, forms):
    """
    Склонение слов в русском языке
    forms: (единственное, множественное 2-4, множественное 5+)
    Пример: pluralize(5, ('задача', 'задачи', 'задач'))
    """
    n = abs(number)
    n %= 100
    if n >= 5 and n <= 20:
        return forms[2]
    n %= 10
    if n == 1:
        return forms[0]
    if n >= 2 and n <= 4:
        return forms[1]
    return forms[2]

# === Классы ===

class SettingsManager:
    """Управление настройками приложения"""
    
    @staticmethod
    def load():
        """Загрузка настроек из файла"""
        default_settings = {
            "sounds_enabled": True
        }
        
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Объединяем с настройками по умолчанию
                    default_settings.update(settings)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
        
        return default_settings
    
    @staticmethod
    def save(settings):
        """Сохранение настроек в файл"""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
    
    @staticmethod
    def get(key, default=None):
        """Получить значение настройки"""
        settings = SettingsManager.load()
        return settings.get(key, default)
    
    @staticmethod
    def set(key, value):
        """Установить значение настройки"""
        settings = SettingsManager.load()
        settings[key] = value
        SettingsManager.save(settings)

# Цветовая схема (только темная тема)
THEME = {
        "window_bg_start": "#1a1a2e",
        "window_bg_end": "#16213e",
        "card_bg": "rgba(30, 30, 50, 0.6)",
        "card_bg_hover": "rgba(40, 40, 60, 0.7)",
        "input_bg": "rgba(20, 20, 35, 0.5)",
        "input_bg_focus": "rgba(20, 20, 35, 0.7)",
        "text_primary": "#ffffff",
        "text_secondary": "rgba(255, 255, 255, 0.8)",
        "text_tertiary": "rgba(255, 255, 255, 0.6)",
        "border_color": "rgba(255, 255, 255, 0.15)",
        "grip_bg": "rgba(255, 255, 255, 0.15)",
        "grip_bg_hover": "rgba(255, 255, 255, 0.25)",
        "form_bg": "rgba(30, 30, 50, 0.4)",
        "icon_color": "rgba(255, 255, 255, 0.9)",
        "placeholder_color": "rgba(255, 255, 255, 0.5)",
        "accent_bg": "rgba(107, 207, 127, 0.4)",
        "accent_hover": "rgba(107, 207, 127, 0.6)",
        "accent_text": "#ffffff",
        "secondary_bg": "rgba(255, 255, 255, 0.1)",
        "secondary_hover": "rgba(255, 255, 255, 0.15)",
        "secondary_text": "#ffffff",
        "scroll_handle": "rgba(255, 255, 255, 0.2)",
}

PRIORITY_COLORS = {
    "high": "#ff6b6b",
    "medium": "#ffd93d", 
    "low": "#6bcf7f"
}

PRIORITY_NAMES = {
    "high": "Высокий",
    "medium": "Средний",
    "low": "Низкий"
}


class SoundManager:
    @staticmethod
    def play_complete_sound():
        """Проигрывает приятный щелчок как в современных таск-менеджерах"""
        # Проверяем, включены ли звуки
        if not SettingsManager.get("sounds_enabled", True):
            return
        
        try:
            import winsound
            import os
            import threading
            
            # Определяем пути
            # В PyInstaller exe ресурсы распаковываются во временную папку
            if getattr(sys, 'frozen', False):
                # Запущено из exe
                base_dir = os.path.dirname(sys.executable)
                # Пытаемся найти audio рядом с exe
                audio_dir = os.path.join(base_dir, "audio")
                if not os.path.exists(audio_dir):
                    # Если нет рядом с exe, ищем в временной папке PyInstaller
                    base_dir = sys._MEIPASS
                    audio_dir = os.path.join(base_dir, "audio")
            else:
                # Запущено из скрипта
                base_dir = os.path.dirname(os.path.abspath(__file__))
                audio_dir = os.path.join(base_dir, "audio")
            
            # 1. Сначала ищем пользовательский файл рядом с exe (приоритет)
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                user_audio_dir = os.path.join(exe_dir, "audio")
                os.makedirs(user_audio_dir, exist_ok=True)
                custom_sound = os.path.join(user_audio_dir, "custom.wav")
                if os.path.exists(custom_sound):
                    winsound.PlaySound(custom_sound, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    return
            
            # 2. Ищем пользовательский файл в папке проекта (для запуска из скрипта)
            custom_sound = os.path.join(audio_dir, "custom.wav")
            if os.path.exists(custom_sound):
                winsound.PlaySound(custom_sound, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return

            # 3. Если есть встроенный сгенерированный щелчок (из ресурсов exe)
            click_sound = os.path.join(audio_dir, "click.wav")
            if os.path.exists(click_sound):
                winsound.PlaySound(click_sound, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
                
            # 4. Генерируем приятный щелчок программно (короткий высокочастотный звук)
            # Используем отдельный поток, чтобы не блокировать UI
            def play_click():
                try:
                    # Короткий, мягкий щелчок: высокая частота, очень короткая длительность
                    # Частота ~2000 Hz дает приятный "тик" звук
                    winsound.Beep(2000, 30)  # 30ms - очень короткий щелчок
                except:
                    pass
            
            thread = threading.Thread(target=play_click, daemon=True)
            thread.start()
            
        except Exception as e:
            # Тихий fallback - просто игнорируем ошибки
            pass

class ZoomManager:
    """Управление масштабированием интерфейса"""
    _scale = 1.0
    _callbacks = []

    @classmethod
    def set_scale(cls, scale: float):
        cls._scale = scale
        for cb in cls._callbacks:
            cb()

    @classmethod
    def get_scale(cls) -> float:
        return cls._scale

    @classmethod
    def add_callback(cls, callback):
        cls._callbacks.append(callback)
        
    @classmethod
    def scaled(cls, value: int) -> int:
        return int(value * cls._scale)
        
    @classmethod
    def font(cls, family: str, size: int, weight=QFont.Normal) -> QFont:
        return QFont(family, cls.scaled(size), weight)
        
    @classmethod
    def stylesheet_font_size(cls, size: int) -> str:
        return f"font-size: {cls.scaled(size)}px;"


@dataclass
class Task:
    """Модель задачи"""
    id: int
    title: str
    description: str
    priority: str
    status: str
    due_date: str
    created: str
    repeat_type: Optional[str] = None  # "daily", "weekly", "monthly" или None
    last_repeated_date: Optional[str] = None  # Дата последнего повторения в формате "yyyy-MM-dd"
    time_spent: int = 0  # Время выполнения в секундах
    is_running: bool = False  # Флаг запущенного таймера


class TaskStorage:
    """Хранилище задач в JSON"""
    
    @staticmethod
    def load() -> List[Task]:
        """Загрузка задач из файла"""
        if not TASKS_FILE.exists():
            return []
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                tasks = []
                for item in data:
                    # Добавляем дефолтные значения для новых полей, если их нет
                    if "repeat_type" not in item:
                        item["repeat_type"] = None
                    if "last_repeated_date" not in item:
                        item["last_repeated_date"] = None
                    if "time_spent" not in item:
                        item["time_spent"] = 0
                    if "is_running" not in item:
                        item["is_running"] = False
                    else:
                         # Сбрасываем флаг запуска при старте (на случай аварийного закрытия)
                         item["is_running"] = False
                    tasks.append(Task(**item))
                return tasks
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return []
    
    @staticmethod
    def save(tasks: List[Task]) -> None:
        """Сохранение задач в файл"""
        try:
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump([asdict(t) for t in tasks], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")


class DraggableDialog(QDialog):
    """Базовый класс для перетаскиваемых и масштабируемых диалогов"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_position = QPoint()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    def add_grip(self, container):
        """Добавить grip для масштабирования"""
        grip_wrapper = QFrame(container)
        grip_wrapper.setFixedSize(24, 24)
        grip_wrapper.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['grip_bg']};
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: {THEME['grip_bg_hover']};
            }}
        """)
        
        # Позиционируем в правом нижнем углу, учитывая отступы
        # Используем координаты относительно видимой области контейнера
        grip_wrapper.move(container.width() - 30, container.height() - 30)
        
        grip_layout = QVBoxLayout(grip_wrapper)
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.setAlignment(Qt.AlignCenter)
        
        resize_icon = QLabel("⇲")
        resize_icon.setStyleSheet(f"""
            color: {THEME['icon_color']};
            font-size: 12px;
            font-weight: bold;
            background: transparent;
        """)
        resize_icon.setAlignment(Qt.AlignCenter)
        grip_layout.addWidget(resize_icon)
        
        size_grip = QSizeGrip(grip_wrapper)
        size_grip.setStyleSheet("background: transparent;")
        
        self.grip_wrapper = grip_wrapper
        grip_wrapper.raise_()  # Поднимаем grip выше других элементов
        return grip_wrapper
    
    def mousePressEvent(self, event):
        """Начало перетаскивания"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Перетаскивание"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def resizeEvent(self, event):
        """Обновление позиции grip при изменении размера"""
        super().resizeEvent(event)


class CleanCalendarWidget(QCalendarWidget):
    """Стабильный календарь с фиксированной сеткой"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFirstDayOfWeek(Qt.Monday)
        self.setNavigationBarVisible(False)

    def showEvent(self, event):
        super().showEvent(event)
        # Убираем рамку у внутренней таблицы
        table = self.findChild(QTableView)
        if table:
            table.setFrameShape(QFrame.NoFrame)
            table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            # Фильтруем выделение, чтобы не было синего фона
            table.setSelectionMode(QAbstractItemView.NoSelection)

    def paintCell(self, painter, rect, date):
        # Просто вызываем стандартный метод отрисовки
        # Стилизация идет через QSS
        super().paintCell(painter, rect, date)


class CustomCalendarWidget(QWidget):
    """Календарь с кастомной навигацией (стрелки и выпадающие списки)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Header row: Navigation
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Prev Button
        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedSize(28, 28)
        self.prev_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.prev_btn.setStyleSheet(self._get_btn_style())
        self.prev_btn.clicked.connect(self._prev_month)
        header_layout.addWidget(self.prev_btn)
        
        # Month Combo
        self.month_combo = QComboBox()
        months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
                  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        self.month_combo.addItems(months)
        self.month_combo.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.month_combo.setCursor(QCursor(Qt.PointingHandCursor))
        self.month_combo.setStyleSheet(self._get_combo_style())
        self.month_combo.currentIndexChanged.connect(self._update_calendar_page)
        header_layout.addWidget(self.month_combo, 1)
        
        # Year Combo
        self.year_combo = QComboBox()
        self.year_combo.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.year_combo.setCursor(QCursor(Qt.PointingHandCursor))
        self.year_combo.setStyleSheet(self._get_combo_style())
        
        # Fill years (current +/- 10)
        current_year = QDate.currentDate().year()
        for y in range(current_year - 10, current_year + 11):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentIndexChanged.connect(self._update_calendar_page)
        header_layout.addWidget(self.year_combo)
        
        # Next Button
        self.next_btn = QPushButton(">")
        self.next_btn.setFixedSize(28, 28)
        self.next_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.next_btn.setStyleSheet(self._get_btn_style())
        self.next_btn.clicked.connect(self._next_month)
        header_layout.addWidget(self.next_btn)
        
        layout.addLayout(header_layout)
        
        # --- Calendar ---
        self.calendar = CleanCalendarWidget()
        self.calendar.setNavigationBarVisible(False) # Hide default nav
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setStyleSheet(f"""
            QCalendarWidget {{
                background-color: transparent;
            }}
            QCalendarWidget QWidget {{ 
                alternate-background-color: {THEME['input_bg']}; 
                color: {THEME['text_primary']};
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                color: {THEME['text_primary']};
                background-color: {THEME['window_bg_start']};
                selection-background-color: {THEME['accent_bg']};
                selection-color: {THEME['accent_text']};
                outline: none;
                border-radius: 4px;
                padding-bottom: 5px; /* Add some internal padding */
            }}
            QCalendarWidget QAbstractItemView::item {{
                border-radius: 4px; 
            }}
            QCalendarWidget QAbstractItemView::item:hover {{
                background-color: {THEME['card_bg_hover']};
                color: {THEME['text_primary']};
            }}
            QCalendarWidget QAbstractItemView:disabled {{
                color: {THEME['text_tertiary']};
            }}
        """)
        self.calendar.currentPageChanged.connect(self._sync_header_with_calendar)
        
        # Add a spacer item or margin to the bottom of the layout
        layout.addWidget(self.calendar)
        # layout.addSpacing(6) # REMOVED: User reported empty space
        
        # Initial Sync
        self._sync_header_with_calendar(self.calendar.yearShown(), self.calendar.monthShown())
        
    def _get_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {THEME['secondary_bg']};
                border: none;
                border-radius: 14px;
                color: {THEME['text_primary']};
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
            }}
        """
        
    def _get_combo_style(self):
        return f"""
            QComboBox {{
                background-color: {THEME['input_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: 6px;
                padding: 4px 8px;
                color: {THEME['text_primary']};
            }}
            QComboBox:hover {{
                background-color: {THEME['input_bg_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {THEME['text_secondary']};
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {THEME['window_bg_end']};
                selection-background-color: {THEME['accent_bg']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border_color']};
                outline: none;
            }}
        """
        
    def _prev_month(self):
        self.calendar.showPreviousMonth()
        
    def _next_month(self):
        self.calendar.showNextMonth()
        
    def _update_calendar_page(self):
        """Update calendar when combo changes (if not called by sync)"""
        # Block signals to avoid recursion loops if needed? 
        # Actually logic is robust enough: sync updates combos -> signal triggers -> update calendar -> loops back...
        # We need to block usage of this function when sync is running.
        if self.calendar.signalsBlocked():
            return
            
        month = self.month_combo.currentIndex() + 1
        year = self.year_combo.currentData()
        self.calendar.setCurrentPage(year, month)
        
    def _sync_header_with_calendar(self, year, month):
        """Update header when calendar page changes"""
        # Block signals from combos to prevent loop
        self.month_combo.blockSignals(True)
        self.year_combo.blockSignals(True)
        
        self.month_combo.setCurrentIndex(month - 1)
        
        # Update years if needed
        try:
            idx = self.year_combo.findData(year)
            if idx == -1:
                # Add it if missing
                self.year_combo.addItem(str(year), year)
                self.year_combo.model().sort(0) # Sort might store as string? data is int.
                # Re-find
                idx = self.year_combo.findData(year)
            self.year_combo.setCurrentIndex(idx)
        except:
            pass
            
        self.month_combo.blockSignals(False)
        self.year_combo.blockSignals(False)


class DateNavigator(QFrame):
    """Виджет навигации по датам"""
    
    def __init__(self, parent=None, on_date_change=None):
        super().__init__(parent)
        self.on_date_change = on_date_change
        self.current_date = QDate.currentDate()
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ZoomManager.scaled(4))
        
        # Кнопка "Вчера"
        self.prev_btn = QPushButton("←")
        self.prev_btn.setFixedSize(ZoomManager.scaled(28), ZoomManager.scaled(28))
        self.prev_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.prev_btn.clicked.connect(lambda: self.change_date(-1))
        layout.addWidget(self.prev_btn)
        
        # Текст даты
        self.date_label = QPushButton()
        self.date_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.date_label.clicked.connect(self._show_calendar)
        layout.addWidget(self.date_label)
        
        # Кнопка "Завтра"
        self.next_btn = QPushButton("→")
        self.next_btn.setFixedSize(ZoomManager.scaled(28), ZoomManager.scaled(28))
        self.next_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.next_btn.clicked.connect(lambda: self.change_date(1))
        layout.addWidget(self.next_btn)
        
        # Styles will be updated by update_styles
        self.update_styles()
        self.update_label()
        
        ZoomManager.add_callback(self.update_styles)
        
    def update_styles(self):
        btn_size = ZoomManager.scaled(28)
        self.prev_btn.setFixedSize(btn_size, btn_size)
        self.next_btn.setFixedSize(btn_size, btn_size)
        
        self.prev_btn.setStyleSheet(self._get_btn_style())
        self.next_btn.setStyleSheet(self._get_btn_style())
        
        self.date_label.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {THEME['text_primary']};
                font-family: 'Segoe UI';
                {ZoomManager.stylesheet_font_size(14)}
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
            }}
        """)

    def _get_btn_style(self):
        return f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {THEME['text_secondary']};
                {ZoomManager.stylesheet_font_size(16)}
                font-weight: bold;
                border-radius: {ZoomManager.scaled(14)}px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['text_primary']};
            }}
        """
        
    def update_label(self):
        today = QDate.currentDate()
        
        if self.current_date == today:
            text = "Сегодня"
        elif self.current_date == today.addDays(1):
            text = "Завтра"
        elif self.current_date == today.addDays(-1):
            text = "Вчера"
        else:
            # Формат даты с месяцем на русском (простой вариант)
            months = ["янв", "фев", "мар", "апр", "май", "июн", 
                      "июл", "авг", "сен", "окт", "ноя", "дек"]
            day = self.current_date.day()
            month = months[self.current_date.month() - 1]
            text = f"{day} {month}"
            
        self.date_label.setText(text)
        
    def change_date(self, days):
        self.current_date = self.current_date.addDays(days)
        self.update_label()
        if self.on_date_change:
            self.on_date_change(self.current_date)
            
            
    def set_date(self, date):
        self.current_date = date
        self.update_label()
        if self.on_date_change:
            self.on_date_change(self.current_date)
            
    def _show_calendar(self):
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        
        # Stylized container for the dialog
        container = QFrame(dialog)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['window_bg_end']};
                border: 1px solid {THEME['border_color']};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0,0,0,0)
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize) # Важно: авто-ресайз по контенту
        layout.addWidget(container)
        
        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(12, 12, 12, 12)
        
        # Use our custom calendar
        custom_calendar = CustomCalendarWidget()
        custom_calendar.calendar.setSelectedDate(self.current_date)
        # Fix bottom clipping by forcing a slightly larger minimum height
        custom_calendar = CustomCalendarWidget()
        custom_calendar.calendar.setSelectedDate(self.current_date)
        # Fix bottom clipping by forcing a slightly larger minimum height
        # custom_calendar.setMinimumHeight(300) # User asked to remove empty space 
        
        def on_selected():
            self.set_date(custom_calendar.calendar.selectedDate())
            dialog.accept()
            
        custom_calendar.calendar.clicked.connect(on_selected)
        inner_layout.addWidget(custom_calendar)
        
        # Resize dialog to fit content
        dialog.adjustSize()
        
        # Position dialog
        pos = self.date_label.mapToGlobal(QPoint(0, self.date_label.height()))
        x = pos.x() - (dialog.width() - self.date_label.width()) // 2
        
        # Keep on screen
        screen_geo = self.screen().geometry()
        if x + dialog.width() > screen_geo.right():
            x = screen_geo.right() - dialog.width() - 10
        if x < screen_geo.left():
            x = screen_geo.left() + 10
            
        dialog.move(x, pos.y() + 5)
        
        dialog.exec()



class CloseButton(QPushButton):
    """Кастомная кнопка закрытия с рисованием крестика"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Фон (Красный)
        rect = self.rect()
        if self.isDown():
            painter.setBrush(QColor(200, 50, 50))
        elif self.underMouse():
            painter.setBrush(QColor(232, 17, 35))
        else:
            painter.setBrush(Qt.transparent)
            
        painter.setPen(Qt.NoPen)
        # Отступ 2 пикселя
        painter.drawEllipse(rect.adjusted(2, 2, -2, -2))
        
        # Крестик
        painter.setPen(QPen(QColor(255, 255, 255), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # Используем float для точности
        c = list(rect.center().toTuple()) # получаем (x, y)
        # В PySide6 center() возвращает QPoint. Преобразуем
        cx, cy = float(rect.width()) / 2.0, float(rect.height()) / 2.0
        
        # Размер крестика
        offset = 5.0
        
        painter.drawLine(cx - offset, cy - offset, cx + offset, cy + offset)
        painter.drawLine(cx + offset, cy - offset, cx - offset, cy + offset)





class MinimizeButton(QPushButton):
    """Кастомная кнопка сворачивания"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        rect = self.rect()
        
        # Желтый кружок только при наведении
        if self.underMouse():
            if self.isDown():
                color = QColor(255, 193, 61, 200)
            else:
                color = QColor(255, 193, 61, 128)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect.adjusted(2, 2, -2, -2))
        
        # Белый шеврон вниз
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI", 12, QFont.Bold)
        painter.setFont(font)
        # Смещаем вверх на 4px для выравнивания с крестиком
        adjusted_rect = rect.adjusted(0, -4, 0, -4)
        painter.drawText(adjusted_rect, Qt.AlignCenter, "⌄")

class TaskDialog(DraggableDialog):
    """Диалог для создания/редактирования задачи"""
    
    def __init__(self, parent=None, task: Optional[Task] = None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("Редактировать задачу" if task else "Новая задача")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        self._setup_ui()
        
        if task:
            self._populate_fields()
    
    def _setup_ui(self):
        """Настройка интерфейса диалога"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Контейнер с фоном
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border-radius: 16px;
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 40)  # Увеличиваем нижний отступ для grip
        layout.setSpacing(16)
        
        # Заголовок
        header_layout = QHBoxLayout()
        title_label = QLabel("✏️ " + ("Редактировать задачу" if self.task else "Новая задача"))
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {THEME['text_primary']};")
        title_label.setTextInteractionFlags(Qt.NoTextInteraction)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Кнопка закрытия
        close_btn = CloseButton()
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Поле названия
        name_label = QLabel("Название")
        name_label.setFont(QFont("Segoe UI", 10))
        name_label.setStyleSheet(f"color: {THEME['text_secondary']};")
        name_label.setTextInteractionFlags(Qt.NoTextInteraction)
        layout.addWidget(name_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название задачи")
        self.title_input.setFont(QFont("Segoe UI", 11))
        self.title_input.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.title_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['input_bg']};
                border: 0px;
                border-radius: 8px;
                padding: 10px 12px;
                color: {THEME['text_primary']};
                selection-background-color: #6bcf7f;
                selection-color: #ffffff;
            }}
            QLineEdit:focus {{
                background-color: {THEME['input_bg_focus']};
                border: 0px;
            }}
            QLineEdit::selection {{
                background-color: #6bcf7f !important;
                color: #ffffff !important;
            }}
        """)
        layout.addWidget(self.title_input)
        
        # Поле описания
        desc_label = QLabel("Описание (необязательно)")
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setStyleSheet(f"color: {THEME['text_secondary']};")
        desc_label.setTextInteractionFlags(Qt.NoTextInteraction)
        layout.addWidget(desc_label)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Добавьте описание задачи...")
        self.description_input.setFont(QFont("Segoe UI", 10))
        self.description_input.setMaximumHeight(100)
        self.description_input.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.description_input.setFrameStyle(QFrame.NoFrame)  # Убираем рамку
        self.description_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {THEME['input_bg']};
                border: 0px;
                border-radius: 8px;
                padding: 10px 12px;
                color: {THEME['text_primary']};
                selection-background-color: #6bcf7f;
                selection-color: #ffffff;
            }}
            QTextEdit:focus {{
                background-color: {THEME['input_bg_focus']};
                border: 0px;
            }}
            QTextEdit::selection {{
                background-color: #6bcf7f !important;
                color: #ffffff !important;
            }}
        """)
        layout.addWidget(self.description_input)
        
        # Приоритет
        priority_label = QLabel("Приоритет")
        priority_label.setFont(QFont("Segoe UI", 10))
        priority_label.setStyleSheet(f"color: {THEME['text_secondary']};")
        priority_label.setTextInteractionFlags(Qt.NoTextInteraction)
        layout.addWidget(priority_label)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["⚡ Высокий", "⭐ Средний", "✓ Низкий"])
        self.priority_combo.setCurrentIndex(1)
        self.priority_combo.setFont(QFont("Segoe UI", 10))
        self.priority_combo.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.priority_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {THEME['input_bg']};
                border: 0px;
                border-radius: 8px;
                padding: 10px 12px;
                color: {THEME['text_primary']};
            }}
            QComboBox:focus {{
                background-color: {THEME['input_bg_focus']};
                border: 0px;
            }}
            QComboBox:hover {{
                background-color: {THEME['input_bg_focus']};
            }}
            QComboBox::drop-down {{
                border: 0px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: 0px;
            }}
        """)
        self.priority_combo.view().setStyleSheet(f"""
            QAbstractItemView {{
                background-color: {THEME['card_bg']};
                border: 1px solid {THEME['border_color']};
                color: {THEME['text_primary']};
            }}
            QAbstractItemView::item {{
                padding: 4px;
            }}
            QAbstractItemView::item:hover {{
                background-color: {THEME['card_bg_hover']};
            }}
            QAbstractItemView::item:selected {{
                background-color: transparent;
                color: {THEME['text_primary']};
            }}
        """)
        layout.addWidget(self.priority_combo)
        
        # Дата выполнения
        date_label = QLabel("Дата выполнения")
        date_label.setFont(QFont("Segoe UI", 10))
        date_label.setStyleSheet(f"color: {THEME['text_secondary']};")
        date_label.setTextInteractionFlags(Qt.NoTextInteraction)
        layout.addWidget(date_label)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setFont(QFont("Segoe UI", 11))
        self.date_edit.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.date_edit.setStyleSheet(f"""
            QDateEdit {{
                background-color: {THEME['input_bg']};
                border: 0px;
                border-radius: 8px;
                padding: 10px 12px;
                color: {THEME['text_primary']};
            }}
            QDateEdit:focus {{
                background-color: {THEME['input_bg_focus']};
            }}
            QDateEdit::drop-down {{
                border: 0px;
            }}
            QDateEdit::down-arrow {{
                image: none; 
                border: 0px;
            }}
            /* Calendar styling handled by global or specific popup style */
        """)
        # We need to style the popup calendar similar to DateNavigator
        self.date_edit.calendarWidget().setStyleSheet(f"""
            QCalendarWidget {{
                background-color: transparent;
            }}
            QCalendarWidget QWidget {{ 
                alternate-background-color: {THEME['input_bg']}; 
                color: {THEME['text_primary']};
            }}
            /* Header styling */
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {THEME['window_bg_start']};
                border-bottom: 1px solid {THEME['border_color']};
            }}
            QCalendarWidget QToolButton {{
                color: {THEME['text_primary']};
                background-color: transparent;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                icon-size: 24px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {THEME['secondary_hover']};
            }}
            QCalendarWidget QMenu {{
                background-color: {THEME['window_bg_end']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border_color']};
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                color: {THEME['text_primary']};
                background-color: {THEME['window_bg_start']};
                selection-background-color: {THEME['accent_bg']};
                selection-color: {THEME['accent_text']};
                outline: none;
            }}
            QCalendarWidget QSpinBox {{
                color: {THEME['text_primary']};
                background-color: {THEME['input_bg']};
                selection-background-color: {THEME['accent_bg']};
            }}
        """)
        layout.addWidget(self.date_edit)
        
        # Повторение задачи
        repeat_label = QLabel("Повторение")
        repeat_label.setFont(QFont("Segoe UI", 10))
        repeat_label.setStyleSheet(f"color: {THEME['text_secondary']};")
        repeat_label.setTextInteractionFlags(Qt.NoTextInteraction)
        layout.addWidget(repeat_label)
        
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["Не повторять", "Ежедневно", "Еженедельно", "Ежемесячно"])
        self.repeat_combo.setFont(QFont("Segoe UI", 10))
        self.repeat_combo.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.repeat_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {THEME['input_bg']};
                border: 0px;
                border-radius: 8px;
                padding: 10px 12px;
                color: {THEME['text_primary']};
            }}
            QComboBox:focus {{
                background-color: {THEME['input_bg_focus']};
                border: 0px;
            }}
            QComboBox:hover {{
                background-color: {THEME['input_bg_focus']};
            }}
            QComboBox::drop-down {{
                border: 0px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: 0px;
            }}
        """)
        self.repeat_combo.view().setStyleSheet(f"""
            QAbstractItemView {{
                background-color: {THEME['card_bg']};
                border: 1px solid {THEME['border_color']};
                color: {THEME['text_primary']};
            }}
            QAbstractItemView::item {{
                padding: 4px;
            }}
            QAbstractItemView::item:hover {{
                background-color: {THEME['card_bg_hover']};
            }}
            QAbstractItemView::item:selected {{
                background-color: transparent;
                color: {THEME['text_primary']};
            }}
        """)
        layout.addWidget(self.repeat_combo)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setFont(QFont("Segoe UI", 10))
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['secondary_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
                padding: 10px 20px;
                color: {THEME['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Сохранить")
        save_btn.setFont(QFont("Segoe UI", 10, QFont.Medium))
        save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent_bg']};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                color: {THEME['accent_text']};
            }}
            QPushButton:hover {{
                background-color: {THEME['accent_hover']};
            }}
        """)
        save_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        
        # Добавляем grip для масштабирования
        self.add_grip(container)
        
        main_layout.addWidget(container)
        
        # Тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)
    
    def _populate_fields(self):
        """Заполнение полей данными задачи"""
        if self.task:
            self.title_input.setText(self.task.title)
            self.description_input.setPlainText(self.task.description)
            
            priority_map = {"high": 0, "medium": 1, "low": 2}
            self.priority_combo.setCurrentIndex(priority_map.get(self.task.priority, 1))
            
            if self.task.due_date:
                date = QDate.fromString(self.task.due_date, "yyyy-MM-dd")
                if date.isValid():
                    self.date_edit.setDate(date)
            
            # Заполнение поля повторения
            repeat_map = {None: 0, "daily": 1, "weekly": 2, "monthly": 3}
            self.repeat_combo.setCurrentIndex(repeat_map.get(self.task.repeat_type, 0))
    
    def get_data(self):
        """Получение данных из формы"""
        priority_map = {0: "high", 1: "medium", 2: "low"}
        repeat_map = {0: None, 1: "daily", 2: "weekly", 3: "monthly"}
        
        return {
            "title": self.title_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "priority": priority_map[self.priority_combo.currentIndex()],
            "due_date": self.date_edit.date().toString("yyyy-MM-dd"),
            "repeat_type": repeat_map[self.repeat_combo.currentIndex()]
        }


class AboutDialog(DraggableDialog):
    """Диалог с информацией о проекте и обновлениях"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Контейнер с фоном
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border-radius: 16px;
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 40)
        layout.setSpacing(20)
        
        # Заголовок
        header_layout = QHBoxLayout()
        title_label = QLabel("ℹ️ О программе")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {THEME['text_primary']};")
        title_label.setTextInteractionFlags(Qt.NoTextInteraction)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Кнопка закрытия
        close_btn = CloseButton()
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        # Область прокрутки для контента
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {THEME['input_bg']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {THEME['border_color']};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {THEME['text_secondary']};
            }}
        """)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        
        # Информация о проекте
        project_frame = QFrame()
        project_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['card_bg']};
                border-radius: 12px;
                border: none;
            }}
        """)
        project_layout = QVBoxLayout(project_frame)
        project_layout.setContentsMargins(16, 16, 16, 16)
        project_layout.setSpacing(12)
        
        project_title = QLabel("😎 TaskMaster")
        project_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        project_title.setStyleSheet(f"color: {THEME['text_primary']};")
        project_title.setTextInteractionFlags(Qt.NoTextInteraction)
        project_layout.addWidget(project_title)
        
        version_label = QLabel("Версия 1.0.0")
        version_label.setFont(QFont("Segoe UI", 11))
        version_label.setStyleSheet(f"color: {THEME['text_secondary']};")
        version_label.setTextInteractionFlags(Qt.NoTextInteraction)
        project_layout.addWidget(version_label)
        
        desc_label = QLabel(
            "Современный легковесный менеджер задач с полупрозрачным интерфейсом "
            "и минималистичным дизайном. Создан для продуктивной работы и удобного "
            "управления задачами."
        )
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setStyleSheet(f"color: {THEME['text_secondary']};")
        desc_label.setWordWrap(True)
        desc_label.setTextInteractionFlags(Qt.NoTextInteraction)
        project_layout.addWidget(desc_label)
        
        content_layout.addWidget(project_frame)
        
        
        # Особенности
        features_frame = QFrame()
        features_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['card_bg']};
                border-radius: 12px;
                border: none;
            }}
        """)
        features_layout = QVBoxLayout(features_frame)
        features_layout.setContentsMargins(16, 16, 16, 16)
        features_layout.setSpacing(12)
        
        features_title = QLabel("⭐ Основные возможности")
        features_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        features_title.setStyleSheet(f"color: {THEME['text_primary']};")
        features_title.setTextInteractionFlags(Qt.NoTextInteraction)
        features_layout.addWidget(features_title)
        
        features_list = [
            "Приоритеты задач (Высокий, Средний, Низкий)",
            "Даты выполнения задач",
            "Фильтрация и поиск",
            "Статистика выполнения",
            "Перетаскивание и масштабирование окон",
            "Автосохранение всех данных"
        ]
        
        for feature_text in features_list:
            feature_item = QLabel(f"• {feature_text}")
            feature_item.setFont(QFont("Segoe UI", 10))
            feature_item.setStyleSheet(f"color: {THEME['text_secondary']};")
            feature_item.setWordWrap(True)
            feature_item.setTextInteractionFlags(Qt.NoTextInteraction)
            features_layout.addWidget(feature_item)
        
        content_layout.addWidget(features_frame)
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll, 1)
        
        # Кнопка закрытия внизу
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_btn_bottom = QPushButton("Закрыть")
        close_btn_bottom.setFont(QFont("Segoe UI", 10))
        close_btn_bottom.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn_bottom.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent_bg']};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                color: {THEME['accent_text']};
            }}
            QPushButton:hover {{
                background-color: {THEME['accent_hover']};
            }}
        """)
        close_btn_bottom.clicked.connect(self.reject)
        buttons_layout.addWidget(close_btn_bottom)
        
        layout.addLayout(buttons_layout)
        
        # Добавляем grip
        self.add_grip(container)
        
        main_layout.addWidget(container)
        
        # Тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)


class TaskViewDialog(DraggableDialog):
    """Диалог для просмотра задачи"""
    
    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.parent_window = parent
        self.setWindowTitle("Просмотр задачи")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Контейнер с фоном
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border-radius: 16px;
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 40)  # Увеличиваем нижний отступ для grip
        layout.setSpacing(16)
        
        # Заголовок с иконкой и кнопка закрытия
        header_layout = QHBoxLayout()
        title_label = QLabel("📋 Описание задачи")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {THEME['text_primary']};")
        title_label.setTextInteractionFlags(Qt.NoTextInteraction)
        title_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Кнопка закрытия
        close_btn = CloseButton()
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        # Единый блок с информацией о задаче
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['card_bg']};
                border-radius: 12px;
                border: none;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(12)
        
        # Название задачи (без фона)
        task_title = QLabel(self.task.title)
        task_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        task_title.setStyleSheet(f"color: {THEME['text_primary']};")
        task_title.setWordWrap(True)
        task_title.setTextInteractionFlags(Qt.NoTextInteraction)
        task_title.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        info_layout.addWidget(task_title)
        
        # Приоритет
        priority_color = PRIORITY_COLORS.get(self.task.priority, "#6bcf7f")
        priority_label = QLabel(f"⚡ Приоритет: {PRIORITY_NAMES[self.task.priority]}")
        priority_label.setFont(QFont("Segoe UI", 11))
        priority_label.setStyleSheet(f"color: {priority_color};")
        priority_label.setTextInteractionFlags(Qt.NoTextInteraction)
        priority_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        info_layout.addWidget(priority_label)
        
        # Статус
        status_label = QLabel(f"📊 Статус: {self.task.status}")
        status_label.setFont(QFont("Segoe UI", 11))
        status_label.setStyleSheet(f"color: {THEME['text_secondary']};")
        status_label.setTextInteractionFlags(Qt.NoTextInteraction)
        status_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        info_layout.addWidget(status_label)
        
        # Описание (если есть)
        if self.task.description:
            desc_label = QLabel("Описание задачи:")
            desc_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            desc_label.setStyleSheet(f"color: {THEME['text_tertiary']};")
            desc_label.setTextInteractionFlags(Qt.NoTextInteraction)
            desc_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            info_layout.addWidget(desc_label)
            
            desc_text = QLabel(self.task.description)
            desc_text.setFont(QFont("Segoe UI", 10))
            desc_text.setStyleSheet(f"""
                color: {THEME['text_primary']};
                background-color: {THEME['input_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
                padding: 12px;
            """)
            desc_text.setWordWrap(True)
            desc_text.setTextInteractionFlags(Qt.NoTextInteraction)
            desc_text.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            info_layout.addWidget(desc_text)
        
        layout.addWidget(info_frame)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addStretch()
        
        edit_btn = QPushButton("✏️ Редактировать")
        edit_btn.setFont(QFont("Segoe UI", 10, QFont.Medium))
        edit_btn.setCursor(QCursor(Qt.PointingHandCursor))
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent_bg']};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                color: {THEME['accent_text']};
            }}
            QPushButton:hover {{
                background-color: {THEME['accent_hover']};
            }}
        """)
        edit_btn.clicked.connect(self._edit_task)
        buttons_layout.addWidget(edit_btn)
        
        close_dialog_btn = QPushButton("Закрыть")
        close_dialog_btn.setFont(QFont("Segoe UI", 10))
        close_dialog_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_dialog_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['secondary_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
                padding: 10px 20px;
                color: {THEME['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
            }}
        """)
        close_dialog_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(close_dialog_btn)
        
        layout.addLayout(buttons_layout)
        
        # Добавляем grip
        self.add_grip(container)
        
        main_layout.addWidget(container)
        
        # Тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)
    
    def _edit_task(self):
        """Открыть диалог редактирования"""
        self.accept()  # Закрываем окно просмотра
        if self.parent_window:
            self.parent_window.edit_task(self.task)


class TaskCard(QFrame):
    """Карточка задачи с современным дизайном"""
    
    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.parent_window = parent
        
        # Ссылки на лейблы
        self.title_label = None
        self.repeat_label = None
        self.priority_label = None
        self.date_label = None
        
        # Drag & Drop
        self.drag_start_position = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Настройка интерфейса карточки"""
        self.setObjectName("taskCard")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Основной layout - компактнее
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        
        # Индикатор приоритета - меньше
        priority_indicator = QFrame()
        priority_indicator.setFixedSize(3, 28)
        priority_color = PRIORITY_COLORS.get(self.task.priority, "#6bcf7f")
        priority_indicator.setStyleSheet(f"""
            background-color: {priority_color};
            border-radius: 2px;
        """)
        layout.addWidget(priority_indicator)
        
        # Контент задачи
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        
        # Заголовок - компактнее
        title_layout = QHBoxLayout()
        title_layout.setSpacing(6)
        
        # Индикатор повторения
        if self.task.repeat_type:
            repeat_icons = {"daily": "🔄", "weekly": "📅", "monthly": "📆"}
            repeat_icon = repeat_icons.get(self.task.repeat_type, "🔄")
            self.repeat_label = QLabel(repeat_icon)
            self.repeat_label.setFont(QFont("Segoe UI", 9))
            repeat_tooltips = {"daily": "Повторяется ежедневно", "weekly": "Повторяется еженедельно", "monthly": "Повторяется ежемесячно"}
            self.repeat_label.setToolTip(repeat_tooltips.get(self.task.repeat_type, "Повторяющаяся задача"))
            self.repeat_label.setTextInteractionFlags(Qt.NoTextInteraction)
            title_layout.addWidget(self.repeat_label)
        
        title_label = QLabel(self.task.title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        title_label.setStyleSheet(f"color: {THEME['text_primary']};")
        if self.task.status == "Выполнено":
            title_label.setStyleSheet(f"color: {THEME['text_tertiary']}; text-decoration: line-through;")
        title_label.setTextInteractionFlags(Qt.NoTextInteraction)
        title_label.setWordWrap(True)  # Включаем перенос текста
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Адаптивное масштабирование
        title_layout.addWidget(title_label)
        self.title_label = title_label
        
        content_layout.addLayout(title_layout)
        
        # Информация о приоритете - компактнее
        info_layout = QHBoxLayout()
        info_layout.setSpacing(6)
        
        self.priority_label = QLabel(f"{PRIORITY_NAMES[self.task.priority]}")
        self.priority_label.setFont(QFont("Segoe UI", 8))
        self.priority_label.setStyleSheet(f"color: {priority_color};")
        self.priority_label.setTextInteractionFlags(Qt.NoTextInteraction)
        info_layout.addWidget(self.priority_label)
        
        # Индикатор даты (если есть)
        if self.task.due_date:
            try:
                task_date = QDate.fromString(self.task.due_date, "yyyy-MM-dd")
                today = QDate.currentDate()
                
                if task_date == today:
                    date_text = "Сегодня"
                    date_color = THEME['text_secondary']
                elif task_date == today.addDays(1):
                    date_text = "Завтра"
                    date_color = THEME['text_secondary']
                elif task_date < today:
                    date_text = f"Просрочено ({task_date.toString('dd.MM')})"
                    date_color = "#ff6b6b" # Red
                else:
                    date_text = task_date.toString("dd.MM")
                    date_color = THEME['text_secondary']
                    
                self.date_label = QLabel(f"📅 {date_text}")
                self.date_label.setFont(QFont("Segoe UI", 8))
                self.date_label.setStyleSheet(f"color: {date_color};")
                self.date_label.setTextInteractionFlags(Qt.NoTextInteraction)
                info_layout.addWidget(self.date_label)
            except:
                pass
        
        info_layout.addStretch()
        content_layout.addLayout(info_layout)
        
        layout.addLayout(content_layout, 1)
        
        # Кнопки действий - горизонтально и компактнее
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(4)
        
        # Контейнер для элементов таймера
        self.timer_controls_container = QWidget()
        timer_controls_layout = QHBoxLayout(self.timer_controls_container)
        timer_controls_layout.setContentsMargins(0, 0, 0, 0)
        timer_controls_layout.setSpacing(4)
        
        # Таймер и кнопка Play
        self.time_label = QLabel(self._format_time(self.task.time_spent))
        self.time_label.setFont(ZoomManager.font("Consolas", 10)) # Моноширинный шрифт для цифр
        self.time_label.setStyleSheet(f"color: {THEME['text_secondary']}; margin-right: 5px;")
        
        self.play_btn = QPushButton()
        self.play_btn.setFixedSize(28, 28)
        self.play_btn.setText("⏯️" if self.task.is_running else "▶️")  # ⏯️ для паузы, ▶️ для play
        self.play_btn.setToolTip("Пауза" if self.task.is_running else "Запустить")
        self.play_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.play_btn.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # Предотвращаем проброс событий
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {THEME['border_color']};
                color: {THEME['accent_text'] if self.task.is_running else THEME['text_secondary']};
                font-size: 14px;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['accent_text']};
            }}
        """)
        self.play_btn.clicked.connect(self._toggle_timer)
        
        timer_controls_layout.addWidget(self.time_label)
        timer_controls_layout.addWidget(self.play_btn)
        
        # Кнопка сброса таймера
        reset_btn = QPushButton("🔄")  # Круговая стрелка
        reset_btn.setFixedSize(28, 28)
        reset_btn.setToolTip("Сбросить таймер")
        reset_btn.setCursor(QCursor(Qt.PointingHandCursor))
        reset_btn.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # Предотвращаем проброс событий
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {THEME['border_color']};
                color: {THEME['text_secondary']};
                font-size: 16px;
                border-radius: 14px;
                padding-bottom: 2px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['text_primary']};
            }}
        """)
        reset_btn.clicked.connect(self._reset_timer)
        timer_controls_layout.addWidget(reset_btn)
        
        # Скрываем контейнер по умолчанию
        self.timer_controls_container.setVisible(False)
        actions_layout.addWidget(self.timer_controls_container)
        
        # Кнопка-переключатель таймера
        self.toggle_timer_btn = QPushButton("⏱️")
        self.toggle_timer_btn.setFixedSize(28, 28)
        self.toggle_timer_btn.setToolTip("Показать таймер")
        self.toggle_timer_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_timer_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {THEME['border_color']};
                color: {THEME['text_secondary']};
                font-size: 14px;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['text_primary']};
            }}
        """)
        self.toggle_timer_btn.clicked.connect(self._toggle_timer_controls)
        actions_layout.addWidget(self.toggle_timer_btn)
        
        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedWidth(1)
        separator.setFixedHeight(20)
        separator.setStyleSheet(f"background-color: {THEME['border_color']}; border: none;")
        actions_layout.addWidget(separator)
        
        # Чекбокс выполнения
        self.checkbox = QPushButton("✓" if self.task.status == "Выполнено" else "")
        self.checkbox.setFixedSize(24, 24)
        self.checkbox.setCheckable(True)
        self.checkbox.setChecked(self.task.status == "Выполнено")
        self.checkbox.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Определение цвета чекбокса
        check_color = "#6bcf7f"
        if self.task.priority == "high":
            check_color = "#ff6b6b"
        elif self.task.priority == "medium":
            check_color = "#ffd93d"
            
        self.checkbox.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#6bcf7f' if self.task.status == 'Выполнено' else 'transparent'};
                border: 2px solid {check_color};
                border-radius: 12px;
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {check_color}40;
            }}
            QPushButton:checked {{
                background-color: {check_color};
                border: 2px solid {check_color};
            }}
        """)
        self.checkbox.clicked.connect(self._on_checked)
        actions_layout.addWidget(self.checkbox)
        
        # Кнопка удаления
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 107, 107, 0.3);
                border: none;
                border-radius: 14px;
                color: #ff6b6b;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 107, 107, 0.5);
            }
        """)
        delete_btn.clicked.connect(self._delete_task)
        actions_layout.addWidget(delete_btn)
        
        layout.addLayout(actions_layout)
        
        # Стили карточки
        self.setStyleSheet(f"""
            QFrame#taskCard {{
                background-color: {THEME['card_bg']};
                border-radius: 10px;
                border: 1px solid {THEME['border_color']};
            }}
            QFrame#taskCard:hover {{
                background-color: {THEME['card_bg_hover']};
            }}
        """)
        
        # Адаптивное масштабирование карточки
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # Применяем текущий масштаб
        self.update_ui_scale()
    
    def mousePressEvent(self, event):
        """Открытие окна просмотра при клике"""
        if event.button() == Qt.LeftButton:
            # Открываем окно просмотра
            dialog = TaskViewDialog(self.task, self.parent_window)
            dialog.exec()
            event.accept()
    
    def _toggle_timer(self):
        """Переключение таймера"""
        self.parent_window.toggle_task_timer(self.task.id)

    def update_time_display(self, seconds):
        """Обновление отображения времени"""
        self.time_label.setText(self._format_time(seconds))
    
    def update_timer_state(self, is_running):
        """Обновление состояния кнопки таймера"""
        self.play_btn.setText("⏯️" if is_running else "▶️")
        self.play_btn.setToolTip("Пауза" if is_running else "Запустить")
        
    def _format_time(self, seconds):
        """Форматирование времени в ЧЧ:ММ:СС"""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        else:
            return f"{m:02d}:{s:02d}"

    def _reset_timer(self):
        """Сброс таймера"""
        if self.parent_window:
            self.parent_window.reset_task_timer(self.task.id)
    
    def _toggle_timer_controls(self):
        """Переключение видимости панели таймера"""
        is_visible = self.timer_controls_container.isVisible()
        self.timer_controls_container.setVisible(not is_visible)
        
        # Обновляем стиль кнопки
        if not is_visible:
            self.toggle_timer_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME['accent_bg']};
                    border: 1px solid {THEME['accent_hover']};
                    color: {THEME['accent_text']};
                    font-size: 14px;
                    border-radius: 14px;
                }}
            """)
            self.toggle_timer_btn.setToolTip("Скрыть таймер")
        else:
            self.toggle_timer_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {THEME['border_color']};
                    color: {THEME['text_secondary']};
                    font-size: 14px;
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['secondary_hover']};
                    color: {THEME['text_primary']};
                }}
            """)
            self.toggle_timer_btn.setToolTip("Показать таймер")


    def _edit_task(self):
        """Открыть диалог редактирования"""
        if self.parent_window:
            self.parent_window.edit_task(self.task)
    
    def _toggle_complete(self):
        """Переключение статуса выполнения"""
        if self.parent_window:
            self.parent_window.toggle_task_status(self.task.id)
    
    
    def _delete_task(self):
        """Удаление задачи"""
        if self.parent_window:
            self.parent_window.delete_task(self.task.id)

    def _on_checked(self, checked):
        # Update styling immediately for responsiveness
        self._update_style()
        
        # Play sound if completing
        if checked:
            SoundManager.play_complete_sound()
            
        # Notify main window
        if self.parent_window:
             self.parent_window.toggle_task_status(self.task.id)

    def _update_style(self):
        """Обновление стилей карточки"""
        # Обновляем стиль чекбокса
        check_color = "#6bcf7f"
        if self.task.priority == "high":
            check_color = "#ff6b6b"
        elif self.task.priority == "medium":
                check_color = "#ffd93d"
        
        is_checked = self.checkbox.isChecked()
        
        self.checkbox.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#6bcf7f' if is_checked else 'transparent'};
                border: 2px solid {check_color};
                border-radius: 12px;
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {check_color}40;
            }}
            QPushButton:checked {{
                background-color: #6bcf7f;
                border: 2px solid #6bcf7f;
            }}
        """)
        
        # Зачеркивание текста
        title_color = THEME['text_tertiary'] if is_checked else THEME['text_primary']
        text_decoration = "line-through" if is_checked else "none"
        
        # Обновляем заголовок напрямую
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"color: {title_color}; text-decoration: {text_decoration};")

    def update_ui_scale(self):
        """Обновление интерфейса при изменении масштаба"""
        # Обновляем шрифты
        if hasattr(self, 'title_label') and self.title_label:
            self.title_label.setFont(ZoomManager.font("Segoe UI", 10, QFont.Medium))
        if hasattr(self, 'repeat_label') and self.repeat_label:
            self.repeat_label.setFont(ZoomManager.font("Segoe UI", 9))
        if hasattr(self, 'priority_label') and self.priority_label:
            self.priority_label.setFont(ZoomManager.font("Segoe UI", 8))
        if hasattr(self, 'date_label') and self.date_label:
            self.date_label.setFont(ZoomManager.font("Segoe UI", 8))
    
    def mousePressEvent(self, event):
        """Начало перетаскивания"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Перетаскивание карточки"""
        # Проверяем, что зажата левая кнопка
        if not (event.buttons() & Qt.LeftButton):
            return
            
        if self.drag_start_position is None:
            return
        
        # Проверяем, что переместились достаточно далеко
        distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
        
        if distance < 10:  # Порог для начала drag
            return
        
        # Создаем drag
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.task.id))  # Передаем ID задачи
        drag.setMimeData(mime_data)
        
        # Создаем превью карточки
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.position().toPoint())
        
        # Сбрасываем позицию чтобы не запускать drag повторно
        self.drag_start_position = None
        
        # Выполняем drag
        drag.exec(Qt.MoveAction)



class CompletedHeaderWidget(QWidget):
    """Заголовок выполненных задач с поддержкой drop для авто-разворачивания"""
    
    def __init__(self, parent_window, parent=None):
        super().__init__(parent)
        self.parent_window = parent_window
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        """При наведении с drag - разворачиваем секцию"""
        if event.mimeData().hasText():
            # Разворачиваем секцию, если она свернута
            if not self.parent_window.completed_tasks_container.isVisible():
                self.parent_window.completed_tasks_container.setVisible(True)
                self.parent_window.toggle_completed_btn.setText("▼")
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Обработка выхода"""
        pass
    
    def dropEvent(self, event):
        """Перенаправляем drop на контейнер задач"""
        if event.mimeData().hasText():
            task_id = event.mimeData().text()
            new_status = "Выполнено"
            if self.parent_window:
                self.parent_window.change_task_status_by_id(task_id, new_status)
            event.acceptProposedAction()


class DropZoneWidget(QWidget):
    """Виджет-контейнер с поддержкой drop"""
    
    def __init__(self, zone_type, parent_window, parent=None):
        super().__init__(parent)
        self.zone_type = zone_type  # 'active' или 'completed'
        self.parent_window = parent_window
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        """Обработка входа в зону drop"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # Подсветка зоны
            self.setStyleSheet(f"background-color: {THEME['accent_bg']};  border-radius: 8px;")
    
    def dragLeaveEvent(self, event):
        """Обработка выхода из зоны drop"""
        self.setStyleSheet("background-color: transparent;")
    
    def dropEvent(self, event):
        """Обработка drop"""
        self.setStyleSheet("background-color: transparent;")
        
        if event.mimeData().hasText():
            task_id = event.mimeData().text()
            
            # Определяем новый статус
            new_status = "Выполнено" if self.zone_type == "completed" else "В процессе"
            
            # Обновляем статус задачи
            if self.parent_window:
                self.parent_window.change_task_status_by_id(task_id, new_status)
            
            event.acceptProposedAction()


class SliderPopup(QDialog):
    """Попап с вертикальным слайдером"""
    def __init__(self, parent=None, title="", value=100, min_val=0, max_val=100, on_change=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['window_bg_start']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
            }}
        """)
        layout.addWidget(container)
        
        inner = QVBoxLayout(container)
        inner.setContentsMargins(10, 15, 10, 15)
        inner.setSpacing(10)
        
        # Заголовок/Иконка
        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {THEME['text_primary']}; font-weight: bold; border: none; font-size: 14px;")
        inner.addWidget(lbl)
        
        # Слайдер
        from PySide6.QtWidgets import QSlider
        self.slider = QSlider(Qt.Vertical)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(value)
        self.slider.setFixedHeight(120) 
        self.slider.setStyleSheet(f"""
            QSlider::groove:vertical {{
                border: 1px solid {THEME['border_color']};
                width: 6px;
                background: {THEME['input_bg']};
                margin: 0px;
                border-radius: 3px;
            }}
            QSlider::handle:vertical {{
                background: {THEME['accent_text']};
                border: 1px solid {THEME['accent_hover']};
                height: 14px;
                width: 14px;
                margin: 0 -5px;
                border-radius: 7px;
            }}
            QSlider::sub-page:vertical {{
                background: {THEME['input_bg']};
                border-radius: 3px;
            }}
            QSlider::add-page:vertical {{
                background: {THEME['accent_hover']};
                border-radius: 3px;
            }}
        """)
        if on_change:
            self.slider.valueChanged.connect(on_change)
        inner.addWidget(self.slider, 0, Qt.AlignHCenter)
        
        # Значение
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setAlignment(Qt.AlignCenter)
        self.val_lbl.setStyleSheet(f"color: {THEME['text_secondary']}; font-size: 11px; border: none;")
        inner.addWidget(self.val_lbl)
        
        self.slider.valueChanged.connect(lambda v: self.val_lbl.setText(str(v)))


class ModernTaskManager(QMainWindow):
    """Главное окно современного менеджера задач"""
    
    def __init__(self):
        super().__init__()
        
        self.tasks: List[Task] = []
        self.drag_position = None
        self.selected_date = QDate.currentDate() # Текущая выбранная дата
        self.update_available = False  # Флаг доступности обновления
        
        # Таймер для трекинга времени
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timers)
        self.timer.start(1000) # Обновление каждую секунду
        
        # Сначала создаем UI, потом загружаем задачи
        self._setup_ui()
        self._load_tasks()
        # Явно обновляем список задач после загрузки
        self._refresh_tasks()
        
        self.setWindowTitle("TaskMaster")
        self.setMinimumSize(320, 400)
        self.resize(380, 600)
        
        # Устанавливаем иконку окна (если еще не установлена)
        if self.windowIcon().isNull():
            app_icon = create_app_icon()
            self.setWindowIcon(app_icon)
        
        # Автоматическая проверка обновлений при запуске (через 3 секунды)
        QTimer.singleShot(3000, self._check_updates_background)
        
        # Убираем рамку и делаем окно полупрозрачным
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Восстановление состояния окна
        saved_geometry = SettingsManager.get("window_geometry")
        if saved_geometry:
            try:
                self.restoreGeometry(QByteArray.fromBase64(saved_geometry.encode()))
            except Exception as e:
                print(f"Ошибка восстановления геометрии: {e}")
                self.resize(460, 600)
        else:
            self.resize(460, 600)
            
        # Восстановление масштаба
        saved_scale = SettingsManager.get("ui_scale", 1.0)
        if saved_scale != 1.0:
             ZoomManager.set_scale(saved_scale)
             
        # Восстановление прозрачности
        saved_opacity = SettingsManager.get("window_opacity", 0.96)
        self.setWindowOpacity(saved_opacity)
        
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        # Сохранение состояния
        try:
            geometry = self.saveGeometry().toBase64().data().decode()
            SettingsManager.set("window_geometry", geometry)
            SettingsManager.set("ui_scale", ZoomManager.get_scale())
            SettingsManager.set("window_opacity", self.windowOpacity())
        except Exception as e:
            print(f"Ошибка сохранения состояния: {e}")
            
        super().closeEvent(event)

        
    def _setup_ui(self):
        """Настройка интерфейса"""
        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        
        # Главный layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Контейнер с фоном
        container = QFrame()
        container.setObjectName("mainContainer")
        container.setStyleSheet(f"""
            QFrame#mainContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border-radius: 20px;
                border: 1px solid {THEME['border_color']};
            }}
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(16)
        
        # Заголовок с кнопкой закрытия
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        # Заголовок
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        title = QLabel("😎 TaskMaster")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {THEME['text_primary']};")
        title.setTextInteractionFlags(Qt.NoTextInteraction)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        

        
        # Кнопка сворачивания
        self.minimize_btn = MinimizeButton()
        self.minimize_btn.setFixedSize(32, 32)
        self.minimize_btn.clicked.connect(self.showMinimized)
        header_layout.addWidget(self.minimize_btn)
        
        # Кнопка закрытия
        close_btn = CloseButton()
        # Немного увеличим для главного окна
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.exit_application)
        header_layout.addWidget(close_btn)
        
        container_layout.addWidget(self.header_widget)
        
        # Навигатор по датам
        self.date_navigator = DateNavigator(self, self._on_date_changed)
        container_layout.addWidget(self.date_navigator)
        
        # Форма добавления задачи
        self.add_form = QFrame()
        self.add_form.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['form_bg']};
                border-radius: 12px;
                border: 1px solid {THEME['border_color']};
            }}
        """)
        
        form_layout = QVBoxLayout(self.add_form)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setSpacing(8)
        
        # Поле ввода названия
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Новая задача...")
        self.title_input.setFont(QFont("Segoe UI", 11))
        self.title_input.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.title_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['input_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {THEME['text_primary']};
                selection-background-color: #6bcf7f;
                selection-color: #ffffff;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(107, 207, 127, 0.6);
                background-color: {THEME['input_bg_focus']};
            }}
            QLineEdit::selection {{
                background-color: #6bcf7f !important;
                color: #ffffff !important;
            }}
        """)
        self.title_input.returnPressed.connect(self._add_task)
        form_layout.addWidget(self.title_input)
        
        # Выбор приоритета и кнопка добавления
        priority_layout = QHBoxLayout()
        priority_layout.setSpacing(8)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["⚡ Высокий", "⭐ Средний", "✓ Низкий"])
        self.priority_combo.setCurrentIndex(1)
        self.priority_combo.setFont(QFont("Segoe UI", 10))
        self.priority_combo.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.priority_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {THEME['input_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
                padding: 8px 12px;
                color: {THEME['text_primary']};
            }}
            QComboBox:hover {{
                background-color: {THEME['input_bg_focus']};
            }}
            QComboBox:focus {{
                border: 1px solid rgba(107, 207, 127, 0.6);
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {THEME['card_bg']};
                border: 1px solid {THEME['border_color']};
                color: {THEME['text_primary']};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {THEME['card_bg_hover']};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: transparent;
                color: {THEME['text_primary']};
            }}
        """)
        # Убираем стретч-фактор 1, чтобы комбобокс не задавливал кнопку
        self.priority_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        priority_layout.addWidget(self.priority_combo)
        
        self.add_btn = QPushButton("+ Добавить")
        # Используем Minimum, но с большим min-width
        self.add_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.add_btn.setFont(QFont("Segoe UI", 10, QFont.Medium))
        self.add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        # Жесткий минимум
        self.add_btn.setMinimumWidth(120) 
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent_bg']};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                color: {THEME['accent_text']};
            }}
            QPushButton:hover {{
                background-color: {THEME['accent_hover']};
            }}
        """)
        self.add_btn.clicked.connect(self._add_task)
        priority_layout.addWidget(self.add_btn)
        
        form_layout.addLayout(priority_layout)
        container_layout.addWidget(self.add_form)
        
        # Счетчик задач
        self.task_counter = QLabel("0 задач")
        self.task_counter.setFont(QFont("Segoe UI", 9))
        self.task_counter.setStyleSheet(f"color: {THEME['text_secondary']};")
        self.task_counter.setTextInteractionFlags(Qt.NoTextInteraction)
        container_layout.addWidget(self.task_counter)
        
        # Область прокрутки для задач
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {THEME['scroll_handle']};
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        # Контейнер для задач
        self.tasks_container = QWidget()
        self.tasks_container.setStyleSheet("background: transparent;")
        main_tasks_layout = QVBoxLayout(self.tasks_container)
        main_tasks_layout.setContentsMargins(0, 0, 0, 0)
        main_tasks_layout.setSpacing(16)
        
        # === Секция активных задач ===
        active_header = QLabel("📋 Активные задачи")
        active_header.setFont(QFont("Segoe UI", 11, QFont.Bold))
        active_header.setStyleSheet(f"color: {THEME['text_primary']}; padding: 8px 0px;")
        main_tasks_layout.addWidget(active_header)
        
        # Контейнер для активных задач с поддержкой drop
        self.active_tasks_container = DropZoneWidget("active", self)
        self.active_tasks_container.setObjectName("active_drop_zone")
        self.active_tasks_layout = QVBoxLayout(self.active_tasks_container)
        self.active_tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.active_tasks_layout.setSpacing(8)
        self.active_tasks_layout.addStretch()
        main_tasks_layout.addWidget(self.active_tasks_container, 1)  # Stretch factor 1
        
        # === Разделитель ===
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {THEME['border_color']}; max-height: 1px;")
        main_tasks_layout.addWidget(separator)
        
        # === Секция выполненных задач ===
        completed_header_widget = CompletedHeaderWidget(self)
        completed_header_layout = QHBoxLayout(completed_header_widget)
        completed_header_layout.setContentsMargins(0, 0, 0, 0)
        completed_header_layout.setSpacing(8)
        
        # Кнопка сворачивания/разворачивания
        self.toggle_completed_btn = QPushButton("▼")
        self.toggle_completed_btn.setFixedSize(24, 24)
        self.toggle_completed_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_completed_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {THEME['text_secondary']};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {THEME['text_primary']};
            }}
        """)
        self.toggle_completed_btn.clicked.connect(self._toggle_completed_section)
        completed_header_layout.addWidget(self.toggle_completed_btn)
        
        self.completed_header_label = QLabel("✅ Выполненные задачи (0)")
        self.completed_header_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.completed_header_label.setStyleSheet(f"color: {THEME['text_secondary']}; padding: 8px 0px;")
        completed_header_layout.addWidget(self.completed_header_label)
        completed_header_layout.addStretch()
        
        main_tasks_layout.addWidget(completed_header_widget)
        
        # Контейнер для выполненных задач с поддержкой drop
        self.completed_tasks_container = DropZoneWidget("completed", self)
        self.completed_tasks_container.setObjectName("completed_drop_zone")
        self.completed_tasks_container.setFixedHeight(200)  # Фиксированная высота для drop зоны
        self.completed_tasks_layout = QVBoxLayout(self.completed_tasks_container)
        self.completed_tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.completed_tasks_layout.setSpacing(8)
        self.completed_tasks_layout.addStretch()
        main_tasks_layout.addWidget(self.completed_tasks_container, 0)  # Stretch factor 0 - не растягивается
        
        # Для обратной совместимости
        self.tasks_layout = self.active_tasks_layout
        
        scroll.setWidget(self.tasks_container)
        container_layout.addWidget(scroll, 1)
        
        # --- Bottom Bar with Zoom Slider ---
        bottom_bar = QFrame()
        bottom_bar.setFixedHeight(40)
        bottom_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['window_bg_start']};
                border-top: none; 
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }}
        """)
        
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 0, 8, 0)
        bottom_layout.setSpacing(10)
        
        # --- Кнопки управления (Шрифт и Прозрачность) ---
        
        # Контейнер для инструментов (скрыт по умолчанию)
        self.tools_container = QFrame()
        self.tools_container.setVisible(False) # Скрыто по умолчанию
        tools_layout = QHBoxLayout(self.tools_container)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(8)
        
        # 1. Шрифт
        self.zoom_btn = QPushButton("Aa")
        self.zoom_btn.setFixedSize(32, 32)
        self.zoom_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.zoom_btn.setToolTip("Размер шрифта")
        self.zoom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border_color']};
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                border-color: {THEME['accent_hover']};
            }}
        """)
        self.zoom_btn.clicked.connect(self._show_zoom_slider)
        tools_layout.addWidget(self.zoom_btn)
        
        # 2. Прозрачность
        self.opacity_btn = QPushButton("💧")
        self.opacity_btn.setFixedSize(32, 32)
        self.opacity_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.opacity_btn.setToolTip("Прозрачность окна")
        self.opacity_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border_color']};
                border-radius: 6px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                border-color: {THEME['accent_hover']};
            }}
        """)
        self.opacity_btn.clicked.connect(self._show_opacity_slider)
        tools_layout.addWidget(self.opacity_btn)
        
        # Разделитель
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedSize(1, 20)
        sep.setStyleSheet(f"background-color: {THEME['border_color']}; border: none;")
        tools_layout.addWidget(sep)
        
        # Кнопка минималистичного режима
        self.minimal_mode_btn = QPushButton("≡")
        self.minimal_mode_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.minimal_mode_btn.setToolTip("Минималистичный режим")
        self.minimal_mode_btn.setCheckable(True)
        self.minimal_mode_btn.setFixedSize(24, 24)
        self.minimal_mode_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {THEME['text_secondary']};
                font-size: 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['text_primary']};
            }}
            QPushButton:checked {{
                background-color: {THEME['accent_bg']};
                color: {THEME['accent_text']};
            }}
        """)
        self.minimal_mode_btn.clicked.connect(self._toggle_minimal_mode)
        tools_layout.addWidget(self.minimal_mode_btn)
        
        # Кнопка включения/выключения звуков
        # Загружаем состояние звуков из настроек
        sounds_enabled = SettingsManager.get("sounds_enabled", True)
        self.sound_btn = QPushButton("🔊" if sounds_enabled else "🔇")
        self.sound_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.sound_btn.setToolTip("Выключить звуки" if sounds_enabled else "Включить звуки")
        self.sound_btn.setCheckable(True)
        self.sound_btn.setChecked(sounds_enabled)
        self.sound_btn.setFixedSize(24, 24)
        self.sound_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {THEME['text_secondary']};
                font-size: 14px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['text_primary']};
            }}
            QPushButton:checked {{
                background-color: {THEME['accent_bg']};
                color: {THEME['accent_text']};
            }}
        """)
        self.sound_btn.clicked.connect(self._toggle_sounds)
        tools_layout.addWidget(self.sound_btn)
        
        # Кнопка закрепления (Always on Top)
        self.pin_btn = QPushButton("📌")
        self.pin_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.pin_btn.setToolTip("Поверх всех окон")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(True) # По умолчанию у нас стоит StaysOnTop
        self.pin_btn.setFixedSize(24, 24)
        self.pin_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {THEME['text_secondary']};
                font-size: 14px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['text_primary']};
            }}
            QPushButton:checked {{
                background-color: {THEME['accent_bg']};
                color: {THEME['accent_text']};
            }}
        """)
        self.pin_btn.clicked.connect(self._toggle_pin)
        tools_layout.addWidget(self.pin_btn)
        
        # Кнопка смены темы (Акцентный цвет)
        self.theme_btn = QPushButton("🎨")
        self.theme_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.theme_btn.setToolTip("Сменить цвет темы")
        self.theme_btn.setFixedSize(24, 24)
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {THEME['text_secondary']};
                font-size: 14px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['text_primary']};
            }}
        """)
        self.theme_btn.clicked.connect(self._show_theme_menu)
        tools_layout.addWidget(self.theme_btn)
        



        # Кнопка справки (Слева от обновления)
        self.help_btn = QPushButton("❓")
        self.help_btn.setFixedSize(32, 32)
        self.help_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.help_btn.setToolTip("О программе")
        self.help_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #ff4d4d;
                border: 1px solid {THEME['border_color']};
                border-radius: 16px; 
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                border-color: #ff4d4d;
            }}
        """)
        self.help_btn.clicked.connect(self._show_about)
        bottom_layout.addWidget(self.help_btn)

        # Кнопка проверки обновлений (с badge)
        update_container = QWidget()
        update_container.setFixedSize(32, 32)
        update_container_layout = QVBoxLayout(update_container)
        update_container_layout.setContentsMargins(0, 0, 0, 0)
        update_container_layout.setSpacing(0)
        
        self.update_btn = QPushButton("🔄")
        self.update_btn.setFixedSize(32, 32)
        self.update_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.update_btn.setToolTip("Проверить обновления")
        self.update_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {THEME['text_secondary']};
                border: 1px solid {THEME['border_color']};
                border-radius: 16px; 
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['text_primary']};
                border-color: {THEME['accent_hover']};
            }}
        """)
        self.update_btn.clicked.connect(self._check_updates)
        
        # Badge для уведомления об обновлении
        self.update_badge = QLabel()
        self.update_badge.setFixedSize(10, 10)
        self.update_badge.setStyleSheet("""
            QLabel {
                background-color: #ff4444;
                border-radius: 5px;
                border: 2px solid #1a1d2e;
            }
        """)
        self.update_badge.hide()  # Скрыт по умолчанию
        self.update_badge.setParent(self.update_btn)
        self.update_badge.move(22, 2)  # Позиция в правом верхнем углу
        
        bottom_layout.addWidget(self.update_btn)

        # Кнопка переключения инструментов (Слева)
        self.toggle_tools_btn = QPushButton("🛠️")
        self.toggle_tools_btn.setFixedSize(32, 32)
        self.toggle_tools_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_tools_btn.setToolTip("Показать инструменты")
        self.toggle_tools_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {THEME['text_secondary']};
                border: 1px solid {THEME['border_color']};
                border-radius: 16px; 
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['text_primary']};
                border-color: {THEME['accent_hover']};
            }}
        """)
        self.toggle_tools_btn.clicked.connect(self._toggle_tools)
        bottom_layout.addWidget(self.toggle_tools_btn)

        # Добавляем контейнер инструментов в нижнюю панель (сразу за кнопкой)
        bottom_layout.addWidget(self.tools_container)
        
        # Спейсер, чтобы сдвинуть всё влево
        bottom_layout.addStretch()
        
        # Интеграция Grip прямо в bottom_bar
        grip_wrapper = QWidget()
        grip_wrapper.setFixedSize(24, 24)
        grip_wrapper.setStyleSheet("background: transparent;")
        
        grip_layout = QVBoxLayout(grip_wrapper)
        grip_layout.setContentsMargins(0,0,0,0)
        
        # Иконка
        resize_icon = QLabel("⇲")
        resize_icon.setStyleSheet(f"""
            color: {THEME['text_secondary']};
            font-size: 12px;
            font-weight: bold;
            background: transparent;
        """)
        resize_icon.setAlignment(Qt.AlignCenter)
        grip_layout.addWidget(resize_icon)
        
        # Сам функциональный QSizeGrip поверх
        size_grip = QSizeGrip(grip_wrapper)
        size_grip.setStyleSheet("background: transparent;")
        size_grip.setFixedSize(24, 24)
        
        # Хак: кладем grip поверх иконки
        # Но проще просто добавить виджет в лейаут
        bottom_layout.addWidget(grip_wrapper)
        
        container_layout.addWidget(bottom_bar)
        
        main_layout.addWidget(container)
    
    
    def _toggle_tools(self):
        """Переключение видимости панели инструментов"""
        is_visible = self.tools_container.isVisible()
        
        # Анимация появления/исчезновения (опционально)
        # Для простоты пока используем setVisible
        self.tools_container.setVisible(not is_visible)
        
        # Обновляем иконку/состояние кнопки
        if not is_visible:
            self.toggle_tools_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME['accent_bg']};
                    color: {THEME['accent_text']};
                    border: 1px solid {THEME['accent_hover']};
                    border-radius: 16px; 
                    font-size: 16px;
                }}
            """)
        else:
            self.toggle_tools_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {THEME['text_secondary']};
                    border: 1px solid {THEME['border_color']};
                    border-radius: 16px; 
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['secondary_hover']};
                    color: {THEME['text_primary']};
                    border-color: {THEME['accent_hover']};
                }}
            """)
    
    def _toggle_completed_section(self):
        """Переключение видимости секции выполненных задач"""
        is_visible = self.completed_tasks_container.isVisible()
        
        if is_visible:
            # Сворачиваем
            self.toggle_completed_btn.setText("▶")
            self.completed_tasks_container.setVisible(False)
        else:
            # Разворачиваем
            self.toggle_completed_btn.setText("▼")
            self.completed_tasks_container.setVisible(True)


    def _show_zoom_slider(self):
        """Показать вертикальный слайдер масштаба"""
        # Текущий масштаб
        current_val = int(ZoomManager.get_scale() * 100)
        
        popup = SliderPopup(
            parent=self, 
            title="Aa", 
            value=current_val, 
            min_val=80, 
            max_val=150, 
            on_change=self._on_zoom_changed
        )
        
        # Важно: сначала подгоняем размер, чтобы знать высоту
        popup.adjustSize()
        
        # Позиционируем над кнопкой
        pos = self.zoom_btn.mapToGlobal(QPoint(0, 0))
        x = pos.x() - (popup.width() - self.zoom_btn.width()) // 2
        y = pos.y() - popup.height() - 10
        
        # Проверка границ экрана
        screen_geo = self.screen().geometry()
        if x < screen_geo.left(): x = screen_geo.left() + 5
        if x + popup.width() > screen_geo.right(): x = screen_geo.right() - popup.width() - 5
        
        popup.move(x, y)
        popup.exec()

    def _show_opacity_slider(self):
        """Показать вертикальный слайдер прозрачности"""
        # Текущая прозрачность (0.0 - 1.0) -> (20 - 100)
        current_opacity = int(self.windowOpacity() * 100)
        
        def on_opacity_change(val):
            self.setWindowOpacity(val / 100.0)
            
        popup = SliderPopup(
            parent=self, 
            title="💧", 
            value=current_opacity, 
            min_val=20, # Не даем сделать совсем прозрачным
            max_val=100, 
            on_change=on_opacity_change
        )
        
        # Важно: сначала подгоняем размер, чтобы знать высоту
        popup.adjustSize()
        
        # Позиционируем над кнопкой
        pos = self.opacity_btn.mapToGlobal(QPoint(0, 0))
        x = pos.x() - (popup.width() - self.opacity_btn.width()) // 2
        y = pos.y() - popup.height() - 10

        # Проверка границ экрана
        screen_geo = self.screen().geometry()
        if x < screen_geo.left(): x = screen_geo.left() + 5
        if x + popup.width() > screen_geo.right(): x = screen_geo.right() - popup.width() - 5
        
        popup.move(x, y)
        popup.exec()

    def mousePressEvent(self, event):
        """Начало перетаскивания окна"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Перетаскивание окна"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def eventFilter(self, obj, event):
        """Фильтр событий для обновления позиции grip"""
        if obj == self.grip_container and event.type() == event.Type.Resize:
            if hasattr(self, 'grip_wrapper'):
                # Размер кнопки 24x24, отступы контейнера 20px, позиционируем: ширина - отступ - размер кнопки
                self.grip_wrapper.move(obj.width() - 44, obj.height() - 44)
                self.grip_wrapper.raise_()
        return super().eventFilter(obj, event)
    
    def showEvent(self, event):
        """Обновление позиции grip при показе окна"""
        super().showEvent(event)
        if hasattr(self, 'grip_wrapper') and hasattr(self, 'grip_container'):
            # Используем QTimer для отложенного обновления после полной отрисовки
            from PySide6.QtCore import QTimer
            QTimer.singleShot(10, lambda: self._update_grip_position())
    
    def _update_grip_position(self):
        """Обновление позиции grip"""
        if hasattr(self, 'grip_wrapper') and hasattr(self, 'grip_container'):
            # Размер кнопки 24x24, отступы контейнера 20px, позиционируем: ширина - отступ - размер кнопки
            self.grip_wrapper.move(self.grip_container.width() - 44, self.grip_container.height() - 44)
            self.grip_wrapper.raise_()
    
    def resizeEvent(self, event):
        """Обновление позиции grip при изменении размера окна"""
        super().resizeEvent(event)
        self._update_grip_position()
    
    def _load_tasks(self):
        """Загрузка задач"""
        self.tasks = TaskStorage.load()
        # Проверяем и создаем повторяющиеся задачи
        self._check_recurring_tasks()
    
    def _refresh_tasks(self):
        """Обновление списка задач"""
        # Проверяем, существуют ли layouts
        if not hasattr(self, 'active_tasks_layout') or self.active_tasks_layout is None:
            return
        
        # Очистка активных задач
        while self.active_tasks_layout.count() > 1:  # Оставляем stretch
            item = self.active_tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Очистка выполненных задач
        while self.completed_tasks_layout.count() > 1:  # Оставляем stretch
            item = self.completed_tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Фильтрация задач по дате
        current_date_str = self.selected_date.toString("yyyy-MM-dd")
        is_today = self.selected_date == QDate.currentDate()
        
        filtered_tasks = []
        for task in self.tasks:
            # Если сегодня - показываем:
            # 1. Задачи без даты (старые/Inbox)
            # 2. Задачи на сегодня
            # 3. Просроченные задачи (дата меньше сегодня)
            if is_today:
                if not task.due_date:
                    filtered_tasks.append(task)
                elif task.due_date <= current_date_str:
                    filtered_tasks.append(task)
            # Иначе показываем только по точному совпадению даты
            elif task.due_date == current_date_str:
                filtered_tasks.append(task)
        
        # Разделяем на активные и выполненные
        active_tasks = [t for t in filtered_tasks if t.status != "Выполнено"]
        completed_tasks = [t for t in filtered_tasks if t.status == "Выполнено"]
        
        # Сортировка активных по приоритету
        priority_map = {"high": 0, "medium": 1, "low": 2}
        active_tasks.sort(key=lambda t: priority_map.get(t.priority, 3))
        
        # Добавление карточек активных задач
        for task in active_tasks:
            card = TaskCard(task, self)
            card.setAcceptDrops(False)  # Карточки не принимают drop
            self.active_tasks_layout.insertWidget(self.active_tasks_layout.count() - 1, card)
        
        # Добавление карточек выполненных задач
        for task in completed_tasks:
            card = TaskCard(task, self)
            card.setAcceptDrops(False)
            self.completed_tasks_layout.insertWidget(self.completed_tasks_layout.count() - 1, card)
        
        # Обновление счетчиков
        total = len(filtered_tasks)
        completed_count = len(completed_tasks)
        
        # Склонения
        tasks_word = pluralize(total, ('задача', 'задачи', 'задач'))
        completed_word = pluralize(completed_count, ('выполнена', 'выполнены', 'выполнено'))
        
        self.task_counter.setText(f"{total} {tasks_word} • {completed_count} {completed_word}")
        self.completed_header_label.setText(f"✅ Выполненные задачи ({completed_count})")
        
        # Автоматическое скрытие/показ секции выполненных задач
        if completed_count == 0:
            # Скрываем секцию если нет выполненных задач
            self.completed_tasks_container.setVisible(False)
            self.toggle_completed_btn.setText("▶")
        else:
            # Показываем секцию если есть выполненные задачи
            if not self.completed_tasks_container.isVisible():
                self.completed_tasks_container.setVisible(True)
                self.toggle_completed_btn.setText("▼")

    def _on_date_changed(self, date):
        """Обработка смены даты"""
        self.selected_date = date
        # НЕ проверяем повторяющиеся задачи при смене даты в навигаторе
        # Проверка выполняется только при загрузке приложения
        self._refresh_tasks()
    
    def _check_recurring_tasks(self):
        """Проверка и создание повторяющихся задач"""
        today = QDate.currentDate()
        today_str = today.toString("yyyy-MM-dd")
        tasks_to_add = []
        tasks_to_update = []
        
        # Получаем список всех существующих дат задач для проверки дубликатов
        existing_dates = set()
        for t in self.tasks:
            if t.due_date and t.title:  # Проверяем по дате и названию
                existing_dates.add((t.due_date, t.title))
        
        for task in self.tasks:
            # Пропускаем задачи без повторения или уже выполненные
            if not task.repeat_type:
                continue
            
            # Пропускаем выполненные задачи - они не должны создавать повторения
            if task.status == "Выполнено":
                continue
            
            # Если задача не имеет даты, пропускаем
            if not task.due_date:
                continue
                
            task_date = QDate.fromString(task.due_date, "yyyy-MM-dd")
            if not task_date.isValid():
                continue
            
            # Определяем дату для следующего повторения
            last_repeated = None
            if task.last_repeated_date:
                last_repeated = QDate.fromString(task.last_repeated_date, "yyyy-MM-dd")
            
            # Вычисляем следующую дату повторения
            next_date = None
            
            if task.repeat_type == "daily":
                # Ежедневно: следующая дата = завтра от последнего повторения или от даты задачи
                if last_repeated and last_repeated.isValid():
                    next_date = last_repeated.addDays(1)
                else:
                    # Первое повторение: создаем на следующий день после даты задачи
                    next_date = task_date.addDays(1)
                
                # Создаем только одну задачу на следующий день, если она еще не наступила в будущем
                # и такой задачи еще нет
                if next_date <= today:
                    date_str = next_date.toString("yyyy-MM-dd")
                    # Проверяем, что такой задачи еще нет
                    if (date_str, task.title) not in existing_dates:
                        new_id = max([t.id for t in self.tasks], default=0) + len(tasks_to_add) + 1
                        new_task = Task(
                            id=new_id,
                            title=task.title,
                            description=task.description,
                            priority=task.priority,
                            status="Не выполнено",
                            due_date=date_str,
                            created=datetime.now().strftime("%d.%m.%Y %H:%M"),
                            repeat_type=task.repeat_type,
                            last_repeated_date=None
                        )
                        tasks_to_add.append(new_task)
                        existing_dates.add((date_str, task.title))
                        # Обновляем дату последнего повторения на дату созданной задачи
                        task.last_repeated_date = date_str
                        tasks_to_update.append(task)
                        
            elif task.repeat_type == "weekly":
                # Еженедельно: следующая дата через 7 дней
                if last_repeated and last_repeated.isValid():
                    next_date = last_repeated.addDays(7)
                else:
                    next_date = task_date.addDays(7)
                
                # Создаем только если следующая дата уже наступила
                if next_date <= today:
                    date_str = next_date.toString("yyyy-MM-dd")
                    # Проверяем, что такой задачи еще нет
                    if (date_str, task.title) not in existing_dates:
                        new_id = max([t.id for t in self.tasks], default=0) + len(tasks_to_add) + 1
                        new_task = Task(
                            id=new_id,
                            title=task.title,
                            description=task.description,
                            priority=task.priority,
                            status="Не выполнено",
                            due_date=date_str,
                            created=datetime.now().strftime("%d.%m.%Y %H:%M"),
                            repeat_type=task.repeat_type,
                            last_repeated_date=None
                        )
                        tasks_to_add.append(new_task)
                        task.last_repeated_date = today_str
                        tasks_to_update.append(task)
                        
            elif task.repeat_type == "monthly":
                # Ежемесячно: следующая дата через 30 дней
                if last_repeated and last_repeated.isValid():
                    next_date = last_repeated.addDays(30)
                else:
                    next_date = task_date.addDays(30)
                
                # Создаем только если следующая дата уже наступила
                if next_date <= today:
                    date_str = next_date.toString("yyyy-MM-dd")
                    # Проверяем, что такой задачи еще нет
                    if (date_str, task.title) not in existing_dates:
                        new_id = max([t.id for t in self.tasks], default=0) + len(tasks_to_add) + 1
                        new_task = Task(
                            id=new_id,
                            title=task.title,
                            description=task.description,
                            priority=task.priority,
                            status="Не выполнено",
                            due_date=date_str,
                            created=datetime.now().strftime("%d.%m.%Y %H:%M"),
                            repeat_type=task.repeat_type,
                            last_repeated_date=None
                        )
                        tasks_to_add.append(new_task)
                        task.last_repeated_date = today_str
                        tasks_to_update.append(task)
        
        # Добавляем новые задачи
        if tasks_to_add:
            self.tasks.extend(tasks_to_add)
            TaskStorage.save(self.tasks)
    
    def _add_task(self):
        """Добавление новой задачи через диалог"""
        # Если в поле ввода есть текст, используем его как начальное название
        initial_title = self.title_input.text().strip()
        
        # Дату берем из навигатора
        current_date_str = self.selected_date.toString("yyyy-MM-dd")
        
        # Создаём временную задачу для передачи начальных данных
        temp_task = None
        if initial_title:
            priority_map = {0: "high", 1: "medium", 2: "low"}
            temp_task = Task(
                id=0,
                title=initial_title,
                description="",
                priority=priority_map[self.priority_combo.currentIndex()],
                status="Не выполнено",
                due_date=current_date_str,
                created=""
            )
        
        dialog = TaskDialog(self, temp_task)
        # Если создаем с нуля, предустанавливаем дату в диалоге
        # The following lines are part of a dataclass definition and should not be inside this method.
        # Assuming the user intended to provide the definition of the Task dataclass,
        # these lines are placed here as per the instruction, but this will cause a syntax error.
        # To make it syntactically correct, these lines should be placed at the module level
        # where the Task dataclass is defined.
        # priority: str = "Средний"     # Высокий, Средний, Низкий
        # due_date: Optional[str] = None # ISO format YYYY-MM-DD

        # def to_dict(self):
        #     return {
        #         "id": self.id,
        #         "title": self.title,
        #         "description": self.description,
        #         "completed": self.completed,
        #         "created_at": self.created_at,
        #         "priority": self.priority,
        #         "due_date": self.due_date
        #     }

        # @classmethod
        # def from_dict(cls, data):
        #     return cls(
        #         id=data["id"],
        #         title=data["title"],
        #         description=data.get("description", ""),
        #         completed=data["completed"],
        #         created_at=data["created_at"],
        #         priority=data.get("priority", "Средний"),
        #         due_date=data.get("due_date")
        #     )
        if not temp_task:
            dialog.date_edit.setDate(self.selected_date)
        
        if dialog.exec():
            data = dialog.get_data()
            
            if not data["title"]:
                return
            
            # Создание задачи
            new_id = max([t.id for t in self.tasks], default=0) + 1
            
            task = Task(
                id=new_id,
                title=data["title"],
                description=data["description"],
                priority=data["priority"],
                status="Не выполнено",
                due_date=data["due_date"],
                created=datetime.now().strftime("%d.%m.%Y %H:%M"),
                repeat_type=data.get("repeat_type"),
                last_repeated_date=None
            )
            
            self.tasks.append(task)
            TaskStorage.save(self.tasks)
            self._refresh_tasks()
            
            # Очистка поля ввода
            self.title_input.clear()
            self.title_input.setFocus()
    
    def toggle_task_status(self, task_id: int):
        """Переключение статуса задачи"""
        for task in self.tasks:
            if task.id == task_id:
                task.status = "Выполнено" if task.status != "Выполнено" else "Не выполнено"
                break
        
        TaskStorage.save(self.tasks)
        self._refresh_tasks()
    
    def delete_task(self, task_id: int):
        """Удаление задачи"""
        self.tasks = [t for t in self.tasks if t.id != task_id]
        TaskStorage.save(self.tasks)
        self._refresh_tasks()
    
    def edit_task(self, task: Task):
        """Редактирование задачи через диалог"""
        dialog = TaskDialog(self, task)
        
        if dialog.exec():
            data = dialog.get_data()
            
            if not data["title"]:
                return
            
            # Обновляем задачу
            for t in self.tasks:
                if t.id == task.id:
                    t.title = data["title"]
                    t.description = data["description"]
                    t.priority = data["priority"]
                    t.due_date = data["due_date"]
                    t.repeat_type = data.get("repeat_type")
                    break
            
            TaskStorage.save(self.tasks)
            self._refresh_tasks()
    
    def _on_zoom_changed(self, value):
        """Обработка изменения масштаба"""
        scale = value / 100.0
        ZoomManager.set_scale(scale)
        self._refresh_ui_scale()
        
    def _refresh_ui_scale(self):
        """Обновление UI при изменении масштаба"""
        # Обновляем отступы макета задач
        if hasattr(self, 'tasks_layout'):
            self.tasks_layout.setSpacing(ZoomManager.scaled(8))
            
            # Обновляем каждую карточку задачи
            for i in range(self.tasks_layout.count()):
                item = self.tasks_layout.itemAt(i)
                widget = item.widget()
                if widget and hasattr(widget, 'update_ui_scale'):
                    widget.update_ui_scale()
        
        # Обновляем шрифт счетчика задач
        if hasattr(self, 'task_counter'):
            self.task_counter.setFont(ZoomManager.font("Segoe UI", 9))
            
        # Обновляем шрифты и элементы основной формы
        if hasattr(self, 'add_btn'):
            self.add_btn.setFont(ZoomManager.font("Segoe UI", 10, QFont.Medium))
            # Динамически обновляем минимальную ширину
            calc_width = ZoomManager.scaled(120)
            self.add_btn.setMinimumWidth(calc_width)
            self.add_btn.setMaximumWidth(16777215) # MAX_SIZE
            
            self.add_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME['accent_bg']};
                    border: none;
                    border-radius: {ZoomManager.scaled(8)}px;
                    padding: {ZoomManager.scaled(8)}px {ZoomManager.scaled(16)}px;
                    color: {THEME['accent_text']};
                }}
                QPushButton:hover {{
                    background-color: {THEME['accent_hover']};
                }}
            """)

            
        if hasattr(self, 'title_input'):
            self.title_input.setFont(ZoomManager.font("Segoe UI", 11))
            self.title_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['input_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: {ZoomManager.scaled(8)}px;
                padding: {ZoomManager.scaled(10)}px {ZoomManager.scaled(12)}px;
                color: {THEME['text_primary']};
                selection-background-color: #6bcf7f;
                selection-color: #ffffff;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(107, 207, 127, 0.6);
                background-color: {THEME['input_bg_focus']};
            }}
            QLineEdit::selection {{
                background-color: #6bcf7f !important;
                color: #ffffff !important;
            }}
        """)
            
        if hasattr(self, 'priority_combo'):
            self.priority_combo.setFont(ZoomManager.font("Segoe UI", 10))
        
        # Обновляем все карточки задач (пересоздаем их)
        self._refresh_tasks()

        # Обновляем шрифты в инпутах
        font_input = ZoomManager.font("Segoe UI", 11)
        if hasattr(self, 'title_input'):
            self.title_input.setFont(font_input)
            
        # Force layout update
        self.updateGeometry()

    def _toggle_minimal_mode(self, checked):
        """Переключение минималистичного режима"""
        visible = not checked
        
        # Скрываем/показываем элементы
        if hasattr(self, 'header_widget'):
            self.header_widget.setVisible(visible)
        
        # Скрываем форму добавления
        if hasattr(self, 'add_form'):
            self.add_form.setVisible(visible)
            
        # Скрываем счетчик
        if hasattr(self, 'task_counter'):
            self.task_counter.setVisible(visible)
            
        # Можно немного уменьшить окно автоматически при переходе в мини-режим, если оно слишком большое
        if checked:
            self._saved_geometry = self.geometry()
            self.resize(self.width(), 300) # Compact height
        elif hasattr(self, '_saved_geometry'):
            self.setGeometry(self._saved_geometry)

    def _toggle_sounds(self, checked):
        """Переключение звуков"""
        SettingsManager.set("sounds_enabled", checked)
        # Обновляем иконку кнопки
        self.sound_btn.setText("🔊" if checked else "🔇")
        self.sound_btn.setToolTip("Включить звуки" if not checked else "Выключить звуки")
    
    def _toggle_pin(self, checked):
        """Переключение режима 'Поверх всех окон'"""
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
        self.show() # Необходимо вызвать show после изменения флагов
        
    def _show_about(self):
        """Показать диалог 'О программе'"""
        dialog = AboutDialog(self)
        dialog.exec()
        
    def _check_updates(self):
        """Проверка обновлений через GitHub"""
        from PySide6.QtWidgets import QMessageBox, QProgressDialog
        import urllib.request
        import json
        
        # Скрываем badge так как пользователь проверяет обновления
        self._show_update_badge(False)
        
        try:
            from version import __version__, GITHUB_API_URL
        except ImportError:
            __version__ = "1.0.0"
            GITHUB_API_URL = "https://api.github.com/repos/elementary1997/taskmaster/releases/latest"
        
        # Диалог проверки
        progress = QProgressDialog("Проверка обновлений...", None, 0, 0, self)
        progress.setWindowTitle("TaskMaster")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()
        
        try:
            # Запрос к GitHub API
            req = urllib.request.Request(GITHUB_API_URL)
            req.add_header('User-Agent', 'TaskMaster')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                latest_version = data['tag_name'].lstrip('v')
                download_url = data.get('html_url', '')
                changelog = data.get('body', 'Нет описания изменений')
                
                progress.close()
                
                # Сравнение версий
                if self._compare_versions(latest_version, __version__) > 0:
                    # Доступно обновление
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Доступно обновление")
                    msg.setIcon(QMessageBox.Information)
                    msg.setText(f"Доступна новая версия TaskMaster v{latest_version}")
                    msg.setInformativeText(
                        f"Текущая версия: v{__version__}\n"
                        f"Новая версия: v{latest_version}\n\n"
                        f"Изменения:\n{changelog[:200]}..."
                    )
                    
                    # Кнопки
                    download_btn = msg.addButton("Скачать", QMessageBox.AcceptRole)
                    msg.addButton("Позже", QMessageBox.RejectRole)
                    
                    # Стилизация
                    msg.setStyleSheet(f"""
                        QMessageBox {{
                            background-color: {THEME['window_bg_end']};
                        }}
                        QLabel {{
                            color: {THEME['text_primary']};
                            font-size: 13px;
                        }}
                        QPushButton {{
                            background-color: {THEME['accent_bg']};
                            color: {THEME['accent_text']};
                            border: none;
                            border-radius: 6px;
                            padding: 8px 20px;
                            min-width: 100px;
                            font-size: 13px;
                        }}
                        QPushButton:hover {{
                            background-color: {THEME['accent_hover']};
                        }}
                    """)
                    
                    msg.exec()
                    
                    if msg.clickedButton() == download_btn:
                        # Открываем страницу релиза в браузере
                        import webbrowser
                        webbrowser.open(download_url)
                else:
                    # Уже последняя версия
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Обновление TaskMaster")
                    msg.setText(f"У вас установлена последняя версия TaskMaster v{__version__}")
                    msg.setIcon(QMessageBox.Information)
                    
                    # Стилизация
                    msg.setStyleSheet(f"""
                        QMessageBox {{
                            background-color: {THEME['window_bg_end']};
                        }}
                        QLabel {{
                            color: {THEME['text_primary']};
                            font-size: 14px;
                        }}
                        QPushButton {{
                            background-color: {THEME['accent_bg']};
                            color: {THEME['accent_text']};
                            border: none;
                            border-radius: 6px;
                            padding: 6px 16px;
                            min-width: 80px;
                        }}
                        QPushButton:hover {{
                            background-color: {THEME['accent_hover']};
                        }}
                    """)
                    msg.exec()
                    
        except urllib.error.HTTPError as e:
            progress.close()
            
            if e.code == 404:
                # Нет релизов на GitHub
                msg = QMessageBox(self)
                msg.setWindowTitle("Обновление TaskMaster")
                msg.setText(f"У вас установлена последняя версия TaskMaster v{__version__}")
                msg.setInformativeText("Релизы пока не опубликованы на GitHub.")
                msg.setIcon(QMessageBox.Information)
                msg.setStyleSheet(f"""
                    QMessageBox {{
                        background-color: {THEME['window_bg_end']};
                    }}
                    QLabel {{
                        color: {THEME['text_primary']};
                        font-size: 13px;
                    }}
                    QPushButton {{
                        background-color: {THEME['accent_bg']};
                        color: {THEME['accent_text']};
                        border: none;
                        border-radius: 6px;
                        padding: 6px 16px;
                    }}
                """)
                msg.exec()
            else:
                # Другая HTTP ошибка
                msg = QMessageBox(self)
                msg.setWindowTitle("Ошибка")
                msg.setText("Не удалось проверить обновления")
                msg.setInformativeText(f"HTTP ошибка: {e.code}")
                msg.setIcon(QMessageBox.Warning)
                msg.setStyleSheet(f"""
                    QMessageBox {{
                        background-color: {THEME['window_bg_end']};
                    }}
                    QLabel {{
                        color: {THEME['text_primary']};
                    }}
                    QPushButton {{
                        background-color: {THEME['accent_bg']};
                        color: {THEME['accent_text']};
                        border: none;
                        border-radius: 6px;
                        padding: 6px 16px;
                    }}
                """)
                msg.exec()
                    
        except Exception as e:
            progress.close()
            
            # Ошибка проверки
            msg = QMessageBox(self)
            msg.setWindowTitle("Ошибка")
            msg.setText("Не удалось проверить обновления")
            msg.setInformativeText(f"Проверьте подключение к интернету\n\nОшибка: {str(e)}")
            msg.setIcon(QMessageBox.Warning)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {THEME['window_bg_end']};
                }}
                QLabel {{
                    color: {THEME['text_primary']};
                }}
                QPushButton {{
                    background-color: {THEME['accent_bg']};
                    color: {THEME['accent_text']};
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                }}
            """)
            msg.exec()
    
    def _check_updates_background(self):
        """Фоновая проверка обновлений без показа диалогов"""
        import urllib.request
        import json
        from threading import Thread
        
        try:
            from version import __version__, GITHUB_API_URL
        except ImportError:
            return  # Если нет version.py - пропускаем
        
        def check_in_background():
            try:
                req = urllib.request.Request(GITHUB_API_URL)
                req.add_header('User-Agent', 'TaskMaster')
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    latest_version = data['tag_name'].lstrip('v')
                    
                    # Сравниваем версии
                    if self._compare_versions(latest_version, __version__) > 0:
                        # Обновление доступно - показываем badge
                        QTimer.singleShot(0, lambda: self._show_update_badge(True))
                    else:
                        # Обновлений нет
                        QTimer.singleShot(0, lambda: self._show_update_badge(False))
            except:
                # Тихо игнорируем ошибки фоновой проверки
                pass
        
        # Запускаем в отдельном потоке чтобы не блокировать UI
        Thread(target=check_in_background, daemon=True).start()
    
    def _show_update_badge(self, show):
        """Показать/скрыть badge обновления"""
        self.update_available = show
        if show:
            self.update_badge.show()
            self.update_btn.setToolTip("Доступно обновление! Нажмите для подробностей")
        else:
            self.update_badge.hide()
            self.update_btn.setToolTip("Проверить обновления")
    
    def _compare_versions(self, v1, v2):
        """Сравнение версий (v1 > v2 = 1, v1 == v2 = 0, v1 < v2 = -1)"""
        def normalize(v):
            return [int(x) for x in v.split('.')]
        
        parts1 = normalize(v1)
        parts2 = normalize(v2)
        
        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        
        return 0
    
    def _show_theme_menu(self):
        """Показать меню выбора темы"""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction, QColor
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME['window_bg_end']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 5px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {THEME['secondary_hover']};
            }}
        """)
        
        themes = {
            "Зеленый (По умолчанию)": {
                'accent_bg': "rgba(107, 207, 127, 0.4)",
                'accent_hover': "rgba(107, 207, 127, 0.6)",
                'accent_text': "#ffffff"
            },
            "Синий": {
                'accent_bg': "rgba(64, 156, 255, 0.4)",
                'accent_hover': "rgba(64, 156, 255, 0.6)",
                'accent_text': "#ffffff"
            },
            "Фиолетовый": {
                'accent_bg': "rgba(170, 64, 255, 0.4)",
                'accent_hover': "rgba(170, 64, 255, 0.6)",
                'accent_text': "#ffffff"
            },
            "Оранжевый": {
                'accent_bg': "rgba(255, 149, 0, 0.4)",
                'accent_hover': "rgba(255, 149, 0, 0.6)",
                'accent_text': "#ffffff"
            },
            "Розовый": {
                'accent_bg': "rgba(255, 45, 85, 0.4)",
                'accent_hover': "rgba(255, 45, 85, 0.6)",
                'accent_text': "#ffffff"
            }
        }
        
        for name, theme_data in themes.items():
            action = QAction(f"● {name}", self)
            # Замыкание для захвата данных темы
            action.triggered.connect(lambda checked=False, t=theme_data: self._apply_custom_theme(t))
            menu.addAction(action)
            
        menu.exec(self.theme_btn.mapToGlobal(QPoint(0, -menu.sizeHint().height())))
        
    def _apply_custom_theme(self, theme_data):
        """Применение выбранной темы"""
        THEME.update(theme_data)
        
        # Обновляем глобальные стили
        global GLOBAL_STYLE
        GLOBAL_STYLE = f"""
            QWidget {{
                color: {THEME['text_primary']};
                font-family: 'Segoe UI';
            }}
            QToolTip {{
                background-color: {THEME['window_bg_end']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border_color']};
            }}
        """
        QApplication.instance().setStyleSheet(GLOBAL_STYLE)
        
        # Перерисовываем интерфейс (самый простой способ - обновить стили ключевых элементов)
        # Или можно просто перезапустить установку стилей, но для простоты просто обновим фон
        self.setStyleSheet(self.styleSheet())
        
        # Обновляем кнопку добавления (она использует акцентный цвет)
        if hasattr(self, 'add_btn'):
            self.add_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME['accent_bg']};
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    color: {THEME['accent_text']};
                }}
                QPushButton:hover {{
                    background-color: {THEME['accent_hover']};
                }}
            """)
            
        # Обновляем чекбоксы в задачах
        self._refresh_tasks()
        """Циклическое переключение акцентного цвета"""
        # Текущий акцент
        current_accent = THEME['accent_bg']
        
        # Варианты цветов (R, G, B) для accent_bg (с прозрачностью 0.4) и accent_text
        themes = [
            # Green (Default)
            {
                'accent_bg': "rgba(107, 207, 127, 0.4)",
                'accent_hover': "rgba(107, 207, 127, 0.6)",
                'accent_text': "#ffffff"
            },
            # Blue
            {
                'accent_bg': "rgba(64, 156, 255, 0.4)",
                'accent_hover': "rgba(64, 156, 255, 0.6)",
                'accent_text': "#ffffff"
            },
            # Purple
            {
                'accent_bg': "rgba(170, 64, 255, 0.4)",
                'accent_hover': "rgba(170, 64, 255, 0.6)",
                'accent_text': "#ffffff"
            },
            # Orange
            {
                'accent_bg': "rgba(255, 149, 0, 0.4)",
                'accent_hover': "rgba(255, 149, 0, 0.6)",
                'accent_text': "#ffffff"
            },
             # Pink
            {
                'accent_bg': "rgba(255, 45, 85, 0.4)",
                'accent_hover': "rgba(255, 45, 85, 0.6)",
                'accent_text': "#ffffff"
            }
        ]
        
        # Находим следующий индекс
        next_index = 0
        for i, theme in enumerate(themes):
            if theme['accent_bg'] == current_accent:
                next_index = (i + 1) % len(themes)
                break
        
        # Применяем новую тему
        new_theme = themes[next_index]
        THEME.update(new_theme)
        
        # Обновляем стили
        self._refresh_styles()
        
    def _refresh_styles(self):
        """Обновление стилей всех элементов"""
        # Обновляем кнопку добавления (она использует accent_bg)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent_bg']};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                color: {THEME['accent_text']};
            }}
            QPushButton:hover {{
                background-color: {THEME['accent_hover']};
            }}
        """)
        
        # Обновляем слайдер
        # The zoom_slider is not a direct member of the main window, it's part of SliderPopup.
        # This section should be removed or moved to SliderPopup's styling.
        # For now, commenting it out as it refers to self.zoom_slider which doesn't exist here.
        # self.zoom_slider.setStyleSheet(f"""
        #     QSlider::groove:horizontal {{
        #         border: 1px solid {THEME['border_color']};
        #         height: 4px;
        #         background: {THEME['input_bg']};
        #         margin: 0px;
        #         border-radius: 2px;
        #     }}
        #     QSlider::handle:horizontal {{
        #         background: {THEME['accent_text']};
        #         border: 1px solid {THEME['accent_hover']};
        #         width: 14px;
        #         height: 14px;
        #         margin: -5px 0;
        #         border-radius: 7px;
        #     }}
        #     QSlider::sub-page:horizontal {{
        #         background: {THEME['accent_hover']};
        #         border-radius: 2px;
        #     }}
        # """)
        
        # Кнопка минимализма (checked state uses accent)
        self.minimal_mode_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {THEME['text_secondary']};
                font-size: 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['text_primary']};
            }}
            QPushButton:checked {{
                background-color: {THEME['accent_bg']};
                color: {THEME['accent_text']};
            }}
        """)
        
        # Кнопка пина (checked state uses accent)
        self.pin_btn.setStyleSheet(self.minimal_mode_btn.styleSheet())
        
        # DateNavigator (selection uses accent) - it updates itself via update_styles callback in ZoomManager?
        # No, ZoomManager callbacks only called on zoom change.
        # But DateNavigator reads THEME every time it updates.
        # So we just need to trigger an update.
        if hasattr(self, 'date_navigator'):
            self.date_navigator.update_styles()
            self.date_navigator.update_label()
            
        # Task Cards (re-create them to apply new theme)
        self._refresh_tasks()

    def exit_application(self):
        """Полный выход из приложения"""
        QApplication.instance().quit()


    def _update_timers(self):
        """Обновление таймеров активных задач"""
        save_needed = False
        for task in self.tasks:
            if task.is_running:
                task.time_spent += 1
                save_needed = True
                
        if save_needed:
            # Обновляем UI активных задач без полной перерисовки
            # Находим карточки активных задач
            if hasattr(self, 'tasks_layout'):
                for i in range(self.tasks_layout.count()):
                    item = self.tasks_layout.itemAt(i)
                    if item and item.widget():
                        card = item.widget()
                        if isinstance(card, TaskCard) and card.task.is_running:
                            card.update_time_display(card.task.time_spent)
            
            # Сохраняем не каждый тик, а, скажем, раз в минуту или при закрытии? 
            # Для надежности сохраняем раз в 10 секунд или полагаемся на автосохранение при выходе/паузе.
            # Пока оставим сохранение в памяти, сброс на диск при паузе/выходе.
            pass

    def toggle_task_timer(self, task_id):
        """Переключение таймера задачи"""
        for task in self.tasks:
            if task.id == task_id:
                # Если запускаем эту задачу, останавливаем другие (опционально)
                if not task.is_running:
                    for t in self.tasks:
                        if t.is_running:
                            t.is_running = False
                            # Обновляем UI остановленной задачи
                            self._refresh_single_task_card(t.id)
                
                task.is_running = not task.is_running
                TaskStorage.save(self.tasks)
                
                # Обновляем UI текущей задачи
                self._refresh_single_task_card(task_id)
                break
    
    def reset_task_timer(self, task_id):
        """Сброс таймера задачи"""
        for task in self.tasks:
            if task.id == task_id:
                task.time_spent = 0
                task.is_running = False
                TaskStorage.save(self.tasks)
                self._refresh_single_task_card(task_id)
                break
    
    def change_task_status_by_id(self, task_id, new_status):
        """Изменение статуса задачи (для drag & drop)"""
        for task in self.tasks:
            if str(task.id) == task_id:
                task.status = new_status
                TaskStorage.save(self.tasks)
                # Полное обновление, так как задача перемещается между секциями
                self._refresh_tasks()
                break
    
    def _refresh_single_task_card(self, task_id):
        """Обновление одной карточки задачи"""
        if hasattr(self, 'tasks_layout'):
            for i in range(self.tasks_layout.count()):
                item = self.tasks_layout.itemAt(i)
                if item and item.widget():
                    card = item.widget()
                    if isinstance(card, TaskCard) and card.task.id == task_id:
                        # Находим обновленную задачу
                        for task in self.tasks:
                            if task.id == task_id:
                                # Обновляем состояние без пересоздания
                                card.task = task
                                card.update_time_display(task.time_spent)
                                card.update_timer_state(task.is_running)
                                return


def create_app_icon():
    """Создание иконки приложения"""
    # Пытаемся загрузить иконку из файла
    base_dir = Path(__file__).parent.resolve()
    
    # В PyInstaller exe ресурсы распаковываются во временную папку
    if getattr(sys, 'frozen', False):
        # Запущено из exe
        exe_dir = Path(sys.executable).parent
        icon_paths = [
            exe_dir / "icon.ico",
            exe_dir / "icon.png",
        ]
        # Также проверяем временную папку PyInstaller
        if hasattr(sys, '_MEIPASS'):
            icon_paths.extend([
                Path(sys._MEIPASS) / "icon.ico",
                Path(sys._MEIPASS) / "icon.png",
            ])
    else:
        # Запущено из скрипта
        icon_paths = [
            base_dir / "icon.ico",
            base_dir / "icon.png",
        ]
    
    # Пытаемся загрузить иконку
    for icon_path in icon_paths:
        if icon_path.exists():
            return QIcon(str(icon_path))
    
    # Если иконки нет, создаем программно
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))  # Прозрачный фон
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Градиентный фон
    from PySide6.QtGui import QRadialGradient
    gradient = QRadialGradient(16, 16, 16)
    gradient.setColorAt(0, QColor(107, 207, 127, 255))
    gradient.setColorAt(1, QColor(64, 156, 255, 255))
    
    painter.setBrush(gradient)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, 28, 28)
    
    # Текст/эмодзи
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Segoe UI Emoji", 18, QFont.Bold)
    painter.setFont(font)
    painter.drawText(0, 0, 32, 32, Qt.AlignCenter, "😎")
    painter.end()
    
    icon = QIcon(pixmap)
    return icon


def main():
    """Главная функция запуска приложения"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Не закрывать при закрытии окна (для трея)
    
    # Создаем и устанавливаем иконку приложения
    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)
    
    # Применяем глобальный стиль для отключения focus rect
    app.setStyleSheet(GLOBAL_STYLE)
    
    # Установка шрифта по умолчанию
    app.setFont(QFont("Segoe UI", 10))
    
    window = ModernTaskManager()
    
    # Устанавливаем иконку окна
    window.setWindowIcon(app_icon)
    
    # Создаем системный трей
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray_icon = QSystemTrayIcon(app_icon, window)
        tray_icon.setToolTip("TaskMaster - Менеджер задач")
        
        # Меню трея
        from PySide6.QtWidgets import QMenu
        tray_menu = QMenu()
        
        show_action = QAction("Показать", window)
        show_action.triggered.connect(window.show)
        show_action.triggered.connect(window.raise_)
        show_action.triggered.connect(window.activateWindow)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Скрыть", window)
        hide_action.triggered.connect(window.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Выход", window)
        quit_action.triggered.connect(app.quit)
        tray_menu.addAction(quit_action)
        
        tray_icon.setContextMenu(tray_menu)
        tray_icon.activated.connect(lambda reason: window.show() if reason == QSystemTrayIcon.DoubleClick else None)
        tray_icon.show()
        
        window.tray_icon = tray_icon  # Сохраняем ссылку
    
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()



