#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI-приложение для парсера документации на основе PySide6.
"""

import os
import sys
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTextEdit, QFileDialog, QProgressBar, QGroupBox, QTabWidget,
    QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QTextCursor

from doc_parser.config import DEFAULT_CONFIG
from doc_parser.core.parser import DocumentationParser
from doc_parser.exporters.text_formats import MarkdownExporter, JsonExporter, CsvExporter
from doc_parser.exporters.ai_formats import ClaudeExporter
from doc_parser.exporters.web_formats import HtmlExporter, ZipExporter


class ParserWorker(QThread):
    """
    Рабочий поток для выполнения парсинга в фоне.
    """
    progress_signal = Signal(str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)
    
    def __init__(self, url, config):
        """
        Инициализация потока.
        
        Args:
            url: URL для парсинга
            config: Конфигурация парсера
        """
        super().__init__()
        self.url = url
        self.config = config
        
    def run(self):
        """Запуск парсинга в отдельном потоке."""
        try:
            # Создаем объект парсера
            self.progress_signal.emit("Инициализация парсера...")
            parser = DocumentationParser(self.config)
            
            # Устанавливаем хук для логгера
            old_info = parser.logger.info
            def new_info(msg):
                self.progress_signal.emit(msg)
                old_info(msg)
            parser.logger.info = new_info
            
            # Запускаем обход
            self.progress_signal.emit(f"Начало обхода URL: {self.url}")
            results = parser.crawl(self.url)
            
            # Сигнализируем о завершении
            self.progress_signal.emit(f"Обход завершен. Обработано URL: {len(results)}")
            self.finished_signal.emit(results)
            
        except Exception as e:
            import traceback
            error_text = f"Ошибка: {e}\n{traceback.format_exc()}"
            self.error_signal.emit(error_text)


class DocParserGUI(QMainWindow):
    """
    Главное окно GUI-приложения для парсера документации.
    """
    
    def __init__(self):
        """Инициализация главного окна."""
        super().__init__()
        
        # Настройка окна
        self.setWindowTitle("DocParser - Парсер документации")
        self.setGeometry(100, 100, 800, 600)
        
        # Инициализация UI
        self.setup_ui()
        
        # Данные
        self.results = None
        self.parser_worker = None
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса."""
        # Главный виджет и лейаут
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Создаем вкладки
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Вкладка парсинга
        parser_tab = QWidget()
        parser_layout = QVBoxLayout(parser_tab)
        tab_widget.addTab(parser_tab, "Парсинг")
        
        # Вкладка экспорта
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        tab_widget.addTab(export_tab, "Экспорт результатов")
        
        # Вкладка логов
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)
        tab_widget.addTab(logs_tab, "Логи")
        
        # === Вкладка парсинга ===
        # URL группа
        url_group = QGroupBox("URL для парсинга")
        url_layout = QHBoxLayout(url_group)
        
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://docs.example.com")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        
        parser_layout.addWidget(url_group)
        
        # Настройки парсера
        settings_group = QGroupBox("Настройки парсера")
        settings_layout = QVBoxLayout(settings_group)
        
        # Глубина обхода
        depth_layout = QHBoxLayout()
        depth_label = QLabel("Глубина обхода:")
        self.depth_spinner = QSpinBox()
        self.depth_spinner.setMinimum(1)
        self.depth_spinner.setMaximum(10)
        self.depth_spinner.setValue(DEFAULT_CONFIG['max_depth'])
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.depth_spinner)
        depth_layout.addStretch()
        
        # Задержка между запросами
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Задержка (сек):")
        self.delay_spinner = QDoubleSpinBox()
        self.delay_spinner.setMinimum(0.1)
        self.delay_spinner.setMaximum(10.0)
        self.delay_spinner.setValue(DEFAULT_CONFIG['delay'])
        self.delay_spinner.setSingleStep(0.1)
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_spinner)
        delay_layout.addStretch()
        
        # Таймаут запроса
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Таймаут (сек):")
        self.timeout_spinner = QSpinBox()
        self.timeout_spinner.setMinimum(5)
        self.timeout_spinner.setMaximum(120)
        self.timeout_spinner.setValue(DEFAULT_CONFIG['timeout'])
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_spinner)
        timeout_layout.addStretch()
        
        # Флаги
        flags_layout = QHBoxLayout()
        self.follow_links_checkbox = QCheckBox("Следовать по ссылкам")
        self.follow_links_checkbox.setChecked(DEFAULT_CONFIG['follow_links'])
        self.save_assets_checkbox = QCheckBox("Сохранять ассеты")
        self.save_assets_checkbox.setChecked(DEFAULT_CONFIG['save_assets'])
        flags_layout.addWidget(self.follow_links_checkbox)
        flags_layout.addWidget(self.save_assets_checkbox)
        flags_layout.addStretch()
        
        # Фильтры URL
        filters_group = QGroupBox("Фильтры URL")
        filters_layout = QVBoxLayout(filters_group)
        
        include_layout = QHBoxLayout()
        include_label = QLabel("Включать URL:")
        self.include_input = QLineEdit()
        self.include_input.setPlaceholderText("Regex паттерн (опционально)")
        include_layout.addWidget(include_label)
        include_layout.addWidget(self.include_input)
        
        exclude_layout = QHBoxLayout()
        exclude_label = QLabel("Исключать URL:")
        self.exclude_input = QLineEdit()
        self.exclude_input.setPlaceholderText("Regex паттерн (опционально)")
        exclude_layout.addWidget(exclude_label)
        exclude_layout.addWidget(self.exclude_input)
        
        filters_layout.addLayout(include_layout)
        filters_layout.addLayout(exclude_layout)
        
        # Добавляем все настройки в группу
        settings_layout.addLayout(depth_layout)
        settings_layout.addLayout(delay_layout)
        settings_layout.addLayout(timeout_layout)
        settings_layout.addLayout(flags_layout)
        settings_layout.addWidget(filters_group)
        
        parser_layout.addWidget(settings_group)
        
        # Формат экспорта
        format_group = QGroupBox("Формат экспорта")
        format_layout = QHBoxLayout(format_group)
        
        format_label = QLabel("Формат:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["markdown", "json", "csv", "claude", "html", "zip"])
        self.format_combo.setCurrentText(DEFAULT_CONFIG['output_format'])
        
        output_dir_label = QLabel("Директория:")
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setText(DEFAULT_CONFIG['output_dir'])
        self.output_dir_button = QPushButton("...")
        self.output_dir_button.clicked.connect(self.choose_output_dir)
        
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        format_layout.addWidget(output_dir_label)
        format_layout.addWidget(self.output_dir_input)
        format_layout.addWidget(self.output_dir_button)
        
        parser_layout.addWidget(format_group)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Запустить парсинг")
        self.start_button.clicked.connect(self.start_parsing)
        self.stop_button = QPushButton("Остановить")
        self.stop_button.clicked.connect(self.stop_parsing)
        self.stop_button.setEnabled(False)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        
        parser_layout.addLayout(buttons_layout)
        
        # Прогресс
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)  # Индикатор активности
        self.progress_bar.hide()
        
        progress_layout.addWidget(self.progress_bar)
        
        parser_layout.addLayout(progress_layout)
        
        # === Вкладка экспорта ===
        self.export_info_label = QLabel("Для экспорта сначала выполните парсинг.")
        export_layout.addWidget(self.export_info_label)
        
        export_format_group = QGroupBox("Формат экспорта")
        export_format_layout = QHBoxLayout(export_format_group)
        
        export_format_label = QLabel("Формат:")
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["markdown", "json", "csv", "claude", "html", "zip"])
        
        export_dir_label = QLabel("Директория:")
        self.export_dir_input = QLineEdit()
        self.export_dir_button = QPushButton("...")
        self.export_dir_button.clicked.connect(self.choose_export_dir)
        
        export_format_layout.addWidget(export_format_label)
        export_format_layout.addWidget(self.export_format_combo)
        export_format_layout.addWidget(export_dir_label)
        export_format_layout.addWidget(self.export_dir_input)
        export_format_layout.addWidget(self.export_dir_button)
        
        export_layout.addWidget(export_format_group)
        
        export_buttons_layout = QHBoxLayout()
        self.export_button = QPushButton("Экспорт результатов")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        
        export_buttons_layout.addWidget(self.export_button)
        export_buttons_layout.addStretch()
        
        export_layout.addLayout(export_buttons_layout)
        export_layout.addStretch()
        
        # === Вкладка логов ===
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        logs_layout.addWidget(self.logs_text)
        
        # Добавляем статус бар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")
    
    def choose_output_dir(self):
        """Выбор директории для результатов."""
        directory = QFileDialog.getExistingDirectory(
            self, "Выберите директорию для результатов", 
            self.output_dir_input.text()
        )
        if directory:
            self.output_dir_input.setText(directory)
    
    def choose_export_dir(self):
        """Выбор директории для экспорта."""
        directory = QFileDialog.getExistingDirectory(
            self, "Выберите директорию для экспорта", 
            self.export_dir_input.text()
        )
        if directory:
            self.export_dir_input.setText(directory)
    
    def start_parsing(self):
        """Запуск процесса парсинга."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Предупреждение", "Пожалуйста, введите URL для парсинга")
            return
        
        # Настройка конфигурации
        config = {
            'max_depth': self.depth_spinner.value(),
            'delay': self.delay_spinner.value(),
            'timeout': self.timeout_spinner.value(),
            'follow_links': self.follow_links_checkbox.isChecked(),
            'save_assets': self.save_assets_checkbox.isChecked(),
            'output_format': self.format_combo.currentText(),
            'output_dir': self.output_dir_input.text(),
        }
        
        # Добавляем фильтры, если заданы
        include_pattern = self.include_input.text().strip()
        if include_pattern:
            config['include_patterns'] = [include_pattern]
        
        exclude_pattern = self.exclude_input.text().strip()
        if exclude_pattern:
            config['exclude_patterns'] = [exclude_pattern]
        
        # Создаем выходную директорию
        os.makedirs(config['output_dir'], exist_ok=True)
        
        # Обновляем UI
        self.progress_bar.show()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.logs_text.clear()
        self.statusBar.showMessage("Выполняется парсинг...")
        
        # Запускаем парсинг в отдельном потоке
        self.parser_worker = ParserWorker(url, config)
        self.parser_worker.progress_signal.connect(self.update_progress)
        self.parser_worker.finished_signal.connect(self.parsing_finished)
        self.parser_worker.error_signal.connect(self.parsing_error)
        self.parser_worker.start()
    
    def stop_parsing(self):
        """Остановка процесса парсинга."""
        if self.parser_worker and self.parser_worker.isRunning():
            self.parser_worker.terminate()
            self.parser_worker = None
            self.update_progress("Парсинг прерван пользователем.")
            self.statusBar.showMessage("Парсинг прерван")
            
            # Обновляем UI
            self.progress_bar.hide()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
    def update_progress(self, message):
        """Обновление статуса парсинга."""
        self.logs_text.append(message)
        # Прокрутка в конец
        cursor = self.logs_text.textCursor()
        cursor.movePosition(QTextCursor.End)  # Используем константу из QTextCursor
        self.logs_text.setTextCursor(cursor)
    
    def parsing_finished(self, results):
        """Обработка завершения парсинга."""
        self.results = results
        
        # Обновляем UI
        self.progress_bar.hide()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(True)
        
        # Обновляем информацию на вкладке экспорта
        num_urls = len(results)
        self.export_info_label.setText(f"Парсинг завершен. Обработано URL: {num_urls}.")
        
        # Копируем текущие настройки экспорта
        self.export_format_combo.setCurrentText(self.format_combo.currentText())
        self.export_dir_input.setText(self.output_dir_input.text())
        
        self.statusBar.showMessage(f"Парсинг завершен. Обработано URL: {num_urls}")
        
        # Сразу экспортируем результаты
        output_dir = self.output_dir_input.text()
        output_format = self.format_combo.currentText()
        self.export_specific_format(results, output_dir, output_format)
    
    def parsing_error(self, error_text):
        """Обработка ошибки парсинга."""
        self.progress_bar.hide()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        self.logs_text.append(f"ОШИБКА: {error_text}")
        self.statusBar.showMessage("Ошибка парсинга")
        
        # Показываем сообщение об ошибке
        QMessageBox.critical(self, "Ошибка парсинга", error_text)
    
    def export_results(self):
        """Экспорт результатов в выбранный формат."""
        if not self.results:
            QMessageBox.warning(self, "Предупреждение", "Нет данных для экспорта. Сначала выполните парсинг.")
            return
        
        output_dir = self.export_dir_input.text()
        output_format = self.export_format_combo.currentText()
        
        # Проверяем директорию вывода
        if not output_dir:
            QMessageBox.warning(self, "Предупреждение", "Выберите директорию для экспорта")
            return
        
        # Создаем директорию, если не существует
        os.makedirs(output_dir, exist_ok=True)
        
        # Экспортируем в выбранный формат
        self.export_specific_format(self.results, output_dir, output_format)
    
    def export_specific_format(self, results, output_dir, output_format):
        """
        Экспорт результатов в конкретный формат.
        
        Args:
            results: Данные для экспорта
            output_dir: Директория вывода
            output_format: Формат вывода
        """
        try:
            if output_format == 'markdown':
                exporter = MarkdownExporter()
                saved_files = exporter.save_results(results, output_dir)
                self.update_progress(f"Результаты сохранены в формате Markdown. Файлов: {len(saved_files)}")
                
            elif output_format == 'json':
                exporter = JsonExporter()
                output_path = os.path.join(output_dir, 'results.json')
                saved_file = exporter.save_results(results, output_path)
                self.update_progress(f"Результаты сохранены в JSON: {saved_file}")
                
            elif output_format == 'csv':
                exporter = CsvExporter()
                output_path = os.path.join(output_dir, 'results.csv')
                saved_file = exporter.export_results(results, output_path)
                self.update_progress(f"Результаты сохранены в CSV: {saved_file}")
                
                # Также сохраняем ссылки
                links_path = os.path.join(output_dir, 'links.csv')
                links_file = exporter.export_links(results, links_path)
                self.update_progress(f"Ссылки сохранены в: {links_file}")
                
            elif output_format == 'claude':
                exporter = ClaudeExporter()
                output_path = os.path.join(output_dir, 'claude.md')
                saved_file = exporter.export_for_claude(results, output_path)
                self.update_progress(f"Результаты сохранены в формате для Claude: {saved_file}")
                
                # Также сохраняем чанки
                chunked_dir = os.path.join(output_dir, 'claude_chunks')
                chunk_files = exporter.export_chunked(results, chunked_dir)
                self.update_progress(f"Чанки сохранены в директории: {chunked_dir}")
                
            elif output_format == 'html':
                exporter = HtmlExporter({'save_assets': self.save_assets_checkbox.isChecked()})
                saved_files = exporter.save_results(results, output_dir)
                index_path = os.path.join(output_dir, 'index.html')
                self.update_progress(f"Результаты сохранены в HTML. Индексный файл: {index_path}")
                
            elif output_format == 'zip':
                exporter = ZipExporter({'save_assets': self.save_assets_checkbox.isChecked()})
                output_path = os.path.join(output_dir, 'documentation.zip')
                saved_file = exporter.export_to_zip(results, output_path)
                self.update_progress(f"Результаты сохранены в ZIP-архив: {saved_file}")
                
            else:
                self.update_progress(f"Неизвестный формат: {output_format}")
                return
            
            # Показываем сообщение об успехе
            QMessageBox.information(
                self, 
                "Экспорт завершен", 
                f"Результаты успешно экспортированы в формате {output_format}."
            )
            
            # Открываем директорию с результатами
            if sys.platform == 'win32':
                os.startfile(output_dir)
            else:
                import subprocess
                subprocess.Popen(['xdg-open', output_dir])
            
        except Exception as e:
            import traceback
            error_text = f"Ошибка при экспорте: {e}\n{traceback.format_exc()}"
            self.update_progress(f"ОШИБКА: {error_text}")
            QMessageBox.critical(self, "Ошибка экспорта", error_text)


def run_app():
    """Запуск GUI-приложения."""
    app = QApplication(sys.argv)
    window = DocParserGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run_app()
