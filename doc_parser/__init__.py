#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DocParser - Модульный парсер документации для AI-обработки.
"""

from doc_parser.core.parser import DocumentationParser
from doc_parser.core.profiles import detect_site_profile
from doc_parser.config import VERSION

__version__ = VERSION
__all__ = ['DocumentationParser', 'detect_site_profile']
