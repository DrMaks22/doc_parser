#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Экспортеры для веб-форматов (HTML, ZIP).
"""

import os
import re
import zipfile
import shutil
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests


class HtmlExporter:
    """
    Экспортер для формата HTML.
    """
    
    def __init__(self, config=None):
        """
        Инициализация экспортера.
        
        Args:
            config: Словарь с настройками
        """
        self.config = config or {}
    
    def export_page(self, page_data, output_path, assets_dir=None):
        """
        Экспортирует данные страницы в HTML.
        
        Args:
            page_data: Словарь с данными страницы
            output_path: Путь для сохранения файла
            assets_dir: Директория для сохранения ассетов (если None, не сохраняет)
            
        Returns:
            str: Путь к сохраненному файлу
        """
        # Создаем директорию, если не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Создаем шаблон HTML
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{page_data.get('title', 'Документация')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; }}
                .container {{ display: flex; }}
                .nav {{ width: 300px; padding: 20px; border-right: 1px solid #eee; }}
                .content {{ flex: 1; padding: 20px; }}
                @media (max-width: 768px) {{
                    .container {{ flex-direction: column; }}
                    .nav {{ width: 100%; border-right: none; border-bottom: 1px solid #eee; }}
                }}
                pre {{ background-color: #f5f5f5; padding: 10px; overflow: auto; }}
                code {{ font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="nav">
                    {page_data.get('navigation_html', '')}
                </div>
                <div class="content">
                    <h1>{page_data.get('title', 'Документация')}</h1>
                    <p>URL: <a href="{page_data.get('url', '#')}">{page_data.get('url', '')}</a></p>
                    {page_data.get('content_html', '')}
                </div>
            </div>
        </body>
        </html>
        """
        
        # Сохраняем файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        # Если нужно сохранять ассеты
        if assets_dir and self.config.get('save_assets', False):
            self._save_assets(page_data, assets_dir)
        
        return output_path
    
    def _save_assets(self, page_data, assets_dir):
        """
        Сохраняет ассеты (изображения, CSS, JS) из страницы.
        
        Args:
            page_data: Словарь с данными страницы
            assets_dir: Директория для сохранения ассетов
        """
        # Создаем директорию для ассетов
        os.makedirs(assets_dir, exist_ok=True)
        
        # Парсим HTML
        soup = BeautifulSoup(page_data.get('content_html', ''), 'lxml')
        
        # Находим все ассеты
        images = soup.find_all('img', src=True)
        css_links = soup.find_all('link', rel='stylesheet', href=True)
        js_scripts = soup.find_all('script', src=True)
        
        # URL страницы для относительных ссылок
        base_url = page_data.get('url', '')
        
        # Сохраняем изображения
        for img in images:
            src = img['src']
            # Получаем полный URL
            full_url = urljoin(base_url, src)
            try:
                # Получаем имя файла
                parsed_url = urlparse(full_url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    continue
                
                # Создаем путь для сохранения
                save_path = os.path.join(assets_dir, filename)
                
                # Скачиваем файл
                response = requests.get(full_url, stream=True)
                response.raise_for_status()
                
                # Сохраняем файл
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Обновляем src в HTML
                img['src'] = os.path.join('assets', filename)
            except Exception as e:
                print(f"Ошибка при сохранении изображения {src}: {e}")
        
        # Аналогично для CSS и JS
        for link in css_links + js_scripts:
            src_attr = 'href' if link.name == 'link' else 'src'
            src = link[src_attr]
            
            # Получаем полный URL
            full_url = urljoin(base_url, src)
            try:
                # Получаем имя файла
                parsed_url = urlparse(full_url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    continue
                
                # Создаем путь для сохранения
                save_path = os.path.join(assets_dir, filename)
                
                # Скачиваем файл
                response = requests.get(full_url)
                response.raise_for_status()
                
                # Сохраняем файл
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                # Обновляем src в HTML
                link[src_attr] = os.path.join('assets', filename)
            except Exception as e:
                print(f"Ошибка при сохранении ресурса {src}: {e}")
        
        # Обновляем HTML в page_data
        page_data['content_html'] = str(soup)
    
    def save_results(self, results, output_dir):
        """
        Сохраняет результаты парсинга в HTML-файлы.
        
        Args:
            results: Словарь с результатами парсинга
            output_dir: Директория для сохранения файлов
            
        Returns:
            list: Список путей к сохраненным файлам
        """
        saved_files = []
        
        # Создаем директорию для ассетов
        assets_dir = os.path.join(output_dir, 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        
        for url, page_data in results.items():
            # Создаем имя файла из URL
            filename = re.sub(r'[^\w\-]', '_', url) + '.html'
            output_path = os.path.join(output_dir, filename)
            
            # Сохраняем файл
            saved_file = self.export_page(page_data, output_path, assets_dir)
            saved_files.append(saved_file)
        
        # Создаем индексный файл
        index_path = os.path.join(output_dir, 'index.html')
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Документация - Индекс</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
                    h1 {{ border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    ul {{ list-style-type: none; padding: 0; }}
                    li {{ margin-bottom: 10px; }}
                    a {{ text-decoration: none; color: #0366d6; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <h1>Документация - Индекс</h1>
                <ul>
                    {
                        ''.join(
                            f'<li><a href="{re.sub(r"[^\w\-]", "_", url)}.html">{page_data.get("title", url)}</a></li>'
                            for url, page_data in sorted(results.items(), key=lambda x: x[1].get('title', x[0]))
                        )
                    }
                </ul>
            </body>
            </html>
            """)
        
        saved_files.append(index_path)
        
        return saved_files


class ZipExporter:
    """
    Экспортер для формата ZIP.
    """
    
    def __init__(self, config=None):
        """
        Инициализация экспортера.
        
        Args:
            config: Словарь с настройками
        """
        self.config = config or {}
        self.html_exporter = HtmlExporter(config)
    
    def export_to_zip(self, results, output_path):
        """
        Экспортирует результаты парсинга в ZIP-архив.
        
        Args:
            results: Словарь с результатами парсинга
            output_path: Путь для сохранения ZIP-архива
            
        Returns:
            str: Путь к сохраненному архиву
        """
        # Создаем временную директорию
        temp_dir = output_path + '_temp'
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Сохраняем HTML-файлы
            self.html_exporter.save_results(results, temp_dir)
            
            # Создаем ZIP-архив
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            return output_path
        finally:
            # Удаляем временную директорию
            shutil.rmtree(temp_dir, ignore_errors=True)
