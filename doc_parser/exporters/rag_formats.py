#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Экспортеры для форматов RAG (Retrieval-Augmented Generation).
"""

import os
import json
import hashlib
from typing import Dict, List, Optional
import numpy as np
from dataclasses import dataclass
import logging

@dataclass
class ChunkMetadata:
    """Метаданные чанка для RAG."""
    id: str
    source_url: str
    title: str
    type: str  # text, code, table, list
    position: int
    length: int
    embedding: Optional[List[float]] = None
    parent_section: Optional[str] = None
    next_chunk_id: Optional[str] = None
    prev_chunk_id: Optional[str] = None

class RAGExporter:
    """
    Экспортер для форматов RAG с поддержкой векторных эмбеддингов.
    """
    
    def __init__(self, config=None):
        """
        Инициализация экспортера.
        
        Args:
            config: Словарь с настройками
        """
        self.config = config or {}
        self.logger = logging.getLogger('rag_exporter')
        
        # Настройки эмбеддингов
        self.embedding_config = {
            'enabled': self.config.get('enable_embeddings', True),
            'batch_size': self.config.get('embedding_batch_size', 32),
            'model': self.config.get('embedding_model', 'all-MiniLM-L6-v2'),
            'normalize': self.config.get('normalize_embeddings', True),
        }
        
        # Инициализация модели эмбеддингов (ленивая)
        self._embedding_model = None
    
    def _get_embedding_model(self):
        """Ленивая инициализация модели эмбеддингов."""
        if not self._embedding_model and self.embedding_config['enabled']:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(self.embedding_config['model'])
            except ImportError:
                self.logger.warning("sentence-transformers не установлен. Эмбеддинги будут отключены.")
                self.embedding_config['enabled'] = False
        return self._embedding_model
    
    def _generate_chunk_id(self, content: str, url: str, position: int) -> str:
        """Генерация уникального ID для чанка."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:8]
        return f"{url_hash}-{content_hash}-{position}"
    
    def _create_chunk_metadata(
        self, 
        content: str, 
        url: str, 
        title: str, 
        chunk_type: str,
        position: int,
        embedding: Optional[List[float]] = None,
        parent_section: Optional[str] = None
    ) -> ChunkMetadata:
        """Создание метаданных для чанка."""
        return ChunkMetadata(
            id=self._generate_chunk_id(content, url, position),
            source_url=url,
            title=title,
            type=chunk_type,
            position=position,
            length=len(content),
            embedding=embedding,
            parent_section=parent_section
        )
    
    def _compute_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Вычисление эмбеддингов для списка текстов."""
        if not self.embedding_config['enabled']:
            return [None] * len(texts)
        
        model = self._get_embedding_model()
        if not model:
            return [None] * len(texts)
        
        try:
            # Вычисляем эмбеддинги батчами
            embeddings = []
            for i in range(0, len(texts), self.embedding_config['batch_size']):
                batch = texts[i:i + self.embedding_config['batch_size']]
                batch_embeddings = model.encode(batch)
                
                if self.embedding_config['normalize']:
                    batch_embeddings = batch_embeddings / np.linalg.norm(batch_embeddings, axis=1, keepdims=True)
                
                embeddings.extend(batch_embeddings.tolist())
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Ошибка при вычислении эмбеддингов: {e}")
            return [None] * len(texts)
    
    def _process_chunks(self, page_data: Dict) -> List[Dict]:
        """Обработка чанков страницы."""
        chunks = []
        url = page_data['url']
        title = page_data.get('title', '')
        
        if 'rag_content' not in page_data:
            return chunks
        
        rag_content = page_data['rag_content']
        
        # Обработка текстовых чанков
        texts = [chunk['text'] for chunk in rag_content.get('chunks', [])]
        embeddings = self._compute_embeddings(texts)
        
        for i, chunk in enumerate(rag_content.get('chunks', [])):
            metadata = self._create_chunk_metadata(
                content=chunk['text'],
                url=url,
                title=title,
                chunk_type='text',
                position=i,
                embedding=embeddings[i] if embeddings else None
            )
            
            chunks.append({
                'content': chunk['text'],
                'metadata': metadata.__dict__
            })
        
        # Обработка кода
        code_texts = [block['code'] for block in rag_content.get('code_blocks', [])]
        code_embeddings = self._compute_embeddings(code_texts)
        
        for i, block in enumerate(rag_content.get('code_blocks', [])):
            metadata = self._create_chunk_metadata(
                content=block['code'],
                url=url,
                title=title,
                chunk_type='code',
                position=len(chunks) + i,
                embedding=code_embeddings[i] if code_embeddings else None
            )
            
            chunks.append({
                'content': block['code'],
                'language': block.get('language', ''),
                'metadata': metadata.__dict__
            })
        
        # Обработка таблиц
        for i, table in enumerate(rag_content.get('tables', [])):
            table_text = ' '.join(
                [' '.join(table.get('headers', ''))] +
                [' '.join(row) for row in table.get('rows', [])]
            )
            
            metadata = self._create_chunk_metadata(
                content=table_text,
                url=url,
                title=title,
                chunk_type='table',
                position=len(chunks) + i
            )
            
            chunks.append({
                'content': table_text,
                'headers': table.get('headers', []),
                'rows': table.get('rows', []),
                'metadata': metadata.__dict__
            })
        
        # Обработка списков
        for i, lst in enumerate(rag_content.get('lists', [])):
            list_text = ' '.join(lst.get('items', []))
            
            metadata = self._create_chunk_metadata(
                content=list_text,
                url=url,
                title=title,
                chunk_type='list',
                position=len(chunks) + i
            )
            
            chunks.append({
                'content': list_text,
                'items': lst.get('items', []),
                'list_type': lst.get('type', 'ul'),
                'metadata': metadata.__dict__
            })
        
        # Связываем чанки
        for i in range(len(chunks)):
            if i > 0:
                chunks[i]['metadata']['prev_chunk_id'] = chunks[i-1]['metadata']['id']
            if i < len(chunks) - 1:
                chunks[i]['metadata']['next_chunk_id'] = chunks[i+1]['metadata']['id']
        
        return chunks
    
    def export_results(self, results: Dict) -> Dict:
        """
        Экспортирует результаты парсинга в формат для RAG.
        
        Args:
            results: Словарь с результатами парсинга
            
        Returns:
            dict: Структурированные данные для RAG
        """
        rag_data = {
            'chunks': [],
            'metadata': {
                'total_pages': len(results),
                'total_chunks': 0,
                'chunk_types': {
                    'text': 0,
                    'code': 0,
                    'table': 0,
                    'list': 0
                }
            }
        }
        
        # Обрабатываем каждую страницу
        for url, page_data in results.items():
            chunks = self._process_chunks(page_data)
            rag_data['chunks'].extend(chunks)
            
            # Обновляем статистику
            for chunk in chunks:
                chunk_type = chunk['metadata']['type']
                rag_data['metadata']['chunk_types'][chunk_type] += 1
            
            rag_data['metadata']['total_chunks'] += len(chunks)
        
        return rag_data
    
    def save_results(self, results: Dict, output_path: str) -> str:
        """
        Сохраняет результаты в файл.
        
        Args:
            results: Словарь с результатами парсинга
            output_path: Путь для сохранения файла
            
        Returns:
            str: Путь к сохраненному файлу
        """
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Экспортируем данные
        rag_data = self.export_results(results)
        
        # Сохраняем в файл
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rag_data, f, ensure_ascii=False, indent=2)
        
        return output_path
