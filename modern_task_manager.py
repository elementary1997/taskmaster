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
from typing import List, Optional, Dict
import os
import shutil
import urllib.request
import urllib.error
import ctypes
from ctypes import wintypes

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QScrollArea,
    QFrame, QSizeGrip, QGraphicsDropShadowEffect, QDialog, QTextEdit, QSizePolicy,
    QCalendarWidget, QDateEdit, QSystemTrayIcon, QTableView, QAbstractItemView, QLayout,
    QProgressBar, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt, QPoint, QRect, QPropertyAnimation, QEasingCurve, Property, QStandardPaths, QDate, QSize, QTimer, QByteArray, Signal, QThread, QEvent
from PySide6.QtGui import (
    QIcon, QFont, QColor, QPalette, QLinearGradient, QGradient, 
    QPainter, QPen, QBrush, QCursor, QAction, QPixmap, QDrag
)
from PySide6.QtCore import QMimeData


# Функция для генерации глобального стиля с учётом текущей темы
def get_global_style():
    """Генерирует глобальный стиль с использованием цветов из текущей темы"""
    return f"""
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {{
            outline: none !important;
            border: 1px solid {THEME['accent_hover']} !important;
        }}
        QLineEdit, QTextEdit, QComboBox, QDateEdit {{
            outline: none;
        }}
        QTextEdit:focus {{
            border: 0px !important;
        }}
        QLabel {{
            selection-background-color: transparent;
            selection-color: inherit;
        }}
        QToolTip {{
            background-color: {THEME['window_bg_start']} !important;
            color: {THEME['text_primary']} !important;
            border: 1px solid {THEME['border_color']} !important;
            border-radius: 6px !important;
            padding: 5px !important;
        }}
    """

def get_input_field_style():
    """Генерирует стиль для полей ввода с использованием цветов из текущей темы"""
    return f"""
        QLineEdit, QTextEdit, QComboBox, QDateEdit {{
            background-color: {THEME['input_bg']};
            border: 1px solid {THEME['border_color']};
            color: {THEME['text_primary']};
            border-radius: 8px;
            padding: 10px 12px;
        }}
        QLineEdit:focus, QDateEdit:focus {{
            background-color: {THEME['input_bg_focus']};
            border: 1px solid {THEME['accent_hover']} !important;
            outline: none;
        }}
        QComboBox:focus {{
            background-color: {THEME['input_bg_focus']};
            border: 1px solid {THEME['accent_hover']} !important;
            outline: none;
        }}
        QTextEdit:focus {{
            background-color: {THEME['input_bg_focus']};
            border: 0px !important;
            outline: none;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QComboBox QAbstractItemView {{
            background-color: {THEME['window_bg_start']};
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
            background-color: {THEME['accent_bg']};
            color: {THEME['accent_text']};
        }}
    """



# Константы
# Определение пути к файлу данных
def get_data_file():
    """Получить путь к файлу данных в папке пользователя"""
    # Windows: C:/Users/<User>/AppData/Local/TaskMaster/tasks.json
    # Linux: ~/.local/share/TaskMaster/tasks.json
    base_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    app_dir = Path(base_path) / "TaskMaster"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / "tasks.json"

TASKS_FILE = get_data_file()

# Файл настроек
def get_settings_file():
    """Получить путь к файлу настроек"""
    base_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    app_dir = Path(base_path) / "TaskMaster"
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
    
    @staticmethod
    def get_all_tags():
        """Получение списка всех тегов из настроек"""
        settings = SettingsManager.load()
        return set(settings.get("all_tags", []))
    
    @staticmethod
    def add_tag(tag):
        """Добавление тега в список всех тегов"""
        settings = SettingsManager.load()
        if "all_tags" not in settings:
            settings["all_tags"] = []
        if tag not in settings["all_tags"]:
            settings["all_tags"].append(tag)
            SettingsManager.save(settings)
    
    @staticmethod
    def remove_tag(tag):
        """Удаление тега из списка всех тегов"""
        settings = SettingsManager.load()
        if "all_tags" in settings and tag in settings["all_tags"]:
            settings["all_tags"].remove(tag)
            SettingsManager.save(settings)

# Цветовая схема (только темная тема)
# Цветовая схема по умолчанию (базовая темная тема)
DEFAULT_THEME = {
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

# Текущая активная тема (инициализируется базовой)
THEME = DEFAULT_THEME.copy()

PRIORITY_COLORS = {
    "high": "#ff6b6b",
    "medium": "#f59e0b", # Darker Amber for better white text contrast
    "low": "#6bcf7f"
}

# Доступные темы оформления
AVAILABLE_THEMES = {
    "Изумрудный туман": {
        'window_bg_start': "#004d40",
        'window_bg_end': "#002420",
        'card_bg': "rgba(107, 207, 127, 0.15)",
        'card_bg_hover': "rgba(107, 207, 127, 0.25)",
        'input_bg': "rgba(0, 36, 32, 0.5)",
        'input_bg_focus': "rgba(0, 36, 32, 0.7)",
        'text_primary': "#ffffff",
        'text_secondary': "rgba(255, 255, 255, 0.8)",
        'text_tertiary': "rgba(255, 255, 255, 0.6)",
        'border_color': "rgba(107, 207, 127, 0.25)",
        'grip_bg': "rgba(255, 255, 255, 0.15)",
        'grip_bg_hover': "rgba(255, 255, 255, 0.25)",
        'form_bg': "rgba(0, 77, 64, 0.4)",
        'icon_color': "rgba(255, 255, 255, 0.9)",
        'placeholder_color': "rgba(255, 255, 255, 0.5)",
        'accent_bg': "rgba(107, 207, 127, 0.4)",
        'accent_hover': "rgba(107, 207, 127, 0.6)",
        'accent_text': "#ffffff",
        'secondary_bg': "rgba(255, 255, 255, 0.1)",
        'secondary_hover': "rgba(255, 255, 255, 0.15)",
        'secondary_text': "#ffffff",
        'scroll_handle': "rgba(255, 255, 255, 0.2)"
    },
    "Сапфировая ночь": {
        'window_bg_start': "#1a1a2e",
        'window_bg_end': "#16213e",
        'card_bg': "rgba(64, 156, 255, 0.15)",
        'card_bg_hover': "rgba(64, 156, 255, 0.25)",
        'input_bg': "rgba(20, 20, 35, 0.5)",
        'input_bg_focus': "rgba(20, 20, 35, 0.7)",
        'text_primary': "#ffffff",
        'text_secondary': "rgba(255, 255, 255, 0.8)",
        'text_tertiary': "rgba(255, 255, 255, 0.6)",
        'border_color': "rgba(64, 156, 255, 0.25)",
        'grip_bg': "rgba(255, 255, 255, 0.15)",
        'grip_bg_hover': "rgba(255, 255, 255, 0.25)",
        'form_bg': "rgba(30, 30, 50, 0.4)",
        'icon_color': "rgba(255, 255, 255, 0.9)",
        'placeholder_color': "rgba(255, 255, 255, 0.5)",
        'accent_bg': "rgba(64, 156, 255, 0.4)",
        'accent_hover': "rgba(64, 156, 255, 0.6)",
        'accent_text': "#ffffff",
        'secondary_bg': "rgba(255, 255, 255, 0.1)",
        'secondary_hover': "rgba(255, 255, 255, 0.15)",
        'secondary_text': "#ffffff",
        'scroll_handle': "rgba(255, 255, 255, 0.2)"
    },
    "Windows 11 Dark": {
        'window_bg_start': "#1d1d1d",
        'window_bg_end': "#1d1d1d",
        'card_bg': "rgba(32, 32, 32, 0.7)",
        'card_bg_hover': "rgba(40, 40, 40, 0.8)",
        'input_bg': "rgba(30, 30, 30, 0.6)",
        'input_bg_focus': "rgba(25, 25, 25, 0.8)",
        'text_primary': "#ffffff",
        'text_secondary': "rgba(255, 255, 255, 0.8)",
        'text_tertiary': "rgba(255, 255, 255, 0.5)",
        'border_color': "rgba(255, 255, 255, 0.1)",
        'grip_bg': "rgba(255, 255, 255, 0.1)",
        'grip_bg_hover': "rgba(255, 255, 255, 0.2)",
        'form_bg': "rgba(32, 32, 32, 0.5)",
        'icon_color': "#ffffff",
        'placeholder_color': "rgba(255, 255, 255, 0.4)",
        'accent_bg': "#0067c0",
        'accent_hover': "#0078d4",
        'accent_text': "#ffffff",
        'secondary_bg': "rgba(255, 255, 255, 0.08)",
        'secondary_hover': "rgba(255, 255, 255, 0.12)",
        'secondary_text': "#ffffff",
        'scroll_handle': "rgba(255, 255, 255, 0.15)"
    },
    "Windows 11 Light": {
        'window_bg_start': "#f3f3f3",
        'window_bg_end': "#f3f3f3",
        'card_bg': "rgba(255, 255, 255, 0.8)",
        'card_bg_hover': "rgba(255, 255, 255, 0.95)",
        'input_bg': "#ffffff",
        'input_bg_focus': "#ffffff",
        'text_primary': "#000000",
        'text_secondary': "rgba(0, 0, 0, 0.8)",
        'text_tertiary': "rgba(0, 0, 0, 0.5)",
        'border_color': "rgba(0, 0, 0, 0.1)",
        'grip_bg': "rgba(0, 0, 0, 0.05)",
        'grip_bg_hover': "rgba(0, 0, 0, 0.1)",
        'form_bg': "rgba(255, 255, 255, 0.5)",
        'icon_color': "#000000",
        'placeholder_color': "rgba(0, 0, 0, 0.4)",
        'accent_bg': "#0067c0",
        'accent_hover': "#0078d4",
        'accent_text': "#ffffff",
        'secondary_bg': "rgba(0, 0, 0, 0.05)",
        'secondary_hover': "rgba(0, 0, 0, 0.1)",
        'secondary_text': "#000000",
        'scroll_handle': "rgba(0, 0, 0, 0.15)"
    }
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
    time_log: Dict[str, int] = field(default_factory=dict) # Лог времени по дням {"yyyy-MM-dd": seconds}
    is_running: bool = False  # Флаг запущенного таймера
    completion_date: Optional[str] = None  # Дата завершения в формате "dd.MM.yyyy HH:mm"
    tags: List[str] = field(default_factory=list)  # Список тегов задачи


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
                    if "time_log" not in item:
                        item["time_log"] = {}
                    if "is_running" not in item:
                        item["is_running"] = False
                    else:
                         # Сбрасываем флаг запуска при старте (на случай аварийного закрытия)
                         item["is_running"] = False
                    if "completion_date" not in item:
                        item["completion_date"] = None
                    if "tags" not in item:
                        item["tags"] = []
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
        
    def apply_standard_shadow(self, widget):
        """Применяет стандартный эффект тени к виджету"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 180))
        widget.setGraphicsEffect(shadow)
        
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
        
        # Фон (Красный при наведении)
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
        
        # Крестик - определяем цвет в зависимости от типа темы
        # Если тема темная (белый текст), используем белый цвет для кнопки
        # Если тема светлая (темный текст), используем черный цвет для кнопки
        text_color = THEME.get('text_primary', '#ffffff')
        # Проверяем, является ли цвет светлым (темная тема) или темным (светлая тема)
        is_dark_theme = text_color.lower().startswith('#fff') or '255' in text_color.lower()
        
        if self.underMouse() or self.isDown():
            # При наведении (красный фон) всегда белый для контраста
            icon_color = QColor(255, 255, 255)
        elif is_dark_theme:
            # Темная тема - белый крестик
            icon_color = QColor(255, 255, 255)
        else:
            # Светлая тема - черный крестик
            icon_color = QColor(0, 0, 0)
        
        painter.setPen(QPen(icon_color, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
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
        
        # Минус - определяем цвет в зависимости от типа темы
        # Если тема темная (белый текст), используем белый цвет для кнопки
        # Если тема светлая (темный текст), используем черный цвет для кнопки
        text_color = THEME.get('text_primary', '#ffffff')
        # Проверяем, является ли цвет светлым (темная тема) или темным (светлая тема)
        is_dark_theme = text_color.lower().startswith('#fff') or '255' in text_color.lower()
        
        if self.underMouse() or self.isDown():
            # При наведении (желтый фон) всегда черный для контраста
            icon_color = QColor(0, 0, 0)
        elif is_dark_theme:
            # Темная тема - белый минус
            icon_color = QColor(255, 255, 255)
        else:
            # Светлая тема - черный минус
            icon_color = QColor(0, 0, 0)
        
        painter.setPen(icon_color)
        font = QFont("Segoe UI", 16, QFont.Bold) # Чуть крупнее для минуса
        painter.setFont(font)
        # Убираем сильное смещение вверх, минус обычно центрирован лучше
        adjusted_rect = rect.adjusted(0, -2, 0, 0) 
        painter.drawText(adjusted_rect, Qt.AlignCenter, "−")

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
        # Увеличиваем отступы для тени
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Контейнер с фоном
        self.container = QFrame()
        self.container.setObjectName("dialogContainer")
        self.container.setStyleSheet(f"""
            QFrame#dialogContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }}
            QLabel {{
                selection-background-color: transparent;
                selection-color: inherit;
            }}
        """)
        main_layout.addWidget(self.container)
        
        # Тень через базовый класс
        self.apply_standard_shadow(self.container)
        
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(24, 24, 24, 40)  # Увеличиваем нижний отступ для grip
        layout.setSpacing(16)
        
        # Заголовок
        header_layout = QHBoxLayout()
        title_label = QLabel("✏️ " + ("Редактировать задачу" if self.task else "Новая задача"))
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet(f"""
            color: {THEME['text_primary']};
            background: transparent;
            border: none;
            outline: none;
        """)
        title_label.setTextInteractionFlags(Qt.NoTextInteraction)
        title_label.setFocusPolicy(Qt.NoFocus)
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
        name_label.setStyleSheet(f"color: {THEME['text_secondary']}; background: transparent; border: none; outline: none;")
        name_label.setTextInteractionFlags(Qt.NoTextInteraction)
        name_label.setFocusPolicy(Qt.NoFocus)
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
        desc_label.setStyleSheet(f"color: {THEME['text_secondary']}; background: transparent; border: none; outline: none;")
        desc_label.setTextInteractionFlags(Qt.NoTextInteraction)
        desc_label.setFocusPolicy(Qt.NoFocus)
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
        priority_label.setStyleSheet(f"color: {THEME['text_secondary']}; background: transparent; border: none; outline: none;")
        priority_label.setTextInteractionFlags(Qt.NoTextInteraction)
        priority_label.setFocusPolicy(Qt.NoFocus)
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
        date_label.setStyleSheet(f"color: {THEME['text_secondary']}; background: transparent; border: none; outline: none;")
        date_label.setTextInteractionFlags(Qt.NoTextInteraction)
        date_label.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(date_label)
        
        self.current_due_date = QDate.currentDate()
        self.date_btn = QPushButton()
        self.date_btn.setFont(QFont("Segoe UI", 11))
        self.date_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.date_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['input_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
                padding: 10px 12px;
                color: {THEME['text_primary']};
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {THEME['input_bg_focus']};
                border: 1px solid {THEME['accent_bg']}40;
            }}
        """)
        self.date_btn.clicked.connect(self._show_dialog_calendar)
        self._update_date_btn_text()
        layout.addWidget(self.date_btn)
        
        # Повторение задачи
        repeat_label = QLabel("Повторение")
        repeat_label.setFont(QFont("Segoe UI", 10))
        repeat_label.setStyleSheet(f"color: {THEME['text_secondary']}; background: transparent; border: none; outline: none;")
        repeat_label.setTextInteractionFlags(Qt.NoTextInteraction)
        repeat_label.setFocusPolicy(Qt.NoFocus)
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
        
        # Теги
        tags_label = QLabel("Теги")
        tags_label.setFont(QFont("Segoe UI", 10))
        tags_label.setStyleSheet(f"color: {THEME['text_secondary']}; background: transparent; border: none; outline: none;")
        tags_label.setTextInteractionFlags(Qt.NoTextInteraction)
        tags_label.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(tags_label)
        
        # Контейнер для тегов
        tags_container = QFrame()
        tags_container.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['input_bg']};
                border: 0px;
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        tags_layout = QVBoxLayout(tags_container)
        tags_layout.setContentsMargins(8, 8, 8, 8)
        tags_layout.setSpacing(6)
        
        # Виджет для отображения выбранных тегов
        self.selected_tags_widget = QWidget()
        self.selected_tags_layout = QHBoxLayout()
        self.selected_tags_layout.setContentsMargins(0, 0, 0, 0)
        self.selected_tags_layout.setSpacing(4)
        self.selected_tags_widget.setLayout(self.selected_tags_layout)
        self.selected_tags_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        tags_layout.addWidget(self.selected_tags_widget)
        
        # Кнопка добавления тега
        add_tag_btn = QPushButton("+ Добавить тег")
        add_tag_btn.setFont(QFont("Segoe UI", 9))
        add_tag_btn.setCursor(QCursor(Qt.PointingHandCursor))
        add_tag_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['secondary_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: 6px;
                padding: 6px 12px;
                color: {THEME['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
            }}
        """)
        add_tag_btn.clicked.connect(self._show_tags_dialog)
        tags_layout.addWidget(add_tag_btn)
        
        layout.addWidget(tags_container)
        
        # Хранилище выбранных тегов
        self.selected_tags = []
        
        # Информационные поля (Дата создания/выполнения)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        if self.task:
            creation_label = QLabel(f"📅 Создана: {self.task.created}")
            creation_label.setFont(QFont("Segoe UI", 9))
            creation_label.setStyleSheet(f"color: {THEME['text_tertiary']}; background: transparent;")
            info_layout.addWidget(creation_label)
            
            if self.task.status == "Выполнено" and self.task.completion_date:
                comp_label = QLabel(f"✅ Выполнена: {self.task.completion_date}")
                comp_label.setFont(QFont("Segoe UI", 9))
                comp_label.setStyleSheet(f"color: {THEME['text_tertiary']}; background: transparent;")
                info_layout.addWidget(comp_label)
        else:
            # Для новой задачи показываем текущую дату как дату создания (будущую)
            creation_label = QLabel(f"📅 Будет создана: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            creation_label.setFont(QFont("Segoe UI", 9))
            creation_label.setStyleSheet(f"color: {THEME['text_tertiary']}; background: transparent;")
            info_layout.addWidget(creation_label)
            
        layout.addLayout(info_layout)
        
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
        self.add_grip(self.container)
    
    def _update_date_btn_text(self):
        """Обновление текста на кнопке даты"""
        months = ["янв", "фев", "мар", "апр", "май", "июн", 
                  "июл", "авг", "сен", "окт", "ноя", "дек"]
        day = self.current_due_date.day()
        month = months[self.current_due_date.month() - 1]
        year = self.current_due_date.year()
        
        self.date_btn.setText(f"📅 {day} {month} {year}")

    def _show_dialog_calendar(self):
        """Показ календаря для выбора даты в диалоге"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        
        container = QFrame(dialog)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['window_bg_end']};
                border: 1px solid {THEME['border_color']};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)
        
        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(12, 12, 12, 12)
        
        custom_calendar = CustomCalendarWidget()
        custom_calendar.calendar.setSelectedDate(self.current_due_date)
        
        def on_selected():
            self.current_due_date = custom_calendar.calendar.selectedDate()
            self._update_date_btn_text()
            dialog.accept()
            
        custom_calendar.calendar.clicked.connect(on_selected)
        inner_layout.addWidget(custom_calendar)
        
        dialog.adjustSize()
        pos = self.date_btn.mapToGlobal(QPoint(0, self.date_btn.height()))
        dialog.move(pos.x(), pos.y() + 5)
        dialog.exec()

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
                    self.current_due_date = date
                    self._update_date_btn_text()
            
            # Заполнение поля повторения
            repeat_map = {None: 0, "daily": 1, "weekly": 2, "monthly": 3}
            self.repeat_combo.setCurrentIndex(repeat_map.get(self.task.repeat_type, 0))
            
            # Заполнение тегов
            if hasattr(self.task, 'tags') and self.task.tags:
                self.selected_tags = self.task.tags.copy()
                self._update_selected_tags()
            
            # Заполнение тегов
            if hasattr(self.task, 'tags') and self.task.tags:
                self.selected_tags = self.task.tags.copy()
                self._update_selected_tags()
    
    def _show_tags_dialog(self):
        """Показ диалога выбора тегов"""
        dialog = TagsDialog(self, self.selected_tags)
        if dialog.exec():
            self.selected_tags = dialog.get_selected_tags()
            self._update_selected_tags()
    
    def _update_selected_tags(self):
        """Обновление отображения выбранных тегов"""
        # Очищаем текущие теги
        while self.selected_tags_layout.count():
            item = self.selected_tags_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)  # Отключаем от родителя перед удалением
                    widget.deleteLater()
                else:
                    # Удаляем stretch или другие элементы
                    self.selected_tags_layout.removeItem(item)
        
        # Добавляем выбранные теги
        for tag in self.selected_tags:
            tag_widget = QFrame()
            tag_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {THEME['accent_bg']};
                    border: 1px solid {THEME['accent_hover']};
                    border-radius: 12px;
                    padding: 4px 8px;
                }}
            """)
            tag_layout = QHBoxLayout(tag_widget)
            tag_layout.setContentsMargins(4, 2, 4, 2)
            tag_layout.setSpacing(4)
            
            tag_label = QLabel(tag)
            tag_label.setFont(QFont("Segoe UI", 9))
            tag_label.setStyleSheet(f"color: {THEME['accent_text']};")
            tag_layout.addWidget(tag_label)
            
            remove_btn = QPushButton("×")
            remove_btn.setFixedSize(16, 16)
            remove_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            remove_btn.setCursor(QCursor(Qt.PointingHandCursor))
            remove_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    color: {THEME['accent_text']};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.2);
                }}
            """)
            remove_btn.clicked.connect(lambda checked, t=tag: self._remove_tag(t))
            tag_layout.addWidget(remove_btn)
            
            self.selected_tags_layout.addWidget(tag_widget)
        
        self.selected_tags_layout.addStretch()
    
    def _remove_tag(self, tag):
        """Удаление тега из списка выбранных тегов для этой задачи (не из системы)"""
        try:
            if tag in self.selected_tags:
                # Удаляем тег только из локального списка этой задачи
                # Тег остается в системе и может быть использован в других задачах
                self.selected_tags.remove(tag)
                self._update_selected_tags()
        except Exception as e:
            print(f"Ошибка при удалении тега: {e}")
            import traceback
            traceback.print_exc()
    
    def get_data(self):
        """Получение данных из формы"""
        priority_map = {0: "high", 1: "medium", 2: "low"}
        repeat_map = {0: None, 1: "daily", 2: "weekly", 3: "monthly"}
        
        return {
            "title": self.title_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "priority": priority_map[self.priority_combo.currentIndex()],
            "due_date": self.current_due_date.toString("yyyy-MM-dd"),
            "repeat_type": repeat_map[self.repeat_combo.currentIndex()],
            "tags": self.selected_tags.copy()
        }


class TagsDialog(DraggableDialog):
    """Диалог для выбора и создания тегов"""
    
    def __init__(self, parent=None, selected_tags=None):
        super().__init__(parent)
        self.selected_tags = selected_tags.copy() if selected_tags else []
        self.setWindowTitle("Управление тегами")
        self.setModal(True)
        self.setMinimumWidth(400)
        # Убираем фиксированную минимальную высоту - будет подстраиваться под содержимое
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Настройка интерфейса диалога"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Контейнер с фоном
        self.container = QFrame()
        self.container.setObjectName("tagsDialogContainer")
        self.container.setStyleSheet(f"""
            QFrame#tagsDialogContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }}
        """)
        main_layout.addWidget(self.container)
        
        self.apply_standard_shadow(self.container)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(24, 24, 24, 40)
        layout.setSpacing(16)
        
        # Заголовок
        header_layout = QHBoxLayout()
        title_label = QLabel("🏷️ Управление тегами")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {THEME['text_primary']}; background: transparent; border: none;")
        title_label.setTextInteractionFlags(Qt.NoTextInteraction)
        title_label.setFocusPolicy(Qt.NoFocus)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_btn = CloseButton()
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        # Создание нового тега
        new_tag_label = QLabel("Создать новый тег")
        new_tag_label.setFont(QFont("Segoe UI", 10))
        new_tag_label.setStyleSheet(f"color: {THEME['text_secondary']}; background: transparent; border: none;")
        new_tag_label.setTextInteractionFlags(Qt.NoTextInteraction)
        new_tag_label.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(new_tag_label)
        
        new_tag_layout = QHBoxLayout()
        new_tag_layout.setSpacing(8)
        
        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("Введите название тега")
        self.new_tag_input.setFont(QFont("Segoe UI", 10))
        self.new_tag_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['input_bg']};
                border: 0px;
                border-radius: 8px;
                padding: 10px 12px;
                color: {THEME['text_primary']};
            }}
            QLineEdit:focus {{
                background-color: {THEME['input_bg_focus']};
            }}
        """)
        new_tag_layout.addWidget(self.new_tag_input)
        
        add_btn = QPushButton("Добавить")
        add_btn.setFont(QFont("Segoe UI", 10))
        add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        add_btn.setStyleSheet(f"""
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
        add_btn.clicked.connect(self._add_new_tag)
        new_tag_layout.addWidget(add_btn)
        
        layout.addLayout(new_tag_layout)
        
        # Список существующих тегов
        existing_label = QLabel("Существующие теги")
        existing_label.setFont(QFont("Segoe UI", 10))
        existing_label.setStyleSheet(f"color: {THEME['text_secondary']}; background: transparent; border: none;")
        existing_label.setTextInteractionFlags(Qt.NoTextInteraction)
        existing_label.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(existing_label)
        
        # Скроллируемая область для тегов (максимум 5 тегов видно)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {THEME['form_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
            }}
        """)
        # Высота для 5 тегов: примерно 45px на тег * 5 = 225px + отступы 16px = 241px
        scroll.setMaximumHeight(241)
        scroll.setMinimumHeight(0)  # Минимум 0, чтобы подстраивалось под содержимое
        
        tags_widget = QWidget()
        tags_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME['form_bg']};
            }}
        """)
        self.tags_layout = QVBoxLayout(tags_widget)
        self.tags_layout.setContentsMargins(8, 8, 8, 8)
        self.tags_layout.setSpacing(6)
        
        scroll.setWidget(tags_widget)
        layout.addWidget(scroll)
        
        self.tags_widget = tags_widget
        self.scroll_area = scroll  # Сохраняем ссылку для обновления размера
        self._load_tags()
        
        # После загрузки тегов обновляем размер и фиксируем его
        QTimer.singleShot(100, self._fix_dialog_size)
        
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
        
        ok_btn = QPushButton("✓ Применить")
        ok_btn.setFont(QFont("Segoe UI", 10))
        ok_btn.setCursor(QCursor(Qt.PointingHandCursor))
        ok_btn.setStyleSheet(f"""
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
        ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_btn)
        
        layout.addLayout(buttons_layout)
        
        self.add_grip(self.container)
        
        # Подключаем Enter для добавления тега
        self.new_tag_input.returnPressed.connect(self._add_new_tag)
    
    def _load_tags(self):
        """Загрузка списка всех тегов из настроек и задач"""
        # Загружаем все теги из настроек (постоянное хранилище)
        all_tags = SettingsManager.get_all_tags()
        
        # Также добавляем теги из задач (на случай если есть теги, которые еще не в настройках)
        parent_window = self.parent()
        window = parent_window
        while window and not hasattr(window, 'tasks'):
            if hasattr(window, 'parent'):
                window = window.parent()
            elif hasattr(window, 'parent_window'):
                window = window.parent_window
            else:
                break
        
        if window and hasattr(window, 'tasks'):
            tasks = window.tasks
            for task in tasks:
                if hasattr(task, 'tags') and task.tags:
                    all_tags.update(task.tags)
                    # Сохраняем теги из задач в настройки (на случай если их там еще нет)
                    for tag in task.tags:
                        SettingsManager.add_tag(tag)
        
        # Добавляем уже выбранные теги, если их нет в списке
        all_tags.update(self.selected_tags)
        
        # Очищаем текущий layout
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Создаем виджеты для каждого тега с кнопкой удаления
        for tag in sorted(all_tags):
            tag_widget = QFrame()
            tag_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {THEME['form_bg']};
                    border: 1px solid {THEME['border_color']};
                    border-radius: 8px;
                    padding: 0px;
                }}
            """)
            tag_layout = QHBoxLayout(tag_widget)
            tag_layout.setContentsMargins(8, 6, 6, 6)
            tag_layout.setSpacing(8)
            
            checkbox = QPushButton()  # Используем кнопку вместо чекбокса для лучшего вида
            checkbox.setCheckable(True)
            checkbox.setChecked(tag in self.selected_tags)
            checkbox.setText(f"🏷️ {tag}")
            checkbox.setFont(QFont("Segoe UI", 10))
            checkbox.setCursor(QCursor(Qt.PointingHandCursor))
            checkbox.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    color: {THEME['text_primary']};
                    text-align: left;
                    padding: 4px 8px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['card_bg_hover']};
                    border-radius: 4px;
                }}
                QPushButton:checked {{
                    background-color: {THEME['accent_bg']};
                    color: {THEME['accent_text']};
                    border-radius: 4px;
                }}
            """)
            checkbox.clicked.connect(lambda checked, t=tag: self._toggle_tag(t, checked))
            tag_layout.addWidget(checkbox)
            
            # Кнопка удаления тега из системы
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(24, 24)
            delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
            delete_btn.setToolTip("Удалить тег из системы")
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    color: {THEME['text_secondary']};
                    border-radius: 4px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 0, 0, 0.2);
                    color: #ff6b6b;
                }}
            """)
            delete_btn.clicked.connect(lambda checked, t=tag: self._delete_tag_from_system(t))
            tag_layout.addWidget(delete_btn)
            
            self.tags_layout.addWidget(tag_widget)
        
        # Размер уже будет обновлен в _fix_dialog_size, не нужно вызывать здесь
    
    def _adjust_tags_area_size(self):
        """Подстройка размера области тегов: минимум под содержимое, максимум на 5 тегов"""
        if not hasattr(self, 'scroll_area') or not hasattr(self, 'tags_widget'):
            return
        
        # Вычисляем нужную высоту на основе количества тегов
        tag_count = self.tags_layout.count()
        if tag_count == 0:
            # Если тегов нет, минимальная высота
            self.scroll_area.setMinimumHeight(0)
            self.scroll_area.setMaximumHeight(241)
        else:
            # Высота одного тега примерно 45px (отступы + контент)
            # Отступы layout: 8px сверху + 8px снизу = 16px
            # Spacing между тегами: 6px * (количество - 1)
            spacing = 6 * (tag_count - 1) if tag_count > 1 else 0
            content_height = (45 * tag_count) + 16 + spacing
            
            # Максимум на 5 тегов
            max_height = 241
            # Минимум - под содержимое, но не больше максимума
            min_height = min(content_height, max_height)
            
            self.scroll_area.setMinimumHeight(min_height)
            self.scroll_area.setMaximumHeight(max_height)
    
    def _fix_dialog_size(self):
        """Фиксация размера диалога после первоначальной настройки"""
        # Сначала настраиваем размер области тегов
        self._adjust_tags_area_size()
        # Затем фиксируем размер всего диалога
        self.adjustSize()
        # Сохраняем текущий размер и фиксируем его
        current_size = self.size()
        self._fixed_size = current_size
        self.setFixedSize(current_size)
        self._dialog_size_fixed = True
    
    def _restore_dialog_size_after_update(self, saved_size):
        """Восстановление размера диалога после обновления списка тегов"""
        # Обновляем размер области тегов
        self._adjust_tags_area_size()
        # Восстанавливаем сохраненный размер
        self.setFixedSize(saved_size)
        self._fixed_size = saved_size
    
    def _toggle_tag(self, tag, checked):
        """Переключение выбора тега"""
        # Сохраняем текущий размер диалога перед изменением
        if not hasattr(self, '_dialog_size_fixed'):
            return
        
        if checked:
            if tag not in self.selected_tags:
                self.selected_tags.append(tag)
        else:
            if tag in self.selected_tags:
                self.selected_tags.remove(tag)
        
        # Восстанавливаем размер, если он изменился
        if hasattr(self, '_fixed_size'):
            self.setFixedSize(self._fixed_size)
    
    def _add_new_tag(self):
        """Добавление нового тега"""
        tag_text = self.new_tag_input.text().strip()
        if tag_text:
            # Сохраняем тег в настройки (постоянное хранилище)
            SettingsManager.add_tag(tag_text)
            
            if tag_text not in self.selected_tags:
                self.selected_tags.append(tag_text)
            
            # Сохраняем текущий размер перед обновлением
            if hasattr(self, '_fixed_size'):
                saved_size = self._fixed_size
            else:
                saved_size = self.size()
            
            self.new_tag_input.clear()
            self._load_tags()
            
            # Обновляем размер области тегов и восстанавливаем размер диалога
            QTimer.singleShot(50, lambda: self._restore_dialog_size_after_update(saved_size))
            # Автоматически выбираем новый тег
            QTimer.singleShot(100, lambda: self._select_tag_after_load(tag_text))
    
    def _select_tag_after_load(self, tag_text):
        """Выбор тега после загрузки списка"""
        for i in range(self.tags_layout.count()):
            item = self.tags_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # Ищем кнопку с этим тегом
                for child in widget.findChildren(QPushButton):
                    if child.isCheckable() and tag_text in child.text():
                        child.setChecked(True)
                        break
    
    def _delete_tag_from_system(self, tag):
        """Удаление тега из всех задач в системе"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Удаление тега",
            f"Вы уверены, что хотите удалить тег '{tag}' из всех задач?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Ищем ModernTaskManager через цепочку parent
            parent_window = self.parent()
            window = parent_window
            while window and not hasattr(window, 'tasks'):
                if hasattr(window, 'parent'):
                    window = window.parent()
                elif hasattr(window, 'parent_window'):
                    window = window.parent_window
                else:
                    break
            
            if window and hasattr(window, 'tasks'):
                # Удаляем тег из всех задач
                removed_count = 0
                for task in window.tasks:
                    if hasattr(task, 'tags') and task.tags and tag in task.tags:
                        task.tags.remove(tag)
                        removed_count += 1
                
                # Сохраняем изменения в задачах
                if removed_count > 0:
                    TaskStorage.save(window.tasks)
                    window._refresh_tasks()
                
                # Удаляем тег из постоянного хранилища
                SettingsManager.remove_tag(tag)
                
                # Сохраняем текущий размер перед обновлением
                if hasattr(self, '_fixed_size'):
                    saved_size = self._fixed_size
                else:
                    saved_size = self.size()
                
                # Обновляем список тегов в диалоге
                self._load_tags()
                
                # Обновляем размер области тегов и восстанавливаем размер диалога
                QTimer.singleShot(50, lambda: self._restore_dialog_size_after_update(saved_size))
                
                QMessageBox.information(
                    self,
                    "Тег удален",
                    f"Тег '{tag}' удален из {removed_count} задач и из системы."
                )
    
    def get_selected_tags(self):
        """Получение списка выбранных тегов"""
        return self.selected_tags.copy()


class NotificationButton(QPushButton):
    """Кнопка уведомлений с индикатором"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(ZoomManager.scaled(32), ZoomManager.scaled(32))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.has_notifications = False
        self.setStyleSheet("background: transparent; border: none;")
        
        # Регистрируем callback для обновления при изменении масштаба
        ZoomManager.add_callback(self._update_scale)
        
    def _update_scale(self):
        """Обновление размера при изменении масштаба"""
        self.setFixedSize(ZoomManager.scaled(32), ZoomManager.scaled(32))
        self.update()
        
    def set_notification_state(self, has_notifications):
        self.has_notifications = has_notifications
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Icon (Bell)
        painter.setPen(QColor(THEME['text_secondary']))
        if self.has_notifications:
            painter.setPen(QColor(THEME['text_primary']))
            
        font = QFont("Segoe UI Emoji", ZoomManager.scaled(14))
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "🔔")
        
        # Red Badge
        if self.has_notifications:
            size = self.width()
            badge_size = ZoomManager.scaled(8)
            badge_x = size - badge_size - ZoomManager.scaled(2)
            badge_y = ZoomManager.scaled(4)
            painter.setBrush(QColor("#ff4444"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(badge_x), int(badge_y), int(badge_size), int(badge_size))

class NotificationDialog(DraggableDialog):
    """Диалог с уведомлениями о просроченных задачах"""
    def __init__(self, parent, overdue_tasks):
        super().__init__(parent)
        self.overdue_tasks = overdue_tasks
        self.settings_manager = parent.settings_manager if hasattr(parent, 'settings_manager') else SettingsManager()
        self.parent_window = parent
        
        self.setWindowTitle("Уведомления")
        self.setMinimumWidth(ZoomManager.scaled(320))
        self.resize(ZoomManager.scaled(320), ZoomManager.scaled(400))
        
        # Отслеживаем перемещение главного окна для обновления позиции
        if parent:
            parent.installEventFilter(self)
        
         # Основной лейаут для тени
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            ZoomManager.scaled(15), 
            ZoomManager.scaled(15), 
            ZoomManager.scaled(15), 
            ZoomManager.scaled(15)
        )
        
        self.container = QFrame()
        self.container.setObjectName("notifyContainer")
        self._update_container_style()
        main_layout.addWidget(self.container)
        self.apply_standard_shadow(self.container)
        
        self._setup_ui()
        
        # Отслеживаем перемещение главного окна для обновления позиции
        if parent:
            parent.installEventFilter(self)
        
        # Регистрируем callback для обновления при изменении масштаба
        ZoomManager.add_callback(self.update_ui_scale)
        
    def _update_container_style(self):
        """Обновление стиля контейнера с учетом масштаба"""
        self.container.setStyleSheet(f"""
            QFrame#notifyContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border: 1px solid {THEME['border_color']};
                border-radius: {ZoomManager.scaled(20)}px;
            }}
        """)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header ( draggable block )
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(
            ZoomManager.scaled(20), 
            ZoomManager.scaled(20), 
            ZoomManager.scaled(20), 
            ZoomManager.scaled(10)
        )
        
        # Заголовок меняется в зависимости от наличия уведомлений
        if self.overdue_tasks:
            title_text = "⚠️ Просроченные задачи"
        else:
            title_text = "🔔 Уведомления"
        self.title = QLabel(title_text)
        self.title.setFont(ZoomManager.font("Segoe UI", 16, QFont.Bold))
        self.title.setStyleSheet(f"color: {THEME['text_primary']}; background: transparent; border: none;")
        header_layout.addWidget(self.title)
        
        header_layout.addStretch()
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(ZoomManager.scaled(30), ZoomManager.scaled(30))
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._update_close_btn_style()
        self.close_btn.clicked.connect(self.close)
        header_layout.addWidget(self.close_btn)
        
        layout.addWidget(header_frame)
        
        # List
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setSpacing(ZoomManager.scaled(10))
        self.content_layout.setContentsMargins(
            ZoomManager.scaled(20), 
            0, 
            ZoomManager.scaled(20), 
            ZoomManager.scaled(10)
        )
        
        self.task_items = []  # Сохраняем ссылки на элементы задач
        
        if not self.overdue_tasks:
            # Если уведомлений нет, показываем сообщение
            no_notifications_label = QLabel("✅ У вас нет уведомлений")
            no_notifications_label.setFont(ZoomManager.font("Segoe UI", 14))
            no_notifications_label.setStyleSheet(f"""
                color: {THEME['text_secondary']};
                background: transparent;
                border: none;
                padding: {ZoomManager.scaled(20)}px;
            """)
            no_notifications_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(no_notifications_label)
        else:
            # Показываем список просроченных задач
            for task in self.overdue_tasks:
                # Создаем кастомный QFrame с обработчиком клика
                class TaskItemFrame(QFrame):
                    def __init__(self, parent_dialog, task_item):
                        super().__init__()
                        self.parent_dialog = parent_dialog
                        self.task_item = task_item
                        self.setCursor(QCursor(Qt.PointingHandCursor))
                    
                    def mousePressEvent(self, event):
                        if event.button() == Qt.LeftButton:
                            self.parent_dialog._open_task(self.task_item)
                        super().mousePressEvent(event)
                
                item = TaskItemFrame(self, task)
                item.setStyleSheet(f"""
                    QFrame {{
                        background: {THEME['card_bg']};
                        border-radius: {ZoomManager.scaled(10)}px;
                        border: 1px solid {THEME['border_color']};
                    }}
                    QFrame:hover {{
                        background: {THEME['card_bg_hover']};
                        border: 1px solid {THEME.get('accent_hover', THEME['border_color'])};
                    }}
                """)
                item_layout = QVBoxLayout(item)
                item_layout.setContentsMargins(
                    ZoomManager.scaled(15), 
                    ZoomManager.scaled(10), 
                    ZoomManager.scaled(15), 
                    ZoomManager.scaled(10)
                )
                
                t_title = QLabel(task.title)
                t_title.setFont(QFont("Segoe UI", 10, QFont.Medium))
                t_title.setStyleSheet("border: none; background: transparent; color: #ff6b6b;")
                t_title.setWordWrap(True)
                
                # Форматируем дату в формат DD.MM.YYYY
                try:
                    task_date = QDate.fromString(task.due_date, "yyyy-MM-dd")
                    if task_date.isValid():
                        formatted_date = task_date.toString("dd.MM.yyyy")
                    else:
                        formatted_date = task.due_date  # Если не удалось распарсить, оставляем как есть
                except:
                    formatted_date = task.due_date  # Если ошибка, оставляем как есть
                
                t_date = QLabel(f"Срок: {formatted_date}")
                t_date.setFont(QFont("Segoe UI", 8))
                t_date.setStyleSheet(f"border: none; background: transparent; color: {THEME['text_secondary']};")
                
                item_layout.addWidget(t_title)
                item_layout.addWidget(t_date)
                
                self.task_items.append((item, t_title, t_date, task))
                self.content_layout.addWidget(item)
        
        self.content_layout.addStretch()
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)
        
        # Footer
        footer_frame = QFrame()
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(
            ZoomManager.scaled(20), 
            ZoomManager.scaled(10), 
            ZoomManager.scaled(20), 
            ZoomManager.scaled(20)
        )
        
        # Кнопка "Очистить уведомления" показывается только если есть уведомления
        if self.overdue_tasks:
            self.clear_btn = QPushButton("Очистить уведомления")
            self.clear_btn.setCursor(Qt.PointingHandCursor)
            self.clear_btn.setFont(ZoomManager.font("Segoe UI", 10))
            self._update_clear_btn_style()
            self.clear_btn.clicked.connect(self._clear_and_close)
            footer_layout.addWidget(self.clear_btn)
        else:
            # Если уведомлений нет, показываем кнопку "Закрыть"
            self.close_dialog_btn = QPushButton("Закрыть")
            self.close_dialog_btn.setCursor(Qt.PointingHandCursor)
            self.close_dialog_btn.setFont(ZoomManager.font("Segoe UI", 10))
            self.close_dialog_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME['secondary_bg']};
                    color: {THEME['text_primary']};
                    border: 1px solid {THEME['border_color']};
                    border-radius: {ZoomManager.scaled(10)}px;
                    padding: {ZoomManager.scaled(10)}px {ZoomManager.scaled(20)}px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['secondary_hover']};
                }}
            """)
            self.close_dialog_btn.clicked.connect(self.close)
            footer_layout.addWidget(self.close_dialog_btn)
        
        layout.addWidget(footer_frame)
        
    def _update_close_btn_style(self):
        """Обновление стиля кнопки закрытия с учетом масштаба"""
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {THEME['text_secondary']};
                font-size: {ZoomManager.scaled(18)}px;
                border: none;
            }}
            QPushButton:hover {{ 
                color: {THEME['text_primary']}; 
                background-color: {THEME['secondary_hover']};
                border-radius: {ZoomManager.scaled(15)}px;
            }}
        """)
        
    def _update_clear_btn_style(self):
        """Обновление стиля кнопки очистки с учетом масштаба"""
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['secondary_bg']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border_color']};
                border-radius: {ZoomManager.scaled(10)}px;
                padding: {ZoomManager.scaled(10)}px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
            }}
        """)
        
    def update_ui_scale(self):
        """Обновление интерфейса при изменении масштаба"""
        # Обновляем размеры окна
        self.setMinimumWidth(ZoomManager.scaled(320))
        if self.width() > 0:
            self.resize(ZoomManager.scaled(320), ZoomManager.scaled(400))
        
        # Обновляем отступы основного лейаута
        main_layout = self.layout()
        if main_layout:
            main_layout.setContentsMargins(
                ZoomManager.scaled(15), 
                ZoomManager.scaled(15), 
                ZoomManager.scaled(15), 
                ZoomManager.scaled(15)
            )
        
        # Обновляем стиль контейнера
        self._update_container_style()
        
        # Обновляем заголовок
        if hasattr(self, 'title'):
            self.title.setFont(ZoomManager.font("Segoe UI", 16, QFont.Bold))
        
        # Обновляем отступы заголовка
        container_layout = self.container.layout()
        if container_layout and container_layout.count() > 0:
            header_frame = container_layout.itemAt(0).widget()
            if header_frame:
                header_layout = header_frame.layout()
                if header_layout:
                    header_layout.setContentsMargins(
                        ZoomManager.scaled(20), 
                        ZoomManager.scaled(20), 
                        ZoomManager.scaled(20), 
                        ZoomManager.scaled(10)
                    )
        
        # Обновляем кнопку закрытия
        if hasattr(self, 'close_btn'):
            self.close_btn.setFixedSize(ZoomManager.scaled(30), ZoomManager.scaled(30))
            self._update_close_btn_style()
        
        # Обновляем отступы контента
        if hasattr(self, 'content_layout'):
            self.content_layout.setSpacing(ZoomManager.scaled(10))
            self.content_layout.setContentsMargins(
                ZoomManager.scaled(20), 
                0, 
                ZoomManager.scaled(20), 
                ZoomManager.scaled(10)
            )
        
        # Обновляем элементы задач
        for item, t_title, t_date, task in self.task_items:
            item.setStyleSheet(f"""
                QFrame {{
                    background: {THEME['card_bg']};
                    border-radius: {ZoomManager.scaled(10)}px;
                    border: 1px solid {THEME['border_color']};
                }}
                QFrame:hover {{
                    background: {THEME['card_bg_hover']};
                    border: 1px solid {THEME.get('accent_hover', THEME['border_color'])};
                }}
            """)
            item_layout = item.layout()
            if item_layout:
                item_layout.setContentsMargins(
                    ZoomManager.scaled(15), 
                    ZoomManager.scaled(10), 
                    ZoomManager.scaled(15), 
                    ZoomManager.scaled(10)
                )
            t_title.setFont(QFont("Segoe UI", 10, QFont.Medium))
            t_date.setFont(QFont("Segoe UI", 8))
        
        # Обновляем кнопку очистки
        if hasattr(self, 'clear_btn'):
            self.clear_btn.setFont(ZoomManager.font("Segoe UI", 10))
            self._update_clear_btn_style()
        
        # Обновляем отступы футера
        footer_frame = self.container.layout().itemAt(self.container.layout().count() - 1).widget()
        if footer_frame:
            footer_layout = footer_frame.layout()
            if footer_layout:
                footer_layout.setContentsMargins(
                    ZoomManager.scaled(20), 
                    ZoomManager.scaled(10), 
                    ZoomManager.scaled(20), 
                    ZoomManager.scaled(20)
                )
        
    def _open_task(self, task):
        """Открыть задачу в диалоге просмотра"""
        dialog = TaskViewDialog(task, self.parent_window)
        dialog.exec()
    
    def _clear_and_close(self):
        # Очищаем уведомления в родительском окне
        if self.parent_window:
            self.parent_window.clear_notifications()
        
        # Очищаем список задач в этом окне
        # Удаляем все элементы задач
        for item, t_title, t_date, task in self.task_items:
            item.setParent(None)
            item.deleteLater()
        self.task_items.clear()
        
        # Очищаем layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
        
        # Показываем сообщение "нет уведомлений"
        no_notifications_label = QLabel("✅ У вас нет уведомлений")
        no_notifications_label.setFont(ZoomManager.font("Segoe UI", 14))
        no_notifications_label.setStyleSheet(f"""
            color: {THEME['text_secondary']};
            background: transparent;
            border: none;
            padding: {ZoomManager.scaled(20)}px;
        """)
        no_notifications_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(no_notifications_label)
        
        # Обновляем заголовок
        if hasattr(self, 'title'):
            self.title.setText("🔔 Уведомления")
        
        # Обновляем кнопку - меняем текст на "Закрыть" и меняем обработчик
        if hasattr(self, 'clear_btn'):
            self.clear_btn.setText("Закрыть")
            self.clear_btn.clicked.disconnect()
            self.clear_btn.clicked.connect(self.close)
            # Обновляем стиль кнопки
            self.clear_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME['secondary_bg']};
                    color: {THEME['text_primary']};
                    border: 1px solid {THEME['border_color']};
                    border-radius: {ZoomManager.scaled(10)}px;
                    padding: {ZoomManager.scaled(10)}px {ZoomManager.scaled(20)}px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['secondary_hover']};
                }}
            """)
        
        # Обновляем список просроченных задач в диалоге
        self.overdue_tasks = []
    
    def eventFilter(self, obj, event):
        """Отслеживание перемещения главного окна для обновления позиции диалога"""
        if obj == self.parent_window and event.type() == QEvent.Move:
            # Обновляем позицию диалога при перемещении главного окна
            self._update_position()
        return super().eventFilter(obj, event)
    
    def _update_position(self):
        """Обновление позиции диалога относительно кнопки уведомлений"""
        if not hasattr(self.parent_window, 'notification_btn'):
            return
        
        btn_pos = self.parent_window.notification_btn.mapToGlobal(QPoint(0, 0))
        btn_width = self.parent_window.notification_btn.width()
        btn_height = self.parent_window.notification_btn.height()
        
        # Позиционируем диалог: выравниваем правый край диалога с правым краем кнопки
        x = btn_pos.x() + btn_width - self.width()
        y = btn_pos.y() + btn_height  # Прямо под кнопкой
        
        # Проверяем границы экрана
        screen_geo = self.screen().geometry()
        if x + self.width() > screen_geo.right():
            x = btn_pos.x()  # Выравниваем по левому краю кнопки
        if x < screen_geo.left():
            x = screen_geo.left() + ZoomManager.scaled(10)
        if y + self.height() > screen_geo.bottom():
            y = btn_pos.y() - self.height()  # Показываем сверху кнопки
        if y < screen_geo.top():
            y = screen_geo.top() + ZoomManager.scaled(10)
        
        self.move(x, y)

class AboutDialog(DraggableDialog):
    """Диалог с информацией о проекте и обновлениях"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(580)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        # Увеличиваем отступы для тени
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Контейнер с фоном
        container = QFrame()
        container.setObjectName("aboutContainer")
        container.setStyleSheet(f"""
            QFrame#aboutContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }}
            QLabel {{
                selection-background-color: transparent;
                selection-color: inherit;
            }}
        """)
        main_layout.addWidget(container)
        
        self.apply_standard_shadow(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 40)
        layout.setSpacing(20)
        
        # Заголовок
        header_layout = QHBoxLayout()
        title_label = QLabel("ℹ️ О программе")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet(f"""
            color: {THEME['text_primary']};
            background: transparent;
            border: none;
            outline: none;
        """)

        title_label.setTextInteractionFlags(Qt.NoTextInteraction)
        title_label.setFocusPolicy(Qt.NoFocus)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Кнопка закрытия
        close_btn = CloseButton()
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        layout.setSpacing(20)
        
        # Информация о проекте
        project_frame = QFrame()
        project_frame.setFrameShape(QFrame.NoFrame)  # Убираем рамку
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
        project_title.setStyleSheet(f"color: {THEME['text_primary']}; border: none; background: transparent;")
        project_title.setTextInteractionFlags(Qt.NoTextInteraction)
        project_layout.addWidget(project_title)
        
        version_label = QLabel("Версия 1.0.2")
        version_label.setFont(QFont("Segoe UI", 11))
        version_label.setStyleSheet(f"color: {THEME['text_secondary']}; border: none; background: transparent;")
        version_label.setTextInteractionFlags(Qt.NoTextInteraction)
        project_layout.addWidget(version_label)
        
        desc_label = QLabel(
            "Современный легковесный менеджер задач с полупрозрачным интерфейсом "
            "и минималистичным дизайном. Создан для продуктивной работы и удобного "
            "управления задачами."
        )
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setStyleSheet(f"color: {THEME['text_secondary']}; border: none; background: transparent;")
        desc_label.setWordWrap(True)
        desc_label.setTextInteractionFlags(Qt.NoTextInteraction)
        project_layout.addWidget(desc_label)
        
        layout.addWidget(project_frame)
        
        
        # Особенности
        features_frame = QFrame()
        features_frame.setFrameShape(QFrame.NoFrame)  # Убираем рамку
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
        features_title.setStyleSheet(f"color: {THEME['text_primary']}; border: none; background: transparent;")
        features_title.setTextInteractionFlags(Qt.NoTextInteraction)
        features_layout.addWidget(features_title)
        
        features_list = [
            "Приоритеты задач (Высокий, Средний, Низкий)",
            "Даты выполнения задач",
            "Статистика выполнения",
            "Перетаскивание и масштабирование окон",
            "Автосохранение всех данных"
        ]
        
        for feature_text in features_list:
            feature_item = QLabel(f"• {feature_text}")
            feature_item.setFont(QFont("Segoe UI", 10))
            feature_item.setStyleSheet(f"color: {THEME['text_secondary']}; border: none; background: transparent; padding: 4px 0px;")
            feature_item.setWordWrap(True)
            feature_item.setTextInteractionFlags(Qt.NoTextInteraction)
            features_layout.addWidget(feature_item)
        
        layout.addWidget(features_frame)
        layout.addStretch()
        
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
        # Увеличиваем отступы для тени
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Контейнер с фоном
        container = QFrame()
        container.setObjectName("viewContainer")
        container.setStyleSheet(f"""
            QFrame#viewContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }}
            QLabel {{
                selection-background-color: transparent;
                selection-color: inherit;
            }}
        """)
        main_layout.addWidget(container)
        
        self.apply_standard_shadow(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 40)  # Увеличиваем нижний отступ для grip
        layout.setSpacing(16)
        
        # Заголовок с иконкой и кнопка закрытия
        header_layout = QHBoxLayout()
        title_label = QLabel("📋 Описание задачи")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet(f"""
            color: {THEME['text_primary']};
            background: transparent;
            border: none;
            outline: none;
        """)

        title_label.setTextInteractionFlags(Qt.NoTextInteraction)
        title_label.setFocusPolicy(Qt.NoFocus)
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
        task_title.setStyleSheet(f"color: {THEME['text_primary']}; background: transparent; border: none; outline: none;")
        task_title.setWordWrap(True)
        task_title.setTextInteractionFlags(Qt.NoTextInteraction)
        task_title.setFocusPolicy(Qt.NoFocus)
        task_title.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        info_layout.addWidget(task_title)
        
        # Приоритет
        priority_color = PRIORITY_COLORS.get(self.task.priority, "#6bcf7f")
        priority_label = QLabel(f"⚡ Приоритет: {PRIORITY_NAMES[self.task.priority]}")
        priority_label.setFont(QFont("Segoe UI", 11))
        priority_label.setStyleSheet(f"color: {priority_color}; background: transparent; border: none; outline: none;")
        priority_label.setTextInteractionFlags(Qt.NoTextInteraction)
        priority_label.setFocusPolicy(Qt.NoFocus)
        priority_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        info_layout.addWidget(priority_label)
        
        # Статус
        status_label = QLabel(f"📊 Статус: {self.task.status}")
        status_label.setFont(QFont("Segoe UI", 11))
        status_label.setStyleSheet(f"color: {THEME['text_secondary']}; background: transparent; border: none; outline: none;")
        status_label.setTextInteractionFlags(Qt.NoTextInteraction)
        status_label.setFocusPolicy(Qt.NoFocus)
        status_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        info_layout.addWidget(status_label)
        
        # Срок выполнения (если есть)
        if self.task.due_date:
            try:
                task_date = QDate.fromString(self.task.due_date, "yyyy-MM-dd")
                today = QDate.currentDate()
                
                if task_date == today.addDays(1):
                    date_text = "Завтра"
                    date_color = THEME['text_secondary']
                elif task_date < today:
                    date_text = f"Просрочено ({task_date.toString('dd.MM')})"
                    date_color = "#ff6b6b"  # Red
                else:
                    # Показываем дату в формате dd.MM
                    date_text = task_date.toString("dd.MM")
                    date_color = THEME['text_secondary']
                
                due_date_label = QLabel(f"📅 Срок выполнения: {date_text}")
                due_date_label.setFont(QFont("Segoe UI", 11))
                due_date_label.setStyleSheet(f"color: {date_color}; background: transparent; border: none; outline: none;")
                due_date_label.setTextInteractionFlags(Qt.NoTextInteraction)
                due_date_label.setFocusPolicy(Qt.NoFocus)
                due_date_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                info_layout.addWidget(due_date_label)
            except:
                pass
        
        # Теги (если есть)
        if hasattr(self.task, 'tags') and self.task.tags:
            tags_label = QLabel("🏷️ Теги: " + ", ".join(self.task.tags))
            tags_label.setFont(QFont("Segoe UI", 10))
            tags_label.setStyleSheet(f"color: {THEME['text_secondary']}; background: transparent; border: none; outline: none;")
            tags_label.setTextInteractionFlags(Qt.NoTextInteraction)
            tags_label.setFocusPolicy(Qt.NoFocus)
            tags_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            tags_label.setWordWrap(True)
            info_layout.addWidget(tags_label)
        
        # Описание (если есть)
        if self.task.description:
            desc_label = QLabel("Описание задачи:")
            desc_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            desc_label.setStyleSheet(f"color: {THEME['text_tertiary']}; background: transparent; border: none; outline: none;")
            desc_label.setTextInteractionFlags(Qt.NoTextInteraction)
            desc_label.setFocusPolicy(Qt.NoFocus)
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
            desc_text.setFocusPolicy(Qt.NoFocus)
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
        priority_indicator.setFixedSize(ZoomManager.scaled(3), ZoomManager.scaled(28))
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
        
        # Индикатор даты убран из карточки - теперь показывается только в диалоге описания
        
        # Теги (если есть)
        if hasattr(self.task, 'tags') and self.task.tags:
            tags_text = " ".join([f"🏷️ {tag}" for tag in self.task.tags])
            tags_label = QLabel(tags_text)
            tags_label.setFont(QFont("Segoe UI", 9))
            tags_label.setStyleSheet(f"color: {THEME['text_tertiary']};")
            tags_label.setTextInteractionFlags(Qt.NoTextInteraction)
            info_layout.addWidget(tags_label)
        
        # Дата выполнения (для архива)
        if self.task.status == "Выполнено" and self.task.completion_date:
            comp_date_label = QLabel(f"✅ {self.task.completion_date}")
            comp_date_label.setFont(QFont("Segoe UI", 8))
            comp_date_label.setStyleSheet(f"color: {THEME['text_tertiary']};")
            comp_date_label.setTextInteractionFlags(Qt.NoTextInteraction)
            info_layout.addWidget(comp_date_label)
            
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
        self.play_btn.setFixedSize(ZoomManager.scaled(28), ZoomManager.scaled(28))
        self.play_btn.setText("⏯️" if self.task.is_running else "▶️")  # ⏯️ для паузы, ▶️ для play
        self.play_btn.setToolTip("Пауза" if self.task.is_running else "Запустить")
        self.play_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.play_btn.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # Предотвращаем проброс событий
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {THEME['border_color']};
                color: {THEME['accent_text'] if self.task.is_running else THEME['text_secondary']};
                font-size: {ZoomManager.scaled(14)}px;
                border-radius: {ZoomManager.scaled(14)}px;
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
        reset_btn.setFixedSize(ZoomManager.scaled(28), ZoomManager.scaled(28))
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
        self.toggle_timer_btn = QPushButton()
        timer_icon = create_timer_icon()
        if not timer_icon.isNull():
            # Используем иконку из файла
            self.toggle_timer_btn.setIcon(timer_icon)
            self.toggle_timer_btn.setIconSize(QSize(ZoomManager.scaled(30), ZoomManager.scaled(30)))  # Почти размер кнопки 32x32
        else:
            # Fallback на эмодзи, если иконка не найдена
            self.toggle_timer_btn.setText("⏱️")
        self.toggle_timer_btn.setFixedSize(ZoomManager.scaled(32), ZoomManager.scaled(32))
        self.toggle_timer_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_timer_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {THEME['border_color']};
                border-radius: {ZoomManager.scaled(16)}px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
            }}
        """)
        self.toggle_timer_btn.clicked.connect(self._toggle_timer_controls)
        actions_layout.addWidget(self.toggle_timer_btn)
        
        # Разделитель
        self.timer_separator = QFrame()
        self.timer_separator.setFrameShape(QFrame.VLine)
        self.timer_separator.setFrameShadow(QFrame.Sunken)
        self.timer_separator.setFixedWidth(ZoomManager.scaled(1))
        self.timer_separator.setFixedHeight(ZoomManager.scaled(20))
        self.timer_separator.setStyleSheet(f"background-color: {THEME['border_color']}; border: none;")
        actions_layout.addWidget(self.timer_separator)
        
        # Чекбокс выполнения
        self.checkbox = QPushButton("✓" if self.task.status == "Выполнено" else "")
        self.checkbox.setFixedSize(ZoomManager.scaled(24), ZoomManager.scaled(24))
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
                border: {ZoomManager.scaled(2)}px solid {check_color};
                border-radius: {ZoomManager.scaled(12)}px;
                color: #ffffff;
                font-weight: bold;
                font-size: {ZoomManager.scaled(14)}px;
            }}
            QPushButton:hover {{
                background-color: {check_color}40;
            }}
            QPushButton:checked {{
                background-color: {check_color};
                border: {ZoomManager.scaled(2)}px solid {check_color};
            }}
        """)
        self.checkbox.clicked.connect(self._on_checked)
        actions_layout.addWidget(self.checkbox)
        
        # Кнопка удаления
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(ZoomManager.scaled(30), ZoomManager.scaled(30))
        delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 107, 107, 0.3);
                border: none;
                border-radius: {ZoomManager.scaled(14)}px;
                color: #ff6b6b;
                font-size: {ZoomManager.scaled(16)}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 107, 107, 0.5);
            }}
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
                    border-radius: 16px;
                }}
            """)
        else:
            self.toggle_timer_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {THEME['border_color']};
                    border-radius: 16px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['secondary_hover']};
                }}
            """)


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
        """Обработка клика по checkbox задачи"""
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
        # Обновляем размеры кнопок
        if hasattr(self, 'play_btn'):
            self.play_btn.setFixedSize(ZoomManager.scaled(28), ZoomManager.scaled(28))
            self.play_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {THEME['border_color']};
                    color: {THEME['accent_text'] if self.task.is_running else THEME['text_secondary']};
                    font-size: {ZoomManager.scaled(14)}px;
                    border-radius: {ZoomManager.scaled(14)}px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['secondary_hover']};
                    color: {THEME['accent_text']};
                }}
            """)
        
        if hasattr(self, 'toggle_timer_btn'):
            self.toggle_timer_btn.setFixedSize(ZoomManager.scaled(32), ZoomManager.scaled(32))
            self.toggle_timer_btn.setIconSize(QSize(ZoomManager.scaled(30), ZoomManager.scaled(30)))
            self.toggle_timer_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {THEME['border_color']};
                    border-radius: {ZoomManager.scaled(16)}px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['secondary_hover']};
                }}
            """)
        
        if hasattr(self, 'checkbox'):
            self.checkbox.setFixedSize(ZoomManager.scaled(24), ZoomManager.scaled(24))
            check_color = "#6bcf7f"
            if self.task.priority == "high":
                check_color = "#ff6b6b"
            elif self.task.priority == "medium":
                check_color = "#ffd93d"
            self.checkbox.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#6bcf7f' if self.task.status == 'Выполнено' else 'transparent'};
                    border: {ZoomManager.scaled(2)}px solid {check_color};
                    border-radius: {ZoomManager.scaled(12)}px;
                    color: #ffffff;
                    font-weight: bold;
                    font-size: {ZoomManager.scaled(14)}px;
                }}
                QPushButton:hover {{
                    background-color: {check_color}40;
                }}
                QPushButton:checked {{
                    background-color: {check_color};
                    border: {ZoomManager.scaled(2)}px solid {check_color};
                }}
            """)
        
        # Обновляем шрифты
        if hasattr(self, 'title_label') and self.title_label:
            self.title_label.setFont(ZoomManager.font("Segoe UI", 10, QFont.Medium))
        if hasattr(self, 'repeat_label') and self.repeat_label:
            self.repeat_label.setFont(ZoomManager.font("Segoe UI", 9))
        if hasattr(self, 'priority_label') and self.priority_label:
            self.priority_label.setFont(ZoomManager.font("Segoe UI", 8))
        if hasattr(self, 'time_label'):
            self.time_label.setFont(ZoomManager.font("Consolas", 10))
    
    def mousePressEvent(self, event):
        """Начало перетаскивания"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Обработка отпускания кнопки мыши"""
        if event.button() == Qt.LeftButton:
            # Если это был клик (а не drag), открываем окно просмотра
            if self.drag_start_position is not None:
                distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
                if distance < 10:  # Это был клик, а не drag
                    # Открываем окно просмотра задачи
                    dialog = TaskViewDialog(self.task, self.parent_window)
                    dialog.exec()
            self.drag_start_position = None
        super().mouseReleaseEvent(event)
    
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
        """При наведении с drag - принимаем drop"""
        if event.mimeData().hasText():
            # Не разворачиваем секцию автоматически - пользователь должен открыть вручную
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



class DownloadThread(QThread):
    """Поток для скачивания файла с отслеживанием прогресса"""
    progress = Signal(int)
    finished = Signal(str)  # Путь к скачанному файлу или ошибка (начинается с "ERROR:")

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            req = urllib.request.Request(self.url)
            req.add_header('User-Agent', 'TaskMaster-Updater')
            
            with urllib.request.urlopen(req) as response:
                total_size = int(response.info().get('Content-Length', 0))
                bytes_downloaded = 0
                chunk_size = 1024 * 64
                
                with open(self.dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((bytes_downloaded / total_size) * 100)
                            self.progress.emit(percent)
            
            self.finished.emit(self.dest_path)
        except (FileNotFoundError, OSError) as e:
            # Ошибки, связанные с отсутствием файлов PyInstaller
            error_msg = str(e)
            if 'base_library.zip' in error_msg or '_MEI' in error_msg:
                self.finished.emit("ERROR: Не удалось загрузить обновление. Пожалуйста, скачайте обновление вручную с GitHub.")
            else:
                self.finished.emit(f"ERROR: {str(e)}")
        except Exception as e:
            self.finished.emit(f"ERROR: {str(e)}")


class UpdateDialog(QDialog):
    """Диалог уведомления об обновлении с поддержкой Markdown"""
    def __init__(self, parent, version, changelog, download_url):
        super().__init__(parent)
        self.download_url = download_url
        self.version = version
        
        self.setWindowTitle("Обновление доступно")
        self.setMinimumSize(450, 500)
        self.setStyleSheet(f"background-color: {THEME['window_bg_end']}; color: {THEME['text_primary']};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Заголовок
        title_lbl = QLabel(f"🚀 Доступна версия v{version}")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {THEME['accent_hover']};")
        layout.addWidget(title_lbl)
        
        # Чейнджлог
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMarkdown(changelog)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
                padding: 10px;
                color: {THEME['text_primary']};
                font-size: 13px;
            }}
        """)
        layout.addWidget(self.text_edit)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid {THEME['border_color']};
                border-radius: 5px;
                text-align: center;
                color: {THEME['text_primary']};
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME['accent_bg']};
                border-radius: 4px;
            }}
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Статус скачивания
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #4cd137; font-weight: bold;")
        self.status_lbl.hide()
        layout.addWidget(self.status_lbl)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.update_btn = QPushButton("Обновить сейчас")
        self.update_btn.setFixedHeight(36)
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent_bg']};
                color: {THEME['accent_text']};
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {THEME['accent_hover']};
            }}
        """)
        self.update_btn.clicked.connect(self._start_download)
        
        self.later_btn = QPushButton("Позже")
        self.later_btn.setFixedHeight(36)
        self.later_btn.setCursor(Qt.PointingHandCursor)
        self.later_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {THEME['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        self.later_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.later_btn)
        btn_layout.addWidget(self.update_btn)
        layout.addLayout(btn_layout)
        
        # Для перетаскивания
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def _start_download(self):
        # Если ссылка не на EXE (например, просто страница релиза), открываем в браузере
        if not self.download_url.lower().endswith('.exe'):
            import webbrowser
            webbrowser.open(self.download_url)
            self.status_lbl.setText("🌐 Открыта страница загрузки в браузере")
            self.status_lbl.show()
            self.update_btn.setText("Закрыть")
            self.update_btn.clicked.disconnect()
            self.update_btn.clicked.connect(self.accept)
            return

        self.update_btn.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # Определяем путь для скачивания
        temp_dir = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
        # Определяем имя файла из URL или используем стандартное
        filename = os.path.basename(self.download_url)
        if not filename or not filename.endswith('.exe'):
            filename = "TaskMaster-Installer.exe"
        self.temp_dest = os.path.join(temp_dir, filename)
        
        self.download_thread = DownloadThread(self.download_url, self.temp_dest)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.start()

    def _on_download_finished(self, result):
        if result.startswith("ERROR:"):
            self.update_btn.setEnabled(True)
            self.status_lbl.setText(f"Ошибка: {result[6:]}")
            self.status_lbl.setStyleSheet("color: #ff4444;")
            self.status_lbl.show()
            return
        
        # Это инсталлятор - запускаем его для обновления
        try:
            import subprocess
            # Запускаем инсталлятор (он сам определит, что это обновление)
            subprocess.Popen([result], shell=True)
            self.status_lbl.setText("✅ Инсталлятор запущен. Закройте приложение для обновления.")
            self.status_lbl.setStyleSheet("color: #4cd137;")
            self.status_lbl.show()
            self.update_btn.setText("🚀 Закрыть и обновить")
            self.update_btn.clicked.disconnect()
            self.update_btn.clicked.connect(self._close_and_update)
            self.update_btn.setEnabled(True)
        except Exception as e:
            self.status_lbl.setText(f"❌ Ошибка запуска инсталлятора: {str(e)}")
            self.status_lbl.setStyleSheet("color: #ff4444;")
            self.status_lbl.show()
            self.update_btn.setEnabled(True)

    def _close_and_update(self):
        """Закрытие приложения для обновления через инсталлятор"""
        self.accept()  # Закрываем диалог
        QApplication.quit()  # Закрываем приложение

    def _replace_executable(self, new_file_path):
        try:
            current_exe = sys.executable
            # Проверяем, запущены ли мы как EXE (frozen)
            is_frozen = getattr(sys, 'frozen', False)
            
            if not is_frozen:
                # Если мы просто скрипт, то имитируем успех (для тестов)
                print(f"DEBUG: Not frozen. Would replace {current_exe} with {new_file_path}")
                return True
                
            bak_file = current_exe + ".bak"
            
            # 1. Удаляем старый .bak если есть
            if os.path.exists(bak_file):
                try: os.remove(bak_file)
                except: pass
            
            # 2. Переименовываем текущий EXE (на Windows это можно делать с запущенным файлом)
            os.rename(current_exe, bak_file)
            
            # 3. Копируем новый файл на место старого
            shutil.copy2(new_file_path, current_exe)
            
            return True
        except Exception as e:
            print(f"Update error: {str(e)}")
            return False



class CompletedTasksDialog(DraggableDialog):
    """Диалог для просмотра и управления выполненными задачами"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Архив задач")
        self.resize(420, 550)
        self.parent_window = parent
        self.all_completed_tasks = []  # Все выполненные задачи
        self.selected_date = QDate.currentDate()  # Выбранная дата
        
        # Основной лейаут для тени
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Контейнер
        self.container = QFrame()
        self.container.setObjectName("dialogContainer")
        self.container.setStyleSheet(f"""
            QFrame#dialogContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 20px;
            }}
        """)
        main_layout.addWidget(self.container)
        
        self.apply_standard_shadow(self.container)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header ( draggable )
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 20, 20, 10)
        
        header_title = QLabel("Архив задач")
        header_title.setFont(ZoomManager.font("Segoe UI", 16, QFont.Bold))
        header_title.setStyleSheet(f"color: {THEME['text_primary']};")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {THEME['text_secondary']};
                font-size: 18px;
                border: none;
            }}
            QPushButton:hover {{
                color: {THEME['text_primary']};
                background-color: {THEME['secondary_hover']};
                border-radius: 15px;
            }}
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header_frame)
        
        # Навигатор по датам
        self.date_navigator = DateNavigator(self, self._on_date_changed)
        date_nav_frame = QFrame()
        date_nav_layout = QHBoxLayout(date_nav_frame)
        date_nav_layout.setContentsMargins(20, 10, 20, 10)
        date_nav_layout.addWidget(self.date_navigator)
        layout.addWidget(date_nav_frame)

        
        # Область скролла
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.tasks_layout = QVBoxLayout(scroll_content)
        self.tasks_layout.setContentsMargins(20, 10, 20, 20)
        self.tasks_layout.setSpacing(10)
        self.tasks_layout.addStretch()
        
        self.scroll.setWidget(scroll_content)
        layout.addWidget(self.scroll)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.tasks_container = QWidget()
        self.tasks_container.setStyleSheet("background: transparent;")
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(15, 0, 15, 20)
        self.tasks_layout.setSpacing(8)
        self.tasks_layout.addStretch()
        
        self.scroll.setWidget(self.tasks_container)
        layout.addWidget(self.scroll)
        
        # Добавляем grip
        self.add_grip(self.container)
    
    def _on_date_changed(self, date):
        """Обработчик изменения даты"""
        self.selected_date = date
        self._refresh_tasks()
    
    def _refresh_tasks(self):
        """Обновление списка задач по выбранной дате"""
        # Фильтруем задачи по дате выполнения
        current_date_str = self.selected_date.toString("yyyy-MM-dd")
        filtered_tasks = []
        
        for task in self.all_completed_tasks:
            # Проверяем дату выполнения задачи
            if task.completion_date:
                # Если дата выполнения совпадает с выбранной датой
                if task.completion_date == current_date_str:
                    filtered_tasks.append(task)
        
        # Отображаем отфильтрованные задачи
        self._display_tasks(filtered_tasks)
    
    def _display_tasks(self, tasks):
        """Отображение списка задач"""
        # Очистка
        while self.tasks_layout.count() > 1: # Оставляем stretch
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Добавление
        for task in tasks:
            # Создаем карточку, передаем parent_window для обработки кликов (чекбокс, удаление)
            card = TaskCard(task, self.parent_window) 
            card.setAcceptDrops(False)
            
            # Скрываем кнопку таймера и разделитель в архиве
            if hasattr(card, 'toggle_timer_btn'):
                card.toggle_timer_btn.setVisible(False)
            if hasattr(card, 'timer_separator'):
                card.timer_separator.setVisible(False)
            
            self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, card)
        
    def set_tasks(self, tasks, parent_window):
        """Установка списка всех выполненных задач"""
        self.all_completed_tasks = tasks
        self.parent_window = parent_window
        # Обновляем отображение по текущей выбранной дате
        self._refresh_tasks()

class TimeReportDialog(DraggableDialog):
    """Диалог отчета по времени за выбранный день"""
    def __init__(self, parent=None, initial_date=None):
        super().__init__(parent)
        self.selected_date = initial_date or QDate.currentDate()
        self.tasks = parent.tasks if parent else []
        self.parent_window = parent
        
        self.setWindowTitle("Отчет по времени")
        self.setMinimumWidth(400)
        self.setMinimumHeight(450)
        
        self._setup_ui()
        self._refresh_report()

    def _setup_ui(self):
        # Основной лейаут для тени
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Контейнер
        self.container = QFrame()
        self.container.setObjectName("reportContainer")
        self.container.setStyleSheet(f"""
            QFrame#reportContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border: 1px solid {THEME['border_color']};
                border-radius: 20px;
            }}
        """)
        main_layout.addWidget(self.container)
        
        # Применяем тень
        self.apply_standard_shadow(self.container)
        
        inner_layout = QVBoxLayout(self.container)
        inner_layout.setContentsMargins(25, 25, 25, 25)
        inner_layout.setSpacing(18)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(12)
        
        self.title_icon_lbl = QLabel()
        self.title_icon_lbl.setFixedSize(32, 32)
        self.title_icon_lbl.setPixmap(create_report_icon(size=32).pixmap(32, 32))
        header.addWidget(self.title_icon_lbl)
        
        title_lbl = QLabel("Отчет по времени")
        title_lbl.setFont(ZoomManager.font("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {THEME['text_primary']}; background: transparent;")
        header.addWidget(title_lbl)
        
        header.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {THEME['text_secondary']};
                font-size: 20px;
                border: none;
            }}
            QPushButton:hover {{
                color: {THEME['text_primary']};
                background-color: {THEME['secondary_hover']};
                border-radius: 16px;
            }}
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        
        inner_layout.addLayout(header)
        
        # Date Navigation
        date_nav = QHBoxLayout()
        date_nav.setSpacing(12)
        
        prev_btn = QPushButton("◀")
        prev_btn.setFixedSize(36, 36)
        prev_btn.setCursor(QCursor(Qt.PointingHandCursor))
        prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['secondary_bg']};
                color: {THEME['text_primary']};
                border-radius: 10px;
                border: 1px solid {THEME['border_color']};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                border-color: {THEME['accent_hover']};
            }}
        """)
        prev_btn.clicked.connect(lambda: self._change_date(-1))
        
        self.date_btn = QPushButton(self.selected_date.toString("dd.MM.yyyy"))
        self.date_btn.setFixedHeight(36)
        self.date_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.date_btn.setFont(ZoomManager.font("Segoe UI", 11, QFont.Medium))
        self.date_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['input_bg']};
                color: {THEME['text_primary']};
                padding: 0 20px;
                border: 1px solid {THEME['border_color']};
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {THEME['input_bg_focus']};
                border-color: {THEME['accent_hover']};
            }}
        """)
        self.date_btn.clicked.connect(self._show_calendar)
        
        next_btn = QPushButton("▶")
        next_btn.setFixedSize(36, 36)
        next_btn.setCursor(QCursor(Qt.PointingHandCursor))
        next_btn.setStyleSheet(prev_btn.styleSheet())
        next_btn.clicked.connect(lambda: self._change_date(1))
        
        date_nav.addWidget(prev_btn)
        date_nav.addWidget(self.date_btn, 1)
        date_nav.addWidget(next_btn)
        
        inner_layout.addLayout(date_nav)
        
        # Tasks List
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll.verticalScrollBar().setStyleSheet(f"""
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {THEME['scroll_handle']};
                border-radius: 4px;
            }}
        """)
        
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        
        self.scroll.setWidget(self.list_container)
        inner_layout.addWidget(self.scroll)
        
        # Footer
        footer = QHBoxLayout()
        footer.setContentsMargins(5, 5, 5, 5)
        
        self.total_lbl = QLabel("Итого: 00:00:00")
        self.total_lbl.setFont(ZoomManager.font("Segoe UI", 11, QFont.Bold))
        self.total_lbl.setStyleSheet(f"color: {THEME['text_primary']}; background: transparent;")
        footer.addWidget(self.total_lbl)
        
        footer.addStretch()
        
        export_btn = QPushButton("Экспорт")
        export_btn.setFixedHeight(36)
        export_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_btn.setFont(ZoomManager.font("Segoe UI", 10, QFont.Bold))
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['accent_bg']};
                color: {THEME['accent_text']};
                padding: 0 25px;
                border-radius: 12px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME['accent_hover']};
            }}
        """)
        export_btn.clicked.connect(self._export_report)
        footer.addWidget(export_btn)
        
        inner_layout.addLayout(footer)

    def _change_date(self, days):
        self.selected_date = self.selected_date.addDays(days)
        self.date_btn.setText(self.selected_date.toString("dd.MM.yyyy"))
        self._refresh_report()

    def _show_calendar(self):
        cal_dialog = QDialog(self)
        cal_dialog.setWindowTitle("Выбор даты")
        cal_dialog.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        cal_dialog.setAttribute(Qt.WA_TranslucentBackground)
        
        # Стилизованный контейнер
        container = QFrame(cal_dialog)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['window_bg_start']};
                border: 1px solid {THEME['border_color']};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(cal_dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)
        
        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(10, 10, 10, 10)
        
        calendar = CustomCalendarWidget()
        calendar.calendar.setSelectedDate(self.selected_date)
        inner_layout.addWidget(calendar)
        
        def on_selected():
            self.selected_date = calendar.calendar.selectedDate()
            self.date_btn.setText(self.selected_date.toString("dd.MM.yyyy"))
            self._refresh_report()
            cal_dialog.accept()
            
        calendar.calendar.clicked.connect(on_selected)
        
        # Позиционирование по центру под кнопкой даты
        cal_dialog.adjustSize()
        pos = self.date_btn.mapToGlobal(QPoint(0, self.date_btn.height()))
        x = pos.x() + (self.date_btn.width() - cal_dialog.width()) // 2
        
        # Проверка границ экрана
        screen_geo = self.screen().geometry()
        if x + cal_dialog.width() > screen_geo.right():
            x = screen_geo.right() - cal_dialog.width() - 10
        if x < screen_geo.left():
            x = screen_geo.left() + 10
            
        cal_dialog.move(x, pos.y() + 5)
        
        cal_dialog.exec()

    def _refresh_report(self):
        # Очистка текущего списка
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        date_str = self.selected_date.toString("yyyy-MM-dd")
        total_seconds = 0
        found_any = False
        
        # Сортируем задачи по времени
        report_data = []
        for task in self.tasks:
            time_val = task.time_log.get(date_str, 0)
            if time_val > 0:
                report_data.append((task, time_val))
                
        report_data.sort(key=lambda x: x[1], reverse=True)
        
        for task, time_val in report_data:
            total_seconds += time_val
            found_any = True
            
            item_frame = QFrame()
            item_frame.setObjectName("reportItem")
            item_frame.setCursor(QCursor(Qt.PointingHandCursor))
            item_frame.setProperty("taskId", task.id)
            item_frame.setStyleSheet(f"""
                QFrame#reportItem {{
                    background-color: {THEME['secondary_bg']};
                    border-radius: 10px;
                }}
                QFrame#reportItem:hover {{
                    background-color: {THEME['secondary_hover']};
                }}
            """)
            item_frame.installEventFilter(self)
            
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(15, 12, 15, 12)
            
            text_container = QVBoxLayout()
            text_container.setSpacing(2)
            
            title_lbl = QLabel(task.title)
            title_lbl.setFont(ZoomManager.font("Segoe UI", 10, QFont.Medium))
            title_lbl.setWordWrap(True)
            title_lbl.setStyleSheet(f"color: {THEME['text_primary']}; background: transparent; border: none;")
            text_container.addWidget(title_lbl)
            
            if task.description:
                # Показываем короткое превью описания
                preview = task.description.split('\n')[0]
                if len(preview) > 60: preview = preview[:57] + "..."
                desc_lbl = QLabel(preview)
                desc_lbl.setFont(ZoomManager.font("Segoe UI", 8))
                desc_lbl.setStyleSheet(f"color: {THEME['text_tertiary']}; background: transparent; border: none;")
                text_container.addWidget(desc_lbl)
                item_frame.setToolTip(task.description)
            
            time_lbl = QLabel(self._format_time(time_val))
            time_lbl.setFont(ZoomManager.font("Consolas", 10, QFont.Bold))
            time_lbl.setStyleSheet(f"color: {THEME['text_primary']}; background: transparent; border: none;")
            
            item_layout.addLayout(text_container, 1)
            item_layout.addWidget(time_lbl)
            
            self.list_layout.insertWidget(self.list_layout.count() - 1, item_frame)
            
        if not found_any:
            no_tasks_lbl = QLabel("В этот день задач не зафиксировано")
            no_tasks_lbl.setAlignment(Qt.AlignCenter)
            no_tasks_lbl.setStyleSheet(f"color: {THEME['text_tertiary']}; padding: 20px;")
            self.list_layout.insertWidget(0, no_tasks_lbl)
            
        self.total_lbl.setText(f"Итого: {self._format_time(total_seconds)}")

    def eventFilter(self, obj, event):
        if obj.objectName() == "reportItem" and event.type() == QEvent.MouseButtonPress:
            task_id = obj.property("taskId")
            self._view_task(task_id)
            return True
        return super().eventFilter(obj, event)

    def _view_task(self, task_id):
        from typing import List
        target_task = next((t for t in self.tasks if t.id == task_id), None)
        if target_task:
            dialog = TaskViewDialog(target_task, self.parent_window)
            dialog.exec()
            # Обновляем отчет при закрытии (вдруг задачу удалили/изменили)
            self._refresh_report()

    def _format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _export_report(self):
        date_str = self.selected_date.toString("dd.MM.yyyy")
        filename = f"Report_{self.selected_date.toString('yyyy-MM-dd')}.txt"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"ОТЧЕТ ПО ВРЕМЕНИ: {date_str}\n")
                f.write("-" * 40 + "\n\n")
                
                date_key = self.selected_date.toString("yyyy-MM-dd")
                total_seconds = 0
                
                for task in self.tasks:
                    time_val = task.time_log.get(date_key, 0)
                    if time_val > 0:
                        total_seconds += time_val
                        f.write(f"[{self._format_time(time_val)}] {task.title}\n")
                        if task.description:
                            f.write(f"   Описание: {task.description}\n")
                        f.write("-" * 20 + "\n")
                
                f.write(f"\nВСЕГО ЗА ДЕНЬ: {self._format_time(total_seconds)}\n")
            
            QMessageBox.information(self, "Экспорт", f"Отчет сохранен в файл: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчет: {e}")

class ModernTaskManager(QMainWindow):
    """Главное окно современного менеджера задач"""
    update_found = Signal(bool)
    
    def __init__(self):
        super().__init__()
        
        # Очистка старых версий после обновления
        self._cleanup_old_version()
        
        self.tasks: List[Task] = []
        self.drag_position = None
        self.selected_date = QDate.currentDate() # Текущая выбранная дата
        self.update_available = False  # Флаг доступности обновления
        self.current_filter = "all"    # Текущий фильтр задач
        self.current_tag_filter = None  # Текущий фильтр по тегу (None = все теги)
        self._initial_resize_done = False # Флаг для предотвращения авторесайза после старта
        self.notifications_dismissed = False  # Флаг: пользователь закрыл уведомления
        self.overdue_tasks: List[Task] = []  # Список просроченных задач
        self._active_filter_menu = None  # Ссылка на открытое меню фильтров
        
        # Устанавливаем eventFilter для отслеживания перемещения окна
        self.installEventFilter(self)
        
        # Таймер для трекинга времени
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timers)
        self.timer.start(1000) # Обновление каждую секунду
        
        # Загружаем сохраненную тему перед созданием UI
        saved_theme = SettingsManager.get("current_theme")
        if saved_theme and saved_theme in AVAILABLE_THEMES:
            THEME.update(AVAILABLE_THEMES[saved_theme])
        
        # Константы для расчета размера (определяем ДО создания UI)
        self.MAX_VISIBLE_ACTIVE = 4  # Максимум видимых активных задач
        self.MAX_VISIBLE_COMPLETED = 2  # Максимум видимых выполненных задач
        self.TASK_CARD_HEIGHT = 80  # Примерная высота карточки задачи (с отступами)
        self.BASE_HEIGHT = 250  # Высота базовых элементов (заголовок, форма, фильтры)
        self.HEADER_HEIGHT = 30  # Высота заголовка секции
        self.SEPARATOR_HEIGHT = 10  # Высота разделителя
        self.BOTTOM_BAR_HEIGHT = 45  # Высота нижней панели
        self.SPACING = 8  # Отступ между элементами
        
        # Сначала создаем UI, потом загружаем задачи
        self._setup_ui()
        self._load_tasks()
        # Явно обновляем список задач после загрузки
        self._refresh_tasks()
        
        # Применяем стили и фиксы прозрачности при запуске
        self._refresh_styles()
        
        # Подключаем сигнал обновления
        self.update_found.connect(self._show_update_badge)
        
        self.setWindowTitle("TaskMaster")
        self.setMinimumSize(320, 400)
        
        # Временный размер, будет пересчитан после загрузки задач
        self.resize(380, 400)
        
        # Устанавливаем иконку окна (если еще не установлена)
        if self.windowIcon().isNull():
            app_icon = create_app_icon()
            self.setWindowIcon(app_icon)
        
        # Автоматическая проверка обновлений при запуске (через 2 секунды)
        QTimer.singleShot(2000, self._check_updates_background)
        
        # Убираем рамку через NCCALCSIZE (см. nativeEvent), но оставляем флаг Window
        # чтобы работало Aero Snap.
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint
        )
        # Отключаем прозрачность, чтобы избежать черных артефактов
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Восстановление состояния окна (геометрия)
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

        # ТРЕКИНГ СОСТОЯНИЯ ПОПАПОВ (Fix for detachment bug)
        self._active_popups = set()
        self._patch_combos()
        
    def _patch_combos(self):
        """Патчит методы showPopup/hidePopup для всех комбобоксов"""
        combos = self.findChildren(QComboBox)
        # print(f"DEBUG: Found {len(combos)} combos via findChildren", flush=True)
        for combo in combos:
            self._patch_single_combo(combo)
            
        # Эксплицитный патч для гарантии
        if hasattr(self, 'priority_combo'):
             # print("DEBUG: Explicitly patching priority_combo", flush=True)
             self._patch_single_combo(self.priority_combo)
        if hasattr(self, 'filter_combo'):
             self._patch_single_combo(self.filter_combo)
            
    def _patch_single_combo(self, combo):
        # Чтобы не патчить дважды
        if getattr(combo, "_is_patched", False):
            return
            
        # print(f"DEBUG: Patching combo: {combo}", flush=True)
            
        old_show = combo.showPopup
        old_hide = combo.hidePopup
        
        def new_show():
            # print(f"DEBUG: Showing popup for {combo}", flush=True)
            self._active_popups.add(combo)
            old_show()
            
        def new_hide():
            # print(f"DEBUG: Hiding popup (grace period) for {combo}", flush=True)
            # Задержка удаления из списка активных, чтобы успеть заблокировать перетаскивание
            # если событие Hide вызвано кликом заголовка. 
            # 200 мс достаточно.
            QTimer.singleShot(200, lambda: self._active_popups.discard(combo))
            old_hide()
        
        combo.showPopup = new_show
        combo.hidePopup = new_hide
        combo._is_patched = True

    def nativeEvent(self, eventType, message):
        try:
            # PySide6: message is int (pointer)
            msg = ctypes.wintypes.MSG.from_address(int(message))
        except Exception as e:
            print(f"Error reading MSG: {e}")
            return super().nativeEvent(eventType, message)

        if msg.message == 0x0083: # WM_NCCALCSIZE
            # Обработка NCCALCSIZE позволяет убрать стандартную рамку Windows,
            # но сохранить функциональность (прилипание, горячие клавиши)
            return True, 0

        if msg.message == 0x0112: # WM_SYSCOMMAND
            # Ловим команду перемещения или изменения размера
            cmd = msg.wParam & 0xFFF0
            if cmd == 0xF010 or cmd == 0xF000: # SC_MOVE or SC_SIZE
                self._force_close_popups()

        if msg.message == 0x00A1: # WM_NCLBUTTONDOWN
            # Если началось перемещение окна (клик по заголовку)
            if msg.wParam == 2: # HTCAPTION
                # Проверяем, не кликнули ли на кнопку фильтров
                if hasattr(self, 'filter_btn') and self.filter_btn.isVisible():
                    # Получаем координаты клика
                    x = ctypes.c_short(msg.lParam & 0xFFFF).value
                    y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                    global_pos = QPoint(x, y)
                    filter_btn_global_pos = self.filter_btn.mapToGlobal(QPoint(0, 0))
                    filter_btn_rect = QRect(filter_btn_global_pos, self.filter_btn.size())
                    if filter_btn_rect.contains(global_pos):
                        return True, 0 # Блокируем перетаскивание
                
                # Если есть открытые меню - закрываем их и БЛОКИРУЕМ перетаскивание
                # (чтобы список не "уезжал" вместе с окном)
                if self._has_active_popups():
                    self._force_close_popups()
                    return True, 0 # Консьюмим событие, перетаскивание НЕ начнется

        if msg.message == 0x0231: # WM_ENTERSIZEMOVE
             self._force_close_popups()
        
        if msg.message == 0x0084: # WM_NCHITTEST
            # Если есть активное всплывающее окно - блокируем нативное перетаскивание,
            # возвращая HTCLIENT.
            if self._has_active_popups():
                return True, 1 # HTCLIENT

            # Получаем координаты мыши (LPARAM = y << 16 | x)
            x = ctypes.c_short(msg.lParam & 0xFFFF).value
            y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
            
            global_pos = QPoint(x, y)
            local_pos = self.mapFromGlobal(global_pos)
            
            # --- Логика изменения размера (Borders) ---
            # Увеличиваем зону захвата для удобства
            border_width = 8
            w = self.width()
            h = self.height()
            lx = local_pos.x()
            ly = local_pos.y()
            
            resize_result = None
            
            if lx < border_width:
                if ly < border_width:
                    resize_result = 13 # HTTOPLEFT
                elif ly > h - border_width:
                    resize_result = 16 # HTBOTTOMLEFT
                else:
                    resize_result = 10 # HTLEFT
            elif lx > w - border_width:
                if ly < border_width:
                    resize_result = 14 # HTTOPRIGHT
                elif ly > h - border_width:
                    resize_result = 17 # HTBOTTOMRIGHT
                else:
                    resize_result = 11 # HTRIGHT
            elif ly < border_width:
                resize_result = 12 # HTTOP
            elif ly > h - border_width:
                resize_result = 15 # HTBOTTOM
                
            if resize_result:
                return True, resize_result

            # Проверяем, не кликнули ли на кнопку фильтров
            if hasattr(self, 'filter_btn') and self.filter_btn.isVisible():
                filter_btn_global_pos = self.filter_btn.mapToGlobal(QPoint(0, 0))
                filter_btn_rect = QRect(filter_btn_global_pos, self.filter_btn.size())
                if filter_btn_rect.contains(global_pos):
                    return True, 1 # HTCLIENT - не перетаскивать
            
            # --- Логика перемещения (Title Bar) ---
            if hasattr(self, 'header_widget'):
                # Определяем глобальную позицию заголовка
                header_pos = self.header_widget.mapTo(self, QPoint(0,0))
                header_rect = QRect(header_pos, self.header_widget.size())
                
                if header_rect.contains(local_pos):
                     # Проверяем дочерний виджет (кнопки)
                    child = self.header_widget.childAt(self.header_widget.mapFrom(self, local_pos))
                    
                    if not isinstance(child, QPushButton):
                         # Если есть активные попапы - блокируем драг (возвращаем HTCLIENT)
                         if self._has_active_popups():
                             return True, 1 # HTCLIENT
                             
                         # Иначе разрешаем стандартный драг Windows (HTCAPTION)
                         # Это вернет прилипание (Snap Layouts)
                         return True, 2 # HTCAPTION
            
            return True, 1 # HTCLIENT
            
        return super().nativeEvent(eventType, message)

    # mousePressEvent удален, так как мы вернули нативный драг для работы Snap

    def _has_active_popups(self):
        """Проверка наличия активных всплывающих окон"""
        # Проверяем меню фильтров
        if self._active_filter_menu and self._active_filter_menu.isVisible():
            return True
        
        # 0. Самая надежная проверка через monkey-patching
        if hasattr(self, '_active_popups') and self._active_popups:
             # print(f"DEBUG: NCHITTEST sees active popups: {self._active_popups}", flush=True)
             return True

        # 1. Обычный Qt механизм
        if QApplication.activePopupWidget():
            return True
            
        # 2. Топ-левел виджеты с флагом Popup
        for widget in QApplication.topLevelWidgets():
            if widget is not self and widget.isWindow() and widget.isVisible():
                 flags = widget.windowFlags()
                 if (flags & Qt.Popup) or (flags & Qt.ToolTip) or (flags & Qt.SplashScreen):
                    return True

        # 3. Все QComboBox в интерфейсе (общий случай)
        for combo in self.findChildren(QComboBox):
            if combo.isVisible() and combo.view() and combo.view().isVisible():
                return True
                
        return False
        
    def _force_close_popups(self):
        """Принудительное закрытие всех всплывающих окон"""
        # 0. Закрываем меню фильтров
        if self._active_filter_menu:
            self._active_filter_menu.close()
            self._active_filter_menu = None
        
        # 1. Закрываем через наш надежный список
        if hasattr(self, '_active_popups'):
            for combo in list(self._active_popups):
                combo.hidePopup()
        
        # 2. Обычный Qt механизм
        popup = QApplication.activePopupWidget()
        if popup:
            popup.close()
            
        # 3. Топ-левел виджеты с флагом Popup
        for widget in QApplication.topLevelWidgets():
            if widget is not self and widget.isWindow() and widget.isVisible():
                 # Проверяем флаги
                 flags = widget.windowFlags()
                 if (flags & Qt.Popup) or (flags & Qt.ToolTip):
                    widget.close()

        # 4. Все QComboBox в интерфейсе
        for combo in self.findChildren(QComboBox):
            if combo.isVisible():
                combo.hidePopup()
                # Агрессивное скрытие контейнера view
                if combo.view() and combo.view().window():
                     combo.view().window().setVisible(False)
        
        # Обработка событий для мгновенного применения
        QApplication.processEvents()
        
    def _cleanup_old_version(self):
        """Удаляет старый .bak файл, оставшийся после обновления"""
        try:
            current_exe = sys.executable
            bak_file = current_exe + ".bak"
            if os.path.exists(bak_file):
                os.remove(bak_file)
                print(f"Cleaned up old version: {bak_file}")
        except Exception as e:
            # Если файл еще занят или другая ошибка - просто игнорируем
            pass
            
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
        self.main_container = QFrame()
        self.main_container.setObjectName("mainContainer")
        self.main_container.setStyleSheet(f"""
            QFrame#mainContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['window_bg_start']},
                    stop:1 {THEME['window_bg_end']}
                );
                border: none;
            }}
        """)
        
        container_layout = QVBoxLayout(self.main_container)
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
        
        self.app_title_lbl = QLabel("TaskMaster")
        self.app_title_lbl.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.app_title_lbl.setStyleSheet(f"color: {THEME['text_primary']};")
        self.app_title_lbl.setTextInteractionFlags(Qt.NoTextInteraction)
        title_layout.addWidget(self.app_title_lbl)
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        

        
        # Кнопка уведомлений
        self.notification_btn = NotificationButton()
        self.notification_btn.clicked.connect(self._show_notifications)
        # Кнопка всегда видна, но badge показывается только при наличии просроченных задач
        header_layout.addWidget(self.notification_btn)
        
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
                background-color: {THEME['accent_bg']};
                color: {THEME['accent_text']};
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
        
        # === Кнопка фильтров (Компактная) ===
        filter_header_layout = QHBoxLayout()
        filter_header_layout.setContentsMargins(0, 5, 0, 5)
        
        # Счетчик задач
        self.task_counter = QLabel("0 задач")
        self.task_counter.setFont(QFont("Segoe UI", 9))
        self.task_counter.setStyleSheet(f"color: {THEME['text_secondary']};")
        self.task_counter.setTextInteractionFlags(Qt.NoTextInteraction)
        
        filter_header_layout.addWidget(self.task_counter)
        filter_header_layout.addStretch()
        
        # Создаем кастомную кнопку, которая блокирует перетаскивание окна
        class FilterButton(QPushButton):
            def __init__(self, parent_window, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.parent_window = parent_window
            
            def mousePressEvent(self, event):
                """Перехватываем нажатие мыши, чтобы предотвратить перетаскивание окна"""
                if event.button() == Qt.LeftButton:
                    # Сбрасываем позицию перетаскивания в родительском окне
                    if hasattr(self.parent_window, 'drag_position'):
                        self.parent_window.drag_position = None
                    # Принимаем событие, чтобы оно не передавалось родителю
                    event.accept()
                super().mousePressEvent(event)
            
            def mouseMoveEvent(self, event):
                """Перехватываем движение мыши, чтобы предотвратить перетаскивание окна"""
                if event.buttons() == Qt.LeftButton:
                    # Сбрасываем позицию перетаскивания в родительском окне
                    if hasattr(self.parent_window, 'drag_position'):
                        self.parent_window.drag_position = None
                    # Принимаем событие, чтобы оно не передавалось родителю
                    event.accept()
                super().mouseMoveEvent(event)
            
            def mouseReleaseEvent(self, event):
                """Перехватываем отпускание мыши"""
                if event.button() == Qt.LeftButton:
                    # Сбрасываем позицию перетаскивания в родительском окне
                    if hasattr(self.parent_window, 'drag_position'):
                        self.parent_window.drag_position = None
                    event.accept()
                super().mouseReleaseEvent(event)
        
        self.filter_btn = FilterButton(self, "🔘 Фильтры: Все")
        self.filter_btn.setCursor(Qt.PointingHandCursor)
        self.filter_btn.setFixedHeight(28)
        self.filter_btn.setMinimumWidth(130)
        self.filter_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid {THEME['border_color']};
                color: {THEME['text_secondary']};
                border-radius: 14px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: {THEME['text_primary']};
            }}
        """)
        self.filter_btn.clicked.connect(self._show_filter_menu)
        filter_header_layout.addWidget(self.filter_btn)
        
        container_layout.addLayout(filter_header_layout)
        
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
        main_tasks_layout.setSpacing(0)  # Полностью убираем отступ
        
        # === Секция активных задач ===
        self.active_header = QLabel("📋 Активные задачи")
        self.active_header.setFont(ZoomManager.font("Segoe UI", 11, QFont.Bold))
        self.active_header.setStyleSheet(f"color: {THEME['text_primary']}; padding: 0px;") # Убираем отступы
        main_tasks_layout.addWidget(self.active_header)
        
        # Контейнер для активных задач с поддержкой drop
        self.active_tasks_container = DropZoneWidget("active", self)
        self.active_tasks_container.setObjectName("active_drop_zone")
        self.active_tasks_container.setMinimumHeight(0)  # Минимальная высота 0, если задач нет
        self.active_tasks_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)  # Не растягиваться
        # self.active_tasks_container.setStyleSheet("border: 2px solid red;") # DEBUG
        self.active_tasks_layout = QVBoxLayout(self.active_tasks_container)
        self.active_tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.active_tasks_layout.setSpacing(4) # Небольшой отступ между задачами
        self.active_tasks_layout.addStretch()
        main_tasks_layout.addWidget(self.active_tasks_container, 0)  # Stretch factor 0 - не растягивается
        
        main_tasks_layout.addStretch()
        
        # Для обратной совместимости
        self.tasks_layout = self.active_tasks_layout
        
        scroll.setWidget(self.tasks_container)
        container_layout.addWidget(scroll, 1)
        
        # --- Bottom Bar with Zoom Slider ---
        self.bottom_bar = QFrame()
        self.bottom_bar.setObjectName("bottomBar")
        self.bottom_bar.setFixedHeight(ZoomManager.scaled(45))
        self.bottom_bar.setStyleSheet(f"""
            QFrame#bottomBar {{
                background-color: {THEME['card_bg']};
                border: 1px solid {THEME['border_color']}; 
                border-radius: 22px;
            }}
        """)
        
        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(15, 0, 10, 0)
        bottom_layout.setSpacing(8)
        
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
        
        # Кнопка управления тегами
        self.tags_btn = QPushButton("🏷️")
        self.tags_btn.setFixedSize(32, 32)
        self.tags_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.tags_btn.setToolTip("Управление тегами")
        self.tags_btn.setStyleSheet(f"""
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
        self.tags_btn.clicked.connect(self._show_tags_manager)
        tools_layout.addWidget(self.tags_btn)
        
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
        
        # Кнопка отчетов
        self.report_btn = QPushButton()
        self.report_btn.setToolTip("Отчеты")
        self.report_btn.setFixedSize(24, 24)
        self.report_btn.setIcon(create_report_icon(size=20))
        self.report_btn.setIconSize(QSize(20, 20))
        self.report_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
            }}
        """)
        self.report_btn.clicked.connect(self._open_time_report)
        tools_layout.addWidget(self.report_btn)
        



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
        self.update_btn.setObjectName("updateBtn")  # Для точного применения стилей
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
        bottom_layout.addWidget(self.update_btn)

        # Кнопка переключения инструментов (Слева)
        self.toggle_tools_btn = QPushButton("🛠️")
        self.toggle_tools_btn.setObjectName("toolsBtn")
        self.toggle_tools_btn.setFixedSize(32, 32)
        self.toggle_tools_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_tools_btn.clicked.connect(self._toggle_tools)
        bottom_layout.addWidget(self.toggle_tools_btn)
        
        # Начальная установка подсказок и инициализация стилей
        self.toggle_tools_btn.setToolTip("Показать инструменты")
        self._update_bottom_bar_styles()

        # Добавляем контейнер инструментов в нижнюю панель (сразу за кнопкой)
        bottom_layout.addWidget(self.tools_container)
        
        # Кнопка выполненных задач (справа, принимает drop перетаскиваемых задач)
        self.completed_tasks_btn = QPushButton()
        self.completed_tasks_btn.setFixedSize(32, 32)
        self.completed_tasks_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.completed_tasks_btn.setToolTip("Архив задач")
        self.completed_tasks_btn.clicked.connect(self._open_completed_tasks_dialog)
        # Разрешаем drop на кнопку и обрабатываем его через eventFilter
        self.completed_tasks_btn.setAcceptDrops(True)
        self.completed_tasks_btn.installEventFilter(self)
        self._update_completed_btn_style()
        bottom_layout.addWidget(self.completed_tasks_btn)
        
        # Спейсер, чтобы сдвинуть всё влево
        bottom_layout.addStretch()
        
        # Добавляем нижнюю панель в контейнер с отступами для эффекта «пилюли»
        bottom_wrapper = QWidget()
        bottom_wrapper_layout = QHBoxLayout(bottom_wrapper)
        bottom_wrapper_layout.setContentsMargins(15, 0, 15, 12)
        bottom_wrapper_layout.setSpacing(0)
        bottom_wrapper_layout.addWidget(self.bottom_bar)
        container_layout.addWidget(bottom_wrapper)
        
        # Убеждаемся, что главный контейнер добавлен в основной лейаут центрального виджета
        if main_layout.count() == 0:
            main_layout.addWidget(self.main_container)
    
    
    def _toggle_tools(self):
        """Переключение видимости панели инструментов"""
        is_visible = self.tools_container.isVisible()
        self.tools_container.setVisible(not is_visible)
        
        # Обновляем подсказку
        self.toggle_tools_btn.setToolTip("Скрыть инструменты" if not is_visible else "Показать инструменты")
        
        # Обновляем стили всех кнопок через центральный метод
        self._update_bottom_bar_styles()
    
    def _open_completed_tasks_dialog(self):
        """Открытие диалога выполненных задач"""
        dialog = CompletedTasksDialog(self)
        
        # Фильтруем выполненные задачи
        completed_tasks = [t for t in self.tasks if t.status == "Выполнено"]
        
        dialog.set_tasks(completed_tasks, self)
        dialog.exec()
    
    def _update_completed_btn_style(self):
        """Обновление стиля кнопки выполненных задач"""
        if hasattr(self, 'completed_tasks_btn'):
            self.completed_tasks_btn.setStyleSheet(f"""
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
    def _open_time_report(self):
        """Открытие диалога отчета по времени"""
        dialog = TimeReportDialog(self)
        dialog.exec()

    def _show_tags_manager(self):
        """Показать диалог управления тегами с фильтрацией"""
        # Получаем все уникальные теги из задач
        all_tags = set()
        for task in self.tasks:
            if hasattr(task, 'tags') and task.tags:
                all_tags.update(task.tags)
        
        if not all_tags:
            QMessageBox.information(self, "Теги", "У вас пока нет тегов. Добавьте теги к задачам через диалог редактирования.")
            return
        
        # Создаем меню с тегами для фильтрации
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME['card_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                border-radius: 4px;
                color: {THEME['text_primary']};
            }}
            QMenu::item:selected {{
                background-color: {THEME['accent_bg']};
                color: {THEME['accent_text']};
            }}
        """)
        
        # Опция "Все теги"
        all_action = QAction("🔘 Все теги", self)
        all_action.setCheckable(True)
        all_action.setChecked(self.current_tag_filter is None)
        all_action.triggered.connect(lambda: self._set_tag_filter(None))
        menu.addAction(all_action)
        
        menu.addSeparator()
        
        # Опции для каждого тега
        for tag in sorted(all_tags):
            action = QAction(f"🏷️ {tag}", self)
            action.setCheckable(True)
            action.setChecked(self.current_tag_filter == tag)
            action.triggered.connect(lambda checked, t=tag: self._set_tag_filter(t))
            menu.addAction(action)
        
        # Показываем меню над кнопкой
        menu.adjustSize()  # Подгоняем размер меню
        btn_pos = self.tags_btn.mapToGlobal(QPoint(0, 0))
        menu_pos = QPoint(btn_pos.x(), btn_pos.y() - menu.height() - 4)
        
        # Проверка границ экрана
        screen_geo = self.screen().geometry()
        if menu_pos.y() < screen_geo.top():
            menu_pos.setY(btn_pos.y() + self.tags_btn.height() + 4)  # Если не помещается вверху, показываем внизу
        
        menu.exec(menu_pos)
    
    def _set_tag_filter(self, tag):
        """Установка фильтра по тегу"""
        self.current_tag_filter = tag
        self._refresh_tasks()
    
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
            # Закрываем меню фильтров при начале перемещения
            if self._active_filter_menu and self._active_filter_menu.isVisible():
                self._active_filter_menu.close()
                self._active_filter_menu = None
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def moveEvent(self, event):
        """Обработка перемещения окна"""
        # Закрываем меню фильтров при перемещении окна
        if self._active_filter_menu and self._active_filter_menu.isVisible():
            self._active_filter_menu.close()
            self._active_filter_menu = None
        super().moveEvent(event)
    
    def eventFilter(self, obj, event):
        """Фильтр событий: позиция grip и drop на кнопку выполненных задач"""
        # Закрываем меню фильтров при перемещении главного окна
        if obj == self and event.type() == QEvent.Move:
            if self._active_filter_menu and self._active_filter_menu.isVisible():
                self._active_filter_menu.close()
                self._active_filter_menu = None
        
        # Предотвращаем перетаскивание окна при клике на кнопку фильтров
        if hasattr(self, 'filter_btn') and obj == self.filter_btn:
            if event.type() == QEvent.MouseButtonPress:
                # Останавливаем перетаскивание окна, если оно началось
                self.drag_position = None
                # Принимаем событие, чтобы оно не передавалось дальше
                return False
            elif event.type() == QEvent.MouseMove:
                # Если мышь движется над кнопкой, не начинаем перетаскивание
                if event.buttons() == Qt.LeftButton:
                    self.drag_position = None
                return False
        
        # Обновление позиции grip внизу окна
        if hasattr(self, 'grip_container') and obj == self.grip_container and event.type() == QEvent.Resize:
            if hasattr(self, 'grip_wrapper'):
                # Размер кнопки 24x24, отступы контейнера 20px, позиционируем: ширина - отступ - размер кнопки
                self.grip_wrapper.move(obj.width() - 44, obj.height() - 44)
                self.grip_wrapper.raise_()

        # Поддержка drag&drop задач на кнопку выполненных задач
        if hasattr(self, 'completed_tasks_btn') and obj == self.completed_tasks_btn:
            # При наведении с drag принимаем событие (если в mime есть id задачи)
            if event.type() in (QEvent.DragEnter, QEvent.DragMove):
                if event.mimeData().hasText():
                    event.acceptProposedAction()
                    return True
            # Обработка сброса задачи на кнопку
            if event.type() == QEvent.Drop:
                if event.mimeData().hasText():
                    task_id = event.mimeData().text()
                    # Переносим задачу в выполненные
                    self.change_task_status_by_id(task_id, "Выполнено")
                    event.acceptProposedAction()
                    return True

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
        while self.active_tasks_layout.count() > 0:
            item = self.active_tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Очистка активных задач
        while self.active_tasks_layout.count() > 0:
            item = self.active_tasks_layout.takeAt(0)
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
        
        # Применяем дополнительные фильтры
        if self.current_filter in ["high", "medium", "low"]:
            active_tasks = [t for t in active_tasks if t.priority == self.current_filter]
        
        # Фильтрация по тегам
        if self.current_tag_filter:
            active_tasks = [t for t in active_tasks if hasattr(t, 'tags') and t.tags and self.current_tag_filter in t.tags]
        
        # Сортировка активных по приоритету
        priority_map = {"high": 0, "medium": 1, "low": 2}
        active_tasks.sort(key=lambda t: priority_map.get(t.priority, 3))
        
        # Добавление карточек активных задач
        for task in active_tasks:
            card = TaskCard(task, self)
            card.setAcceptDrops(False)  # Карточки не принимают drop
            self.active_tasks_layout.addWidget(card)
        
        if active_tasks:
             self.active_tasks_layout.addStretch()
             
        # Обновление иконки выполненных задач
        self._update_completed_btn_icon(len(completed_tasks))
        
        # Обновляем стиль кнопки выполненных задач
        self._update_completed_btn_style()
        
        # Обновляем уведомления
        self._check_overdue_tasks()
        
        # Обновление счетчиков
        total = len(filtered_tasks)
        completed_count = len(completed_tasks)
        
        tasks_word = pluralize(total, ('задача', 'задачи', 'задач'))
        self.task_counter.setText(f"{total} {tasks_word}")
        
        # Устанавливаем максимальную высоту для активных задач - ОТКЛЮЧЕНО
        # Пусть контейнер растет вместе с задачами, а скролл обрабатывается QScrollArea
        self.active_tasks_container.setMaximumHeight(16777215)
        self.active_tasks_container.setMinimumHeight(0)
        
        # Подстраиваем размер окна
        self._adjust_window_size(len(active_tasks), completed_count)

    def _update_completed_btn_icon(self, count):
        """Обновление иконки кнопки выполненных задач с индикатором"""
        if not hasattr(self, 'completed_tasks_btn'):
            return
            
        # Базовая иконка (галочка)
        # Создаем пустой Pixmap
        size = 32
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Рисуем галочку (текст)
        font = QFont("Segoe UI Emoji", 16)
        painter.setFont(font)
        painter.setPen(QColor(THEME['text_secondary']))
        # Центрируем галочку
        painter.drawText(QRect(0, 0, size, size), Qt.AlignCenter, "✅")
        
        # Если есть задачи, рисуем красную точку
        if count > 0:
            dot_size = 10
            painter.setBrush(QColor("#ff4d4d")) # Красный
            painter.setPen(Qt.NoPen)
            # Рисуем в правом верхнем углу
            painter.drawEllipse(size - dot_size - 2, 2, dot_size, dot_size)
            
        painter.end()
        
        self.completed_tasks_btn.setIcon(QIcon(pixmap))
        self.completed_tasks_btn.setIconSize(QSize(24, 24))
        
        # Обновляем стиль для соответствия остальным кнопкам (граница)
        self.completed_tasks_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {THEME['text_secondary']};
                border: 1px solid {THEME['border_color']};
                border-radius: 16px; 
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
                color: {THEME['text_primary']};
                border-color: {THEME['accent_hover']};
            }}
        """)

    def _open_completed_tasks_dialog(self):
        """Открытие диалога выполненных задач"""
        dialog = CompletedTasksDialog(self)
        
        # Фильтруем выполненные задачи
        completed_tasks = [t for t in self.tasks if t.status == "Выполнено"]
        
        # Используем отдельный список для диалога, но передаем self как родительское окно
        dialog.set_tasks(completed_tasks, self)
        dialog.exec()
        
        # После закрытия диалога обновляем список, так как задачи могли восстановить/удалить
        self._load_tasks()
        self._refresh_tasks()

    def _adjust_window_size(self, active_count, completed_count):
        """Автоматическая подстройка размера окна на основе количества задач"""
        # Если это не первый запуск, не меняем размер окна автоматически
        if getattr(self, '_initial_resize_done', False):
            return

        self._initial_resize_done = True
        # Вычисляем высоту для активных задач (максимум 4)
        visible_active = min(active_count, self.MAX_VISIBLE_ACTIVE)
        active_height = visible_active * self.TASK_CARD_HEIGHT if visible_active > 0 else 0
        
        # Вычисляем общую высоту окна (Completed теперь не учитываем в высоте)
        total_height = (
            self.BASE_HEIGHT +  # Базовые элементы (заголовок, форма, фильтры)
            self.HEADER_HEIGHT +  # Заголовок активных задач
            active_height +  # Высота активных задач
            20 # Немного запаса
        )
        
        # Устанавливаем минимальную высоту, если задач нет вообще
        if active_count == 0 and completed_count == 0:
            total_height = self.BASE_HEIGHT + self.HEADER_HEIGHT + self.SEPARATOR_HEIGHT + self.HEADER_HEIGHT + self.BOTTOM_BAR_HEIGHT + self.SPACING * 2
        
        # Получаем текущую ширину окна
        current_width = self.width()
        
        # Устанавливаем новый размер окна
        self.resize(current_width, total_height)

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
        
        if not temp_task:
            # Убеждаемся, что дата в календаре соответствует выбранной в навигаторе
            self.date_navigator.current_date = self.selected_date
            self.date_navigator.update_label()
            
        dialog = TaskDialog(self, temp_task)
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
                last_repeated_date=None,
                tags=data.get("tags", [])
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
                old_status = task.status
                task.status = "Выполнено" if task.status != "Выполнено" else "Не выполнено"
                
                # Обновляем дату выполнения
                if task.status == "Выполнено":
                    task.completion_date = datetime.now().strftime("%d.%m.%Y %H:%M")
                else:
                    task.completion_date = None
                
                # Если задача перенесена в выполненные, скрываем её из списка (обновление через _refresh_tasks)
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
                    t.tags = data.get("tags", [])
                    break
            
            TaskStorage.save(self.tasks)
            self._refresh_tasks()
    
    def _on_zoom_changed(self, value):
        """Обработка изменения масштаба"""
        scale = value / 100.0
        ZoomManager.set_scale(scale)
        self._refresh_ui_scale()
        self._check_overdue_tasks()
    
    def _check_overdue_tasks(self):
        """Проверка просроченных задач и обновление иконки"""
        today = QDate.currentDate()
        old_overdue_ids = {task.id for task in self.overdue_tasks}  # Сохраняем старые ID
        self.overdue_tasks = []
        
        for task in self.tasks:
            # Проверяем только активные задачи
            if task.status != "completed" and task.due_date:
                try:
                    due = QDate.fromString(task.due_date, "yyyy-MM-dd")
                    if due < today:
                        self.overdue_tasks.append(task)
                except:
                    pass
        
        # Если появились новые просроченные задачи (которых не было в старом списке), сбрасываем флаг
        new_overdue_ids = {task.id for task in self.overdue_tasks}
        if new_overdue_ids - old_overdue_ids:  # Есть новые задачи
            self.notifications_dismissed = False
                    
        has_overdue = len(self.overdue_tasks) > 0 and not self.notifications_dismissed
        
        if hasattr(self, 'notification_btn'):
            # Кнопка всегда видна, но badge показывается только при наличии просроченных задач и если не закрыты
            self.notification_btn.set_notification_state(has_overdue)
            # Принудительное обновление для немедленного отображения изменений
            self.notification_btn.update()
    
    def _show_notifications(self):
        """Показать диалог уведомлений"""
        # Если уведомления были очищены пользователем, показываем пустой список
        # (уведомления появятся только при следующем запуске программы)
        if self.notifications_dismissed:
            tasks_to_show = []
        else:
            tasks_to_show = self.overdue_tasks
        
        # Всегда показываем диалог, даже если уведомлений нет
        dialog = NotificationDialog(self, tasks_to_show)
        
        # Позиционируем диалог точно под кнопкой уведомлений (прилипает к иконке)
        if hasattr(self, 'notification_btn'):
            dialog.adjustSize()
            # Получаем глобальную позицию кнопки
            btn_pos = self.notification_btn.mapToGlobal(QPoint(0, 0))
            btn_width = self.notification_btn.width()
            btn_height = self.notification_btn.height()
            
            # Позиционируем диалог: выравниваем правый край диалога с правым краем кнопки
            # и размещаем сразу под кнопкой (без отступа или с минимальным)
            x = btn_pos.x() + btn_width - dialog.width()
            y = btn_pos.y() + btn_height  # Прямо под кнопкой, без отступа
            
            # Проверяем, чтобы диалог не выходил за границы экрана
            screen_geo = self.screen().geometry()
            
            # Если диалог выходит за правый край экрана, выравниваем по левому краю кнопки
            if x + dialog.width() > screen_geo.right():
                x = btn_pos.x()  # Выравниваем по левому краю кнопки
            if x < screen_geo.left():
                x = screen_geo.left() + ZoomManager.scaled(10)
            
            # Если диалог не помещается снизу, показываем сверху кнопки
            if y + dialog.height() > screen_geo.bottom():
                y = btn_pos.y() - dialog.height()  # Показываем сверху кнопки
            if y < screen_geo.top():
                y = screen_geo.top() + ZoomManager.scaled(10)
            
            dialog.move(x, y)
        
        dialog.exec()
        
    def clear_notifications(self):
        """Очистить уведомления (скрыть до следующего запуска/обновления)"""
        # Устанавливаем флаг, что пользователь закрыл уведомления
        self.notifications_dismissed = True
        # Обновляем состояние кнопки (убираем badge) - принудительно
        if hasattr(self, 'notification_btn'):
            # Прямо устанавливаем флаг и обновляем
            self.notification_btn.has_notifications = False
            self.notification_btn.update()
            # Дополнительно вызываем set_notification_state для гарантии
            self.notification_btn.set_notification_state(False)
             
    def _refresh_ui_scale(self):
        """Обновление UI при изменении масштаба"""
        # Обновляем отступы макетов
        if hasattr(self, 'active_tasks_layout'):
            self.active_tasks_layout.setSpacing(ZoomManager.scaled(4))
            # Обновляем каждую карточку активной задачи
            for i in range(self.active_tasks_layout.count()):
                item = self.active_tasks_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if hasattr(widget, 'update_ui_scale'):
                        widget.update_ui_scale()
        
        
        
        if hasattr(self, 'tasks_layout'):
            self.tasks_layout.setSpacing(ZoomManager.scaled(8))
        
        # Обновляем заголовки секций
        if hasattr(self, 'active_header'):
            self.active_header.setFont(ZoomManager.font("Segoe UI", 11, QFont.Bold))
            self.active_header.setStyleSheet(f"color: {THEME['text_primary']}; padding: {ZoomManager.scaled(8)}px 0px;")
        
        
        
        # Обновляем кнопку переключения выполненных задач
        if hasattr(self, 'toggle_completed_btn'):
            self.toggle_completed_btn.setFixedSize(ZoomManager.scaled(24), ZoomManager.scaled(24))
            self.toggle_completed_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {THEME['text_secondary']};
                    border: none;
                    font-size: {ZoomManager.scaled(18)}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    color: {THEME['text_primary']};
                }}
            """)
        
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
        
        # Обновляем нижнюю панель
        if hasattr(self, 'bottom_bar'):
            self.bottom_bar.setFixedHeight(ZoomManager.scaled(45))
        
        # Обновляем кнопку фильтров
        if hasattr(self, 'filter_btn'):
            self.filter_btn.setFixedHeight(ZoomManager.scaled(28))
        
        # Обновляем разделитель
        if hasattr(self, 'separator'):
            self.separator.setFixedHeight(ZoomManager.scaled(1))
        
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
        
        try:
            from version import __version__, GITHUB_API_URL
        except ImportError:
            __version__ = "1.0.1"
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
                changelog = data.get('body', 'Нет описания изменений')
                
                # Ищем только инсталлятор в активах релиза (TaskMaster-Installer-*.exe)
                installer_url = None
                if 'assets' in data:
                    for asset in data['assets']:
                        asset_name = asset['name']
                        # Ищем только инсталлятор
                        if 'installer' in asset_name.lower() and asset_name.lower().endswith('.exe'):
                            installer_url = asset['browser_download_url']
                            break
                
                # Если инсталлятор не найден, используем html_url как запасной вариант
                if not installer_url:
                    installer_url = data.get('html_url', '')
                
                progress.close()
                
                # Сравнение версий
                if self._compare_versions(latest_version, __version__) > 0:
                    # Доступно обновление - показываем badge и диалог
                    self._show_update_badge(True)
                    dialog = UpdateDialog(self, latest_version, changelog, installer_url)
                    dialog.exec()
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
                    
        except (FileNotFoundError, OSError) as e:
            # Ошибки, связанные с отсутствием файлов PyInstaller (base_library.zip и т.д.)
            progress.close()
            error_msg = str(e)
            if 'base_library.zip' in error_msg or '_MEI' in error_msg:
                # Это ошибка PyInstaller - просто игнорируем проверку обновлений
                msg = QMessageBox(self)
                msg.setWindowTitle("TaskMaster")
                msg.setText("Проверка обновлений временно недоступна")
                msg.setInformativeText("Приложение работает в режиме без проверки обновлений.")
                msg.setIcon(QMessageBox.Warning)
                msg.setStyleSheet(f"""
                    QMessageBox {{
                        background-color: {THEME['window_bg_end']};
                        color: {THEME['text_primary']};
                    }}
                """)
                msg.exec()
            else:
                # Другая ошибка файловой системы
                msg = QMessageBox(self)
                msg.setWindowTitle("Ошибка")
                msg.setText("Не удалось проверить обновления")
                msg.setInformativeText(f"Ошибка: {error_msg}")
                msg.setIcon(QMessageBox.Critical)
                msg.setStyleSheet(f"""
                    QMessageBox {{
                        background-color: {THEME['window_bg_end']};
                        color: {THEME['text_primary']};
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
        import threading
        import urllib.request
        import json
        
        def check_in_background():
            print("Update check started in background...")
            try:
                import version
                print(f"Current version: {version.__version__}")
                
                req = urllib.request.Request(version.GITHUB_API_URL, headers={'User-Agent': 'TaskMaster'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode())
                    latest_version = data['tag_name'].lstrip('v')
                    print(f"Latest version found: {latest_version}")
                    
                    if self._compare_versions(latest_version, version.__version__) > 0:
                        print("Update available! Emitting signal...")
                        self.update_found.emit(True)
                    else:
                        print("No update available.")
                        self.update_found.emit(False)
            except (FileNotFoundError, OSError) as e:
                # Ошибки, связанные с отсутствием файлов PyInstaller - просто игнорируем
                error_msg = str(e)
                if 'base_library.zip' in error_msg or '_MEI' in error_msg:
                    print("Update check skipped: PyInstaller files not found (running from exe)")
                else:
                    print(f"Background update check failed (file system error): {e}")
            except Exception as e:
                print(f"Background update check failed: {e}")
        
        threading.Thread(target=check_in_background, daemon=True).start()
    
    def _show_update_badge(self, show):
        """Показать/скрыть индикацию обновления"""
        self.update_available = show
        if show:
            # Используем синий цвет для обновления (выглядит как инфо, а не как ошибка)
            self.update_btn.setText("")
            self.update_btn.setIcon(create_notification_icon("#4dabf7", 64))
            self.update_btn.setIconSize(QSize(24, 24))
            self.update_btn.setToolTip("Доступно новое обновление! Нажмите для установки 🚀")
        else:
            self.update_btn.setIcon(QIcon()) # Убираем иконку
            self.update_btn.setText("🔄")
            self.update_btn.setToolTip("Проверить обновления")
        
        # Обновляем стили кнопок
        self._update_bottom_bar_styles()
    
    def _update_bottom_bar_styles(self):
        """Обновление стилей кнопок в нижней панели"""
        
        # Общий стиль для кнопок нижней панели
        base_btn_style = f"""
            QPushButton {{
                background-color: transparent !important;
                color: {THEME['text_secondary']} !important;
                border: 1px solid {THEME['border_color']} !important;
                border-radius: 16px; 
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']} !important;
                color: {THEME['text_primary']} !important;
                border-color: {THEME['accent_hover']} !important;
            }}
        """

        # 1. Кнопка обновления
        if self.update_available:
            self.update_btn.setStyleSheet(f"""
                QPushButton#updateBtn {{
                    background-color: transparent !important;
                    border: 2px solid #4dabf7 !important;
                    border-radius: 16px; 
                }}
                QPushButton#updateBtn:hover {{
                    background-color: rgba(77, 171, 247, 0.1) !important;
                }}
            """)
        else:
            self.update_btn.setStyleSheet(f"""
                QPushButton#updateBtn {{
                    background-color: transparent !important;
                    color: {THEME['text_secondary']} !important;
                    border: 1px solid {THEME['border_color']} !important;
                    border-radius: 16px; 
                    font-size: 16px;
                }}
                QPushButton#updateBtn:hover {{
                    background-color: {THEME['secondary_hover']} !important;
                    color: {THEME['text_primary']} !important;
                    border-color: {THEME['accent_hover']} !important;
                }}
            """)

        # 2. Кнопка справки
        if hasattr(self, 'help_btn'):
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

        # 3. Кнопка инструментов
        is_tools_visible = self.tools_container.isVisible()
        if is_tools_visible:
            self.toggle_tools_btn.setStyleSheet(f"""
                QPushButton#toolsBtn {{
                    background-color: {THEME['accent_bg']} !important;
                    color: {THEME['accent_text']} !important;
                    border: 1px solid {THEME['accent_hover']} !important;
                    border-radius: 16px; 
                    font-size: 16px;
                }}
            """)
        else:
            self.toggle_tools_btn.setStyleSheet(f"""
                QPushButton#toolsBtn {{
                    background-color: transparent !important;
                    color: {THEME['text_secondary']} !important;
                    border: 1px solid {THEME['border_color']} !important;
                    border-radius: 16px; 
                    font-size: 16px;
                }}
                QPushButton#toolsBtn:hover {{
                    background-color: {THEME['secondary_hover']} !important;
                    color: {THEME['text_primary']} !important;
                    border-color: {THEME['accent_hover']} !important;
                }}
            """)
            
        # 4. Кнопки внутри панели инструментов (zoom, opacity, pin, theme)
        if hasattr(self, 'zoom_btn'):
            # Zoom (Aa)
            self.zoom_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {THEME['border_color']};
                    color: {THEME['text_primary']};
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['secondary_hover']};
                    border-color: {THEME['accent_hover']};
                }}
            """)
            
        if hasattr(self, 'opacity_btn'):
            # Opacity (Drop)
            self.opacity_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {THEME['border_color']};
                    color: {THEME['text_primary']};
                    border-radius: 6px;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['secondary_hover']};
                    border-color: {THEME['accent_hover']};
                }}
            """)
            
        if hasattr(self, 'pin_btn'):
            # Pin icon
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
            
        if hasattr(self, 'theme_btn'):
            # Theme icon
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
        
        for name, theme_data in AVAILABLE_THEMES.items():
            action = QAction(f"● {name}", self)
            # Замыкание для захвата имени и данных темы
            action.triggered.connect(lambda checked=False, n=name, t=theme_data: self._apply_custom_theme(n, t))
            menu.addAction(action)
            
        # Корректируем позицию, чтобы меню не выходило за границы окна
        menu_height = menu.sizeHint().height()
        menu_width = menu.sizeHint().width()
        
        # Позиция над кнопкой
        menu_pos = self.theme_btn.mapToGlobal(QPoint(0, -menu_height))
        
        # Границы окна
        window_rect = self.geometry()
        
        # Проверка правой границы
        if menu_pos.x() + menu_width > window_rect.right() - 5:
            menu_pos.setX(window_rect.right() - menu_width - 5)
            
        menu.exec(menu_pos)
        
    def _apply_custom_theme(self, theme_name, theme_data):
        """Применение выбранной темы"""
        # Сначала сбрасываем к стандартным значениям (базовая темная тема)
        # Это предотвращает "залипание" цветов светлой темы при переходе на темную
        THEME.update(DEFAULT_THEME)
        THEME.update(theme_data)
        
        # Сохраняем выбранную тему в настройки
        SettingsManager.set("current_theme", theme_name)
        
        # Обновляем глобальные стили приложения с новыми цветами темы
        QApplication.instance().setStyleSheet(get_global_style())
        
        self._refresh_styles()

    def _refresh_styles(self):
        """Обновление стилей всех элементов"""
        # Обновляем заголовок приложения
        if hasattr(self, 'app_title_lbl'):
            self.app_title_lbl.setStyleSheet(f"color: {THEME['text_primary']};")
        
        # Обновляем фон основного контейнера
        if hasattr(self, 'main_container'):
            self.main_container.setStyleSheet(f"""
                QFrame#mainContainer {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 {THEME['window_bg_start']},
                        stop:1 {THEME['window_bg_end']}
                    );
                    border: none;
                }}
            """)
            
        # Обновляем нижнюю панель (bottom_bar) до формы «пилюли»
        if hasattr(self, 'bottom_bar'):
            self.bottom_bar.setStyleSheet(f"""
                QFrame#bottomBar {{
                    background-color: {THEME['card_bg']};
                    border: 1px solid {THEME['border_color']}; 
                    border-radius: 22px;
                }}
            """)

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
        # ... (пропуск закомментированного кода слайдера)

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
        
        # Обновляем стрелку выполненных
        
        
        if hasattr(self, 'date_navigator'):
            self.date_navigator.update_styles()
            self.date_navigator.update_label()

        if hasattr(self, 'priority_combo'):
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
                    border: 1px solid {THEME['accent_hover']};
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
                    padding: 6px 10px;
                }}
                QComboBox QAbstractItemView::item:selected {{
                    background-color: {THEME['accent_bg']};
                    color: {THEME['accent_text']};
                }}
            """)
            
        # Task Cards (re-create them to apply new theme)
        self._refresh_tasks()
        
        # Обновляем кнопку фильтров
        if hasattr(self, 'filter_btn'):
            self.filter_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 1px solid {THEME['border_color']};
                    color: {THEME['text_secondary']};
                    border-radius: 14px;
                    padding: 0 12px;
                    font-size: 11px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: {THEME['text_primary']};
                }}
            """)
            
        # Обновление подсказок (ToolTips) - Применяем максимально жестко
        tooltip_style = f"""
            QToolTip {{
                background-color: {THEME['window_bg_start']} !important;
                color: {THEME['text_primary']} !important;
                border: 1px solid {THEME['border_color']} !important;
                border-radius: 6px !important;
                padding: 5px !important;
            }}
        """
        QApplication.instance().setStyleSheet(get_global_style() + tooltip_style)
        self.setStyleSheet(self.styleSheet() + tooltip_style)
        
        # Обновляем кнопки закрытия и сворачивания (они используют paintEvent)
        for btn in self.findChildren(CloseButton):
            btn.update()
        for btn in self.findChildren(MinimizeButton):
            btn.update()
        
        # КРИТИЧЕСКИ ВАЖНО: Применяем новые стили полей ввода с цветами из текущей темы
        input_style = get_input_field_style()
        for widget in self.findChildren(QLineEdit):
            widget.setStyleSheet(input_style)
        
        for widget in self.findChildren(QComboBox):
            # Для QComboBox нужно сохранить дополнительные стили, если они есть
            widget.setStyleSheet(input_style)
            # Явно отключаем прозрачность для выпадающего списка
            if hasattr(widget, 'view') and widget.view():
                widget.view().setAttribute(Qt.WA_TranslucentBackground, False)
                if widget.view().window():
                    widget.view().window().setAttribute(Qt.WA_TranslucentBackground, False)
        
        for widget in self.findChildren(QDateEdit):
            widget.setStyleSheet(input_style)
        
        # Обновление индикатора обновления
        if hasattr(self, 'update_badge'):
            self.update_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: #ff4444;
                    border: 2px solid {THEME['window_bg_end']};
                    border-radius: 6px;
                }}
            """)
        
        # Обновление формы добавления задачи
        if hasattr(self, 'add_form'):
            self.add_form.setStyleSheet(f"""
                QFrame {{
                    background-color: {THEME['form_bg']};
                    border-radius: 12px;
                    border: 1px solid {THEME['border_color']};
                }}
            """)

        # Обновление поля ввода названия с правильными цветами выделения
        if hasattr(self, 'title_input'):
            # Определяем цвет выделения на основе акцента темы
            selection_bg = THEME['accent_bg'].replace("0.4", "1.0") # Делаем непрозрачным
            # Если это rgba, попробуем преобразовать или просто используем accent_hover
            
            self.title_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {THEME['input_bg']};
                    border: 1px solid {THEME['border_color']};
                    border-radius: 8px;
                    padding: 10px 12px;
                    color: {THEME['text_primary']};
                    selection-background-color: {THEME['accent_hover']};
                    selection-color: {THEME['accent_text']};
                }}
                QLineEdit:focus {{
                    border: 1px solid {THEME['accent_hover']};
                    background-color: {THEME['input_bg_focus']};
                }}
                QLineEdit::selection {{
                    background-color: {THEME['accent_hover']};
                    color: {THEME['accent_text']};
                }}
            """)
            
        # Обновление заголовков и разделителей
        if hasattr(self, 'active_header'):
            self.active_header.setStyleSheet(f"color: {THEME['text_primary']}; padding: 8px 0px;")
            
        if hasattr(self, 'separator'):
            self.separator.setStyleSheet(f"background-color: {THEME['border_color']}; border: none; max-height: 1px; min-height: 1px;")
            
        if hasattr(self, 'completed_header_label'):
            self.completed_header_label.setStyleSheet(f"color: {THEME['text_secondary']}; padding: 8px 0px;")
        
        # Обновление кнопок нижней панели
        self._update_bottom_bar_styles()

    def exit_application(self):
        """Полный выход из приложения"""
        QApplication.instance().quit()


    def _update_timers(self):
        """Обновление таймеров активных задач"""
        save_needed = False
        date_str = QDate.currentDate().toString("yyyy-MM-dd")
        
        for task in self.tasks:
            if task.is_running:
                task.time_spent += 1
                
                # Логируем время по дням
                if not hasattr(task, 'time_log') or task.time_log is None:
                    task.time_log = {}
                
                task.time_log[date_str] = task.time_log.get(date_str, 0) + 1
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
                
                # Если задача перенесена в выполненные, закрываем секцию выполненных задач
                if new_status == "Выполнено":
                    if hasattr(self, 'completed_tasks_container'):
                        self.completed_tasks_container.setVisible(False)
                        self.toggle_completed_btn.setText("▶")
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
                                
    def _show_filter_menu(self):
        """Показать выпадающее меню фильтров"""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        # Закрываем предыдущее меню, если оно открыто
        if self._active_filter_menu:
            self._active_filter_menu.close()
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME['window_bg_end']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 32px 8px 16px;
                border-radius: 4px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background-color: {THEME['accent_bg']};
                color: {THEME['accent_text']};
            }}
            QMenu::icon {{
                padding-left: 10px;
            }}
        """)
        
        # Сохраняем ссылку на меню
        self._active_filter_menu = menu
        
        # Закрываем меню при его закрытии
        menu.aboutToHide.connect(lambda: setattr(self, '_active_filter_menu', None))
        
        filters = [
            ("all", "📋 Все задачи"),
            ("high", "🚩 Высокий приоритет"),
            ("medium", "🟠 Средний приоритет"),
            ("low", "🟢 Низкий приоритет")
        ]
        
        for filter_id, label in filters:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(self.current_filter == filter_id)
            action.triggered.connect(lambda checked, fid=filter_id: self._set_filter(fid))
            menu.addAction(action)
            
        # Корректируем позицию, чтобы меню не выходило за границы главного окна
        menu_pos = self.filter_btn.mapToGlobal(QPoint(0, self.filter_btn.height() + 4))
        
        # Получаем предполагаемую ширину меню
        menu_width = menu.sizeHint().width()
        
        # Границы главного окна (в глобальных координатах)
        window_rect = self.geometry()
        
        # Если меню выходит за правую границу окна (с отступом 10px)
        if menu_pos.x() + menu_width > window_rect.right() - 10:
            menu_pos.setX(window_rect.right() - menu_width - 10)
            
        # Показываем меню
        menu.exec(menu_pos)
    
    def _set_filter(self, filter_id):
        """Установка текущего фильтра"""
        self.current_filter = filter_id
        
        # Находим название для кнопки
        filters = {
            "all": "🔘 Фильтры: Все",
            "high": "🔘 Фильтры: Высокий",
            "medium": "🔘 Фильтры: Средний",
            "low": "🔘 Фильтры: Низкий"
        }
        self.filter_btn.setText(filters.get(filter_id, "🔘 Фильтры"))
            
        # Обновляем список задач
        self._refresh_tasks()



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


def create_timer_icon():
    """Создание иконки таймера"""
    # Пытаемся загрузить иконку из файла
    base_dir = Path(__file__).parent.resolve()
    
    # В PyInstaller exe ресурсы распаковываются во временную папку
    if getattr(sys, 'frozen', False):
        # Запущено из exe
        exe_dir = Path(sys.executable).parent
        icon_paths = [
            exe_dir / "icons" / "timer.png",
        ]
        # Также проверяем временную папку PyInstaller
        if hasattr(sys, '_MEIPASS'):
            icon_paths.extend([
                Path(sys._MEIPASS) / "icons" / "timer.png",
            ])
    else:
        # Запущено из скрипта
        icon_paths = [
            base_dir / "icons" / "timer.png",
        ]
    
    # Пытаемся загрузить иконку
    for icon_path in icon_paths:
        if icon_path.exists():
            return QIcon(str(icon_path))
    
    # Если иконки нет, возвращаем пустую иконку (fallback на эмодзи)
    return QIcon()


def create_notification_icon(color="#4dabf7", size=64):
    """Программное создание красивой иконки уведомления (восклицательный знак)"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 1. Свечение (Glow)
    glow_color = QColor(color)
    glow_color.setAlpha(50)
    painter.setBrush(glow_color)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    
    # 2. Основной круг (Border)
    painter.setBrush(Qt.NoBrush)
    pen = QPen(QColor(color), size // 15)
    painter.setPen(pen)
    margin = size // 10
    painter.drawEllipse(margin, margin, size - 2*margin, size - 2*margin)
    
    # 3. Восклицательный знак (Perfectly symmetrical)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    
    # Палочка
    rect_w = size // 8
    rect_h = size // 2.5
    rect_x = (size - rect_w) // 2
    rect_y = size // 4
    painter.drawRoundedRect(rect_x, rect_y, rect_w, rect_h, rect_w // 2, rect_w // 2)
    
    # Точка
    dot_size = size // 8
    dot_x = (size - dot_size) // 2
    dot_y = size - size // 3.5
    painter.drawEllipse(dot_x, dot_y, dot_size, dot_size)
    
    painter.end()
    return QIcon(pixmap)


def create_report_icon(color="#6bcf7f", size=64):
    """Программное создание иконки отчета (графема)"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Свечение подложки
    glow = QColor(color)
    glow.setAlpha(40)
    painter.setBrush(glow)
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(4, 4, size-8, size-8, size//4, size//4)
    
    # График (три столбика)
    painter.setBrush(QColor(color))
    
    w = size // 5
    spacing = size // 10
    
    # Столбик 1 (низкий)
    painter.drawRoundedRect(spacing*2, size - spacing*2 - size//3, w, size//3, 2, 2)
    # Столбик 2 (высокий)
    painter.drawRoundedRect(spacing*2 + w + spacing, spacing*2, w, size - spacing*4, 2, 2)
    # Столбик 3 (средний)
    painter.drawRoundedRect(spacing*2 + (w + spacing)*2, size - spacing*2 - size//2, w, size//2, 2, 2)
    
    painter.end()
    return QIcon(pixmap)


def main():
    """Главная функция запуска приложения"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Не закрывать при закрытии окна (для трея)
    
    # Создаем и устанавливаем иконку приложения
    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)
    
    # Применяем глобальный стиль для отключения focus rect
    app.setStyleSheet(get_global_style())
    
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



