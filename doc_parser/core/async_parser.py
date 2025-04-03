import asyncio
import aiohttp
import time
from collections import deque
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed

from doc_parser.config import DEFAULT_CONFIG
from doc_parser.utils.helpers import normalize_url, is_valid_url, is_same_domain, matches_pattern
from doc_parser.core.profiles import detect_site_profile

class AsyncDocumentationParser:
    """
    Асинхронный парсер документации, использующий aiohttp и asyncio для быстрой параллельной обработки.
    """
    def __init__(self, config=None):
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # Используем набор для отслеживания посещённых URL и очередь для обработки
        self.visited_urls = set()
        self.url_queue = asyncio.Queue()
        self.results = {}
        self.semaphore = asyncio.Semaphore(self.config.get('max_concurrent', 10))
    
    async def fetch_url(self, session, url):
        """
        Асинхронно загружает страницу через aiohttp с повторными попытками.
        """
        headers = {'User-Agent': self.config['user_agent']}
        retry_policy = AsyncRetrying(stop=stop_after_attempt(self.config.get('retries', 3)),
                                     wait=wait_fixed(self.config.get('delay', 0.5)),
                                     reraise=True)
        async for attempt in retry_policy:
            with attempt:
                async with session.get(url, headers=headers, timeout=self.config['timeout']) as response:
                    response.raise_for_status()
                    return await response.text()
    
    async def parse_url(self, session, url, depth):
        """
        Асинхронно парсит URL, определяет профиль, извлекает контент и собирает ссылки для дальнейшего обхода.
        """
        norm_url = normalize_url(url)
        if norm_url in self.visited_urls:
            return
        self.visited_urls.add(norm_url)
        
        try:
            html_content = await self.fetch_url(session, norm_url)
        except Exception as e:
            print(f"Ошибка при загрузке {norm_url}: {e}")
            return
        
        soup = BeautifulSoup(html_content, 'lxml')
        profile = detect_site_profile(norm_url, html_content)
        if profile is None:
            # Если профиль не определён, используем Generic профиль
            from doc_parser.profiles.ai_docs import GenericProfile
            profile = GenericProfile()
            print(f"Профиль не определён, используем Generic профиль для {norm_url}")
        else:
            print(f"Определён профиль: {profile.name} для {norm_url}")
        
        content = profile.extract_content(soup)
        navigation = profile.extract_navigation(soup)
        
        result = {
            'url': norm_url,
            'title': soup.title.text.strip() if soup.title else '',
            'content_html': str(content) if content else '',
            'navigation_html': str(navigation) if navigation else '',
            'profile': profile.name,
            'depth': depth,
            'links': []
        }
        
        # Если разрешен обход ссылок и глубина не превышена
        if self.config['follow_links'] and depth < self.config['max_depth']:
            links = self.extract_links(soup, norm_url)
            result['links'] = links
            for link in links:
                # Фильтрация ссылок по шаблону
                if self.config['include_patterns'] and not matches_pattern(link, self.config['include_patterns']):
                    continue
                if matches_pattern(link, self.config['exclude_patterns']):
                    continue
                await self.url_queue.put((link, depth + 1))
        
        self.results[norm_url] = result
        # Краткая задержка для обхода
        await asyncio.sleep(self.config.get('delay', 0.5))
    
    def extract_links(self, soup, base_url):
        """
        Извлекает и нормализует ссылки из страницы.
        """
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            full_url = normalize_url(href, base_url)
            if not is_valid_url(full_url):
                continue
            if not is_same_domain(full_url, base_url):
                continue
            links.append(full_url)
        return links
    
    async def worker(self, session):
        """
        Рабочая корутина, которая обрабатывает URL из очереди.
        """
        while True:
            try:
                url, depth = await self.url_queue.get()
            except asyncio.CancelledError:
                break
            async with self.semaphore:
                await self.parse_url(session, url, depth)
            self.url_queue.task_done()
    
    async def crawl(self, start_url):
        """
        Запускает асинхронный обход сайта, начиная с start_url.
        """
        # Добавляем стартовый URL в очередь
        await self.url_queue.put((start_url, 0))
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(self.worker(session)) for _ in range(self.config.get('max_concurrent', 10))]
            await self.url_queue.join()
            for task in tasks:
                task.cancel()
        return self.results

# Пример использования асинхронного парсера:
# async def main():
#     parser = AsyncDocumentationParser({
#         'max_depth': 3,
#         'delay': 0.5,
#         'timeout': 30,
#         'retries': 3,
#         'user_agent': 'DocParser/Async/1.0',
#         'include_patterns': [],
#         'exclude_patterns': [],
#         'follow_links': True,
#         'max_concurrent': 10,
#         'output_dir': 'output',
#     })
#     results = await parser.crawl("https://docs.example.com")
#     print(f"Обработано URL: {len(results)}")
#
# if __name__ == '__main__':
#     asyncio.run(main())
