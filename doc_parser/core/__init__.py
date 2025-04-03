#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основные компоненты парсера документации.
"""

from doc_parser.core.parser import DocumentationParser
from doc_parser.core.profiles import SiteProfile, registry, detect_site_profile
from doc_parser.core.extraction import ContentExtractor, ContentProcessor

__all__ = [
    'DocumentationParser',
    'SiteProfile',
    'registry',
    'detect_site_profile',
    'ContentExtractor',
    'ContentProcessor'
]
