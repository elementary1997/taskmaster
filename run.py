#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Запуск современного менеджера задач на PySide6.
"""

import sys
import os

# Добавляем путь к текущей директории
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from task_manager_qt import main as qt_main

    if __name__ == "__main__":
        qt_main()

except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что установлены зависимости:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Ошибка запуска: {e}")
    sys.exit(1)