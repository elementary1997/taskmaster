"""
GUI версия инсталлятора TaskMaster с изображением
"""
import os
import sys
import shutil
import winreg
import zipfile
import importlib.util
import ctypes
from pathlib import Path
import threading

# Импортируем PySide6 для GUI
try:
    from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                                   QLabel, QPushButton, QProgressBar, QTextEdit, QFrame)
    from PySide6.QtCore import Qt, QThread, Signal, QSize
    from PySide6.QtGui import QPixmap, QFont, QIcon
    HAS_QT = True
except ImportError:
    HAS_QT = False
    # Fallback на консольную версию
    from installer import install as console_install

if HAS_QT:
    class UninstallThread(QThread):
        """Поток для удаления"""
        progress = Signal(str)
        finished = Signal(bool, str)
        
        def __init__(self, install_dir):
            super().__init__()
            self.install_dir = Path(install_dir)
        
        def run(self):
            try:
                # Импортируем функции из installer.py
                try:
                    import installer
                    get_desktop_path = installer.get_desktop_path
                except ImportError:
                    # Если прямой импорт не работает, используем динамическую загрузку
                    if getattr(sys, "frozen", False):
                        possible_paths = [
                            Path(sys._MEIPASS) / "installer.py",
                            Path(__file__).parent / "installer.py",
                        ]
                        installer_path = None
                        for path in possible_paths:
                            if path.exists():
                                installer_path = path
                                break
                        
                        if not installer_path:
                            raise FileNotFoundError("installer.py не найден")
                    else:
                        installer_path = Path(__file__).parent / "installer.py"
                    
                    spec = importlib.util.spec_from_file_location("installer", installer_path)
                    installer_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(installer_module)
                    get_desktop_path = installer_module.get_desktop_path
                
                self.progress.emit("Начало удаления...")
                
                # Удаляем запись из реестра
                self.progress.emit("Удаление записи из реестра...")
                try:
                    uninstall_key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                        0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
                    )
                    winreg.DeleteKey(uninstall_key, "TaskMaster")
                    winreg.CloseKey(uninstall_key)
                    self.progress.emit("✅ Запись в реестре удалена")
                except Exception as e:
                    self.progress.emit(f"⚠️  Не удалось удалить запись из реестра: {e}")
                
                # Удаляем ярлык с рабочего стола
                self.progress.emit("Удаление ярлыка с рабочего стола...")
                try:
                    desktop = Path(get_desktop_path())
                    desktop_shortcut = desktop / "TaskMaster.lnk"
                    if desktop_shortcut.exists():
                        desktop_shortcut.unlink()
                        self.progress.emit("✅ Ярлык удален")
                    else:
                        self.progress.emit("ℹ️  Ярлык не найден")
                except Exception as e:
                    self.progress.emit(f"⚠️  Не удалось удалить ярлык: {e}")
                
                # Удаляем файлы
                self.progress.emit(f"Удаление файлов из {self.install_dir}...")
                if self.install_dir.exists():
                    try:
                        shutil.rmtree(self.install_dir)
                        self.progress.emit("✅ Файлы удалены")
                    except Exception as e:
                        self.progress.emit(f"⚠️  Ошибка удаления файлов: {e}")
                        self.progress.emit("   Некоторые файлы могут быть заблокированы")
                        self.finished.emit(False, f"Ошибка удаления: {e}")
                        return
                else:
                    self.progress.emit("ℹ️  Папка установки не найдена")
                
                self.finished.emit(True, "Удаление завершено успешно!")
            except Exception as e:
                self.finished.emit(False, f"Ошибка удаления: {str(e)}")
    
    class UninstallDialog(QDialog):
        """Диалог удаления с прогрессом"""
        def __init__(self, install_dir):
            super().__init__()
            self.install_dir = install_dir
            self.uninstall_complete = False
            self.setWindowTitle("Удаление TaskMaster")
            self.setFixedSize(550, 500)
            self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)
            # Устанавливаем красивый фон
            self.setStyleSheet("""
                QDialog {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                }
            """)
            self._setup_ui()
            self._start_uninstall()
        
        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Белый контейнер с содержимым
            main_container = QFrame()
            main_container.setStyleSheet("""
                QFrame {
                    background: white;
                }
            """)
            main_layout = QVBoxLayout(main_container)
            main_layout.setSpacing(20)
            main_layout.setContentsMargins(30, 30, 30, 30)
            
            # Иконка
            icon_label = QLabel("🗑️")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFont(QFont("Segoe UI", 48))
            main_layout.addWidget(icon_label)
            
            # Заголовок
            title_label = QLabel("Удаление TaskMaster")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
            title_label.setStyleSheet("color: #333;")
            main_layout.addWidget(title_label)
            
            # Прогресс бар
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    text-align: center;
                    background: #f0f0f0;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    border-radius: 4px;
                }
            """)
            main_layout.addWidget(self.progress_bar)
            
            # Лог удаления
            log_label = QLabel("Прогресс удаления:")
            log_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
            log_label.setStyleSheet("color: #333;")
            main_layout.addWidget(log_label)
            
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setMaximumHeight(200)
            self.log_text.setStyleSheet("""
                QTextEdit {
                    background: #f9f9f9;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 5px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 9pt;
                }
            """)
            main_layout.addWidget(self.log_text)
            
            # Кнопка закрыть/готово
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            self.close_btn = QPushButton("Закрыть")
            self.close_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.close_btn.setFixedWidth(200)
            self.close_btn.setEnabled(False)
            self.close_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    padding: 12px 30px;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #5568d3, stop:1 #653a91);
                }
                QPushButton:disabled {
                    background: #ccc;
                }
            """)
            self.close_btn.clicked.connect(self.accept)
            
            button_layout.addWidget(self.close_btn)
            main_layout.addLayout(button_layout)
            
            layout.addWidget(main_container)
        
        def _start_uninstall(self):
            self.log_text.clear()
            self.log_text.append("Начало удаления...")
            
            self.uninstall_thread = UninstallThread(self.install_dir)
            self.uninstall_thread.progress.connect(self._on_progress)
            self.uninstall_thread.finished.connect(self._on_finished)
            self.uninstall_thread.start()
        
        def _on_progress(self, message):
            self.log_text.append(message)
        
        def _on_finished(self, success, message):
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.log_text.append(message)
            
            if success:
                self.uninstall_complete = True
                self.close_btn.setText("Готово")
                self.close_btn.setEnabled(True)
                self.close_btn.setStyleSheet("""
                    QPushButton {
                        background: #107c10;
                        color: white;
                        padding: 12px 30px;
                        border-radius: 8px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: #0e6b0e;
                    }
                """)
            else:
                self.close_btn.setText("Закрыть")
                self.close_btn.setEnabled(True)
    
    class UpdateConfirmDialog(QDialog):
        """Диалог подтверждения обновления или удаления"""
        def __init__(self, install_dir, has_update=True):
            super().__init__()
            self.install_dir = install_dir
            self.has_update = has_update
            self.action = None  # "update" или "uninstall"
            self.setWindowTitle("TaskMaster")
            self.setFixedSize(500, 350)
            self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)
            # Устанавливаем красивый фон
            self.setStyleSheet("""
                QDialog {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                }
            """)
            self._setup_ui()
        
        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Белый контейнер с содержимым
            main_container = QFrame()
            main_container.setStyleSheet("""
                QFrame {
                    background: white;
                }
            """)
            main_layout = QVBoxLayout(main_container)
            main_layout.setSpacing(20)
            main_layout.setContentsMargins(30, 30, 30, 30)
            
            # Иконка
            icon_label = QLabel("🔄" if self.has_update else "ℹ️")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFont(QFont("Segoe UI", 48))
            main_layout.addWidget(icon_label)
            
            # Заголовок
            if self.has_update:
                title_label = QLabel("Обнаружена установленная версия")
            else:
                title_label = QLabel("Нет доступных обновлений")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
            title_label.setStyleSheet("color: #333;")
            main_layout.addWidget(title_label)
            
            # Информация о пути
            path_label = QLabel(f"Путь установки:\n{self.install_dir}")
            path_label.setAlignment(Qt.AlignCenter)
            path_label.setWordWrap(True)
            path_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    color: #333;
                }
            """)
            main_layout.addWidget(path_label)
            
            # Вопрос или сообщение
            if self.has_update:
                question_label = QLabel("Выберите действие:")
                question_label.setAlignment(Qt.AlignCenter)
                question_label.setFont(QFont("Segoe UI", 11))
                question_label.setStyleSheet("color: #666;")
                main_layout.addWidget(question_label)
            else:
                message_label = QLabel("У вас установлена последняя версия TaskMaster.")
                message_label.setAlignment(Qt.AlignCenter)
                message_label.setWordWrap(True)
                message_label.setFont(QFont("Segoe UI", 11))
                message_label.setStyleSheet("color: #666;")
                main_layout.addWidget(message_label)
            
            # Кнопки
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            if self.has_update:
                # Две кнопки: Удалить и Обновить
                uninstall_btn = QPushButton("Удалить")
                uninstall_btn.setFont(QFont("Segoe UI", 10))
                uninstall_btn.setFixedWidth(110)
                uninstall_btn.setStyleSheet("""
                    QPushButton {
                        background: #e0e0e0;
                        color: #333;
                        padding: 10px 20px;
                        border-radius: 5px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: #d0d0d0;
                    }
                """)
                uninstall_btn.clicked.connect(lambda: self._set_action("uninstall"))
                
                update_btn = QPushButton("Обновить")
                update_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
                update_btn.setFixedWidth(110)
                update_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #667eea, stop:1 #764ba2);
                        color: white;
                        padding: 10px 20px;
                        border-radius: 5px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #5568d3, stop:1 #653a91);
                    }
                """)
                update_btn.clicked.connect(lambda: self._set_action("update"))
                
                button_layout.addWidget(uninstall_btn)
                button_layout.addSpacing(10)
                button_layout.addWidget(update_btn)
            else:
                # Одна кнопка: Удалить
                uninstall_btn = QPushButton("Удалить")
                uninstall_btn.setFont(QFont("Segoe UI", 10))
                uninstall_btn.setFixedWidth(110)
                uninstall_btn.setStyleSheet("""
                    QPushButton {
                        background: #e0e0e0;
                        color: #333;
                        padding: 10px 20px;
                        border-radius: 5px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: #d0d0d0;
                    }
                """)
                uninstall_btn.clicked.connect(lambda: self._set_action("uninstall"))
                button_layout.addWidget(uninstall_btn)
            
            main_layout.addLayout(button_layout)
            
            layout.addWidget(main_container)
        
        def _set_action(self, action):
            """Устанавливает действие и закрывает диалог"""
            self.action = action
            if action == "update":
                self.accept()
            elif action == "uninstall":
                # Для удаления возвращаем специальный код
                self.done(2)  # QDialog.Rejected = 0, Accepted = 1, используем 2 для удаления
    
    class UninstallThread(QThread):
        """Поток для удаления"""
        progress = Signal(str)
        finished = Signal(bool, str)
        
        def __init__(self, install_dir):
            super().__init__()
            self.install_dir = Path(install_dir)
        
        def run(self):
            try:
                # Импортируем функции из installer.py
                try:
                    import installer
                    get_desktop_path = installer.get_desktop_path
                except ImportError:
                    # Если прямой импорт не работает, используем динамическую загрузку
                    if getattr(sys, "frozen", False):
                        possible_paths = [
                            Path(sys._MEIPASS) / "installer.py",
                            Path(__file__).parent / "installer.py",
                        ]
                        installer_path = None
                        for path in possible_paths:
                            if path.exists():
                                installer_path = path
                                break
                        
                        if not installer_path:
                            raise FileNotFoundError("installer.py не найден")
                    else:
                        installer_path = Path(__file__).parent / "installer.py"
                    
                    spec = importlib.util.spec_from_file_location("installer", installer_path)
                    installer_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(installer_module)
                    get_desktop_path = installer_module.get_desktop_path
                
                self.progress.emit("Начало удаления...")
                
                # Удаляем запись из реестра
                self.progress.emit("Удаление записи из реестра...")
                try:
                    uninstall_key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                        0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
                    )
                    winreg.DeleteKey(uninstall_key, "TaskMaster")
                    winreg.CloseKey(uninstall_key)
                    self.progress.emit("✅ Запись в реестре удалена")
                except Exception as e:
                    self.progress.emit(f"⚠️  Не удалось удалить запись из реестра: {e}")
                
                # Удаляем ярлык с рабочего стола
                self.progress.emit("Удаление ярлыка с рабочего стола...")
                try:
                    desktop = Path(get_desktop_path())
                    desktop_shortcut = desktop / "TaskMaster.lnk"
                    if desktop_shortcut.exists():
                        desktop_shortcut.unlink()
                        self.progress.emit("✅ Ярлык удален")
                    else:
                        self.progress.emit("ℹ️  Ярлык не найден")
                except Exception as e:
                    self.progress.emit(f"⚠️  Не удалось удалить ярлык: {e}")
                
                # Удаляем файлы
                self.progress.emit(f"Удаление файлов из {self.install_dir}...")
                if self.install_dir.exists():
                    try:
                        shutil.rmtree(self.install_dir)
                        self.progress.emit("✅ Файлы удалены")
                    except Exception as e:
                        self.progress.emit(f"⚠️  Ошибка удаления файлов: {e}")
                        self.progress.emit("   Некоторые файлы могут быть заблокированы")
                        self.finished.emit(False, f"Ошибка удаления: {e}")
                        return
                else:
                    self.progress.emit("ℹ️  Папка установки не найдена")
                
                self.finished.emit(True, "Удаление завершено успешно!")
            except Exception as e:
                self.finished.emit(False, f"Ошибка удаления: {str(e)}")
    
    class InstallThread(QThread):
        """Поток для установки"""
        progress = Signal(str)
        finished = Signal(bool, str)
        
        def __init__(self, install_dir, archive_path, base_path, is_update=False):
            super().__init__()
            self.install_dir = install_dir
            self.archive_path = archive_path
            self.base_path = base_path
            self.is_update = is_update
        
        def run(self):
            try:
                # Импортируем функции из installer.py
                # Пробуем прямой импорт сначала
                try:
                    import installer
                    get_desktop_path = installer.get_desktop_path
                    create_shortcut = installer.create_shortcut
                    uninstall_existing = installer.uninstall_existing
                except ImportError:
                    # Если прямой импорт не работает, используем динамическую загрузку
                    if getattr(sys, "frozen", False):
                        possible_paths = [
                            Path(sys._MEIPASS) / "installer.py",
                            self.base_path / "installer.py",
                            Path(__file__).parent / "installer.py",
                        ]
                        installer_path = None
                        for path in possible_paths:
                            if path.exists():
                                installer_path = path
                                break
                        
                        if not installer_path:
                            raise FileNotFoundError("installer.py не найден")
                    else:
                        installer_path = Path(__file__).parent / "installer.py"
                    
                    spec = importlib.util.spec_from_file_location("installer", installer_path)
                    installer_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(installer_module)
                    
                    get_desktop_path = installer_module.get_desktop_path
                    create_shortcut = installer_module.create_shortcut
                    uninstall_existing = installer_module.uninstall_existing
                
                if self.is_update:
                    self.progress.emit("Обновление установки...")
                    # При обновлении директория уже существует
                    if not self.install_dir.exists():
                        self.install_dir.mkdir(parents=True, exist_ok=True)
                else:
                    self.progress.emit("Создание директории...")
                    self.install_dir.mkdir(parents=True, exist_ok=True)
                
                self.progress.emit("Распаковка файлов...")
                try:
                    with zipfile.ZipFile(self.archive_path, 'r') as zipf:
                        # При обновлении перезаписываем файлы
                        zipf.extractall(self.install_dir)
                    self.progress.emit("✅ Файлы распакованы")
                except Exception as e:
                    self.progress.emit(f"⚠️  Ошибка при распаковке: {e}")
                    # Пытаемся продолжить, возможно некоторые файлы заблокированы
                    pass
                
                self.progress.emit("Создание ярлыка...")
                try:
                    desktop = Path(get_desktop_path())
                    desktop_shortcut = desktop / "TaskMaster.lnk"
                    exe_path = self.install_dir / "TaskMaster.exe"
                    
                    # Удаляем старый ярлык, если существует
                    if desktop_shortcut.exists():
                        try:
                            desktop_shortcut.unlink()
                        except:
                            pass
                    
                    icon_path = None
                    icon_ico = self.install_dir / "icon.ico"
                    icon_png = self.install_dir / "icon.png"
                    if icon_ico.exists():
                        icon_path = str(icon_ico)
                    elif icon_png.exists():
                        icon_path = str(icon_png)
                    elif exe_path.exists():
                        icon_path = str(exe_path)
                    
                    create_shortcut(str(exe_path), str(desktop_shortcut), str(self.install_dir), "TaskMaster", icon_path)
                    self.progress.emit("✅ Ярлык создан")
                except Exception as e:
                    self.progress.emit(f"⚠️  Не удалось создать ярлык: {e}")
                
                self.progress.emit("Создание записи в реестре...")
                try:
                    uninstall_key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                        0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
                    )
                    # Удаляем старую запись, если существует (при обновлении)
                    try:
                        winreg.DeleteKey(uninstall_key, "TaskMaster")
                    except:
                        pass  # Записи может не быть
                    
                    taskmaster_key = winreg.CreateKey(uninstall_key, "TaskMaster")
                    winreg.SetValueEx(taskmaster_key, "DisplayName", 0, winreg.REG_SZ, "TaskMaster")
                    winreg.SetValueEx(taskmaster_key, "UninstallString", 0, winreg.REG_SZ, 
                                     str(self.install_dir / "uninstall.exe"))
                    winreg.SetValueEx(taskmaster_key, "InstallLocation", 0, winreg.REG_SZ, str(self.install_dir))
                    # Получаем версию из version.py
                    try:
                        import version
                        app_version = version.__version__
                    except ImportError:
                        app_version = "1.0.3"
                    winreg.SetValueEx(taskmaster_key, "DisplayVersion", 0, winreg.REG_SZ, app_version)
                    winreg.SetValueEx(taskmaster_key, "Publisher", 0, winreg.REG_SZ, "TaskMaster")
                    winreg.CloseKey(taskmaster_key)
                    winreg.CloseKey(uninstall_key)
                    self.progress.emit("✅ Запись в реестре создана")
                except Exception as e:
                    self.progress.emit(f"⚠️  Не удалось создать запись в реестре: {e}")
                
                action_text = "Обновление" if self.is_update else "Установка"
                self.finished.emit(True, f"{action_text} завершена успешно!")
            except Exception as e:
                self.finished.emit(False, f"Ошибка установки: {str(e)}")
    
    class InstallerDialog(QDialog):
        """GUI диалог установки"""
        def __init__(self, install_dir, archive_path, base_path, is_update=False):
            super().__init__()
            self.install_dir = Path(install_dir)
            self.archive_path = archive_path
            self.is_update = is_update
            # Убеждаемся, что base_path не None
            if base_path is None:
                if getattr(sys, "frozen", False):
                    base_path = Path(sys._MEIPASS)
                else:
                    base_path = Path(__file__).parent
            self.base_path = Path(base_path) if base_path else Path(__file__).parent
            self.installation_complete = False
            title = "Обновление TaskMaster" if is_update else "Установка TaskMaster"
            self.setWindowTitle(title)
            self.setFixedSize(550, 650)
            self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)
            # Устанавливаем красивый фон
            self.setStyleSheet("""
                QDialog {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                }
            """)
            self._setup_ui()
        
        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Белый контейнер с содержимым
            main_container = QFrame()
            main_container.setStyleSheet("""
                QFrame {
                    background: white;
                }
            """)
            main_layout = QVBoxLayout(main_container)
            main_layout.setSpacing(20)
            main_layout.setContentsMargins(30, 30, 30, 30)
            
            # Заголовок с изображением
            header_frame = QFrame()
            header_layout = QVBoxLayout(header_frame)
            header_layout.setSpacing(10)
            
            # Изображение/логотип
            logo_label = QLabel()
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setFixedHeight(120)
            
            # Пытаемся загрузить изображение
            # В скомпилированном exe иконка может быть в разных местах
            logo_path = None
            possible_paths = [
                self.base_path / "icon.png",
                self.base_path / "icon.ico",
                self.base_path.parent / "icon.png",
                self.base_path.parent / "icon.ico",
            ]
            
            # Если скомпилировано, также проверяем sys._MEIPASS
            if getattr(sys, "frozen", False):
                meipass = Path(sys._MEIPASS)
                possible_paths.extend([
                    meipass / "icon.png",
                    meipass / "icon.ico",
                ])
            
            for path in possible_paths:
                if path and path.exists():
                    logo_path = path
                    break
            
            if logo_path and logo_path.exists():
                pixmap = QPixmap(str(logo_path))
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    logo_label.setPixmap(scaled_pixmap)
                else:
                    # Если изображение не загрузилось, используем текст
                    logo_label.setText("📋 TaskMaster")
                    logo_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
            else:
                # Если нет изображения, используем текст
                logo_label.setText("📋 TaskMaster")
                logo_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
            
            header_layout.addWidget(logo_label)
            
            # Заголовок
            title_text = "Обновление TaskMaster" if self.is_update else "Установка TaskMaster"
            title_label = QLabel(title_text)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
            header_layout.addWidget(title_label)
            
            # Версия
            # Получаем версию из архива app_files.zip (из собранной программы)
            app_version = _get_installer_version()
            version_label = QLabel(f"Версия {app_version}")
            version_label.setAlignment(Qt.AlignCenter)
            version_label.setFont(QFont("Segoe UI", 10))
            version_label.setStyleSheet("color: #666;")
            header_layout.addWidget(version_label)
            
            main_layout.addWidget(header_frame)
            
            # Путь установки с возможностью изменения
            path_frame = QFrame()
            path_layout = QVBoxLayout(path_frame)
            path_layout.setSpacing(8)
            
            path_label = QLabel("Путь установки:")
            path_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
            path_label.setStyleSheet("color: #333;")
            path_layout.addWidget(path_label)
            
            path_input_layout = QHBoxLayout()
            path_input_layout.setSpacing(8)
            self.path_input = QLabel(str(self.install_dir))
            self.path_input.setWordWrap(True)
            self.path_input.setStyleSheet("""
                QLabel {
                    padding: 8px 10px;
                    background: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    color: #333;
                    min-height: 20px;
                }
            """)
            path_input_layout.addWidget(self.path_input, 1)  # Растягиваем поле
            
            browse_btn = QPushButton("Обзор...")
            browse_btn.setFont(QFont("Segoe UI", 9))
            browse_btn.setFixedHeight(36)  # Высота как у поля ввода
            browse_btn.setFixedWidth(80)  # Фиксированная ширина
            browse_btn.setStyleSheet("""
                QPushButton {
                    background: #667eea;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 5px;
                    border: none;
                }
                QPushButton:hover {
                    background: #5568d3;
                }
            """)
            browse_btn.clicked.connect(self._browse_path)
            path_input_layout.addWidget(browse_btn, 0)  # Не растягиваем кнопку
            
            path_layout.addLayout(path_input_layout)
            main_layout.addWidget(path_frame)
            
            # Прогресс бар (скрыт до начала установки)
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)  # Скрываем до начала установки
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    text-align: center;
                    background: #f0f0f0;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    border-radius: 4px;
                }
            """)
            main_layout.addWidget(self.progress_bar)
            
            # Лог установки
            log_label = QLabel("Прогресс установки:")
            log_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
            log_label.setStyleSheet("color: #333;")
            main_layout.addWidget(log_label)
            
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setMaximumHeight(120)
            self.log_text.setStyleSheet("""
                QTextEdit {
                    background: #f9f9f9;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 5px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 9pt;
                }
            """)
            main_layout.addWidget(self.log_text)
            
            # Кнопка установки/готово
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            btn_text = "Обновить" if self.is_update else "Установить"
            self.install_btn = QPushButton(btn_text)
            self.install_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.install_btn.setFixedWidth(200)
            self.install_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    padding: 12px 30px;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #5568d3, stop:1 #653a91);
                }
                QPushButton:disabled {
                    background: #ccc;
                }
            """)
            self.install_btn.clicked.connect(self._on_install_button_clicked)
            
            button_layout.addWidget(self.install_btn)
            main_layout.addLayout(button_layout)
            
            # Добавляем контейнер в основной layout
            layout.addWidget(main_container)
        
        def _browse_path(self):
            """Выбор пути установки"""
            from PySide6.QtWidgets import QFileDialog
            current_path = str(self.install_dir.parent if self.install_dir.name == "TaskMaster" else self.install_dir)
            new_path = QFileDialog.getExistingDirectory(
                self,
                "Выберите папку для установки",
                current_path,
                QFileDialog.ShowDirsOnly
            )
            if new_path:
                new_path_obj = Path(new_path)
                # Если выбрана папка, которая не заканчивается на TaskMaster, добавляем её
                if new_path_obj.name != "TaskMaster":
                    self.install_dir = new_path_obj / "TaskMaster"
                else:
                    self.install_dir = new_path_obj
                self.path_input.setText(str(self.install_dir))
        
        def _on_install_button_clicked(self):
            """Обработчик нажатия кнопки установки/готово"""
            if self.installation_complete:
                # Если установка завершена, закрываем диалог
                self.accept()
            else:
                # Начинаем установку
                self._start_install()
        
        def _start_install(self):
            self.install_btn.setEnabled(False)
            self.progress_bar.setVisible(True)  # Показываем прогресс бар
            self.progress_bar.setRange(0, 0)  # Неопределенный прогресс во время установки
            self.log_text.clear()
            action_text = "обновления" if self.is_update else "установки"
            self.log_text.append(f"Начало {action_text}...")
            
            self.install_thread = InstallThread(self.install_dir, self.archive_path, self.base_path, self.is_update)
            self.install_thread.progress.connect(self._on_progress)
            self.install_thread.finished.connect(self._on_finished)
            self.install_thread.start()
        
        def _on_progress(self, message):
            self.log_text.append(message)
        
        def _on_finished(self, success, message):
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.log_text.append(message)
            
            if success:
                self.installation_complete = True
                self.install_btn.setText("Готово")
                self.install_btn.setEnabled(True)
                self.install_btn.setStyleSheet("""
                    QPushButton {
                        background: #107c10;
                        color: white;
                        padding: 12px 30px;
                        border-radius: 8px;
                        border: none;
                    }
                    QPushButton:hover {
                        background: #0e6b0e;
                    }
                """)
            else:
                self.install_btn.setText("Повторить")
                self.install_btn.setEnabled(True)

def _get_installed_version(install_dir):
    """Получение версии установленной программы"""
    try:
        # Пытаемся прочитать version.py из установленной директории
        version_file = Path(install_dir) / "_internal" / "version.py"
        if not version_file.exists():
            version_file = Path(install_dir) / "version.py"
        
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Ищем __version__ = "1.0.2"
                import re
                match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
        
        # Пытаемся получить из реестра
        try:
            uninstall_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Microsoft\Windows\CurrentVersion\Uninstall\TaskMaster"
            )
            version = winreg.QueryValueEx(uninstall_key, "DisplayVersion")[0]
            winreg.CloseKey(uninstall_key)
            return version
        except:
            pass
        
        return "0.0.0"  # Версия по умолчанию, если не найдена
    except:
        return "0.0.0"

def _get_installer_version():
    """Получение версии из инсталлятора (из архива app_files.zip)"""
    try:
        # Сначала пытаемся прочитать версию из архива app_files.zip
        base_path = Path(__file__).parent if not getattr(sys, "frozen", False) else Path(sys._MEIPASS)
        archive_path = base_path / "app_files.zip"
        
        if not archive_path.exists():
            archive_path = base_path.parent / "installer" / "app_files.zip"
        
        if archive_path.exists():
            try:
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    # Пытаемся найти version.py в архиве
                    version_paths = [
                        "_internal/version.py",  # Приоритет: версия из собранной программы
                        "version.py"
                    ]
                    
                    for version_path in version_paths:
                        try:
                            if version_path in zipf.namelist():
                                content = zipf.read(version_path).decode('utf-8')
                                import re
                                match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                                if match:
                                    found_version = match.group(1)
                                    # Если нашли версию в архиве, возвращаем её
                                    return found_version
                        except Exception as e:
                            continue
            except Exception as e:
                pass
        
        # Только если архив не найден или версия не найдена в архиве,
        # пытаемся прочитать из файла в корне проекта (для разработки)
        try:
            if getattr(sys, "frozen", False):
                version_file = Path(sys._MEIPASS) / "version.py"
            else:
                version_file = Path(__file__).parent.parent / "version.py"
            
            if version_file.exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    import re
                    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        return match.group(1)
        except:
            pass
        
        return "1.0.2"  # Версия по умолчанию
    except:
        return "1.0.2"  # Версия по умолчанию при любой ошибке

def _compare_versions(version1, version2):
    """Сравнение версий. Возвращает: >0 если v1 > v2, 0 если равны, <0 если v1 < v2"""
    def version_tuple(v):
        parts = v.split('.')
        return tuple(int(part) for part in parts)
    
    try:
        v1_tuple = version_tuple(version1)
        v2_tuple = version_tuple(version2)
        
        # Дополняем до одинаковой длины
        max_len = max(len(v1_tuple), len(v2_tuple))
        v1_tuple = v1_tuple + (0,) * (max_len - len(v1_tuple))
        v2_tuple = v2_tuple + (0,) * (max_len - len(v2_tuple))
        
        if v1_tuple > v2_tuple:
            return 1
        elif v1_tuple < v2_tuple:
            return -1
        else:
            return 0
    except:
        return 0

def is_admin():
    """Проверка прав администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    """Запрос прав администратора"""
    if is_admin():
        return True
    else:
        # Перезапускаем с правами администратора
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return False  # Возвращаем False, так как приложение перезапускается
        except:
            return False

def install_gui():
    """GUI установка"""
    if not HAS_QT:
        # Fallback на консольную версию
        return console_install()
    
    # Проверяем права администратора
    if not is_admin():
        # Создаем приложение для показа диалога
        app = QApplication(sys.argv)
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            None,
            "Требуются права администратора",
            "Для установки TaskMaster требуются права администратора.\n\nПерезапустить с правами администратора?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            request_admin()
        return False
    
    app = QApplication(sys.argv)
    
    # Определяем пути
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    
    archive_path = base_path / "app_files.zip"
    
    if not archive_path.exists():
        # Пытаемся найти в родительской директории
        archive_path = base_path.parent / "installer" / "app_files.zip"
    
    if not archive_path.exists():
        print("❌ Архив с файлами приложения не найден")
        return False
    
    # Определяем путь установки
    program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
    install_dir = Path(program_files) / "TaskMaster"
    
    # Проверяем существующую установку
    # Пробуем прямой импорт installer (PyInstaller должен включить его через --hidden-import)
    try:
        import installer
        check_existing_installation = installer.check_existing_installation
        uninstall_existing = installer.uninstall_existing
    except ImportError:
        # Если прямой импорт не работает, пробуем динамическую загрузку
        if getattr(sys, "frozen", False):
            # В скомпилированном exe файл находится в sys._MEIPASS
            possible_paths = [
                Path(sys._MEIPASS) / "installer.py",
                base_path / "installer.py",
            ]
            installer_path = None
            for path in possible_paths:
                if path.exists():
                    installer_path = path
                    break
            
            if not installer_path:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Ошибка", "Не удалось загрузить installer.py")
                return False
        else:
            installer_path = Path(__file__).parent / "installer.py"
            if not installer_path.exists():
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Ошибка", f"Файл installer.py не найден: {installer_path}")
                return False
        
        spec = importlib.util.spec_from_file_location("installer", installer_path)
        installer_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer_module)
        check_existing_installation = installer_module.check_existing_installation
        uninstall_existing = installer_module.uninstall_existing
    
    existing_dir = check_existing_installation()
    is_update_mode = existing_dir is not None
    
    if is_update_mode:
        # Проверяем версию установленной программы
        installed_version = _get_installed_version(existing_dir)
        installer_version = _get_installer_version()
        has_update = _compare_versions(installer_version, installed_version) > 0
        
        # Показываем диалог с выбором действия
        update_dialog = UpdateConfirmDialog(existing_dir, has_update=has_update)
        result = update_dialog.exec()
        
        if result == 2:  # Код для удаления
            # Показываем диалог удаления
            uninstall_dialog = UninstallDialog(existing_dir)
            uninstall_dialog.exec()
            return False  # После удаления не продолжаем установку
        
        if result != QDialog.Accepted:
            return False
        
        # Если обновлений нет, просто закрываем
        if not has_update:
            return False
        
        # Проверяем, запущено ли приложение
        # Режим обновления - проверяем, запущено ли приложение
        try:
            import psutil
            current_exe = None
            if getattr(sys, "frozen", False):
                current_exe = sys.executable
            else:
                # В режиме разработки ищем TaskMaster.exe
                program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
                current_exe = Path(program_files) / "TaskMaster" / "TaskMaster.exe"
            
            # Проверяем, запущен ли TaskMaster
            app_running = False
            if current_exe and current_exe.exists():
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        if proc.info['exe'] and Path(proc.info['exe']).samefile(current_exe):
                            app_running = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                        continue
            
            if app_running:
                # Приложение запущено - показываем диалог закрытия
                from PySide6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    None,
                    "Обновление TaskMaster",
                    f"Обнаружена установленная версия TaskMaster.\n\nДля обновления необходимо закрыть приложение.\n\nЗакрыть приложение и обновить?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # Закрываем все процессы TaskMaster
                    try:
                        for proc in psutil.process_iter(['pid', 'name', 'exe']):
                            try:
                                if proc.info['exe'] and Path(proc.info['exe']).samefile(current_exe):
                                    proc.terminate()
                                    proc.wait(timeout=5)
                            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired, ValueError):
                                try:
                                    proc.kill()
                                except:
                                    pass
                    except:
                        pass
                    
                    # Небольшая задержка для закрытия
                    import time
                    time.sleep(1)
        except ImportError:
            # psutil не установлен - просто продолжаем
            pass
        
        # Используем существующий путь для обновления
        install_dir = existing_dir
    else:
        # Обычная установка
        install_dir = Path(program_files) / "TaskMaster"
    
    dialog = InstallerDialog(install_dir, archive_path, base_path, is_update=is_update_mode)
    result = dialog.exec()
    
    return result == QDialog.Accepted

if __name__ == "__main__":
    if HAS_QT:
        success = install_gui()
        sys.exit(0 if success else 1)
    else:
        # Fallback на консольную версию
        if getattr(sys, "frozen", False):
            installer_path = Path(sys._MEIPASS) / "installer.py"
            if not installer_path.exists():
                installer_path = Path(__file__).parent / "installer.py"
        else:
            installer_path = Path(__file__).parent / "installer.py"
        
        spec = importlib.util.spec_from_file_location("installer", installer_path)
        installer_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer_module)
        
        success = installer_module.install()
        sys.exit(0 if success else 1)
