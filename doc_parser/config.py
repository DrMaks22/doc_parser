#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Глобальная конфигурация для парсера документации.
"""

# Базовые настройки
DEFAULT_CONFIG = {
    'max_depth': 3,               # Максимальная глубина обхода
    'delay': 0.5,                 # Задержка между запросами (секунды)
    'timeout': 30,                # Таймаут запроса (секунды)
    'retries': 3,                 # Количество повторных попыток
    'user_agent': 'DocParser/1.0',  # User-Agent для запросов
    'include_patterns': [],       # Шаблоны URL для включения
    'exclude_patterns': [],       # Шаблоны URL для исключения
    'follow_links': True,         # Следовать ли по ссылкам
    'save_assets': False,         # Сохранять ли ассеты (изображения и т.д.)
    'output_format': 'markdown',  # Формат вывода по умолчанию
    'output_dir': 'output',       # Директория для результатов
    'log_level': 'INFO',          # Уровень логирования
}

# Зависимости
REQUIREMENTS = [
    'requests',
    'beautifulsoup4',
    'tenacity',
    'lxml',
    'fastapi',
    'uvicorn',
    'pyyaml',
    'rich',
    'tqdm',
]

# Селекторы элементов для разных типов документации
COMMON_CONTENT_SELECTORS = {
    'content': ['article', 'main', '.content', '.markdown-body', '.markdown-section', '.theme-default-content'],
    'navigation': ['.sidebar', '.table-of-contents', '.menu', 'nav', '.navigation'],
    'ignore': ['footer', 'header', '.admonition', '.github-fork-ribbon', '.edit-link', '.last-updated'],
}

# Метаданные для определения типа документации
DOC_SYSTEM_METADATA = {
    'gitbook': {
        'hostnames': ['gitbook.io'],
        'meta_generator': ['GitBook'],
        'selectors': {'content': ['.markdown-section'], 'navigation': ['.book-summary']},
    },
    'docusaurus': {
        'hostnames': ['docusaurus.io'],
        'meta_generator': ['Docusaurus'],
        'selectors': {'content': ['article.docusaurus-content'], 'navigation': ['.menu__list']},
    },
    'vuepress': {
        'hostnames': ['vuepress.vuejs.org'],
        'meta_generator': ['VuePress'],
        'selectors': {'content': ['.theme-default-content'], 'navigation': ['.sidebar']},
    },
    'readthedocs': {
        'hostnames': ['readthedocs.io', 'readthedocs.org'],
        'meta_generator': ['Sphinx'],
        'selectors': {'content': ['.document'], 'navigation': ['.wy-nav-side']},
    },
    'mkdocs': {
        'hostnames': ['mkdocs.org'],
        'meta_generator': ['MkDocs'],
        'selectors': {'content': ['.md-content__inner'], 'navigation': ['.md-sidebar__inner']},
    },
    'hugo': {
        'hostnames': ['gohugo.io'],
        'meta_generator': ['Hugo'],
        'selectors': {'content': ['.content'], 'navigation': ['.menu']},
    },
    'docsify': {
        'hostnames': ['docsify.js.org'],
        'meta_generator': ['docsify'],
        'selectors': {'content': ['.content'], 'navigation': ['.sidebar']},
    },
    'nextjs': {
        'hostnames': ['nextjs.org'],
        'meta_generator': ['Next.js'],
        'selectors': {'content': ['.docs-content'], 'navigation': ['.sidebar']},
    },
}

VERSION = '0.1.0'
