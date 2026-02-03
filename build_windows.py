import os
import subprocess
import sys
from pathlib import Path

def build_exe():
    """
    Builds the executable using PyInstaller with all dependencies and resources.
    """
    print("🚀 Starting Windows build process...")
    
    # Base directory
    base_dir = Path(__file__).parent.resolve()
    script_path = base_dir / "modern_task_manager.py"
    audio_dir = base_dir / "audio"
    icons_dir = base_dir / "icons"
    
    if not script_path.exists():
        print(f"❌ Error: Could not find {script_path}")
        return

    # Проверяем наличие папки audio и звуковых файлов
    if not audio_dir.exists():
        print("⚠️  Warning: audio directory not found, creating it...")
        audio_dir.mkdir(exist_ok=True)
    
    # Проверяем наличие папки icons и иконки таймера
    if not icons_dir.exists():
        print("⚠️  Warning: icons directory not found, creating it...")
        icons_dir.mkdir(exist_ok=True)
    
    # Проверяем наличие иконки таймера, если нет - создаем
    timer_icon = icons_dir / "timer.png"
    if not timer_icon.exists():
        print("🎨 Generating timer icon...")
        create_timer_icon = base_dir / "create_timer_icon.py"
        if create_timer_icon.exists():
            try:
                subprocess.check_call([sys.executable, str(create_timer_icon)], cwd=base_dir)
                print("✅ Timer icon generated successfully!")
            except Exception as e:
                print(f"⚠️  Could not generate timer icon: {e}")
        else:
            print("⚠️  create_timer_icon.py not found, skipping timer icon generation")
    
    # Проверяем наличие click.wav, если нет - генерируем
    click_wav = audio_dir / "click.wav"
    if not click_wav.exists():
        print("📢 Generating click.wav sound file...")
        generate_sound = base_dir / "generate_sound.py"
        if generate_sound.exists():
            try:
                subprocess.check_call([sys.executable, str(generate_sound)], cwd=base_dir)
                print("✅ Sound file generated successfully!")
            except Exception as e:
                print(f"⚠️  Could not generate sound file: {e}")
        else:
            print("⚠️  generate_sound.py not found, skipping sound generation")
    
    # Проверяем наличие иконки, если нет - создаем
    icon_path = base_dir / "icon.ico"
    icon_png = base_dir / "icon.png"
    if not icon_path.exists() and not icon_png.exists():
        print("🎨 Generating application icon...")
        create_icon = base_dir / "create_icon.py"
        if create_icon.exists():
            try:
                subprocess.check_call([sys.executable, str(create_icon)], cwd=base_dir)
                print("✅ Icon generated successfully!")
            except Exception as e:
                print(f"⚠️  Could not generate icon: {e}")
        else:
            print("⚠️  create_icon.py not found, skipping icon generation")
    
    # Определяем путь к иконке (приоритет: .ico, затем .png)
    icon_file = None
    if icon_path.exists():
        icon_file = icon_path
    elif icon_png.exists():
        icon_file = icon_png

    # PyInstaller arguments - ОПТИМИЗИРОВАНО для быстрого запуска
    args = [
        "pyinstaller",
        "--noconsole",          # Don't show console window
        "--onefile",            # Bundle everything into one exe
        "--name", "TaskMaster", # Name of the executable
        "--clean",              # Clean cache
        "--windowed",           # Windows subsystem
        
        # Критически важные скрытые импорты
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtMultimedia",
        "--hidden-import", "urllib.request",
        "--hidden-import", "urllib.error",
        "--hidden-import", "urllib.parse",
        "--hidden-import", "json",
        # Критически важные модули для работы Python
        "--hidden-import", "encodings",
        "--hidden-import", "encodings.utf_8",
        "--hidden-import", "encodings.cp1251",
        "--hidden-import", "encodings.latin_1",
        "--hidden-import", "codecs",
        "--hidden-import", "locale",
        "--hidden-import", "winsound",
        "--hidden-import", "threading",
        "--hidden-import", "ctypes",
        "--hidden-import", "ctypes.wintypes",
        # Собираем все подмодули encodings (важно для новых ПК!)
        "--collect-all", "encodings",
        # Собираем все подмодули стандартной библиотеки для urllib
        "--collect-all", "urllib",
        "--collect-all", "http",
        "--collect-all", "email",
        # Включаем все необходимые модули для работы с сетью
        "--collect-submodules", "urllib",
        
        # Включаем папку audio с звуковыми файлами
        "--add-data", f"audio{os.pathsep}audio",
        
        # Включаем папку icons с иконками
        "--add-data", f"icons{os.pathsep}icons",
        
        # Включаем version.py для проверки обновлений
        "--add-data", f"version.py{os.pathsep}.",
        
        # Оптимизация для быстрого запуска
        "--noupx",              # Отключаем UPX (быстрее запуск)
        "--optimize", "2",      # Оптимизация Python байткода
        
        # Исправление проблем с временными файлами PyInstaller
        "--bootloader-ignore-signals",  # Игнорировать сигналы при загрузке
    ]
    
    # Добавляем иконку, если она существует
    if icon_file and icon_file.exists():
        args.extend(["--icon", str(icon_file)])
        # Также включаем иконку в ресурсы для использования в коде
        icon_name = icon_file.name
        args.extend(["--add-data", f"{icon_name}{os.pathsep}."])
        print(f"📌 Using icon: {icon_file.name}")
    else:
        print("⚠️  No icon file found. Using default icon.")
    
    args.append(str(script_path))

    print(f"📦 Building with audio resources and all PySide6 modules...")
    print(f"Running command: pyinstaller {' '.join([a for a in args[1:] if not a.startswith('--') or a in ['--noconsole', '--onefile', '--clean', '--windowed', '--noupx']])}")
    
    try:
        subprocess.check_call(args, cwd=base_dir)
        print("\n✅ Build successful!")
        print(f"📁 Executable is located in: {base_dir / 'dist' / 'TaskMaster.exe'}")
        print(f"📝 Note: The audio folder will be included in the executable.")
        print(f"   Users can add custom.wav to the audio folder next to the exe.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error code {e.returncode}")
        print("💡 Try running: pip install --upgrade pyinstaller")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Ensure pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    build_exe()
