#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Кастомный QLabel без возможности выделения текста
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

class NonSelectableLabel(QLabel):
    """QLabel, который полностью блокирует выделение текста"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # Отключаем все взаимодействия с текстом
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        # Отключаем фокус
        self.setFocusPolicy(Qt.NoFocus)
        # Делаем виджет прозрачным для событий мыши (но видимым визуально)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
    
    def mousePressEvent(self, event):
        """Игнорируем нажатия мыши"""
        event.ignore()
    
    def mouseReleaseEvent(self, event):
        """Игнорируем отпускание мыши"""
        event.ignore()
    
    def mouseMoveEvent(self, event):
        """Игнорируем движение мыши"""
        event.ignore()
    
    def mouseDoubleClickEvent(self, event):
        """Игнорируем двойной клик"""
        event.ignore()
