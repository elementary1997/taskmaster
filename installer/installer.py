"""
Автономный инсталлятор TaskMaster
Этот файл будет упакован в exe с помощью PyInstaller
"""
import os
import sys
import shutil
import winreg
from pathlib import Path
import zipfile
import tempfile

def get_desktop_path():
    """Получить путь к рабочему столу"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        desktop = winreg.QueryValueEx(key, "Desktop")[0]
        winreg.CloseKey(key)
        return desktop
    except:
        # Fallback на стандартный путь
        return os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")

def create_shortcut(target_path, shortcut_path, working_dir, description, icon_path=None):
    """Создать ярлык с иконкой"""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.WorkingDirectory = working_dir
        shortcut.Description = description
        # Устанавливаем иконку если указана
        if icon_path and Path(icon_path).exists():
            shortcut.IconLocation = icon_path
        shortcut.save()
        return True
    except ImportError:
        # Если win32com недоступен, используем альтернативный метод через PowerShell
        try:
            # Создаем ярлык через PowerShell
            ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target_path}"
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Description = "{description}"
'''
            if icon_path and Path(icon_path).exists():
                ps_script += f'$Shortcut.IconLocation = "{icon_path}"\n'
            ps_script += '$Shortcut.Save()'
            
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True
        except:
            pass
        
        # Если PowerShell не сработал, создаем .bat файл как последнюю альтернативу
        try:
            bat_path = shortcut_path.replace(".lnk", ".bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(f'@echo off\ncd /d "{working_dir}"\nstart "" "{target_path}"\n')
            return True
        except:
            return False
    except Exception as e:
        print(f"⚠️  Ошибка создания ярлыка: {e}")
        return False

def check_existing_installation():
    """Проверка наличия установленной версии"""
    install_dir = None
    
    # Проверяем реестр
    try:
        uninstall_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\TaskMaster"
        )
        install_dir = Path(winreg.QueryValueEx(uninstall_key, "InstallLocation")[0])
        winreg.CloseKey(uninstall_key)
        return install_dir
    except:
        pass
    
    # Проверяем стандартный путь
    program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
    default_dir = Path(program_files) / "TaskMaster"
    if default_dir.exists() and (default_dir / "TaskMaster.exe").exists():
        return default_dir
    
    return None

def uninstall_existing(install_dir):
    """Удаление существующей установки"""
    print(f"🗑️  Удаление существующей установки из {install_dir}...")
    
    # Пытаемся использовать деинсталлятор если есть
    uninstaller = install_dir / "uninstall.exe"
    if uninstaller.exists():
        try:
            import subprocess
            result = subprocess.run([str(uninstaller), "/SILENT"], timeout=30, capture_output=True)
            if result.returncode == 0:
                print("✅ Старая версия удалена через деинсталлятор")
                return True
        except Exception as e:
            print(f"⚠️  Деинсталлятор не сработал: {e}")
    
    # Удаляем вручную
    try:
        # Удаляем запись из реестра
        try:
            uninstall_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
            )
            winreg.DeleteKey(uninstall_key, "TaskMaster")
            winreg.CloseKey(uninstall_key)
        except:
            pass
        
        # Удаляем ярлык с рабочего стола
        try:
            desktop = Path(get_desktop_path())
            desktop_shortcut = desktop / "TaskMaster.lnk"
            if desktop_shortcut.exists():
                desktop_shortcut.unlink()
        except:
            pass
        
        # Удаляем файлы
        if install_dir.exists():
            shutil.rmtree(install_dir)
            print("✅ Старая версия удалена")
            return True
    except Exception as e:
        print(f"⚠️  Ошибка удаления: {e}")
        print("   Некоторые файлы могут быть заблокированы")
        return False
    
    return False

def install():
    """Установка приложения"""
    print("🚀 Установка TaskMaster...")
    
    # Проверяем наличие существующей установки
    existing_dir = check_existing_installation()
    is_silent = "/SILENT" in sys.argv or "/S" in sys.argv
    
    if existing_dir:
        print(f"⚠️  Обнаружена существующая установка в: {existing_dir}")
        
        if not is_silent:
            # Спрашиваем пользователя
            has_stdin = hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()
            if has_stdin:
                try:
                    print("\nВыберите действие:")
                    print("1. Удалить старую версию и установить новую")
                    print("2. Отменить установку")
                    response = input("Ваш выбор (1/2, Enter=1): ").strip()
                    if response == "2":
                        print("❌ Установка отменена")
                        return False
                except (EOFError, OSError, RuntimeError):
                    # stdin недоступен, удаляем автоматически
                    pass
        
        # Удаляем существующую установку
        if not uninstall_existing(existing_dir):
            print("⚠️  Не удалось полностью удалить старую версию")
            if not is_silent and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                try:
                    response = input("Продолжить установку? (y/n, Enter=y): ").strip().lower()
                    if response == "n":
                        return False
                except (EOFError, OSError, RuntimeError):
                    pass
        
        # Используем тот же путь для установки
        install_dir = existing_dir
    else:
        # Определяем путь установки по умолчанию
        program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
        install_dir = Path(program_files) / "TaskMaster"
        
        # Спрашиваем пользователя о пути (если не тихая установка)
        has_stdin = hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()
        if not is_silent and has_stdin:
            print(f"\nУстановка в: {install_dir}")
            try:
                response = input("Изменить путь? (y/n, Enter=n): ").strip().lower()
                if response == "y":
                    custom_path = input("Введите путь: ").strip()
                    if custom_path:
                        install_dir = Path(custom_path)
            except (EOFError, OSError, RuntimeError):
                # stdin недоступен (--noconsole режим), используем путь по умолчанию
                pass
    
    # Создаем директорию
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Установка в: {install_dir}")
    except Exception as e:
            print(f"❌ Не удалось создать директорию: {e}")
            if not is_silent and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                try:
                    input("Нажмите Enter для выхода...")
                except (EOFError, OSError, RuntimeError):
                    pass
            return False
    
    # Распаковываем файлы из архива
    # В PyInstaller exe архив находится в _MEIPASS
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        # Для тестирования
        base_path = Path(__file__).parent.parent / "dist" / "TaskMaster"
    
    archive_path = base_path / "app_files.zip"
    
    if not archive_path.exists():
        # Если архива нет, копируем файлы напрямую
        print("📦 Копирование файлов...")
        source_dir = base_path
        if not (source_dir / "TaskMaster.exe").exists():
            # Пытаемся найти в родительской директории
            source_dir = base_path.parent / "TaskMaster"
        
        if (source_dir / "TaskMaster.exe").exists():
            for item in source_dir.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(source_dir)
                    dest_path = install_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)
        else:
            print("❌ Файлы приложения не найдены")
            if not is_silent and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                try:
                    input("Нажмите Enter для выхода...")
                except (EOFError, OSError, RuntimeError):
                    pass
            return False
    else:
        # Распаковываем архив
        print("📦 Распаковка файлов...")
        try:
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(install_dir)
        except Exception as e:
            print(f"❌ Ошибка распаковки: {e}")
            if not is_silent and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                try:
                    input("Нажмите Enter для выхода...")
                except (EOFError, OSError, RuntimeError):
                    pass
            return False
    
    print("✅ Файлы установлены")
    
    # Создаем ярлык на рабочем столе с иконкой
    try:
        desktop = Path(get_desktop_path())
        desktop_shortcut = desktop / "TaskMaster.lnk"
        exe_path = install_dir / "TaskMaster.exe"
        
        # Ищем иконку приложения
        icon_path = None
        icon_ico = install_dir / "icon.ico"
        icon_png = install_dir / "icon.png"
        if icon_ico.exists():
            icon_path = str(icon_ico)
        elif icon_png.exists():
            icon_path = str(icon_png)
        # Если иконки нет в установленной директории, используем иконку из exe
        elif exe_path.exists():
            icon_path = str(exe_path)  # Windows использует иконку из exe
        
        if create_shortcut(str(exe_path), str(desktop_shortcut), str(install_dir), "TaskMaster", icon_path):
            print("✅ Ярлык на рабочем столе создан")
        else:
            print("⚠️  Не удалось создать ярлык (можно создать вручную)")
    except Exception as e:
        print(f"⚠️  Ошибка создания ярлыка: {e}")
    
    # Создаем запись в реестре для деинсталляции
    try:
        uninstall_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
            0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
        )
        
        # Создаем ключ для TaskMaster
        taskmaster_key = winreg.CreateKey(uninstall_key, "TaskMaster")
        winreg.SetValueEx(taskmaster_key, "DisplayName", 0, winreg.REG_SZ, "TaskMaster")
        # Путь к деинсталлятору
        uninstaller_path = install_dir / "uninstall.exe"
        if not uninstaller_path.exists():
            # Если exe нет, используем bat-файл
            bat_path = install_dir / "uninstall.bat"
            if not bat_path.exists():
                # Создаем bat-файл для запуска Python скрипта
                uninstaller_script = install_dir / "uninstaller.py"
                if uninstaller_script.exists():
                    with open(bat_path, "w", encoding="utf-8") as f:
                        f.write(f'@echo off\npython "{uninstaller_script}"\n')
                    uninstaller_path = bat_path
        
        winreg.SetValueEx(taskmaster_key, "UninstallString", 0, winreg.REG_SZ, 
                         str(uninstaller_path))
        winreg.SetValueEx(taskmaster_key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
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
        print("✅ Запись в реестре создана")
    except Exception as e:
        print(f"⚠️  Не удалось создать запись в реестре: {e}")
        print("   (требуются права администратора)")
    
    print("\n✅ Установка завершена!")
    
    # Показываем сообщение только если stdin доступен
    if not is_silent and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
        try:
            input("Нажмите Enter для выхода...")
        except (EOFError, OSError, RuntimeError):
            # stdin недоступен, просто выходим
            pass
    
    return True

if __name__ == "__main__":
    # Проверяем права администратора
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            # Запрашиваем права администратора
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit(0)  # Выходим, так как приложение перезапускается
            except:
                print("❌ Не удалось получить права администратора")
                print("💡 Запустите инсталлятор от имени администратора")
                sys.exit(1)
    except:
        pass  # Если не Windows, пропускаем проверку
    
    # Проверяем, нужно ли использовать GUI версию
    is_silent = "/SILENT" in sys.argv or "/S" in sys.argv
    
    # Если не тихая установка, пробуем GUI
    if not is_silent:
        try:
            # Пытаемся импортировать GUI версию
            if getattr(sys, "frozen", False):
                import importlib.util
                gui_path = Path(sys._MEIPASS) / "installer_gui.py"
                if not gui_path.exists():
                    gui_path = Path(__file__).parent / "installer_gui.py"
            else:
                gui_path = Path(__file__).parent / "installer_gui.py"
            
            if gui_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("installer_gui", gui_path)
                gui_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(gui_module)
                
                if hasattr(gui_module, 'HAS_QT') and gui_module.HAS_QT:
                    success = gui_module.install_gui()
                    sys.exit(0 if success else 1)
        except (ImportError, Exception) as e:
            # GUI версия недоступна, используем консольную
            pass
    
    # Консольная установка
    try:
        success = install()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Ошибка установки: {e}")
        import traceback
        traceback.print_exc()
        
        # Показываем сообщение только если stdin доступен
        if not is_silent and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
            try:
                input("Нажмите Enter для выхода...")
            except (EOFError, OSError, RuntimeError):
                pass
        
        sys.exit(1)
