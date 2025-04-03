#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Интерфейсы для парсера документации (GUI, API, WebUI).
"""

from doc_parser.interface.app import run_app
from doc_parser.interface.api import start_server
from doc_parser.interface.webui import run_webui

__all__ = ['run_app', 'start_server', 'run_webui']
