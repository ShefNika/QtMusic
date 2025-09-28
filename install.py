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

    file = "qt_music-1_0_0-py3-none-any.whl" if sys.platform.startswith('linux') else "qt_music-1.0.0-py3-none-any.whl"
    if not os.path.exists(file):
        print(f"Ошибка! Файл {file} не найден.")
        sys.exit(1)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", file])
    except subprocess.CalledProcessError:
        print("Ошибка! Не удается установить .whl файл.")
        sys.exit(1)
    print("Установка завершена. Запуск приложения осуществляется командой: qt-music")

if __name__ == "__main__":
    main()
