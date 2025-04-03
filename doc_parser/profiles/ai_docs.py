#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Профиль для AI-документации и Generic fallback.
"""

from bs4 import BeautifulSoup
from doc_parser.core.profiles import SiteProfile, registry
from doc_parser.utils.helpers import find_element, extract_text


class AiDocsProfile(SiteProfile):
    """
    Профиль для AI-документации (Claude, других AI-систем).
    """
    
    name = "ai_docs"
    description = "Документация AI-систем"
    
    # Идентификация
    hostnames = ['anthropic.com', 'claude.ai', 'openai.com']
    meta_generator = []
    url_patterns = [r'\.anthropic\.com', r'\.claude\.ai', r'\.openai\.com', r'\/docs']
    
    # Селекторы
    content_selectors = ['.content', 'main', 'article', '.documentation', '.docs-content']
    navigation_selectors = ['.sidebar', 'nav', '.navigation', '.docs-navigation']
    ignore_selectors = ['.footer', 'footer', '.header', 'header', '.feedback', '.edit-link']
    
    def extract_content(self, soup):
        """Извлекает основной контент из AI-документации."""
        content = find_element(soup, self.content_selectors)
        if not content:
            return None
        
        # Очистка специфичных элементов
        for selector in self.ignore_selectors:
            for element in content.select(selector):
                element.decompose()
        
        # Особая обработка для ссылки примеров кода
        for pre in content.find_all('pre'):
            if 'class' in pre.attrs:
                # Сохраняем класс для определения языка программирования
                language = None
                for cls in pre['class']:
                    if cls.startswith('language-'):
                        language = cls.replace('language-', '')
                        break
                
                # Удаляем все атрибуты
                pre.attrs = {}
                
                # Если нашли язык, возвращаем атрибут
                if language:
                    pre['data-language'] = language
        
        return content
    
    def extract_navigation(self, soup):
        """Извлекает навигацию из AI-документации."""
        nav = find_element(soup, self.navigation_selectors)
        return nav


class GenericProfile(SiteProfile):
    """
    Generic профиль с эвристиками для любой документации.
    """
    
    name = "generic"
    description = "Универсальный профиль для любой документации"
    
    # Идентификация (всегда будет последним вариантом)
    hostnames = []
    meta_generator = []
    url_patterns = []
    
    # Селекторы (широкий набор)
    content_selectors = [
        'article', 'main', '.content', '.markdown-body', '.markdown-section', 
        '.documentation', '.docs-content', '.post-content', '.entry-content',
        'div[role="main"]', '.container main', 'div.body', '#content'
    ]
    
    navigation_selectors = [
        '.sidebar', '.table-of-contents', '.menu', 'nav', '.navigation',
        'aside', '.toc', '#toc', '.nav-wrapper', 'ul.summary',
        '.sphinx-sidebar', '#sidebar'
    ]
    
    ignore_selectors = [
        'footer', 'header', '.admonition', '.github-fork-ribbon', '.edit-link', 
        '.feedback', '.page-footer', 'script', 'style', '.navigation', 
        '.page-nav', '.next-prev-links', '.disqus', '#disqus_thread',
        '.comments', '.article-footer', '.sharing', '.related-posts'
    ]
    
    def extract_content(self, soup):
        """
        Извлекает основной контент из страницы с использованием эвристик.
        """
        # Пробуем найти по селекторам
        content = find_element(soup, self.content_selectors)
        if content:
            return self.clean_content(content)
        
        # Пробуем найти по эвристике - наиболее насыщенный текстом блок
        return self._find_richest_content(soup)
    
    def extract_navigation(self, soup):
        """Извлекает навигацию из страницы с использованием эвристик."""
        # Пробуем найти по селекторам
        nav = find_element(soup, self.navigation_selectors)
        if nav:
            return nav
        
        # Пробуем найти по эвристике - блок со ссылками на другие разделы
        return self._find_navigation_by_links(soup)
    
    def _find_richest_content(self, soup):
        """
        Находит блок с наибольшим количеством полезного текста.
        
        Args:
            soup: BeautifulSoup объект
            
        Returns:
            BeautifulSoup элемент с найденным контентом или None
        """
        # Исключаем заведомо не содержательные элементы
        for selector in self.ignore_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Оцениваем все div-ы
        candidates = []
        for div in soup.find_all(['div', 'section', 'article']):
            # Пропускаем явно служебные блоки
            skip = False
            for attr in ['id', 'class', 'role']:
                if attr in div.attrs:
                    value = div[attr]
                    if isinstance(value, list):
                        value = ' '.join(value)
                    
                    if any(term in value.lower() for term in ['nav', 'menu', 'footer', 'header', 'sidebar']):
                        skip = True
                        break
            
            if skip:
                continue
            
            # Подсчитываем текст, заголовки и параграфы
            text_len = len(extract_text(str(div)))
            headers = len(div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
            paragraphs = len(div.find_all('p'))
            
            # Если есть достаточно контента
            if text_len > 100 and (headers > 0 or paragraphs > 1):
                score = text_len + headers * 50 + paragraphs * 10
                candidates.append((div, score))
        
        # Если есть кандидаты, возвращаем лучший
        if candidates:
            best_div = max(candidates, key=lambda x: x[1])[0]
            return best_div
        
        # Возвращаем копию body, если ничего не нашли
        return soup.body
    
    def _find_navigation_by_links(self, soup):
        """
        Находит блок с навигацией по эвристике - много ссылок в маленьком блоке.
        
        Args:
            soup: BeautifulSoup объект
            
        Returns:
            BeautifulSoup элемент с навигацией или None
        """
        nav_candidates = []
        
        # Ищем блоки с высокой плотностью ссылок
        for element in soup.find_all(['div', 'nav', 'aside', 'ul']):
            links = element.find_all('a')
            if not links:
                continue
            
            # Длина текста и количество ссылок
            text_len = len(extract_text(str(element)))
            link_count = len(links)
            
            # Оцениваем плотность ссылок
            if text_len > 0 and link_count > 3:
                link_density = link_count / text_len
                
                # Проверяем, являются ли ссылки навигационными (короткий текст)
                nav_links = 0
                for link in links:
                    link_text = link.get_text().strip()
                    if len(link_text) < 30:
                        nav_links += 1
                
                nav_ratio = nav_links / link_count if link_count > 0 else 0
                
                if link_density > 0.1 and nav_ratio > 0.7:
                    score = link_count * link_density * nav_ratio
                    nav_candidates.append((element, score))
        
        # Находим элемент с наилучшим показателем
        if nav_candidates:
            return max(nav_candidates, key=lambda x: x[1])[0]
        
        return None


# Регистрация профилей
registry.register(AiDocsProfile)
registry.register(GenericProfile)
