#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Экспортеры для AI-форматов (Claude и другие AI-системы).
"""

import os
import re
import json
from bs4 import BeautifulSoup

from doc_parser.utils.helpers import extract_text


class ClaudeExporter:
    """
    Экспортер для формата, оптимизированного под Claude.
    """
    
    def __init__(self, config=None):
        """
        Инициализация экспортера.
        
        Args:
            config: Словарь с настройками
        """
        self.config = config or {}
    
    def format_for_claude(self, results):
        """
        Форматирует результаты парсинга для Claude.
        
        Args:
            results: Словарь с результатами парсинга
            
        Returns:
            str: Форматированный текст для Claude
        """
        output = []
        
        # Добавляем заголовок
        output.append("# Документация\n")
        
        # Сортируем страницы по глубине
        pages = sorted(
            results.items(), 
            key=lambda x: (x[1].get('depth', 0), x[1].get('title', ''))
        )
        
        # Добавляем содержание
        output.append("## Содержание\n")
        
        for url, page_data in pages:
            title = page_data.get('title', url)
            output.append(f"- {title}")
        
        output.append("\n")
        
        # Добавляем страницы
        for url, page_data in pages:
            title = page_data.get('title', url)
            output.append(f"## {title}\n")
            
            # URL
            output.append(f"URL: {url}\n")
            
            # Метаданные
            if any(key in page_data for key in ['description', 'keywords', 'author']):
                output.append("### Метаданные\n")
                
                for key in ['description', 'keywords', 'author']:
                    if key in page_data and page_data[key]:
                        output.append(f"- **{key.capitalize()}**: {page_data[key]}")
                
                output.append("\n")
            
            # Контент
            output.append("### Содержание\n")
            
            if 'content_html' in page_data and page_data['content_html']:
                # Очищаем HTML
                soup = BeautifulSoup(page_data['content_html'], 'lxml')
                
                # Удаляем скрипты и стили
                for tag in soup(['script', 'style', 'iframe']):
                    tag.decompose()
                
                # Форматируем текст
                text = soup.get_text(separator='\n', strip=True)
                text = re.sub(r'\n{3,}', '\n\n', text)
                
                output.append(text + "\n")
            
            output.append("\n---\n")
        
        return "\n".join(output)
    
    def export_for_claude(self, results, output_path):
        """
        Экспортирует результаты парсинга в формате для Claude.
        
        Args:
            results: Словарь с результатами парсинга
            output_path: Путь для сохранения файла
            
        Returns:
            str: Путь к сохраненному файлу
        """
        # Создаем директорию, если не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Форматируем и сохраняем
        formatted_text = self.format_for_claude(results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        
        return output_path
    
    def export_chunked(self, results, output_dir, chunk_size=4000):
        """
        Экспортирует результаты парсинга в разбитые чанки для Claude.
        
        Args:
            results: Словарь с результатами парсинга
            output_dir: Директория для сохранения файлов
            chunk_size: Размер чанка в символах
            
        Returns:
            list: Список путей к сохраненным файлам
        """
        # Создаем директорию, если не существует
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        
        # Сортируем страницы по глубине
        pages = sorted(
            results.items(), 
            key=lambda x: (x[1].get('depth', 0), x[1].get('title', ''))
        )
        
        # Создаем чанки
        chunks = []
        current_chunk = []
        current_size = 0
        
        for url, page_data in pages:
            # Форматируем страницу
            title = page_data.get('title', url)
            page_text = f"## {title}\n\nURL: {url}\n\n"
            
            if 'content_html' in page_data and page_data['content_html']:
                # Очищаем HTML
                text = extract_text(page_data['content_html'])
                page_text += text + "\n\n---\n\n"
            
            # Если текущий чанк + страница превышают лимит, создаем новый чанк
            if current_size + len(page_text) > chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # Добавляем страницу в текущий чанк
            current_chunk.append(page_text)
            current_size += len(page_text)
        
        # Добавляем последний чанк
        if current_chunk:
            chunks.append("\n".join(current_chunk))
        
        # Сохраняем чанки
        for i, chunk_text in enumerate(chunks):
            filename = f"claude_chunk_{i + 1}.md"
            output_path = os.path.join(output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(chunk_text)
            
            saved_files.append(output_path)
        
        # Создаем индексный файл
        index_path = os.path.join(output_dir, "claude_index.md")
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(f"# Документация (разбита на {len(chunks)} чанков)\n\n")
            
            for i, _ in enumerate(chunks):
                f.write(f"- [Чанк {i + 1}](claude_chunk_{i + 1}.md)\n")
        
        saved_files.append(index_path)
        
        return saved_files
