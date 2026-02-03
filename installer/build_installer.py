"""
Скрипт для сборки инсталлятора TaskMaster

Два варианта:
1. Автономный инсталлятор (рекомендуется) - не требует дополнительных программ
2. Inno Setup инсталлятор - требует установки Inno Setup Compiler
"""
import os
import subprocess
import sys
from pathlib import Path

def find_inno_setup():
    """Поиск Inno Setup Compiler"""
    # Стандартные пути установки Inno Setup
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Пытаемся найти через переменную окружения
    inno_path = os.environ.get("INNO_SETUP_PATH")
    if inno_path and os.path.exists(inno_path):
        return inno_path
    
    return None

def build_installer():
    """Сборка инсталлятора"""
    import sys
    
    # Проверяем, какой тип инсталлятора нужен
    use_standalone = os.environ.get("INSTALLER_TYPE", "standalone").lower() == "standalone"
    
    if use_standalone:
        print("🚀 Создаем автономный инсталлятор (не требует дополнительных программ)...")
        # Используем новый скрипт для автономного инсталлятора
        standalone_script = Path(__file__).parent / "create_installer.py"
        if standalone_script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(standalone_script)],
                    check=True
                )
                return result.returncode == 0
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                return False
        else:
            print("❌ Файл create_installer.py не найден")
            return False
    
    print("🚀 Начинаем сборку инсталлятора TaskMaster (Inno Setup)...")
    
    # Базовые директории
    base_dir = Path(__file__).parent.parent.resolve()
    installer_dir = base_dir / "installer"
    dist_dir = base_dir / "dist"
    iss_file = installer_dir / "TaskMaster.iss"
    
    # Проверяем наличие необходимых файлов
    if not iss_file.exists():
        print(f"❌ Ошибка: Не найден файл {iss_file}")
        return False
    
    # Проверяем наличие собранного приложения
    app_dir = dist_dir / "TaskMaster"
    if not app_dir.exists() or not (app_dir / "TaskMaster.exe").exists():
        print(f"❌ Ошибка: Не найдено собранное приложение в {app_dir}")
        print("💡 Сначала запустите: python build_windows.py")
        return False
    
    # Ищем Inno Setup Compiler
    iscc_path = find_inno_setup()
    if not iscc_path:
        print("❌ Ошибка: Inno Setup Compiler не найден!")
        print("\n📥 Пожалуйста, установите Inno Setup:")
        print("   https://jrsoftware.org/isinfo.php")
        print("\n💡 Или укажите путь через переменную окружения INNO_SETUP_PATH")
        return False
    
    print(f"✅ Найден Inno Setup: {iscc_path}")
    
    # Компилируем инсталлятор
    print(f"\n📦 Компилируем инсталлятор из {iss_file}...")
    try:
        # Переходим в директорию installer для правильных относительных путей
        result = subprocess.run(
            [iscc_path, str(iss_file)],
            cwd=installer_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        # Получаем версию из version.py
        try:
            import sys
            sys.path.insert(0, str(base_dir))
            import version
            app_version = version.__version__
        except ImportError:
            app_version = "1.0.3"
        
        # Ищем созданный файл
        installer_exe = installer_dir / "dist" / f"TaskMaster-Setup-{app_version}.exe"
        if installer_exe.exists():
            print(f"\n✅ Инсталлятор успешно создан!")
            print(f"📁 Расположение: {installer_exe}")
            print(f"📊 Размер: {installer_exe.stat().st_size / 1024 / 1024:.2f} MB")
            return True
        else:
            print("\n⚠️  Предупреждение: Инсталлятор не найден в ожидаемом месте")
            print("   Проверьте папку dist в директории installer")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка компиляции инсталлятора:")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    success = build_installer()
    sys.exit(0 if success else 1)
