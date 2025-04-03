#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Система профилей для разных типов документации.
"""

import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from doc_parser.utils.helpers import get_meta_tag, get_domain

class SiteProfile:
    """
    Базовый класс для профилей сайтов документации.
    Определяет селекторы и методы извлечения контента.
    """
    
    name = "base"
    description = "Базовый профиль"
    
    # Идентификация
    hostnames = []
    meta_generator = []
    url_patterns = []
    
    # Селекторы
    content_selectors = []
    navigation_selectors = []
    ignore_selectors = []
    
    def __init__(self):
        """Инициализация профиля."""
        pass
    
    def matches(self, url, soup=None):
        """
        Проверяет, соответствует ли URL и страница данному профилю.
        
        Args:
            url: URL страницы
            soup: BeautifulSoup объект страницы (опционально)
            
        Returns:
            bool: True если соответствует, иначе False
        """
        # Проверка по hostname
        hostname = get_domain(url)
        if self.hostnames and any(h in hostname for h in self.hostnames):
            return True
        
        # Проверка по URL паттернам
        if self.url_patterns and any(re.search(p, url) for p in self.url_patterns):
            return True
        
        # Если soup доступен, проверяем meta generator
        if soup and self.meta_generator:
            generator = get_meta_tag(soup, 'generator')
            if generator and any(g in generator for g in self.meta_generator):
                return True
        
        return False
    
    def get_content_selectors(self):
        """Возвращает селекторы для основного контента."""
        return self.content_selectors
    
    def get_navigation_selectors(self):
        """Возвращает селекторы для навигации."""
        return self.navigation_selectors
    
    def get_ignore_selectors(self):
        """Возвращает селекторы для игнорируемых элементов."""
        return self.ignore_selectors
    
    def extract_content(self, soup):
        """
        Извлекает основной контент из страницы.
        
        Args:
            soup: BeautifulSoup объект
            
        Returns:
            BeautifulSoup объект с контентом или None
        """
        # Реализация в конкретных профилях
        pass
    
    def extract_navigation(self, soup):
        """
        Извлекает навигацию из страницы.
        
        Args:
            soup: BeautifulSoup объект
            
        Returns:
            BeautifulSoup объект с навигацией или None
        """
        # Реализация в конкретных профилях
        pass
    
    def clean_content(self, content):
        """
        Очищает извлеченный контент от нежелательных элементов.
        
        Args:
            content: BeautifulSoup объект
            
        Returns:
            BeautifulSoup объект очищенного контента
        """
        if not content:
            return None
        
        # Удаляем игнорируемые элементы
        for selector in self.get_ignore_selectors():
            for element in content.select(selector):
                element.decompose()
        
        return content


# Реестр профилей
class ProfileRegistry:
    """
    Реестр профилей для разных типов документации.
    """
    
    def __init__(self):
        """Инициализация реестра."""
        self.profiles = {}
    
    def register(self, profile_class):
        """
        Регистрирует профиль в реестре.
        
        Args:
            profile_class: Класс профиля
        """
        profile = profile_class()
        self.profiles[profile.name] = profile
    
    def get_profile(self, name):
        """
        Возвращает профиль по имени.
        
        Args:
            name: Имя профиля
            
        Returns:
            SiteProfile объект или None
        """
        return self.profiles.get(name)
    
    def detect_profile(self, url, soup):
        """
        Определяет профиль для URL и страницы.
        
        Args:
            url: URL страницы
            soup: BeautifulSoup объект
            
        Returns:
            SiteProfile объект или None
        """
        for profile in self.profiles.values():
            if profile.matches(url, soup):
                return profile
        
        # Если не найден конкретный профиль, используем generic
        return self.get_profile('generic')
    
    def get_all_profiles(self):
        """Возвращает список всех профилей."""
        return list(self.profiles.values())


# Глобальный реестр профилей
registry = ProfileRegistry()

# Функция для автоматического определения профиля
def detect_site_profile(url, html_content):
    """
    Определяет профиль сайта по URL и HTML-контенту.
    
    Args:
        url: URL страницы
        html_content: HTML-контент страницы
        
    Returns:
        SiteProfile объект
    """
    soup = BeautifulSoup(html_content, 'lxml')
    return registry.detect_profile(url, soup)
