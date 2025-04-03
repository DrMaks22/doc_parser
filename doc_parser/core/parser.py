#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный модуль парсера документации.
"""

import os
import time
import requests
from collections import deque
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed

from doc_parser.config import DEFAULT_CONFIG
from doc_parser.utils.helpers import (
    setup_logger, normalize_url, is_same_domain, 
    is_valid_url, matches_pattern
)
from doc_parser.core.profiles import detect_site_profile


class DocumentationParser:
    """
    Основной класс парсера документации, который обрабатывает URL и извлекает контент.
    """
    
    def __init__(self, config=None):
        """
        Инициализация парсера с конфигурацией.
        
        Args:
            config: Словарь с конфигурацией или None для использования DEFAULT_CONFIG
        """
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        self.logger = setup_logger('doc_parser', self.config['log_level'])
        self.visited_urls = set()
        self.queue = deque()
        self.results = {}
        
        # Создаем директорию для результатов, если её нет
        os.makedirs(self.config['output_dir'], exist_ok=True)
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def fetch_url(self, url):
        """
        Загружает страницу по URL с настройками из конфигурации.
        
        Args:
            url: URL для загрузки
            
        Returns:
            Текст страницы или None в случае ошибки
        """
        try:
            headers = {'User-Agent': self.config['user_agent']}
            response = requests.get(
                url, 
                headers=headers, 
                timeout=self.config['timeout']
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке {url}: {e}")
            return None
    
    def parse_url(self, url, depth=0):
        """
        Парсит URL и извлекает контент, метаданные и ссылки.
        
        Args:
            url: URL для парсинга
            depth: Текущая глубина обхода
            
        Returns:
            dict: Словарь с результатами парсинга
        """
        self.logger.info(f"Парсинг URL: {url} (глубина: {depth})")
        
        # Нормализуем URL
        url = normalize_url(url)
        
        # Проверяем, не посещали ли мы уже этот URL
        if url in self.visited_urls:
            self.logger.debug(f"URL уже посещен: {url}")
            return None
        
        # Добавляем URL в список посещенных
        self.visited_urls.add(url)
        
        # Загружаем страницу
        html_content = self.fetch_url(url)
        if not html_content:
            return None
        
        # Создаем BeautifulSoup объект
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Определяем профиль сайта
        profile = detect_site_profile(url, html_content)
        if profile is None:
            # Если профиль не определен, используем Generic профиль
            from doc_parser.profiles.ai_docs import GenericProfile
            profile = GenericProfile()
            self.logger.info(f"Профиль не определен, используем Generic профиль")
        else:
            self.logger.info(f"Определен профиль сайта: {profile.name}")
        
        # Извлекаем контент
        content = profile.extract_content(soup)
        
        # Извлекаем навигацию
        navigation = profile.extract_navigation(soup)
        
        # Результаты парсинга
        result = {
            'url': url,
            'title': soup.title.text.strip() if soup.title else '',
            'content_html': str(content) if content else '',
            'navigation_html': str(navigation) if navigation else '',
            'profile': profile.name,
            'depth': depth,
            'links': []
        }
        
        # Обрабатываем ссылки, если нужно
        if self.config['follow_links'] and depth < self.config['max_depth']:
            links = self.extract_links(soup, url)
            result['links'] = links
            
            # Добавляем ссылки в очередь
            for link in links:
                # Проверяем, подходит ли ссылка по шаблонам
                if self.config['include_patterns'] and not matches_pattern(link, self.config['include_patterns']):
                    continue
                if matches_pattern(link, self.config['exclude_patterns']):
                    continue
                
                # Добавляем в очередь
                self.queue.append((link, depth + 1))
        
        # Сохраняем результат
        self.results[url] = result
        
        # Задержка перед следующим запросом
        time.sleep(self.config['delay'])
        
        return result
    
    def extract_links(self, soup, base_url):
        """
        Извлекает ссылки из страницы, которые подходят для обхода.
        
        Args:
            soup: BeautifulSoup объект
            base_url: Базовый URL для относительных ссылок
            
        Returns:
            list: Список нормализованных URL
        """
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Пропускаем якоря, javascript и mailto
            if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            
            # Нормализуем URL
            full_url = normalize_url(href, base_url)
            
            # Проверяем, что URL валидный
            if not is_valid_url(full_url):
                continue
            
            # Проверяем, что URL принадлежит тому же домену
            if not is_same_domain(full_url, base_url):
                continue
            
            links.append(full_url)
        
        return links
    
    def crawl(self, start_url):
        """
        Обходит сайт документации, начиная с указанного URL.
        
        Args:
            start_url: Начальный URL
            
        Returns:
            dict: Словарь с результатами парсинга для всех посещенных URL
        """
        self.logger.info(f"Начало обхода с URL: {start_url}")
        
        # Очищаем состояние
        self.visited_urls = set()
        self.queue = deque([(start_url, 0)])
        self.results = {}
        
        # Обходим все URL в очереди
        while self.queue:
            url, depth = self.queue.popleft()
            self.parse_url(url, depth)
        
        self.logger.info(f"Обход завершен. Обработано URL: {len(self.results)}")
        
        return self.results
