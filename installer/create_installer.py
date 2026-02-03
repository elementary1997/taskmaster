"""
Создание автономного инсталлятора TaskMaster
Не требует установки дополнительных программ - все встроено
"""
import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path
import tempfile

def create_installer_exe():
    """Создание exe-файла инсталлятора с помощью PyInstaller"""
    print("🔨 Создаем автономный инсталлятор...")
    
    base_dir = Path(__file__).parent.parent.resolve()
    installer_dir = base_dir / "installer"
    installer_script = installer_dir / "installer.py"
    
    # Получаем версию из version.py
    try:
        import sys
        sys.path.insert(0, str(base_dir))
        import version
        app_version = version.__version__
    except ImportError:
        app_version = "1.0.3"
    
    # Проверяем наличие собранного приложения
    app_dir = base_dir / "dist" / "TaskMaster"
    if not app_dir.exists() or not (app_dir / "TaskMaster.exe").exists():
        print(f"❌ Ошибка: Не найдено собранное приложение в {app_dir}")
        print("💡 Сначала запустите: python build_windows.py")
        return False
    
    # Используем готовый скрипт инсталлятора
    installer_script = installer_dir / "installer.py"
    uninstaller_script = installer_dir / "uninstaller.py"
    
    if not installer_script.exists():
        print(f"❌ Файл installer.py не найден")
        return False
    
    if not uninstaller_script.exists():
        print(f"⚠️  Файл uninstaller.py не найден (деинсталлятор не будет создан)")
    
    # Собираем инсталлятор с помощью PyInstaller
    print("\\n📦 Собираем exe-файл инсталлятора...")
    
    # Создаем архив с файлами приложения
    app_dir = base_dir / "dist" / "TaskMaster"
    archive_path = installer_dir / "app_files.zip"
    
    print("📦 Создаем архив с файлами приложения...")
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in app_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(app_dir)
                zipf.write(file_path, arcname)
        
        # Добавляем иконку если есть (для использования в ярлыке)
        icon_ico = base_dir / "icon.ico"
        icon_png = base_dir / "icon.png"
        if icon_ico.exists():
            zipf.write(icon_ico, "icon.ico")
        elif icon_png.exists():
            zipf.write(icon_png, "icon.png")
    
    print(f"✅ Архив создан: {archive_path}")
    
    # Используем PyInstaller для создания инсталлятора
    # Пробуем создать GUI версию, если PySide6 доступен
    installer_script_gui = installer_dir / "installer_gui.py"
    use_gui = installer_script_gui.exists()
    
    if use_gui:
        print("📱 Используется GUI версия инсталлятора")
        installer_script = installer_script_gui
        console_flag = "--noconsole"  # GUI не нужна консоль
    else:
        print("📟 Используется консольная версия инсталлятора")
        installer_script = installer_dir / "installer.py"
        console_flag = "--console"  # Консоль для отображения прогресса
    
    pyinstaller_args = [
        "pyinstaller",
        "--onefile",
        console_flag,
        "--name", "TaskMaster-Installer",
        "--add-data", f"{archive_path}{os.pathsep}.",
    ]
    
    # Добавляем installer.py в данные для GUI версии
    if use_gui:
        installer_py = installer_dir / "installer.py"
        if installer_py.exists():
            pyinstaller_args.extend(["--add-data", f"{installer_py}{os.pathsep}."])
    
    # Добавляем иконку если есть (для exe файла)
    icon_file = base_dir / "icon.ico"
    if not icon_file.exists():
        icon_file = base_dir / "icon.png"
    if icon_file.exists():
        pyinstaller_args.extend(["--icon", str(icon_file)])
        # Также добавляем иконку в данные для использования в GUI
        pyinstaller_args.extend(["--add-data", f"{icon_file}{os.pathsep}."])
    
    # Если GUI версия, добавляем скрытые импорты PySide6 и installer
    if use_gui:
        pyinstaller_args.extend([
            "--hidden-import", "PySide6.QtWidgets",
            "--hidden-import", "PySide6.QtCore",
            "--hidden-import", "PySide6.QtGui",
            "--hidden-import", "installer",  # Добавляем installer как скрытый импорт
        ])
    
    # Создаем деинсталлятор заранее
    if uninstaller_script.exists():
        print("📦 Создаем деинсталлятор...")
        try:
            uninstaller_exe = installer_dir / "dist" / "uninstall.exe"
            uninstaller_exe.parent.mkdir(parents=True, exist_ok=True)
            
            # Компилируем деинсталлятор
            subprocess.check_call([
                "pyinstaller",
                "--onefile",
                "--noconsole",
                "--name", "uninstall",
                str(uninstaller_script)
            ], cwd=installer_dir, capture_output=True)
            
            # Копируем в архив
            if (installer_dir / "dist" / "uninstall.exe").exists():
                shutil.copy2(installer_dir / "dist" / "uninstall.exe", archive_path.parent / "uninstall.exe")
                # Добавляем в архив приложения
                with zipfile.ZipFile(archive_path, 'a', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(installer_dir / "dist" / "uninstall.exe", "uninstall.exe")
                print("✅ Деинсталлятор добавлен в архив")
        except Exception as e:
            print(f"⚠️  Не удалось создать деинсталлятор: {e}")
    
    # Добавляем необходимые скрытые импорты
    pyinstaller_args.extend([
        "--hidden-import", "winreg",
        "--hidden-import", "zipfile",
        "--hidden-import", "shutil",
    ])
    
    pyinstaller_args.append(str(installer_script))
    
    try:
        subprocess.check_call(pyinstaller_args, cwd=installer_dir)
        
        installer_exe = installer_dir / "dist" / "TaskMaster-Installer.exe"
        if installer_exe.exists():
            # Перемещаем в корень dist с версией
            final_path = base_dir / "dist" / f"TaskMaster-Installer-{app_version}.exe"
            shutil.move(installer_exe, final_path)
            
            print(f"\\n✅ Инсталлятор создан!")
            print(f"📁 Расположение: {final_path}")
            print(f"📊 Размер: {final_path.stat().st_size / 1024 / 1024:.2f} MB")
            return True
        else:
            print("\\n❌ Инсталлятор не найден после сборки")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\\n❌ Ошибка сборки инсталлятора: {e}")
        return False
    except Exception as e:
        print(f"\\n❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    success = create_installer_exe()
    sys.exit(0 if success else 1)
