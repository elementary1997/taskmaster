#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создание иконки для TaskMaster
Генерирует простую иконку с эмодзи 😎 или символом
"""

from PySide6.QtGui import QPainter, QPixmap, QColor, QFont
from PySide6.QtCore import Qt
from pathlib import Path

def create_icon(output_path="icon.ico", size=256):
    """Создание иконки для приложения"""
    # Создаем pixmap
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))  # Прозрачный фон
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Фон - градиентный круг
    from PySide6.QtGui import QRadialGradient
    gradient = QRadialGradient(size/2, size/2, size/2)
    gradient.setColorAt(0, QColor(107, 207, 127, 255))  # Зеленый центр
    gradient.setColorAt(1, QColor(64, 156, 255, 255))   # Синий край
    
    painter.setBrush(gradient)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, size-4, size-4)
    
    # Текст/эмодзи в центре
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Segoe UI Emoji", int(size * 0.5), QFont.Bold)
    painter.setFont(font)
    
    # Пытаемся нарисовать эмодзи или символ
    text = "😎"
    font_metrics = painter.fontMetrics()
    text_rect = font_metrics.boundingRect(text)
    x = (size - text_rect.width()) / 2
    y = (size + text_rect.height()) / 2 - text_rect.height() / 4
    
    painter.drawText(int(x), int(y), text)
    
    painter.end()
    
    # Сохраняем как PNG (для использования в коде)
    png_path = output_path.replace('.ico', '.png')
    pixmap.save(png_path, "PNG")
    print(f"✅ Created icon: {png_path}")
    
    # Для Windows нужен .ico файл - создаем через PIL если доступен
    try:
        from PIL import Image
        img = Image.open(png_path)
        
        # Создаем ICO с несколькими размерами
        ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        ico_images = []
        for ico_size in ico_sizes:
            ico_images.append(img.resize(ico_size, Image.Resampling.LANCZOS))
        
        img.save(output_path, format='ICO', sizes=[(s[0], s[1]) for s in ico_sizes])
        print(f"✅ Created ICO: {output_path}")
    except ImportError:
        print("⚠️  PIL/Pillow not installed. Install it with: pip install Pillow")
        print(f"   Using PNG instead: {png_path}")
        print("   You can convert PNG to ICO manually or install Pillow")

if __name__ == "__main__":
    icon_path = Path(__file__).parent / "icon.ico"
    create_icon(str(icon_path))