#!/bin/bash

echo "================================"
echo "SubsiSmart KZ - Быстрый старт"
echo "================================"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.8 или новее."
    exit 1
fi

echo "✓ Python найден: $(python3 --version)"
echo ""

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
    echo "✓ Виртуальное окружение создано"
else
    echo "✓ Виртуальное окружение уже существует"
fi

# Активация виртуального окружения
echo ""
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo ""
echo "📥 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Зависимости установлены"

# Проверка наличия данных
echo ""
if [ -f "data/Выгрузка_по_выданным_субсидиям_2025_год__обезлич_.xlsx" ]; then
    echo "✓ Файл данных найден"
else
    echo "⚠️  Файл данных не найден!"
    echo "   Поместите файл 'Выгрузка_по_выданным_субсидиям_2025_год__обезлич_.xlsx'"
    echo "   в папку 'data/'"
fi

# Создание папок
echo ""
echo "📁 Создание необходимых папок..."
mkdir -p results
echo "✓ Папки созданы"

echo ""
echo "================================"
echo "✅ Установка завершена!"
echo "================================"
echo ""
echo "Для запуска консольного анализа:"
echo "  python scoring_engine.py"
echo ""
echo "Для запуска веб-приложения:"
echo "  python app.py"
echo "  Затем откройте: http://localhost:5000"
echo ""
