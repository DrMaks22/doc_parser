#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Профили для JavaScript-систем документации (Docsify, NextJS).
"""

from bs4 import BeautifulSoup
from doc_parser.core.profiles import SiteProfile, registry
from doc_parser.utils.helpers import find_element


class DocsifyProfile(SiteProfile):
    """
    Профиль для Docsify документации.
    """
    
    name = "docsify"
    description = "Docsify документация"
    
    # Идентификация
    hostnames = ['docsify.js.org']
    meta_generator = ['docsify']
    url_patterns = [r'\.docsify\.']
    
    # Селекторы
    content_selectors = ['.content', '#main', 'section.content']
    navigation_selectors = ['.sidebar', '.sidebar-nav', 'aside']
    ignore_selectors = ['.docsify-pagination', '.edit-link']
    
    def extract_content(self, soup):
        """Извлекает основной контент из Docsify страницы."""
        content = find_element(soup, self.content_selectors)
        if not content:
            return None
        
        # Очистка специфичных элементов
        for selector in self.ignore_selectors:
            for element in content.select(selector):
                element.decompose()
        
        return content
    
    def extract_navigation(self, soup):
        """Извлекает навигацию из Docsify страницы."""
        nav = find_element(soup, self.navigation_selectors)
        return nav


class NextJSProfile(SiteProfile):
    """
    Профиль для NextJS документации.
    """
    
    name = "nextjs"
    description = "NextJS документация"
    
    # Идентификация
    hostnames = ['nextjs.org']
    meta_generator = ['Next.js']
    url_patterns = [r'\.nextjs\.org']
    
    # Селекторы
    content_selectors = ['.docs-content', 'main', 'article', '.content']
    navigation_selectors = ['.sidebar', 'nav', '.docs-sidebar']
    ignore_selectors = ['.footer', 'footer', '.edit-page-link']
    
    def extract_content(self, soup):
        """Извлекает основной контент из NextJS страницы."""
        content = find_element(soup, self.content_selectors)
        if not content:
            return None
        
        # Очистка специфичных элементов
        for selector in self.ignore_selectors:
            for element in content.select(selector):
                element.decompose()
        
        # Удаляем распространенные в NextJS компоненты виджетов
        for attr in ['data-component', 'data-reactid']:
            for element in content.find_all(attrs={attr: True}):
                element.decompose()
        
        return content
    
    def extract_navigation(self, soup):
        """Извлекает навигацию из NextJS страницы."""
        nav = find_element(soup, self.navigation_selectors)
        return nav


# Регистрация профилей
registry.register(DocsifyProfile)
registry.register(NextJSProfile)
