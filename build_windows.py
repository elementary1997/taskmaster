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
    
    if not script_path.exists():
        print(f"❌ Error: Could not find {script_path}")
        return

    # Проверяем наличие папки audio и звуковых файлов
    if not audio_dir.exists():
        print("⚠️  Warning: audio directory not found, creating it...")
        audio_dir.mkdir(exist_ok=True)
    
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

    # PyInstaller arguments
    args = [
        "pyinstaller",
        "--noconsole",          # Don't show console window
        "--onefile",            # Bundle everything into one exe
        "--name", "TaskMaster", # Name of the executable
        "--clean",              # Clean cache
        "--windowed",           # Windows subsystem
        
        # Скрытые импорты для PySide6 (импортируются локально в коде)
        "--hidden-import", "PySide6.QtWidgets.QMenu",
        "--hidden-import", "PySide6.QtWidgets.QSlider",
        "--hidden-import", "PySide6.QtCore.QTimer",
        "--hidden-import", "PySide6.QtGui.QAction",
        
        # Включаем все подмодули PySide6
        "--collect-submodules", "PySide6",
        
        # Включаем папку audio с звуковыми файлами
        "--add-data", f"audio{os.pathsep}audio",
        
        # Дополнительные опции для правильной работы
        "--collect-all", "PySide6",  # Собираем все ресурсы PySide6
        "--noupx",  # Отключаем UPX для стабильности
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
