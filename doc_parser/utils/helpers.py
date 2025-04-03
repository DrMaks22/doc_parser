#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Вспомогательные функции для парсера документации.
"""

import logging
import os
import re
import urllib.parse
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Настройка логгера
def setup_logger(name, level=logging.INFO):
    """Настраивает и возвращает логгер с заданным именем и уровнем."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Утилиты для URL
def normalize_url(url, base_url=None):
    """
    Нормализует URL, добавляя базовый URL если необходимо и удаляя фрагменты.
    """
    if base_url:
        url = urljoin(base_url, url)
    
    parsed = urlparse(url)
    normalized = parsed._replace(fragment='').geturl()
    return normalized

def is_same_domain(url1, url2):
    """Проверяет, принадлежат ли два URL одному домену."""
    return urlparse(url1).netloc == urlparse(url2).netloc

def get_domain(url):
    """Возвращает домен URL."""
    return urlparse(url).netloc

def is_valid_url(url):
    """Проверяет, является ли URL допустимым."""
    parsed = urlparse(url)
    return bool(parsed.netloc and parsed.scheme in ['http', 'https'])

def matches_pattern(url, patterns):
    """Проверяет, соответствует ли URL какому-либо из регулярных выражений."""
    if not patterns:
        return False
    return any(re.search(pattern, url) for pattern in patterns)

# Утилиты для HTML
def clean_html(html_content):
    """Очищает HTML от ненужных элементов."""
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Удаление скриптов и стилей
    for tag in soup(['script', 'style']):
        tag.decompose()
    
    return str(soup)

def extract_text(html_content):
    """Извлекает чистый текст из HTML."""
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Удаление всех скриптов и стилей
    for tag in soup(['script', 'style']):
        tag.decompose()
    
    # Получение текста
    text = soup.get_text(separator=' ', strip=True)
    
    # Очистка пробелов
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def find_element(soup, selectors):
    """
    Находит первый элемент, соответствующий одному из селекторов.
    
    Args:
        soup: BeautifulSoup объект
        selectors: Список CSS селекторов
        
    Returns:
        BeautifulSoup элемент или None
    """
    for selector in selectors:
        if '.' in selector and not selector.startswith('.'):
            # Это не CSS селектор, а тег с классом
            tag, class_name = selector.split('.', 1)
            element = soup.find(tag, class_=class_name)
        elif selector.startswith('.'):
            # CSS селектор класса
            element = soup.select_one(selector)
        else:
            # Просто тег
            element = soup.find(selector)
        
        if element:
            return element
    
    return None

def get_meta_tag(soup, name):
    """Получает значение мета-тега по имени."""
    meta = soup.find('meta', attrs={'name': name})
    if meta:
        return meta.get('content', '')
    return ''

def get_title(soup):
    """Получает заголовок страницы."""
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.text.strip()
    return ''
