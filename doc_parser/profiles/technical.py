#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Профили для технических систем документации (ReadTheDocs, VuePress, Hugo).
"""

from bs4 import BeautifulSoup
from doc_parser.core.profiles import SiteProfile, registry
from doc_parser.utils.helpers import find_element


class ReadTheDocsProfile(SiteProfile):
    """
    Профиль для ReadTheDocs (Sphinx) документации.
    """
    
    name = "readthedocs"
    description = "ReadTheDocs (Sphinx) документация"
    
    # Идентификация
    hostnames = ['readthedocs.io', 'readthedocs.org']
    meta_generator = ['Sphinx']
    url_patterns = [r'\.readthedocs\.io', r'\.readthedocs\.org']
    
    # Селекторы
    content_selectors = ['.document', '.body', 'div[role="main"]', '.rst-content']
    navigation_selectors = ['.wy-nav-side', '.sphinxsidebar', 'nav.wy-nav-side']
    ignore_selectors = ['.rst-footer-buttons', '.sourcelink', '.headerlink', '.viewcode-link']
    
    def extract_content(self, soup):
        """Извлекает основной контент из ReadTheDocs страницы."""
        content = find_element(soup, self.content_selectors)
        if not content:
            return None
        
        # Очистка специфичных элементов
        for selector in self.ignore_selectors:
            for element in content.select(selector):
                element.decompose()
        
        # Удаляем атрибуты стиля из <pre> и <code>
        for elem in content.select('pre, code'):
            if 'style' in elem.attrs:
                del elem['style']
        
        return content
    
    def extract_navigation(self, soup):
        """Извлекает навигацию из ReadTheDocs страницы."""
        nav = find_element(soup, self.navigation_selectors)
        
        # Очистка ссылок от лишних атрибутов
        if nav:
            for a in nav.find_all('a'):
                if 'class' in a.attrs:
                    del a['class']
        
        return nav


class VuePressProfile(SiteProfile):
    """
    Профиль для VuePress документации.
    """
    
    name = "vuepress"
    description = "VuePress документация"
    
    # Идентификация
    hostnames = ['vuepress.vuejs.org']
    meta_generator = ['VuePress']
    url_patterns = [r'\.vuepress\.']
    
    # Селекторы
    content_selectors = ['.theme-default-content', '.content', 'main.page']
    navigation_selectors = ['.sidebar', '.sidebar-links', 'aside.sidebar']
    ignore_selectors = ['.page-edit', '.page-nav', '.edit-link', '.last-updated']
    
    def extract_content(self, soup):
        """Извлекает основной контент из VuePress страницы."""
        content = find_element(soup, self.content_selectors)
        if not content:
            return None
        
        # Очистка специфичных для VuePress элементов
        for selector in self.ignore_selectors:
            for element in content.select(selector):
                element.decompose()
        
        return content
    
    def extract_navigation(self, soup):
        """Извлекает навигацию из VuePress страницы."""
        nav = find_element(soup, self.navigation_selectors)
        return nav


class HugoProfile(SiteProfile):
    """
    Профиль для Hugo документации.
    """
    
    name = "hugo"
    description = "Hugo документация"
    
    # Идентификация
    hostnames = ['gohugo.io']
    meta_generator = ['Hugo']
    url_patterns = [r'\.gohugo\.io']
    
    # Селекторы
    content_selectors = ['.content', 'main', 'article.content']
    navigation_selectors = ['.menu', 'nav.menu', '.sidebar']
    ignore_selectors = ['.footer', 'footer', '.edit-page']
    
    def extract_content(self, soup):
        """Извлекает основной контент из Hugo страницы."""
        content = find_element(soup, self.content_selectors)
        if not content:
            return None
        
        # Очистка специфичных элементов
        for selector in self.ignore_selectors:
            for element in content.select(selector):
                element.decompose()
        
        return content
    
    def extract_navigation(self, soup):
        """Извлекает навигацию из Hugo страницы."""
        nav = find_element(soup, self.navigation_selectors)
        return nav


# Регистрация профилей
registry.register(ReadTheDocsProfile)
registry.register(VuePressProfile)
registry.register(HugoProfile)
