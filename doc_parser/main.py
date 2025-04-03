#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный модуль парсера документации.
"""

import os
import sys
import argparse
import time
from rich.console import Console
from rich.progress import Progress

from doc_parser.config import DEFAULT_CONFIG
from doc_parser.core.parser import DocumentationParser
from doc_parser.exporters.text_formats import MarkdownExporter, JsonExporter, CsvExporter
from doc_parser.exporters.ai_formats import ClaudeExporter
from doc_parser.exporters.web_formats import HtmlExporter, ZipExporter
from doc_parser.utils.helpers import setup_logger


def parse_args():
    """Разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description='Парсер документации для AI-обработки'
    )
    
    # Создаем подкоманды
    subparsers = parser.add_subparsers(dest='command', help='Режим работы')
    
    # Подкоманда parse для парсинга из командной строки
    parse_parser = subparsers.add_parser('parse', help='Парсинг URL из командной строки')
    parse_parser.add_argument('url', help='URL документации для парсинга')
    
    parse_parser.add_argument(
        '-o', '--output-dir',
        help='Директория для результатов (по умолчанию: output)',
        default='output'
    )
    
    parse_parser.add_argument(
        '-f', '--format',
        help='Формат вывода (markdown, json, csv, claude, html, zip)',
        default='markdown'
    )
    
    parse_parser.add_argument(
        '-d', '--max-depth',
        help='Максимальная глубина обхода (по умолчанию: 3)',
        type=int,
        default=3
    )
    
    parse_parser.add_argument(
        '--delay',
        help='Задержка между запросами в секундах (по умолчанию: 0.5)',
        type=float,
        default=0.5
    )
    
    parse_parser.add_argument(
        '--timeout',
        help='Таймаут запроса в секундах (по умолчанию: 30)',
        type=int,
        default=30
    )
    
    parse_parser.add_argument(
        '--user-agent',
        help='User-Agent для запросов (по умолчанию: DocParser/1.0)',
        default='DocParser/1.0'
    )
    
    parse_parser.add_argument(
        '--include',
        help='Регулярное выражение для включения URL',
        action='append',
        default=[]
    )
    
    parse_parser.add_argument(
        '--exclude',
        help='Регулярное выражение для исключения URL',
        action='append',
        default=[]
    )
    
    parse_parser.add_argument(
        '--no-follow',
        help='Не следовать по ссылкам',
        action='store_true'
    )
    
    parse_parser.add_argument(
        '--save-assets',
        help='Сохранять ассеты (изображения, CSS, JS)',
        action='store_true'
    )
    
    parse_parser.add_argument(
        '--log-level',
        help='Уровень логирования (DEBUG, INFO, WARNING, ERROR)',
        default='INFO'
    )
    
    # Подкоманда gui для запуска GUI
    gui_parser = subparsers.add_parser('gui', help='Запуск GUI приложения')
    
    # Подкоманда api для запуска API сервера
    api_parser = subparsers.add_parser('api', help='Запуск API сервера')
    api_parser.add_argument(
        '--host',
        help='Хост для API сервера (по умолчанию: 0.0.0.0)',
        default='0.0.0.0'
    )
    api_parser.add_argument(
        '--port',
        help='Порт для API сервера (по умолчанию: 8000)',
        type=int,
        default=8000
    )
    
    # Подкоманда webui для запуска веб-интерфейса
    webui_parser = subparsers.add_parser('webui', help='Запуск веб-интерфейса')
    webui_parser.add_argument(
        '--host',
        help='Хост для веб-интерфейса (по умолчанию: 0.0.0.0)',
        default='0.0.0.0'
    )
    webui_parser.add_argument(
        '--port',
        help='Порт для веб-интерфейса (по умолчанию: 5000)',
        type=int,
        default=5000
    )
    
    return parser.parse_args()


def main():
    """Основная функция программы."""
    # Разбор аргументов
    args = parse_args()
    
    # Если команда не указана, используем 'parse' по умолчанию
    if not args.command:
        print("Ошибка: команда не указана")
        print("Используйте одну из команд: parse, gui, api, webui")
        sys.exit(1)
    
    # Выбор режима работы
    if args.command == 'gui':
        run_gui()
        return
    elif args.command == 'api':
        run_api(args.host, args.port)
        return
    elif args.command == 'webui':
        run_webui(args.host, args.port)
        return
    
    # Режим командной строки (parse)
    # Настройка консоли
    console = Console()
    
    # Приветствие
    console.print(f"[bold blue]DocParser v0.1.0[/bold blue]")
    console.print(f"URL: [green]{args.url}[/green]")
    console.print(f"Формат вывода: [green]{args.format}[/green]")
    console.print(f"Глубина обхода: [green]{args.max_depth}[/green]")
    console.print()
    
    # Настройка конфигурации
    config = {
        'max_depth': args.max_depth,
        'delay': args.delay,
        'timeout': args.timeout,
        'user_agent': args.user_agent,
        'include_patterns': args.include,
        'exclude_patterns': args.exclude,
        'follow_links': not args.no_follow,
        'save_assets': args.save_assets,
        'output_format': args.format,
        'output_dir': args.output_dir,
        'log_level': args.log_level,
    }
    
    # Создаем директорию для результатов
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Создаем парсер
        parser = DocumentationParser(config)
        
        # Запускаем обход
        start_time = time.time()
        console.print("[bold]Обход документации...[/bold]")
        results = parser.crawl(args.url)
        elapsed = time.time() - start_time
        
        console.print(f"[bold green]Обход завершен![/bold green] Обработано URL: {len(results)}")
        console.print(f"Время выполнения: {elapsed:.2f} секунд")
        
        # Экспорт результатов
        console.print("[bold]Экспорт результатов...[/bold]")
        
        if args.format == 'markdown':
            exporter = MarkdownExporter(config)
            saved_files = exporter.save_results(results, args.output_dir)
            console.print(f"[bold green]Результаты сохранены в формате Markdown![/bold green]")
            
        elif args.format == 'json':
            exporter = JsonExporter(config)
            output_path = os.path.join(args.output_dir, 'results.json')
            saved_file = exporter.save_results(results, output_path)
            console.print(f"[bold green]Результаты сохранены в JSON![/bold green]")
            console.print(f"Файл: {saved_file}")
            
        elif args.format == 'csv':
            exporter = CsvExporter(config)
            output_path = os.path.join(args.output_dir, 'results.csv')
            saved_file = exporter.export_results(results, output_path)
            console.print(f"[bold green]Результаты сохранены в CSV![/bold green]")
            console.print(f"Файл: {saved_file}")
            
            # Также сохраняем ссылки
            links_path = os.path.join(args.output_dir, 'links.csv')
            links_file = exporter.export_links(results, links_path)
            console.print(f"Ссылки сохранены в: {links_file}")
            
        elif args.format == 'claude':
            exporter = ClaudeExporter(config)
            output_path = os.path.join(args.output_dir, 'claude.md')
            saved_file = exporter.export_for_claude(results, output_path)
            console.print(f"[bold green]Результаты сохранены в формате для Claude![/bold green]")
            console.print(f"Файл: {saved_file}")
            
            # Также сохраняем чанки
            chunked_dir = os.path.join(args.output_dir, 'claude_chunks')
            chunk_files = exporter.export_chunked(results, chunked_dir)
            console.print(f"Чанки сохранены в: {chunked_dir}")
            
        elif args.format == 'html':
            exporter = HtmlExporter(config)
            saved_files = exporter.save_results(results, args.output_dir)
            console.print(f"[bold green]Результаты сохранены в HTML![/bold green]")
            console.print(f"Индексный файл: {os.path.join(args.output_dir, 'index.html')}")
            
        elif args.format == 'zip':
            exporter = ZipExporter(config)
            output_path = os.path.join(args.output_dir, 'documentation.zip')
            saved_file = exporter.export_to_zip(results, output_path)
            console.print(f"[bold green]Результаты сохранены в ZIP-архив![/bold green]")
            console.print(f"Файл: {saved_file}")
            
        else:
            console.print(f"[bold red]Неизвестный формат: {args.format}[/bold red]")
            sys.exit(1)
        
        console.print("[bold green]Готово![/bold green]")
        
    except KeyboardInterrupt:
        console.print("[bold red]Прервано пользователем![/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Ошибка: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


def run_gui():
    """Запускает GUI-приложение."""
    from doc_parser.interface.app import run_app
    run_app()


def run_api(host="0.0.0.0", port=8000):
    """
    Запускает API-сервер.
    
    Args:
        host: Хост для привязки
        port: Порт для привязки
    """
    from doc_parser.interface.api import start_server
    start_server(host, port)


def run_webui(host="0.0.0.0", port=5000):
    """
    Запускает веб-интерфейс.
    
    Args:
        host: Хост для привязки
        port: Порт для привязки
    """
    from doc_parser.interface.webui import run_webui
    run_webui(host, port)


if __name__ == '__main__':
    main()
