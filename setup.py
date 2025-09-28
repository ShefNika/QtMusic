from setuptools import setup, find_packages

setup(
    name="qt-music",  # Имя пакета
    version="1.0.0",  # Версия пакета
    description="Музыкальный плейлист на PyQt5 с SQLite",
    author="ShefNika",
    packages=find_packages(),
    #py_modules=['main', 'ui_main', 'ui_song_dialog'],
    include_package_data=True,  # Включает все файлы
    package_data={
        '': ['*.py'],  # Включает все .py файлы
    },
    entry_points={
        'console_scripts': [
            'qt-music = main:main',  # Точка входа
        ],
    },
    install_requires=[
        "PyQt5==5.15.2",  # Зависимости
    ],
    python_requires=">=3.5,<3.9",  # Совместимость с Python 3.5–3.8
)