#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Профили для различных систем документации.
"""

# Импорты для регистрации профилей
from doc_parser.profiles import common
from doc_parser.profiles import technical
from doc_parser.profiles import js_based
from doc_parser.profiles import ai_docs

# Импорт отдельных профилей для удобства использования
from doc_parser.profiles.common import GitBookProfile, DocusaurusProfile, MkDocsProfile
from doc_parser.profiles.technical import ReadTheDocsProfile, VuePressProfile, HugoProfile
from doc_parser.profiles.js_based import DocsifyProfile, NextJSProfile
from doc_parser.profiles.ai_docs import AiDocsProfile, GenericProfile

__all__ = [
    'GitBookProfile',
    'DocusaurusProfile',
    'MkDocsProfile',
    'ReadTheDocsProfile',
    'VuePressProfile',
    'HugoProfile',
    'DocsifyProfile',
    'NextJSProfile',
    'AiDocsProfile',
    'GenericProfile'
]
