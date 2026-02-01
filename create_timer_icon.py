#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создание иконки таймера для TaskMaster
Генерирует качественную иконку таймера в современном стиле
"""

from PIL import Image, ImageDraw
from pathlib import Path
import math

def create_timer_icon(output_path="icons/timer.png", size=128):
    """Создание иконки таймера"""
    # Создаем изображение с прозрачным фоном
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = size / 2, size / 2
    radius = size * 0.35  # Радиус основного круга
    
    # Фон - легкий градиентный круг (опционально)
    bg_radius = radius * 1.2
    draw.ellipse([center_x - bg_radius, center_y - bg_radius,
                  center_x + bg_radius, center_y + bg_radius],
                 fill=(107, 207, 127, 20), outline=None)
    
    # Основной круг таймера - белый с легкой тенью
    draw.ellipse([center_x - radius, center_y - radius,
                  center_x + radius, center_y + radius],
                 fill=(255, 255, 255, 240), outline=(200, 200, 200, 180), width=2)
    
    # Внутренний круг для глубины
    inner_radius = radius * 0.85
    draw.ellipse([center_x - inner_radius, center_y - inner_radius,
                  center_x + inner_radius, center_y + inner_radius],
                 fill=(250, 250, 250, 200), outline=None)
    
    # Циферблат - метки часов
    for i in range(12):
        angle = (i * 30 - 90) * math.pi / 180  # Начинаем с 12 часов
        mark_length = radius * 0.15
        x1 = center_x + (radius - mark_length) * math.cos(angle)
        y1 = center_y + (radius - mark_length) * math.sin(angle)
        x2 = center_x + radius * math.cos(angle)
        y2 = center_y + radius * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=(100, 100, 100, 200), width=2)
    
    # Стрелки таймера
    # Часовая стрелка (короткая, указывает на 12)
    hour_angle = -90 * math.pi / 180  # 12 часов
    hour_length = radius * 0.5
    hour_x = center_x + hour_length * math.cos(hour_angle)
    hour_y = center_y + hour_length * math.sin(hour_angle)
    draw.line([(center_x, center_y), (hour_x, hour_y)], 
              fill=(80, 80, 80, 255), width=3)
    
    # Минутная стрелка (длинная, указывает на 3)
    minute_angle = 0 * math.pi / 180  # 3 часа
    minute_length = radius * 0.7
    minute_x = center_x + minute_length * math.cos(minute_angle)
    minute_y = center_y + minute_length * math.sin(minute_angle)
    draw.line([(center_x, center_y), (minute_x, minute_y)], 
              fill=(60, 60, 60, 255), width=2)
    
    # Центральная точка
    center_dot_radius = size * 0.04
    draw.ellipse([center_x - center_dot_radius, center_y - center_dot_radius,
                  center_x + center_dot_radius, center_y + center_dot_radius],
                 fill=(80, 80, 80, 255), outline=None)
    
    # Декоративные элементы - маленькие точки на 12, 3, 6, 9
    dot_radius = size * 0.02
    for i in [0, 3, 6, 9]:  # 12, 3, 6, 9 часов
        angle = (i * 30 - 90) * math.pi / 180
        dot_x = center_x + (radius * 0.75) * math.cos(angle)
        dot_y = center_y + (radius * 0.75) * math.sin(angle)
        draw.ellipse([dot_x - dot_radius, dot_y - dot_radius,
                      dot_x + dot_radius, dot_y + dot_radius],
                     fill=(107, 207, 127, 220), outline=None)
    
    # Создаем директорию если её нет
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Сохраняем как PNG
    img.save(str(output_path), "PNG")
    print(f"Created timer icon: {output_path}")

if __name__ == "__main__":
    icon_path = Path(__file__).parent / "icons" / "timer.png"
    create_timer_icon(str(icon_path))
