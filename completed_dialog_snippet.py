
class CompletedTasksDialog(QDialog):
    """Диалог для просмотра и управления выполненными задачами"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Выполненные задачи")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setStyleSheet(f"""
            QDialog {{
                background: {THEME['window_bg_start']};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QLabel {{
                color: {THEME['text_primary']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок
        header = QLabel("Архив задач")
        header.setFont(ZoomManager.font("Segoe UI", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("padding: 20px 0 10px 0;")
        layout.addWidget(header)
        
        # Область скролла
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.tasks_container = QWidget()
        self.tasks_container.setStyleSheet("background: transparent;")
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(15, 0, 15, 20)
        self.tasks_layout.setSpacing(8)
        self.tasks_layout.addStretch()
        
        self.scroll.setWidget(self.tasks_container)
        layout.addWidget(self.scroll)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['secondary_bg']};
                border: 1px solid {THEME['border_color']};
                border-radius: 8px;
                color: {THEME['text_primary']};
                padding: 8px;
                margin: 0 15px 15px 15px;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary_hover']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
    def set_tasks(self, tasks, parent_window):
        """Отображение списка задач"""
        # Очистка
        while self.tasks_layout.count() > 1: # Оставляем stretch
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Добавление
        for task in tasks:
            # Создаем карточку, но указываем диалог как родителя виджета,
            # но parent_window сохраняем для логики
            card = TaskCard(task, parent_window) 
            # Исправляем логику обновления UI в карточке, если она зависит от self.parent_window
            # TaskCard уже принимает parent_window в init
            
            # Отключаем drug-n-drop в архиве
            card.setAcceptDrops(False)
            
            self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, card)
