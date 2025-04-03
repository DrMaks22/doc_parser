#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Веб-интерфейс для парсера документации на основе Flask.
"""

import os
import sys
import json
import time
import uuid
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

from doc_parser.config import DEFAULT_CONFIG, VERSION
from doc_parser.core.parser import DocumentationParser
from doc_parser.exporters.text_formats import MarkdownExporter, JsonExporter, CsvExporter
from doc_parser.exporters.ai_formats import ClaudeExporter
from doc_parser.exporters.web_formats import HtmlExporter, ZipExporter


# Создаем Flask приложение
app = Flask(__name__, 
            static_folder='webui/static',
            template_folder='webui/templates')
CORS(app)

# Хранилище для задач парсинга
parsing_tasks = {}


class ParsingTask:
    """Задача парсинга документации."""
    
    def __init__(self, url, config):
        """
        Инициализация задачи.
        
        Args:
            url: URL для парсинга
            config: Конфигурация парсера
        """
        self.id = str(uuid.uuid4())
        self.url = url
        self.config = config
        self.status = "pending"
        self.progress = []
        self.results = None
        self.error = None
        self.start_time = time.time()
        self.end_time = None
        self.thread = None
    
    def to_dict(self):
        """Преобразует задачу в словарь."""
        return {
            "id": self.id,
            "url": self.url,
            "config": self.config,
            "status": self.status,
            "progress": self.progress,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_time": self.end_time - self.start_time if self.end_time else None,
            "results_count": len(self.results) if self.results else 0
        }
    
    def run(self):
        """Запускает задачу в отдельном потоке."""
        self.thread = threading.Thread(target=self._run_task)
        self.thread.daemon = True
        self.thread.start()
    
    def _run_task(self):
        """Выполняет задачу парсинга."""
        try:
            self.status = "processing"
            self.add_progress("Инициализация парсера...")
            
            # Создаем парсер
            parser = DocumentationParser(self.config)
            
            # Подменяем логгер
            original_info = parser.logger.info
            def custom_info(message):
                original_info(message)
                self.add_progress(message)
            parser.logger.info = custom_info
            
            # Запускаем парсинг
            self.add_progress(f"Начало обхода URL: {self.url}")
            self.results = parser.crawl(self.url)
            
            # Завершаем задачу
            self.status = "completed"
            self.add_progress(f"Обход завершен. Обработано URL: {len(self.results)}")
            
            # Экспортируем результаты
            self.export_results()
            
            self.end_time = time.time()
            
        except Exception as e:
            import traceback
            self.status = "error"
            self.error = f"{str(e)}\n{traceback.format_exc()}"
            self.add_progress(f"Ошибка: {str(e)}")
            self.end_time = time.time()
    
    def add_progress(self, message):
        """Добавляет сообщение в лог прогресса."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.progress.append(f"[{timestamp}] {message}")
    
    def export_results(self):
        """Экспортирует результаты парсинга."""
        if not self.results:
            return
        
        try:
            output_format = self.config.get("output_format", "markdown")
            output_dir = self.config.get("output_dir", "output")
            
            # Создаем директорию для результатов
            task_output_dir = os.path.join(output_dir, self.id)
            os.makedirs(task_output_dir, exist_ok=True)
            
            self.add_progress(f"Экспорт результатов в формате {output_format}...")
            
            # Выбираем экспортер в зависимости от формата
            if output_format == "markdown":
                exporter = MarkdownExporter(self.config)
                saved_files = exporter.save_results(self.results, task_output_dir)
                self.add_progress(f"Результаты сохранены в формате Markdown. Файлов: {len(saved_files)}")
                
            elif output_format == "json":
                exporter = JsonExporter(self.config)
                output_path = os.path.join(task_output_dir, "results.json")
                saved_file = exporter.save_results(self.results, output_path)
                self.add_progress(f"Результаты сохранены в JSON: {saved_file}")
                
            elif output_format == "csv":
                exporter = CsvExporter(self.config)
                output_path = os.path.join(task_output_dir, "results.csv")
                saved_file = exporter.export_results(self.results, output_path)
                self.add_progress(f"Результаты сохранены в CSV: {saved_file}")
                
                # Также сохраняем ссылки
                links_path = os.path.join(task_output_dir, "links.csv")
                links_file = exporter.export_links(self.results, links_path)
                self.add_progress(f"Ссылки сохранены в: {links_file}")
                
            elif output_format == "claude":
                exporter = ClaudeExporter(self.config)
                output_path = os.path.join(task_output_dir, "claude.md")
                saved_file = exporter.export_for_claude(self.results, output_path)
                self.add_progress(f"Результаты сохранены для Claude: {saved_file}")
                
                # Также сохраняем чанки
                chunked_dir = os.path.join(task_output_dir, "claude_chunks")
                chunk_files = exporter.export_chunked(self.results, chunked_dir)
                self.add_progress(f"Чанки сохранены в: {chunked_dir}")
                
            elif output_format == "html":
                exporter = HtmlExporter(self.config)
                saved_files = exporter.save_results(self.results, task_output_dir)
                self.add_progress(f"Результаты сохранены в HTML. Файлов: {len(saved_files)}")
                
            elif output_format == "zip":
                exporter = ZipExporter(self.config)
                output_path = os.path.join(task_output_dir, "documentation.zip")
                saved_file = exporter.export_to_zip(self.results, output_path)
                self.add_progress(f"Результаты сохранены в ZIP-архив: {saved_file}")
                
            else:
                self.add_progress(f"Неизвестный формат: {output_format}")
                
        except Exception as e:
            import traceback
            self.add_progress(f"Ошибка при экспорте: {str(e)}")


# Маршруты Flask
@app.route('/')
def index():
    """Главная страница."""
    return render_template('index.html', version=VERSION)


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Получение списка задач."""
    tasks = [task.to_dict() for task in parsing_tasks.values()]
    return jsonify(tasks)


@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Создание новой задачи парсинга."""
    data = request.json
    
    # Проверяем URL
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL не указан"}), 400
    
    # Получаем конфигурацию
    config = DEFAULT_CONFIG.copy()
    user_config = data.get('config', {})
    config.update(user_config)
    
    # Создаем директорию для результатов
    output_dir = config.get('output_dir', 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Создаем и запускаем задачу
    task = ParsingTask(url, config)
    parsing_tasks[task.id] = task
    task.run()
    
    return jsonify(task.to_dict())


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Получение информации о задаче."""
    task = parsing_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Задача не найдена"}), 404
    
    return jsonify(task.to_dict())


@app.route('/api/tasks/<task_id>/progress', methods=['GET'])
def get_task_progress(task_id):
    """Получение прогресса задачи."""
    task = parsing_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Задача не найдена"}), 404
    
    return jsonify({
        "id": task.id,
        "status": task.status,
        "progress": task.progress,
        "error": task.error
    })


@app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """Отмена задачи."""
    task = parsing_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Задача не найдена"}), 404
    
    if task.status == "processing" and task.thread and task.thread.is_alive():
        # К сожалению, Python не позволяет безопасно останавливать потоки
        # Можно только пометить задачу как отмененную
        task.status = "cancelled"
        task.add_progress("Задача отменена пользователем")
        task.end_time = time.time()
    
    return jsonify({"status": "ok"})


@app.route('/api/tasks/<task_id>/delete', methods=['DELETE'])
def delete_task(task_id):
    """Удаление задачи."""
    task = parsing_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Задача не найдена"}), 404
    
    # Удаляем задачу из хранилища
    del parsing_tasks[task_id]
    
    return jsonify({"status": "ok"})


@app.route('/api/tasks/<task_id>/results', methods=['GET'])
def get_task_results(task_id):
    """Получение результатов задачи."""
    task = parsing_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Задача не найдена"}), 404
    
    if task.status != "completed":
        return jsonify({"error": f"Задача не завершена. Текущий статус: {task.status}"}), 400
    
    if not task.results:
        return jsonify({"error": "Результаты не найдены"}), 404
    
    # Возвращаем список URL
    urls = list(task.results.keys())
    return jsonify({
        "count": len(urls),
        "urls": urls
    })


@app.route('/api/tasks/<task_id>/results/<path:url>', methods=['GET'])
def get_task_result(task_id, url):
    """Получение результата для конкретного URL."""
    task = parsing_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Задача не найдена"}), 404
    
    if task.status != "completed":
        return jsonify({"error": f"Задача не завершена. Текущий статус: {task.status}"}), 400
    
    if not task.results:
        return jsonify({"error": "Результаты не найдены"}), 404
    
    # Ищем URL в результатах
    for result_url, result_data in task.results.items():
        if result_url == url:
            return jsonify(result_data)
    
    return jsonify({"error": "URL не найден в результатах"}), 404


@app.route('/api/tasks/<task_id>/download', methods=['GET'])
def download_task_results(task_id):
    """Скачивание результатов задачи."""
    task = parsing_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Задача не найдена"}), 404
    
    if task.status != "completed":
        return jsonify({"error": f"Задача не завершена. Текущий статус: {task.status}"}), 400
    
    # Директория с результатами
    output_dir = task.config.get('output_dir', 'output')
    task_output_dir = os.path.join(output_dir, task.id)
    
    if not os.path.exists(task_output_dir):
        return jsonify({"error": "Директория с результатами не найдена"}), 404
    
    # Проверяем формат вывода
    output_format = task.config.get('output_format', 'markdown')
    
    if output_format == 'zip':
        # Для zip возвращаем zip-архив
        zip_path = os.path.join(task_output_dir, "documentation.zip")
        if os.path.exists(zip_path):
            return send_from_directory(
                os.path.dirname(zip_path),
                os.path.basename(zip_path),
                as_attachment=True
            )
    elif output_format == 'json':
        # Для json возвращаем json-файл
        json_path = os.path.join(task_output_dir, "results.json")
        if os.path.exists(json_path):
            return send_from_directory(
                os.path.dirname(json_path),
                os.path.basename(json_path),
                as_attachment=True
            )
    elif output_format == 'csv':
        # Для csv возвращаем csv-файл
        csv_path = os.path.join(task_output_dir, "results.csv")
        if os.path.exists(csv_path):
            return send_from_directory(
                os.path.dirname(csv_path),
                os.path.basename(csv_path),
                as_attachment=True
            )
    elif output_format == 'claude':
        # Для claude возвращаем markdown-файл
        claude_path = os.path.join(task_output_dir, "claude.md")
        if os.path.exists(claude_path):
            return send_from_directory(
                os.path.dirname(claude_path),
                os.path.basename(claude_path),
                as_attachment=True
            )
    
    # Для html и markdown возвращаем ссылку на index.html или список файлов
    if output_format == 'html':
        html_path = os.path.join(task_output_dir, "index.html")
        if os.path.exists(html_path):
            return send_from_directory(
                os.path.dirname(html_path),
                os.path.basename(html_path)
            )
    
    # Возвращаем список файлов
    files = []
    for root, _, filenames in os.walk(task_output_dir):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, task_output_dir)
            files.append({
                "name": rel_path,
                "path": file_path,
                "size": os.path.getsize(file_path)
            })
    
    return jsonify({
        "task_id": task_id,
        "output_format": output_format,
        "output_dir": task_output_dir,
        "files": files
    })


@app.route('/output/<path:filename>')
def serve_output(filename):
    """Отдача файлов из директории output."""
    return send_from_directory('output', filename)


def run_webui(host='0.0.0.0', port=5000):
    """
    Запускает веб-интерфейс.
    
    Args:
        host: Хост для привязки
        port: Порт для привязки
    """
    # Создаем директории для шаблонов и статики
    os.makedirs(os.path.join(os.path.dirname(__file__), 'webui/templates'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'webui/static'), exist_ok=True)
    
    # Запускаем Flask
    app.run(host=host, port=port, debug=True)


if __name__ == '__main__':
    run_webui()
