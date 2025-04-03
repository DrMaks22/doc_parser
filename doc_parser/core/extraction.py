#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для извлечения и обработки контента документации.
"""

import re
from bs4 import BeautifulSoup

from doc_parser.utils.helpers import (
    find_element, extract_text, get_meta_tag, get_title
)


class ContentExtractor:
    """
    Класс для извлечения и обработки контента документации.
    """
    
    def __init__(self, site_profile):
        """
        Инициализация экстрактора с профилем сайта.
        
        Args:
            site_profile: Профиль сайта (SiteProfile объект)
        """
        self.profile = site_profile
    
    def extract_content(self, soup):
        """
        Извлекает основной контент страницы.
        
        Args:
            soup: BeautifulSoup объект
            
        Returns:
            BeautifulSoup объект с контентом или None
        """
        # Используем selectors из профиля
        selectors = self.profile.get_content_selectors()
        content = find_element(soup, selectors)
        
        if not content:
            # Fallback: ищем по эвристике - самый большой текстовый блок
            main_content = self._find_main_content(soup)
            if main_content:
                return main_content
            
            # Если не нашли, возвращаем копию всей страницы
            return BeautifulSoup(str(soup), 'lxml')
        
        # Очищаем контент от нежелательных элементов
        return self.profile.clean_content(content)
    
    def extract_navigation(self, soup):
        """
        Извлекает навигацию страницы.
        
        Args:
            soup: BeautifulSoup объект
            
        Returns:
            BeautifulSoup объект с навигацией или None
        """
        # Используем selectors из профиля
        selectors = self.profile.get_navigation_selectors()
        return find_element(soup, selectors)
    
    def extract_metadata(self, soup, url):
        """
        Извлекает метаданные страницы.
        
        Args:
            soup: BeautifulSoup объект
            url: URL страницы
            
        Returns:
            dict: Словарь с метаданными
        """
        metadata = {
            'title': get_title(soup),
            'description': get_meta_tag(soup, 'description'),
            'keywords': get_meta_tag(soup, 'keywords'),
            'author': get_meta_tag(soup, 'author'),
            'generator': get_meta_tag(soup, 'generator'),
            'url': url,
        }
        
        # Добавляем OpenGraph метаданные
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            if tag.get('property') and tag.get('content'):
                property_name = tag['property'][3:]  # Убираем 'og:'
                metadata[f'og_{property_name}'] = tag['content']
        
        return metadata
    
    def _find_main_content(self, soup):
        """
        Эвристически находит основной контент страницы.
        
        Args:
            soup: BeautifulSoup объект
            
        Returns:
            BeautifulSoup объект с найденным контентом или None
        """
        # Приоритет тегов для поиска
        priority_tags = ['main', 'article', 'div.content', 'div.main', 'div.body']
        
        for tag in priority_tags:
            if '.' in tag:
                tag_name, class_name = tag.split('.')
                elements = soup.find_all(tag_name, class_=class_name)
            else:
                elements = soup.find_all(tag)
            
            if elements:
                # Выбираем элемент с наибольшим количеством текста
                max_text_len = 0
                best_element = None
                
                for element in elements:
                    text_len = len(extract_text(str(element)))
                    if text_len > max_text_len:
                        max_text_len = text_len
                        best_element = element
                
                return best_element
        
        # Если ничего не нашли, ищем div с максимальным количеством текста
        divs = soup.find_all('div')
        max_text_len = 0
        best_div = None
        
        for div in divs:
            text_len = len(extract_text(str(div)))
            if text_len > max_text_len:
                # Проверяем, что это не обёртка всей страницы
                if len(div.find_all('div')) < len(soup.find_all('div')) / 2:
                    max_text_len = text_len
                    best_div = div
        
        return best_div


class ContentProcessor:
    """
    Класс для постобработки извлеченного контента.
    """
    
    def __init__(self):
        """Инициализация процессора."""
        pass
    
    def cleanup(self, html_content):
        """
        Очищает HTML-контент от лишних элементов.
        
        Args:
            html_content: HTML-контент в виде строки
            
        Returns:
            str: Очищенный HTML-контент
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Удаляем скрипты и стили
        for tag in soup(['script', 'style', 'iframe', 'noscript']):
            tag.decompose()
        
        # Удаляем атрибуты оформления
        for tag in soup.find_all(True):
            for attr in list(tag.attrs):
                if attr in ['style', 'class', 'id', 'onclick', 'onload']:
                    del tag[attr]
        
        return str(soup)
    
    def structure(self, html_content):
        """
        Структурирует HTML-контент (добавляет якоря к заголовкам и т.п.).
        
        Args:
            html_content: HTML-контент в виде строки
            
        Returns:
            str: Структурированный HTML-контент
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Добавляем id к заголовкам
        for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for idx, tag in enumerate(soup.find_all(tag_name)):
                if not tag.get('id'):
                    # Генерируем id из текста заголовка
                    text = tag.get_text().strip()
                    slug = re.sub(r'[^\w\s-]', '', text.lower())
                    slug = re.sub(r'[\s-]+', '-', slug)
                    tag['id'] = f"{slug}-{idx}"
        
        return str(soup)
    
    def add_metadata(self, html_content, metadata):
        """
        Добавляет метаданные в HTML-контент.
        
        Args:
            html_content: HTML-контент в виде строки
            metadata: Словарь с метаданными
            
        Returns:
            str: HTML-контент с добавленными метаданными
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Создаем секцию с метаданными
        meta_div = soup.new_tag('div')
        meta_div['class'] = 'doc-metadata'
        meta_div['style'] = 'display: none;'
        
        for key, value in metadata.items():
            meta_item = soup.new_tag('meta')
            meta_item['name'] = f"doc-{key}"
            meta_item['content'] = value
            meta_div.append(meta_item)
        
        # Добавляем в начало документа
        if soup.body:
            soup.body.insert(0, meta_div)
        else:
            soup.append(meta_div)
        
        return str(soup)
