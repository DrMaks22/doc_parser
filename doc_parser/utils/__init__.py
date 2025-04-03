#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Вспомогательные функции для парсера документации.
"""

from doc_parser.utils.helpers import (
    setup_logger, normalize_url, is_same_domain, is_valid_url, matches_pattern,
    clean_html, extract_text, find_element, get_meta_tag, get_title
)

__all__ = [
    'setup_logger',
    'normalize_url',
    'is_same_domain',
    'is_valid_url',
    'matches_pattern',
    'clean_html',
    'extract_text',
    'find_element',
    'get_meta_tag',
    'get_title'
]
