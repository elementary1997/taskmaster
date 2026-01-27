#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой запуск менеджера задач
"""

import sys
import os

# Добавляем путь к текущей директории
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from task_manager import TaskManager
    import tkinter as tk
    
    if __name__ == "__main__":
        root = tk.Tk()
        app = TaskManager(root)
        root.mainloop()
        
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что файл task_manager.py находится в той же директории")
    sys.exit(1)
except Exception as e:
    print(f"Ошибка запуска: {e}")
    sys.exit(1)