"""
Деинсталлятор TaskMaster
"""
import os
import sys
import shutil
import winreg
from pathlib import Path

def uninstall():
    """Удаление приложения"""
    print("🗑️  Удаление TaskMaster...")
    
    # Определяем путь установки из реестра
    install_dir = None
    try:
        uninstall_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\TaskMaster"
        )
        install_dir = winreg.QueryValueEx(uninstall_key, "InstallLocation")[0]
        winreg.CloseKey(uninstall_key)
    except:
        # Если не найдено в реестре, пробуем стандартный путь
        program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
        install_dir = Path(program_files) / "TaskMaster"
    
    if not install_dir or not Path(install_dir).exists():
        print("⚠️  TaskMaster не найден в системе")
        is_silent = "/SILENT" in sys.argv or "/S" in sys.argv
        if not is_silent and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
            try:
                input("Нажмите Enter для выхода...")
            except (EOFError, OSError, RuntimeError):
                pass
        return False
    
    install_dir = Path(install_dir)
    print(f"📁 Удаление из: {install_dir}")
    
    # Удаляем файлы
    try:
        if install_dir.exists():
            shutil.rmtree(install_dir)
            print("✅ Файлы удалены")
    except Exception as e:
        print(f"⚠️  Ошибка удаления файлов: {e}")
        print("   Некоторые файлы могут быть заблокированы")
    
    # Удаляем запись из реестра
    try:
        uninstall_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
            0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
        )
        winreg.DeleteKey(uninstall_key, "TaskMaster")
        winreg.CloseKey(uninstall_key)
        print("✅ Запись в реестре удалена")
    except Exception as e:
        print(f"⚠️  Ошибка удаления записи из реестра: {e}")
    
    # Удаляем ярлык с рабочего стола
    try:
        desktop = Path(os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"))
        desktop_shortcut = desktop / "TaskMaster.lnk"
        if desktop_shortcut.exists():
            desktop_shortcut.unlink()
            print("✅ Ярлык с рабочего стола удален")
    except Exception as e:
        print(f"⚠️  Ошибка удаления ярлыка: {e}")
    
    print("\n✅ Удаление завершено!")
    is_silent = "/SILENT" in sys.argv or "/S" in sys.argv
    if not is_silent and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
        try:
            input("Нажмите Enter для выхода...")
        except (EOFError, OSError, RuntimeError):
            pass
    
    return True

if __name__ == "__main__":
    try:
        success = uninstall()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Ошибка удаления: {e}")
        import traceback
        traceback.print_exc()
        is_silent = "/SILENT" in sys.argv or "/S" in sys.argv
        if not is_silent and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
            try:
                input("Нажмите Enter для выхода...")
            except (EOFError, OSError, RuntimeError):
                pass
        sys.exit(1)
