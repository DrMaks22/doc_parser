# DocParser - Модульный парсер документации для AI-обработки

DocParser - это универсальный инструмент для извлечения контента из систем документации и подготовки его для обработки AI-системами, включая Claude и другие языковые модели.

## Возможности

- 🔍 **Автоматическое определение типа документации**
- 📚 **Поддержка популярных систем документации**:
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
git clone https://github.com/yourusername/doc_parser.git
cd doc_parser

# Установка зависимостей
pip install -r requirements.txt
```

### Зависимости

- requests
- beautifulsoup4
- tenacity
- lxml
- fastapi
- uvicorn
- pyyaml
- rich
- tqdm
- html2text
- flask
- flask-cors
- PySide6 (для GUI)

## Использование

### Командная строка (CLI)

```bash
# Базовый парсинг
python -m doc_parser.main parse https://docs.example.com -o output -f markdown -d 2

# Расширенный пример с фильтрами и настройками
python -m doc_parser.main parse https://docs.python.org/3/ \
    -o output_python \
    -f claude \
    -d 3 \
    --delay 1.0 \
    --include "tutorial" \
    --exclude "whatsnew" \
    --save-assets
```

#### Параметры CLI

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `url` | URL документации для парсинга | (обязательный) |
| `-o, --output-dir` | Директория для результатов | output |
| `-f, --format` | Формат вывода (markdown/json/csv/claude/html/zip) | markdown |
| `-d, --max-depth` | Максимальная глубина обхода | 3 |
| `--delay` | Задержка между запросами в секундах | 0.5 |
| `--timeout` | Таймаут запроса в секундах | 30 |
| `--include` | Регулярное выражение для включения URL | None |
| `--exclude` | Регулярное выражение для исключения URL | None |
| `--no-follow` | Не следовать по ссылкам | False |
| `--save-assets` | Сохранять ассеты (изображения, CSS, JS) | False |
| `--log-level` | Уровень логирования (DEBUG/INFO/WARNING/ERROR) | INFO |

### Графический интерфейс (GUI)

```bash
python -m doc_parser.main gui
```

### Веб-интерфейс (WebUI)

```bash
python -m doc_parser.main webui --port 5000
```

После запуска веб-интерфейс будет доступен по адресу http://localhost:5000/

### API-сервер

```bash
python -m doc_parser.main api --port 8000
```

API-документация будет доступна по адресу http://localhost:8000/docs

## Форматы вывода

### Markdown

Сохраняет каждую страницу как отдельный Markdown-файл с сохранением структуры контента.

### JSON

Экспортирует полную структуру данных в JSON-формате, включая HTML и извлеченный текст.

### CSV

Создает CSV-файл с URL, заголовками и текстовым содержимым страниц, а также отдельный файл ссылок.

### Claude

Специализированный формат для загрузки в Claude AI, с оптимизированной разметкой и структурой. Также создает "чанки" для обработки больших документаций.

### HTML

Сохраняет страницы в HTML с возможностью включения ассетов (изображений, стилей).

### ZIP

Архивирует HTML-экспорт в ZIP-файл для удобной передачи.

## Поддерживаемые системы документации

| Система | Поддерживаемые домены | Примечания |
|---------|----------------------|------------|
| GitBook | gitbook.io, gitbook.com | |
| Docusaurus | docusaurus.io | Документация React |
| MkDocs | mkdocs.org | Популярная Python-система |
| ReadTheDocs (Sphinx) | readthedocs.io, readthedocs.org | Стандарт для Python |
| VuePress | vuepress.vuejs.org | Документация Vue.js |
| Hugo Docs | gohugo.io | Популярный генератор статичных сайтов |
| Docsify | docsify.js.org | JavaScript-система без сборки |
| NextJS | nextjs.org | React-фреймворк |
| AI Docs | anthropic.com, claude.ai, openai.com | Специализированные профили для AI-систем |

Также включен универсальный профиль, который может работать с большинством других систем документации.

## Архитектура

```
doc_parser/
│
├── core/                  # Ядро парсера
│   ├── parser.py          # Основной парсер + обход
│   ├── profiles.py        # Система профилей + детектор
│   └── extraction.py      # Извлечение контента
│
├── profiles/              # Профили систем документации
│   ├── common.py          # GitBook, Docusaurus, MkDocs
│   ├── technical.py       # ReadTheDocs, VuePress, Hugo
│   ├── js_based.py        # Docsify, NextJS
│   └── ai_docs.py         # AI-документация + Generic
│
├── exporters/             # Экспортеры разных форматов
│   ├── text_formats.py    # Markdown, JSON, CSV
│   ├── ai_formats.py      # Claude и другие AI
│   └── web_formats.py     # HTML, ZIP
│
├── utils/                 # Вспомогательные утилиты
│   └── helpers.py         # Логгер, URL и HTML утилиты
│
├── interface/             # Пользовательские интерфейсы
│   ├── app.py             # GUI (PySide6)
│   ├── api.py             # REST API (FastAPI)
│   └── webui.py           # Web UI (Flask)
│
├── main.py                # Точка входа CLI
└── config.py              # Глобальная конфигурация
```

## Описание настроек

### Основные настройки

- **URL документации**: Исходная точка парсера
- **Глубина обхода**: Насколько "глубоко" парсер следует по ссылкам (1-10)
- **Задержка**: Время ожидания между запросами (0.1-10 сек)
- **Таймаут**: Максимальное время ожидания ответа (5-120 сек)

### Формат вывода

- **Формат вывода**: Markdown, JSON, CSV, Claude, HTML, ZIP
- **Директория вывода**: Путь для сохранения результатов

### Фильтры URL

- **Включать URL**: Регулярное выражение для обработки только соответствующих URL
- **Исключать URL**: Регулярное выражение для пропуска соответствующих URL

### Дополнительные параметры

- **Следовать по ссылкам**: Переходить по ссылкам в документах
- **Сохранять ассеты**: Загружать и сохранять ресурсы (изображения, CSS, JS)

## Примеры использования

### Подготовка документации для Claude

```bash
# Парсинг документации Python для Claude
python -m doc_parser.main parse https://docs.python.org/3/tutorial/ -f claude -d 2 -o python_docs
```

### Экспорт в JSON для дальнейшей обработки

```bash
# Экспорт документации в JSON для программной обработки
python -m doc_parser.main parse https://docs.example.com -f json -o data
```

### Фильтрация по разделам

```bash
# Парсинг только разделов с руководством
python -m doc_parser.main parse https://docs.example.com --include "guide|tutorial" -o guides
```

## Расширение функциональности

### Добавление нового профиля

Чтобы добавить поддержку новой системы документации, создайте класс, наследующий от `SiteProfile` в одном из файлов профилей:

```python
class NewSystemProfile(SiteProfile):
    name = "newsystem"
    description = "Новая система документации"
    
    # Идентификация
    hostnames = ['newsystem.com']
    meta_generator = ['NewSystem']
    
    # Селекторы
    content_selectors = ['.content', 'main']
    navigation_selectors = ['.sidebar', 'nav']
    
    def extract_content(self, soup):
        # Кастомная логика извлечения
        # ...
        return content

# Регистрация
registry.register(NewSystemProfile)
```

### Добавление нового экспортера

Для создания нового формата экспорта добавьте новый класс в соответствующий файл экспортеров:

```python
class NewFormatExporter:
    def __init__(self, config=None):
        self.config = config or {}
    
    def export_results(self, results, output_path):
        # Логика экспорта
        # ...
        return output_path
```

## Лицензия

MIT

## Об авторе

DocParser разработан для решения проблемы извлечения структурированной документации для обучения и работы с языковыми моделями, такими как Claude.

## Вклад в проект

Вклады приветствуются! Пожалуйста, создавайте Issues или Pull Requests для улучшения проекта.