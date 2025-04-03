#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Асинхронный парсер документации с поддержкой RAG.
"""

import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential
from typing import Dict, List, Optional, Set
import logging
from dataclasses import dataclass
from urllib.parse import urljoin

from doc_parser.config import DEFAULT_CONFIG
from doc_parser.utils.helpers import normalize_url, is_valid_url, is_same_domain, matches_pattern
from doc_parser.core.profiles import detect_site_profile

@dataclass
class ParsingStats:
    """Статистика парсинга."""
    total_urls: int = 0
    processed_urls: int = 0
    failed_urls: int = 0
    skipped_urls: int = 0
    start_time: float = 0
    end_time: float = 0

class AsyncDocumentationParser:
    """
    Асинхронный парсер документации с улучшенной производительностью и настройками для RAG.
    """
    
    def __init__(self, config=None):
        """Инициализация парсера с расширенной конфигурацией."""
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # Настройки для RAG
        self.rag_config = {
            'chunk_size': self.config.get('chunk_size', 1000),
            'chunk_overlap': self.config.get('chunk_overlap', 200),
            'min_chunk_size': self.config.get('min_chunk_size', 100),
            'extract_code_blocks': self.config.get('extract_code_blocks', True),
            'extract_tables': self.config.get('extract_tables', True),
            'extract_lists': self.config.get('extract_lists', True),
            'preserve_structure': self.config.get('preserve_structure', True),
        }
        
        # Улучшенные настройки парсинга
        self.parsing_config = {
            'max_concurrent_requests': self.config.get('max_concurrent_requests', 10),
            'rate_limit': self.config.get('rate_limit', 10),  # запросов в секунду
            'max_retries': self.config.get('max_retries', 3),
            'backoff_factor': self.config.get('backoff_factor', 2),
            'timeout': self.config.get('timeout', 30),
            'follow_redirects': self.config.get('follow_redirects', True),
            'verify_ssl': self.config.get('verify_ssl', True),
            'headers': self.config.get('headers', {
                'User-Agent': self.config.get('user_agent', 'DocParser/Async/2.0')
            }),
        }
        
        # Состояние парсера
        self.visited_urls: Set[str] = set()
        self.url_queue: asyncio.Queue = asyncio.Queue()
        self.results: Dict = {}
        self.stats = ParsingStats()
        self.logger = logging.getLogger('async_parser')
        
        # Семафоры для контроля конкурентности
        self.request_semaphore = asyncio.Semaphore(self.parsing_config['max_concurrent_requests'])
        self.rate_limiter = asyncio.Semaphore(self.parsing_config['rate_limit'])
    
    async def fetch_url(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Асинхронная загрузка URL с улучшенной обработкой ошибок и повторными попытками."""
        retry_config = AsyncRetrying(
            stop=stop_after_attempt(self.parsing_config['max_retries']),
            wait=wait_exponential(multiplier=self.parsing_config['backoff_factor']),
            reraise=True
        )
        
        async with self.request_semaphore:
            async with self.rate_limiter:
                try:
                    async for attempt in retry_config:
                        with attempt:
                            async with session.get(
                                url,
                                headers=self.parsing_config['headers'],
                                timeout=self.parsing_config['timeout'],
                                ssl=self.parsing_config['verify_ssl'],
                                allow_redirects=self.parsing_config['follow_redirects']
                            ) as response:
                                response.raise_for_status()
                                return await response.text()
                except Exception as e:
                    self.logger.error(f"Ошибка при загрузке {url}: {e}")
                    self.stats.failed_urls += 1
                    return None
    
    async def process_content_for_rag(self, content_html: str) -> Dict:
        """Обработка контента для RAG с сохранением структуры и метаданных."""
        soup = BeautifulSoup(content_html, 'lxml')
        result = {
            'chunks': [],
            'code_blocks': [],
            'tables': [],
            'lists': [],
            'metadata': {}
        }
        
        # Извлечение метаданных
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            if name and content:
                result['metadata'][name] = content
        
        # Разбиение на чанки с сохранением структуры
        current_chunk = []
        current_size = 0
        
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = element.get_text(strip=True)
            if not text:
                continue
            
            # Сохраняем структурные элементы
            if element.name.startswith('h'):
                if current_chunk:
                    result['chunks'].append({
                        'text': ' '.join(current_chunk),
                        'size': current_size
                    })
                    current_chunk = []
                    current_size = 0
            
            # Добавляем текст в текущий чанк
            current_chunk.append(text)
            current_size += len(text)
            
            # Если достигнут размер чанка, сохраняем его
            if current_size >= self.rag_config['chunk_size']:
                result['chunks'].append({
                    'text': ' '.join(current_chunk),
                    'size': current_size
                })
                current_chunk = []
                current_size = 0
        
        # Сохраняем последний чанк
        if current_chunk:
            result['chunks'].append({
                'text': ' '.join(current_chunk),
                'size': current_size
            })
        
        # Извлечение кода
        if self.rag_config['extract_code_blocks']:
            for code in soup.find_all(['pre', 'code']):
                result['code_blocks'].append({
                    'language': code.get('class', [''])[0].replace('language-', ''),
                    'code': code.get_text(strip=True)
                })
        
        # Извлечение таблиц
        if self.rag_config['extract_tables']:
            for table in soup.find_all('table'):
                headers = []
                rows = []
                
                # Извлечение заголовков
                for th in table.find_all('th'):
                    headers.append(th.get_text(strip=True))
                
                # Извлечение данных
                for tr in table.find_all('tr'):
                    row = []
                    for td in tr.find_all('td'):
                        row.append(td.get_text(strip=True))
                    if row:
                        rows.append(row)
                
                result['tables'].append({
                    'headers': headers,
                    'rows': rows
                })
        
        # Извлечение списков
        if self.rag_config['extract_lists']:
            for list_elem in soup.find_all(['ul', 'ol']):
                items = [li.get_text(strip=True) for li in list_elem.find_all('li')]
                result['lists'].append({
                    'type': list_elem.name,
                    'items': items
                })
        
        return result
    
    async def process_url(self, session: aiohttp.ClientSession, url: str, depth: int) -> None:
        """Асинхронная обработка URL с извлечением контента и сохранением структуры."""
        norm_url = normalize_url(url)
        if norm_url in self.visited_urls:
            self.stats.skipped_urls += 1
            return
        
        self.visited_urls.add(norm_url)
        self.stats.processed_urls += 1
        
        html_content = await self.fetch_url(session, norm_url)
        if not html_content:
            return
        
        soup = BeautifulSoup(html_content, 'lxml')
        profile = detect_site_profile(norm_url, html_content)
        
        # Используем Generic профиль если не определен конкретный
        if not profile:
            from doc_parser.profiles.ai_docs import GenericProfile
            profile = GenericProfile()
        
        content = profile.extract_content(soup)
        navigation = profile.extract_navigation(soup)
        
        # Обработка для RAG
        rag_content = await self.process_content_for_rag(str(content) if content else '')
        
        self.results[norm_url] = {
            'url': norm_url,
            'title': soup.title.text.strip() if soup.title else '',
            'content_html': str(content) if content else '',
            'navigation_html': str(navigation) if navigation else '',
            'profile': profile.name,
            'depth': depth,
            'rag_content': rag_content,
            'links': []
        }
        
        if self.config['follow_links'] and depth < self.config['max_depth']:
            links = self._extract_links(soup, norm_url)
            self.results[norm_url]['links'] = links
            
            for link in links:
                if (self.config['include_patterns'] and 
                    not matches_pattern(link, self.config['include_patterns'])):
                    continue
                if matches_pattern(link, self.config['exclude_patterns']):
                    continue
                
                await self.url_queue.put((link, depth + 1))
                self.stats.total_urls += 1
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Извлечение и фильтрация ссылок."""
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith(('#', 'javascript:', 'mailto:')):
                continue
            
            full_url = normalize_url(urljoin(base_url, href))
            if not is_valid_url(full_url) or not is_same_domain(full_url, base_url):
                continue
            
            links.append(full_url)
        return links
    
    async def worker(self, session: aiohttp.ClientSession) -> None:
        """Рабочий процесс обработки URL из очереди."""
        while True:
            try:
                url, depth = await self.url_queue.get()
                await self.process_url(session, url, depth)
                self.url_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ошибка в worker: {e}")
                self.url_queue.task_done()
    
    async def crawl(self, start_url: str) -> Dict:
        """Запуск асинхронного обхода с указанного URL."""
        self.stats = ParsingStats()
        self.stats.total_urls = 1
        
        async with aiohttp.ClientSession() as session:
            await self.url_queue.put((start_url, 0))
            
            workers = [
                asyncio.create_task(self.worker(session))
                for _ in range(self.parsing_config['max_concurrent_requests'])
            ]
            
            await self.url_queue.join()
            
            for worker in workers:
                worker.cancel()
            
            await asyncio.gather(*workers, return_exceptions=True)
        
        return self.results

# Пример использования:
# async def main():
#     parser = AsyncDocumentationParser({
#         'max_depth': 3,
#         'chunk_size': 1000,
#         'max_concurrent_requests': 10,
#         'extract_code_blocks': True,
#         'extract_tables': True,
#         'extract_lists': True,
#     })
#     results = await parser.crawl("https://docs.example.com")
