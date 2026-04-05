"""
БЛОК 11: Дополнительные утилиты и тесты
Utility functions, report generation, and testing framework
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json
from datetime import datetime
from typing import Dict, List, Tuple
import csv
import joblib
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
import os

logger = logging.getLogger(__name__)


# ==================== CSV/Excel Import ====================

class DataImportUtility:
    """Утилита для загрузки заявок из файлов"""
    
    def __init__(self):
        self.logger = logger
    
    def import_applications_from_csv(self, csv_path: str) -> List[Dict]:
        """
        Загружает заявки из CSV файла
        """
        try:
            applications = []
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Валидация и преобразование
                    app = self._validate_row(row)
                    if app:
                        applications.append(app)
            
            self.logger.info(f"✓ Загружено заявок: {len(applications)}")
            return applications
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка импорта: {str(e)}")
            return []
    
    def import_applications_from_excel(self, xlsx_path: str) -> List[Dict]:
        """
        Загружает заявки из Excel файла
        """
        try:
            df = pd.read_excel(xlsx_path)
            applications = []
            
            for _, row in df.iterrows():
                app = self._validate_row(row.to_dict())
                if app:
                    applications.append(app)
            
            self.logger.info(f"✓ Загружено заявок: {len(applications)}")
            return applications
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка импорта: {str(e)}")
            return []
    
    def _validate_row(self, row: Dict) -> Dict:
        """Валидирует строку данных"""
        try:
            # Минимальные обязательные поля
            required = ['farm_name', 'region', 'subsidy_type']
            
            if not all(field in row and row[field] for field in required):
                return None
            
            # Преобразование типов
            validated = {
                'farm_name': str(row['farm_name']).strip(),
                'region': str(row['region']).strip(),
                'subsidy_type': str(row['subsidy_type']).strip(),
                'farm_size_hectares': float(row.get('farm_size_hectares', 0)),
                'annual_revenue': float(row.get('annual_revenue', 0)),
                'previous_subsidies': int(row.get('previous_subsidies', 0)),
            }
            
            return validated
        
        except Exception as e:
            self.logger.warning(f"Ошибка валидации строки: {str(e)}")
            return None


# ==================== Report Generation ====================

class ReportGenerator:
    """Генератор отчетов различных форматов"""
    
    def __init__(self, output_dir: str = 'reports'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    def generate_pdf_report(self, application_id: str, app_data: Dict, 
                           prediction: Dict) -> str:
        """
        Генерирует PDF отчет для рассмотрения комиссией
        """
        try:
            filename = f"application_{application_id}.pdf"
            filepath = self.output_dir / filename
            
            # Создание PDF
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Заголовок
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=30,
                alignment=1  # Center
            )
            
            story.append(Paragraph("Отчет о рассмотрении заявки на субсидию", title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Информация о заявке
            data = [
                ['Параметр', 'Значение'],
                ['ID заявки', application_id],
                ['Наименование хозяйства', app_data.get('farm_name', 'N/A')],
                ['Регион', app_data.get('region', 'N/A')],
                ['Тип субсидии', app_data.get('subsidy_type', 'N/A')],
                ['Размер хозяйства, га', f"{app_data.get('farm_size_hectares', 0):.1f}"],
                ['Годовой доход', f"₸ {app_data.get('annual_revenue', 0):,.0f}"],
            ]
            
            table = Table(data, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 0.3*inch))
            
            # Результаты скоринга
            result_style = ParagraphStyle(
                'ResultColor',
                parent=styles['Heading2'],
                textColor=colors.HexColor('#27ae60'),
                fontSize=16
            )
            
            story.append(Paragraph("Результаты анализа", styles['Heading2']))
            
            score_text = f"Score: {prediction.get('score', 0):.1f}%"
            recommendation = prediction.get('recommendation', 'Неизвестно')
            
            score_data = [
                ['Параметр', 'Значение'],
                ['Скор одобрения', f"{prediction.get('score', 0):.1f}%"],
                ['Рекомендация', recommendation],
                ['Дата анализа', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ]
            
            score_table = Table(score_data, colWidths=[2*inch, 4*inch])
            score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(score_table)
            
            # Построение PDF
            doc.build(story)
            
            self.logger.info(f"✓ PDF отчет создан: {filepath}")
            return str(filepath)
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка создания PDF: {str(e)}")
            return ""
    
    def generate_excel_report(self, applications: List[Dict], 
                            predictions: List[Dict]) -> str:
        """
        Генерирует Excel отчет с результатами
        """
        try:
            filename = f"subsidy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = self.output_dir / filename
            
            # Создание DataFrame
            data = []
            for app, pred in zip(applications, predictions):
                data.append({
                    'ID': app.get('id'),
                    'Хозяйство': app.get('farm_name'),
                    'Регион': app.get('region'),
                    'Тип субсидии': app.get('subsidy_type'),
                    'Размер, га': app.get('farm_size_hectares'),
                    'Доход': app.get('annual_revenue'),
                    'Score': pred.get('score'),
                    'Рекомендация': pred.get('recommendation'),
                    'Дата': datetime.now().isoformat()
                })
            
            df = pd.DataFrame(data)
            
            # Сохранение в Excel с форматированием
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Результаты')
                
                # Форматирование
                worksheet = writer.sheets['Результаты']
                for idx, col in enumerate(df.columns, 1):
                    worksheet.column_dimensions[chr(64+idx)].width = 15
            
            self.logger.info(f"✓ Excel отчет создан: {filepath}")
            return str(filepath)
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка создания Excel: {str(e)}")
            return ""


# ==================== Model Monitoring ====================

class ModelMonitor:
    """Мониторинг производительности моделей"""
    
    def __init__(self, metrics_file: str = 'metrics/model_metrics.json'):
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    def log_prediction(self, prediction_data: Dict) -> None:
        """
        Логирует предсказание для мониторинга
        """
        try:
            metrics = self._load_metrics()
            
            metrics['predictions'].append({
                'timestamp': datetime.now().isoformat(),
                'score': prediction_data.get('score'),
                'recommendation': prediction_data.get('recommendation'),
                'farm_region': prediction_data.get('region'),
            })
            
            # Ограничиваем размер (храним последние 10000)
            if len(metrics['predictions']) > 10000:
                metrics['predictions'] = metrics['predictions'][-10000:]
            
            self._save_metrics(metrics)
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка логирования: {str(e)}")
    
    def get_model_statistics(self) -> Dict:
        """
        Вычисляет статистику модели
        """
        try:
            metrics = self._load_metrics()
            predictions = metrics.get('predictions', [])
            
            if not predictions:
                return {}
            
            df = pd.DataFrame(predictions)
            df['score'] = pd.to_numeric(df['score'], errors='coerce')
            
            stats = {
                'total_predictions': len(df),
                'avg_score': float(df['score'].mean()),
                'median_score': float(df['score'].median()),
                'std_score': float(df['score'].std()),
                'min_score': float(df['score'].min()),
                'max_score': float(df['score'].max()),
                'approval_rate': float((df['recommendation'] == 'Одобрена').sum() / len(df) * 100),
            }
            
            return stats
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка расчета: {str(e)}")
            return {}
    
    def _load_metrics(self) -> Dict:
        """Загружает сохраненные метрики"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'predictions': []}
    
    def _save_metrics(self, metrics: Dict) -> None:
        """Сохраняет метрики"""
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f)


# ==================== Database Backup ====================

class DatabaseBackup:
    """Утилита для автоматического бэкапа БД"""
    
    def __init__(self, backup_dir: str = 'backups'):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    def backup_database(self, db_path: str) -> bool:
        """
        Создает бэкап БД
        """
        try:
            import shutil
            
            if not Path(db_path).exists():
                self.logger.warning(f"БД не найдена: {db_path}")
                return False
            
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(db_path, backup_path)
            
            self.logger.info(f"✓ Бэкап создан: {backup_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка бэкапа: {str(e)}")
            return False
    
    def get_recent_backups(self, n: int = 5) -> List[Path]:
        """
        Получить недавние бэкапы
        """
        try:
            backups = sorted(
                self.backup_dir.glob('backup_*.db'),
                key=os.path.getmtime,
                reverse=True
            )
            return backups[:n]
        except:
            return []


# ==================== Testing Utilities ====================

class TestUtilities:
    """Утилиты для юнит-тестирования"""
    
    @staticmethod
    def create_sample_application() -> Dict:
        """Создает тестовую заявку"""
        return {
            'id': 'TEST_APP_001',
            'farm_name': 'ООО Тестовое Хозяйство',
            'region': 'Акмолинская область',
            'subsidy_type': 'DEV_LIVESTOCK',
            'farm_size_hectares': 500,
            'annual_revenue': 1000000,
            'previous_subsidies': 2,
        }
    
    @staticmethod
    def create_sample_features() -> Dict:
        """Создает тестовые признаки"""
        return {
            'farm_size_hectares': 500,
            'annual_revenue': 1000000,
            'num_employees': 15,
            'equipment_value': 500000,
            'debt_amount': 100000,
            'years_in_operation': 5,
            'previous_subsidies': 2,
        }


if __name__ == '__main__':
    # Example usage
    generator = ReportGenerator()
    sample_app = TestUtilities.create_sample_application()
    sample_pred = {'score': 75.5, 'recommendation': 'Одобрена'}
    
    pdf_path = generator.generate_pdf_report('TEST_001', sample_app, sample_pred)
    
    monitor = ModelMonitor()
    monitor.log_prediction(sample_pred)
    stats = monitor.get_model_statistics()
    
    logger.info(f"✓ Test utilities working")
