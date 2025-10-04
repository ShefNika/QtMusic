import sys
import subprocess
import os

def main():
    if sys.platform.startswith('linux'):
        try:
            subprocess.check_call(["sudo", "apt", "update"])
            subprocess.check_call(["sudo", "apt", "install", "-y", "python3-dev", "qt5-default", "libqt5widgets5"])
        except subprocess.CalledProcessError:
            print("Ошибка! Не удается установить системные зависимости.")
            sys.exit(1)

    whl_files = [f for f in os.listdir('.') if f.endswith('.whl')]
    if not whl_files:
        print("Ошибка! .whl файл не найден в текущей директории.")
        sys.exit(1)
    whl_file = whl_files[0]
    print(f"Найден .whl файл: {whl_file}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", whl_file])
        print("Установка завершена. Запуск приложения осуществляется командой: qt-music")
    except subprocess.CalledProcessError:
        print("Ошибка! Не удается установить .whl файл.")
        sys.exit(1)

if __name__ == "__main__":
    main()
