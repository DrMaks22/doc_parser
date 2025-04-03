#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Профили для общих систем документации (GitBook, Docusaurus, MkDocs).
"""

from bs4 import BeautifulSoup
from doc_parser.core.profiles import SiteProfile, registry
from doc_parser.utils.helpers import find_element


class GitBookProfile(SiteProfile):
    """
    Профиль для GitBook документации.
    """
    
    name = "gitbook"
    description = "GitBook документация"
    
    # Идентификация
    hostnames = ['gitbook.io', 'gitbook.com']
    meta_generator = ['GitBook']
    url_patterns = [r'\.gitbook\.io', r'\.gitbook\.com']
    
    # Селекторы
    content_selectors = ['.markdown-section', '.page-inner', 'article', '.content']
    navigation_selectors = ['.book-summary', '.summary', 'nav.book-summary']
    ignore_selectors = ['.page-footer', '.markdown-section > div.gitbook-plugin']
    
    def extract_content(self, soup):
        """Извлекает основной контент из GitBook страницы."""
        content = find_element(soup, self.content_selectors)
        if not content:
            return None
        
        # Очистка специфичных для GitBook элементов
        for selector in self.ignore_selectors:
            for element in content.select(selector):
                element.decompose()
        
        return content
    
    def extract_navigation(self, soup):
        """Извлекает навигацию из GitBook страницы."""
        nav = find_element(soup, self.navigation_selectors)
        return nav


class DocusaurusProfile(SiteProfile):
    """
    Профиль для Docusaurus документации.
    """
    
    name = "docusaurus"
    description = "Docusaurus документация"
    
    # Идентификация
    hostnames = ['docusaurus.io']
    meta_generator = ['Docusaurus']
    url_patterns = [r'\.docusaurus\.io']
    
    # Селекторы
    content_selectors = ['article.docusaurus-content', '.markdown', 'main article']
    navigation_selectors = ['.menu__list', 'nav.menu', '.table-of-contents']
    ignore_selectors = ['.theme-edit-this-page', '.theme-last-updated', '.docs-prevnext']
    
    def extract_content(self, soup):
        """Извлекает основной контент из Docusaurus страницы."""
        content = find_element(soup, self.content_selectors)
        if not content:
            return None
        
        # Очистка специфичных для Docusaurus элементов
        for selector in self.ignore_selectors:
            for element in content.select(selector):
                element.decompose()
        
        return content
    
    def extract_navigation(self, soup):
        """Извлекает навигацию из Docusaurus страницы."""
        nav = find_element(soup, self.navigation_selectors)
        return nav


class MkDocsProfile(SiteProfile):
    """
    Профиль для MkDocs документации.
    """
    
    name = "mkdocs"
    description = "MkDocs документация"
    
    # Идентификация
    hostnames = ['mkdocs.org']
    meta_generator = ['MkDocs']
    url_patterns = [r'\.readthedocs\.io', r'\.mkdocs\.org']
    
    # Селекторы
    content_selectors = ['.md-content__inner', 'article.md-content__inner', 'div.content']
    navigation_selectors = ['.md-sidebar__inner', '.md-sidebar--primary', 'nav.md-nav']
    ignore_selectors = ['.md-footer', '.md-footer-nav']
    
    def extract_content(self, soup):
        """Извлекает основной контент из MkDocs страницы."""
        content = find_element(soup, self.content_selectors)
        if not content:
            return None
        
        # Очистка специфичных для MkDocs элементов
        for selector in self.ignore_selectors:
            for element in content.select(selector):
                element.decompose()
        
        return content
    
    def extract_navigation(self, soup):
        """Извлекает навигацию из MkDocs страницы."""
        nav = find_element(soup, self.navigation_selectors)
        return nav


# Регистрация профилей
registry.register(GitBookProfile)
registry.register(DocusaurusProfile)
registry.register(MkDocsProfile)
