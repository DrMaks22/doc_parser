# DocParser - Модульный парсер документации для AI-обработки

DocParser - это универсальный инструмент для извлечения контента из различных систем документации и подготовки его для обработки AI-системами.

## Возможности

- 🔍 **Автоматическое определение типа документации**
- 📚 **Поддержка популярных систем**:
  - GitBook, Docusaurus, MkDocs, ReadTheDocs (Sphinx)
  - VuePress/VitePress, Hugo Docs, Docsify, Next.js
- 📊 **Гибкие параметры обхода и извлечения**
- 🔄 **Экспорт в различные форматы**:
  - Markdown, JSON, CSV, HTML, ZIP
  - Специализированный формат для Claude AI
- 🧩 **Модульная расширяемая архитектура**
- 🖥 **Четыре интерфейса**: CLI, GUI, Web UI, REST API

## Установка

```bash
# Клонирование репозитория
git clone https://github.com/DrMaks22/doc_parser.git
cd doc_parser

# Установка зависимостей
pip install -r requirements.txt
```

## Использование

### CLI
```bash
python -m doc_parser.main parse https://docs.example.com -o output -f markdown -d 2
```

### GUI
```bash
python -m doc_parser.main gui
```

### Web UI
```bash
python -m doc_parser.main webui --port 5000
```

### API
```bash
python -m doc_parser.main api --port 8000
```

## Конфигурация

### Параметры парсинга
- `url`: URL документации для парсинга
- `output-dir`: Директория для результатов
- `format`: Формат вывода (markdown/json/csv/claude/html/zip)
- `max-depth`: Максимальная глубина обхода
- `delay`: Задержка между запросами
- `timeout`: Таймаут запроса

### Фильтры URL
- `include`: Регулярное выражение для включения URL
- `exclude`: Регулярное выражение для исключения URL

## Структура проекта

```
doc_parser/
├── core/                  # Ядро парсера
│   ├── parser.py         # Основной парсер
│   ├── profiles.py       # Система профилей
│   └── extraction.py     # Извлечение контента
│
├── profiles/             # Профили документации
│   ├── common.py         # GitBook, Docusaurus, MkDocs
│   ├── technical.py      # ReadTheDocs, VuePress, Hugo
│   ├── js_based.py       # Docsify, NextJS
│   └── ai_docs.py        # AI-документация + Generic
│
├── exporters/            # Экспортеры форматов
│   ├── text_formats.py   # Markdown, JSON, CSV
│   ├── ai_formats.py     # Claude и другие AI
│   └── web_formats.py    # HTML, ZIP
│
├── interface/            # Интерфейсы
│   ├── app.py           # GUI (PySide6)
│   ├── api.py           # REST API (FastAPI)
│   └── webui.py         # Web UI (Flask)
│
└── utils/               # Вспомогательные утилиты
    └── helpers.py       # URL, HTML утилиты
```

## Требования

- Python 3.8+
- beautifulsoup4
- requests
- fastapi
- flask
- PySide6
- tenacity
- aiohttp

## Лицензия

MIT

## Автор

DrMaks22 (doctor.lakhnov@gmail.com)
