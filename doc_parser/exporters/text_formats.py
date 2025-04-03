#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Экспортеры для текстовых форматов (Markdown, JSON, CSV).
"""

import os
import json
import csv
import re
from bs4 import BeautifulSoup
import html2text

from doc_parser.utils.helpers import extract_text


class MarkdownExporter:
    """
    Экспортер для формата Markdown.
    """
    
    def __init__(self, config=None):
        """
        Инициализация экспортера.
        
        Args:
            config: Словарь с настройками
        """
        self.config = config or {}
        
        # Настраиваем конвертер html2text
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.bypass_tables = False
        self.converter.ignore_images = False
        self.converter.unicode_snob = True
        self.converter.body_width = 0  # Отключаем перенос строк
    
    def export_content(self, content_html, metadata=None):
        """
        Экспортирует HTML-контент в Markdown.
        
        Args:
            content_html: HTML-контент в виде строки
            metadata: Метаданные страницы
            
        Returns:
            str: Markdown-текст
        """
        if not content_html:
            return ""
        
        # Предварительная обработка HTML
        soup = BeautifulSoup(content_html, 'lxml')
        
        # Удаляем ненужные элементы
        for selector in ['script', 'style', 'iframe', 'noscript']:
            for tag in soup.find_all(selector):
                tag.decompose()
        
        # Добавляем заголовок из метаданных, если есть
        if metadata and 'title' in metadata:
            title_tag = soup.new_tag('h1')
            title_tag.string = metadata['title']
            soup.insert(0, title_tag)
            
            # Добавляем метаданные
            meta_text = []
            if 'url' in metadata:
                meta_text.append(f"URL: {metadata['url']}")
            if 'description' in metadata:
                meta_text.append(f"Description: {metadata['description']}")
            
            if meta_text:
                meta_div = soup.new_tag('div')
                meta_div.string = '\n'.join(meta_text)
                soup.insert(1, meta_div)
        
        # Преобразуем в Markdown
        markdown = self.converter.handle(str(soup))
        
        # Пост-обработка Markdown
        # Удаляем лишние пробелы и пустые строки
        markdown = re.sub(r'\n{3,}', '\n\n', markdown).strip()
        
        return markdown
    
    def export_navigation(self, navigation_html):
        """
        Экспортирует HTML-навигацию в Markdown.
        
        Args:
            navigation_html: HTML-навигация в виде строки
            
        Returns:
            str: Markdown-текст с навигацией
        """
        if not navigation_html:
            return ""
        
        # Предварительная обработка HTML
        soup = BeautifulSoup(navigation_html, 'lxml')
        
        # Удаляем все, кроме ссылок и текста
        for tag in soup.find_all(True):
            if tag.name not in ['a', 'ul', 'ol', 'li', 'div', 'span', 'p']:
                tag.unwrap()
        
        # Преобразуем в Markdown
        markdown = self.converter.handle(str(soup))
        
        # Добавляем заголовок
        markdown = "## Навигация\n\n" + markdown
        
        return markdown
    
    def export_page(self, page_data):
        """
        Экспортирует данные страницы в Markdown.
        
        Args:
            page_data: Словарь с данными страницы
            
        Returns:
            str: Markdown-текст
        """
        parts = []
        
        # Добавляем заголовок
        if 'title' in page_data:
            parts.append(f"# {page_data['title']}\n")
        
        # Добавляем метаданные
        meta_lines = []
        meta_fields = ['url', 'description', 'keywords', 'author']
        
        for field in meta_fields:
            if field in page_data and page_data[field]:
                meta_lines.append(f"- **{field.capitalize()}**: {page_data[field]}")
        
        if meta_lines:
            parts.append("## Метаданные\n")
            parts.append('\n'.join(meta_lines) + '\n')
        
        # Добавляем основной контент
        if 'content_html' in page_data and page_data['content_html']:
            markdown = self.export_content(page_data['content_html'])
            parts.append("## Содержание\n")
            parts.append(markdown + '\n')
        
        # Добавляем навигацию, если есть
        if 'navigation_html' in page_data and page_data['navigation_html']:
            nav_markdown = self.export_navigation(page_data['navigation_html'])
            if nav_markdown:
                parts.append(nav_markdown)
        
        return '\n'.join(parts)
    
    def save_page(self, output_path, page_data):
        """
        Сохраняет данные страницы в Markdown-файл.
        
        Args:
            output_path: Путь для сохранения файла
            page_data: Словарь с данными страницы
            
        Returns:
            str: Путь к сохраненному файлу
        """
        markdown = self.export_page(page_data)
        
        # Создаем директорию, если не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Сохраняем файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        return output_path
    
    def save_results(self, results, output_dir):
        """
        Сохраняет результаты парсинга в Markdown-файлы.
        
        Args:
            results: Словарь с результатами парсинга
            output_dir: Директория для сохранения файлов
            
        Returns:
            list: Список путей к сохраненным файлам
        """
        saved_files = []
        
        for url, page_data in results.items():
            # Создаем имя файла из URL
            filename = re.sub(r'[^\w\-]', '_', url) + '.md'
            output_path = os.path.join(output_dir, filename)
            
            # Сохраняем файл
            saved_file = self.save_page(output_path, page_data)
            saved_files.append(saved_file)
        
        return saved_files


class JsonExporter:
    """
    Экспортер для формата JSON.
    """
    
    def __init__(self, config=None):
        """
        Инициализация экспортера.
        
        Args:
            config: Словарь с настройками
        """
        self.config = config or {}
    
    def export_results(self, results):
        """
        Экспортирует результаты парсинга в JSON.
        
        Args:
            results: Словарь с результатами парсинга
            
        Returns:
            str: JSON-строка
        """
        # Добавляем простой текст для каждой страницы
        for url, page_data in results.items():
            if 'content_html' in page_data:
                page_data['content_text'] = extract_text(page_data['content_html'])
            
            if 'navigation_html' in page_data:
                page_data['navigation_text'] = extract_text(page_data['navigation_html'])
        
        # Преобразуем в JSON
        return json.dumps(results, ensure_ascii=False, indent=2)
    
    def save_results(self, results, output_path):
        """
        Сохраняет результаты парсинга в JSON-файл.
        
        Args:
            results: Словарь с результатами парсинга
            output_path: Путь для сохранения файла
            
        Returns:
            str: Путь к сохраненному файлу
        """
        # Создаем директорию, если не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Преобразуем в JSON и сохраняем
        json_data = self.export_results(results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
        
        return output_path


class CsvExporter:
    """
    Экспортер для формата CSV.
    """
    
    def __init__(self, config=None):
        """
        Инициализация экспортера.
        
        Args:
            config: Словарь с настройками
        """
        self.config = config or {}
    
    def export_results(self, results, output_path):
        """
        Экспортирует результаты парсинга в CSV.
        
        Args:
            results: Словарь с результатами парсинга
            output_path: Путь для сохранения файла
            
        Returns:
            str: Путь к сохраненному файлу
        """
        # Создаем директорию, если не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Определяем заголовки
        headers = ['url', 'title', 'content_text', 'profile', 'depth']
        
        # Записываем в CSV
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for url, page_data in results.items():
                row = {
                    'url': url,
                    'title': page_data.get('title', ''),
                    'content_text': extract_text(page_data.get('content_html', '')),
                    'profile': page_data.get('profile', ''),
                    'depth': page_data.get('depth', 0)
                }
                writer.writerow(row)
        
        return output_path
    
    def export_links(self, results, output_path):
        """
        Экспортирует ссылки из результатов парсинга в CSV.
        
        Args:
            results: Словарь с результатами парсинга
            output_path: Путь для сохранения файла
            
        Returns:
            str: Путь к сохраненному файлу
        """
        # Создаем директорию, если не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Определяем заголовки
        headers = ['source_url', 'target_url']
        
        # Записываем в CSV
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for url, page_data in results.items():
                for link in page_data.get('links', []):
                    row = {
                        'source_url': url,
                        'target_url': link
                    }
                    writer.writerow(row)
        
        return output_path
