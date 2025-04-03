#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
REST API-сервер для парсера документации.
"""

import os
import logging
import asyncio
import tempfile
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, validator
import uvicorn
import uuid

from doc_parser.config import DEFAULT_CONFIG
from doc_parser.core.parser import DocumentationParser
from doc_parser.exporters.text_formats import MarkdownExporter, JsonExporter, CsvExporter
from doc_parser.exporters.ai_formats import ClaudeExporter
from doc_parser.exporters.web_formats import HtmlExporter, ZipExporter


# Модели данных API
class ParserConfig(BaseModel):
    """Конфигурация парсера для API."""
    max_depth: Optional[int] = DEFAULT_CONFIG['max_depth']
    delay: Optional[float] = DEFAULT_CONFIG['delay']
    timeout: Optional[int] = DEFAULT_CONFIG['timeout']
    user_agent: Optional[str] = DEFAULT_CONFIG['user_agent']
    include_patterns: Optional[List[str]] = []
    exclude_patterns: Optional[List[str]] = []
    follow_links: Optional[bool] = DEFAULT_CONFIG['follow_links']
    save_assets: Optional[bool] = DEFAULT_CONFIG['save_assets']
    output_format: Optional[str] = DEFAULT_CONFIG['output_format']
    
    @validator('output_format')
    def validate_format(cls, v):
        """Проверка формата вывода."""
        valid_formats = ['markdown', 'json', 'csv', 'claude', 'html', 'zip']
        if v not in valid_formats:
            raise ValueError(f"Недопустимый формат вывода. Доступные форматы: {', '.join(valid_formats)}")
        return v


class ParsingRequest(BaseModel):
    """Запрос на парсинг."""
    url: HttpUrl
    config: Optional[ParserConfig] = None


class ParsingJob(BaseModel):
    """Информация о задаче парсинга."""
    job_id: str
    url: str
    status: str
    result_file: Optional[str] = None
    error: Optional[str] = None


# Создаем приложение FastAPI
app = FastAPI(
    title="DocParser API",
    description="REST API для парсера документации",
    version="0.1.0"
)

# Добавляем поддержку CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настраиваем логгер
logger = logging.getLogger("doc_parser_api")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Хранилище задач
parsing_jobs: Dict[str, ParsingJob] = {}

# Временная директория для результатов
TEMP_DIR = os.path.join(tempfile.gettempdir(), "doc_parser_api")
os.makedirs(TEMP_DIR, exist_ok=True)

# Функции для работы с задачами
def get_job_result_path(job_id: str, output_format: str) -> str:
    """
    Получает путь для сохранения результатов задачи.
    
    Args:
        job_id: Идентификатор задачи
        output_format: Формат вывода
        
    Returns:
        str: Путь для сохранения результатов
    """
    job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    if output_format == 'json':
        return os.path.join(job_dir, 'results.json')
    elif output_format == 'csv':
        return os.path.join(job_dir, 'results.csv')
    elif output_format == 'claude':
        return os.path.join(job_dir, 'claude.md')
    elif output_format == 'html':
        return os.path.join(job_dir, 'index.html')
    elif output_format == 'zip':
        return os.path.join(job_dir, 'documentation.zip')
    else:  # markdown и другие
        return job_dir


async def run_parsing_job(job_id: str, url: str, config: Dict[str, Any]):
    """
    Запускает задачу парсинга в фоне.
    
    Args:
        job_id: Идентификатор задачи
        url: URL для парсинга
        config: Конфигурация парсера
    """
    try:
        # Обновляем статус
        parsing_jobs[job_id].status = "processing"
        
        # Запускаем парсер
        parser = DocumentationParser(config)
        
        # Запускаем обход (в отдельном потоке)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, parser.crawl, url)
        
        # Экспортируем результаты
        output_format = config.get('output_format', 'markdown')
        output_path = get_job_result_path(job_id, output_format)
        
        # Экспорт в соответствующий формат
        if output_format == 'markdown':
            exporter = MarkdownExporter(config)
            exporter.save_results(results, output_path)
            # Создаем индексный файл
            index_path = os.path.join(output_path, 'index.md')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(f"# Документация - Индекс\n\n")
                for url, page_data in sorted(results.items(), key=lambda x: x[1].get('title', x[0])):
                    title = page_data.get('title', url)
                    filename = f"{url.replace('://', '_').replace('/', '_')}.md"
                    f.write(f"- [{title}]({filename})\n")
            result_file = index_path
            
        elif output_format == 'json':
            exporter = JsonExporter(config)
            exporter.save_results(results, output_path)
            result_file = output_path
            
        elif output_format == 'csv':
            exporter = CsvExporter(config)
            exporter.export_results(results, output_path)
            result_file = output_path
            
        elif output_format == 'claude':
            exporter = ClaudeExporter(config)
            exporter.export_for_claude(results, output_path)
            result_file = output_path
            
        elif output_format == 'html':
            exporter = HtmlExporter(config)
            exporter.save_results(results, output_path)
            result_file = os.path.join(output_path, 'index.html')
            
        elif output_format == 'zip':
            exporter = ZipExporter(config)
            exporter.export_to_zip(results, output_path)
            result_file = output_path
        
        # Обновляем статус задачи
        parsing_jobs[job_id].status = "completed"
        parsing_jobs[job_id].result_file = result_file
        logger.info(f"Задача {job_id} завершена. Результат: {result_file}")
        
    except Exception as e:
        import traceback
        error_text = f"Ошибка: {e}\n{traceback.format_exc()}"
        logger.error(f"Ошибка в задаче {job_id}: {error_text}")
        
        # Обновляем статус задачи
        parsing_jobs[job_id].status = "error"
        parsing_jobs[job_id].error = str(e)


# Маршруты API
@app.get("/")
async def root():
    """Корневой маршрут."""
    return {"message": "DocParser API", "version": "0.1.0"}


@app.post("/parse", response_model=ParsingJob)
async def parse_url(request: ParsingRequest, background_tasks: BackgroundTasks):
    """
    Запускает парсинг URL.
    
    Args:
        request: Запрос на парсинг
        background_tasks: Фоновые задачи FastAPI
        
    Returns:
        ParsingJob: Информация о созданной задаче
    """
    # Создаем ID задачи
    job_id = str(uuid.uuid4())
    
    # Получаем конфигурацию
    config = DEFAULT_CONFIG.copy()
    if request.config:
        config.update(request.config.dict(exclude_unset=True))
    
    # Создаем задачу
    job = ParsingJob(
        job_id=job_id,
        url=str(request.url),
        status="pending"
    )
    parsing_jobs[job_id] = job
    
    # Запускаем задачу в фоне
    background_tasks.add_task(run_parsing_job, job_id, str(request.url), config)
    
    logger.info(f"Создана задача {job_id} для URL: {request.url}")
    return job


@app.get("/jobs/{job_id}", response_model=ParsingJob)
async def get_job(job_id: str):
    """
    Получает информацию о задаче.
    
    Args:
        job_id: Идентификатор задачи
        
    Returns:
        ParsingJob: Информация о задаче
    """
    if job_id not in parsing_jobs:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    return parsing_jobs[job_id]


@app.get("/jobs")
async def list_jobs():
    """
    Получает список всех задач.
    
    Returns:
        list: Список задач
    """
    return list(parsing_jobs.values())


@app.get("/jobs/{job_id}/download")
async def download_result(job_id: str):
    """
    Скачивает результат задачи.
    
    Args:
        job_id: Идентификатор задачи
        
    Returns:
        FileResponse: Файл с результатом
    """
    if job_id not in parsing_jobs:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    job = parsing_jobs[job_id]
    
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Задача не завершена. Текущий статус: {job.status}")
    
    if not job.result_file or not os.path.exists(job.result_file):
        raise HTTPException(status_code=404, detail="Файл результата не найден")
    
    return FileResponse(
        path=job.result_file,
        filename=os.path.basename(job.result_file),
        media_type="application/octet-stream"
    )


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Удаляет задачу.
    
    Args:
        job_id: Идентификатор задачи
        
    Returns:
        dict: Статус операции
    """
    if job_id not in parsing_jobs:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Удаляем файлы результатов
    job = parsing_jobs[job_id]
    if job.result_file and os.path.exists(job.result_file):
        if os.path.isdir(job.result_file):
            import shutil
            shutil.rmtree(job.result_file, ignore_errors=True)
        else:
            os.remove(job.result_file)
    
    # Удаляем директорию задачи
    job_dir = os.path.join(TEMP_DIR, job_id)
    if os.path.exists(job_dir):
        import shutil
        shutil.rmtree(job_dir, ignore_errors=True)
    
    # Удаляем задачу из хранилища
    del parsing_jobs[job_id]
    
    logger.info(f"Удалена задача {job_id}")
    return {"status": "ok", "message": f"Задача {job_id} удалена"}


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Запускает API-сервер.
    
    Args:
        host: Хост для привязки
        port: Порт для привязки
    """
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
