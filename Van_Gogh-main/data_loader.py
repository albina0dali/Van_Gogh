"""
БЛОК 1: Загрузка и предварительная обработка данных
Module for comprehensive data loading and preprocessing of agricultural subsidy data
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, Tuple, List
import pickle
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataLoader:
    """Класс для загрузки и предварительной обработки данных о субсидиях"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.logger = logger
        self.raw_data = None
        self.processed_data = None
        self.missing_values_strategy = {}
        
    def discover_data_files(self) -> List[Path]:
        """
        Ищет и собирает все поддерживаемые файлы данных
        Поддерживаемые форматы: .xlsx, .xls, .csv
        """
        if not self.data_dir.exists():
            self.logger.error(f"Папка данных не найдена: {self.data_dir}")
            return []
        
        supported_extensions = {'.xlsx', '.xls', '.csv'}
        files = []
        
        for ext in supported_extensions:
            files.extend(self.data_dir.glob(f'*{ext}'))
            files.extend(self.data_dir.glob(f'**/*{ext}'))
        
        files = list(set(files))  # Remove duplicates
        self.logger.info(f"Найдено файлов данных: {len(files)}")
        for f in files:
            self.logger.info(f"  - {f.relative_to(self.data_dir)}")
        
        return sorted(files)
    
    def load_file(self, filepath: Path) -> pd.DataFrame:
        """
        Загружает один файл данных с автоматическим определением формата
        """
        try:
            if filepath.suffix.lower() in {'.xlsx', '.xls'}:
                try:
                    df = pd.read_excel(filepath, skiprows=4)
                except Exception:
                    df = pd.read_excel(filepath)
            elif filepath.suffix.lower() == '.csv':
                # Try multiple encodings
                for encoding in ['utf-8-sig', 'utf-8', 'cp1251', 'latin-1']:
                    try:
                        df = pd.read_csv(filepath, encoding=encoding)
                        break
                    except Exception:
                        continue
            else:
                self.logger.warning(f"Неподдерживаемый формат: {filepath}")
                return pd.DataFrame()
            
            self.logger.info(f"✓ Загружен файл: {filepath.name} ({len(df)} строк)")
            return df
            
        except Exception as e:
            self.logger.error(f"✗ Ошибка при загрузке {filepath}: {str(e)}")
            return pd.DataFrame()
    
    def load_all_data(self) -> pd.DataFrame:
        """
        Загружает и объединяет все доступные файлы данных
        """
        files = self.discover_data_files()
        
        if not files:
            raise FileNotFoundError("В папке data не найдено файлов данных")
        
        dataframes = []
        for filepath in files:
            df = self.load_file(filepath)
            if not df.empty:
                df['source_file'] = filepath.name
                dataframes.append(df)
        
        if not dataframes:
            raise ValueError("Не удалось загрузить ни один файл")
        
        self.raw_data = pd.concat(dataframes, ignore_index=True, sort=False)
        self.logger.info(f"Объединено {len(dataframes)} файлов. Всего строк: {len(self.raw_data)}")
        
        return self.raw_data
    
    def normalize_column_names(self) -> pd.DataFrame:
        """
        Нормализует названия столбцов:
        - Приводит к lowercase
        - Удаляет лишние пробелы
        - Заменяет символы
        """
        if self.raw_data is None:
            raise ValueError("Сначала загрузите данные (load_all_data)")
        
        df = self.raw_data.copy()
        
        # Clean column names
        df.columns = (df.columns
                     .str.strip()
                     .str.lower()
                     .str.replace(r'\s+', '_', regex=True)
                     .str.replace(r'[^\w_]', '', regex=True))
        
        self.logger.info(f"Нормализованы названия столбцов. Всего: {len(df.columns)}")
        self.logger.debug(f"Столбцы: {list(df.columns)}")
        
        return df
    
    def handle_missing_values(self, strategy: Dict[str, str] = None) -> pd.DataFrame:
        """
        Обрабатывает пропущенные значения
        Стратегии: 'drop', 'mean', 'median', 'forward_fill', 'backward_fill'
        """
        df = self.raw_data.copy()
        
        # Default strategy for columns
        if strategy is None:
            strategy = {
                'numeric': 'median',
                'categorical': 'most_frequent',
                'date': 'drop'
            }
        
        missing_before = df.isnull().sum()
        
        self.logger.info("Обработка пропущенных значений:")
        self.logger.info(f"Всего пропусков до обработки: {missing_before.sum()}")
        
        for col in df.columns:
            if df[col].isnull().sum() == 0:
                continue
            
            missing_pct = (df[col].isnull().sum() / len(df)) * 100
            self.logger.info(f"  {col}: {missing_pct:.1f}% ({df[col].isnull().sum()} пропусков)")
            
            if missing_pct > 50:
                # Удалить столбец с >50% пропусков
                df.drop(col, axis=1, inplace=True)
                self.logger.info(f"    → Столбец удален (>50% пропусков)")
            
            elif df[col].dtype in ['float64', 'int64']:
                # Числовые - заполнить медианой
                df[col].fillna(df[col].median(), inplace=True)
                self.logger.info(f"    → Заполнено медианой")
            
            elif df[col].dtype == 'object':
                # Категориальные - режим или удаление
                if df[col].nunique() > 1:
                    df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown', inplace=True)
                    self.logger.info(f"    → Заполнено модой")
            else:
                # Удалить строку
                df.dropna(subset=[col], inplace=True)
                self.logger.info(f"    → Строки удалены")
        
        missing_after = df.isnull().sum()
        self.logger.info(f"Пропусков после обработки: {missing_after.sum()}")
        
        return df
    
    def remove_duplicates(self) -> pd.DataFrame:
        """
        Удаляет дубликаты записей
        """
        df = self.raw_data.copy()
        
        duplicates_before = len(df)
        df.drop_duplicates(inplace=True)
        duplicates_removed = duplicates_before - len(df)
        
        self.logger.info(f"Удалено дубликатов: {duplicates_removed}")
        
        return df
    
    def convert_data_types(self) -> pd.DataFrame:
        """
        Конвертирует типы данных
        - Даты в datetime
        - Числа в numeric
        - Категориальные данные в category
        """
        df = self.raw_data.copy()
        
        self.logger.info("Конвертация типов данных:")
        
        for col in df.columns:
            # Detect and convert dates
            if any(date_indicator in col.lower() for date_indicator in ['дата', 'date', 'время']):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    self.logger.info(f"  {col} → datetime")
                except Exception:
                    pass
            
            # Convert numeric strings to numbers
            elif df[col].dtype == 'object':
                try:
                    numeric_col = pd.to_numeric(df[col], errors='coerce')
                    if numeric_col.notna().sum() / len(df) > 0.8:  # >80% valid
                        df[col] = numeric_col
                        self.logger.info(f"  {col} → numeric")
                except Exception:
                    pass
        
        return df
    
    def preprocess(self) -> pd.DataFrame:
        """
        Полный конвейер предобработки данных
        """
        self.logger.info("=" * 60)
        self.logger.info("НАЧАЛО ПРЕДОБРАБОТКИ ДАННЫХ")
        self.logger.info("=" * 60)
        
        # Шаг 1: Загрузка
        self.logger.info("\n1. Загрузка данных...")
        self.load_all_data()
        
        # Шаг 2: Нормализация названий столбцов
        self.logger.info("\n2. Нормализация названий столбцов...")
        self.raw_data = self.normalize_column_names()
        
        # Шаг 3: Обработка пропусков
        self.logger.info("\n3. Обработка пропущенных значений...")
        self.raw_data = self.handle_missing_values()
        
        # Шаг 4: Удаление дубликатов
        self.logger.info("\n4. Удаление дубликатов...")
        self.raw_data = self.remove_duplicates()
        
        # Шаг 5: Конвертация типов
        self.logger.info("\n5. Конвертация типов данных...")
        self.raw_data = self.convert_data_types()
        
        self.processed_data = self.raw_data.copy()
        
        # Финальная статистика
        self.logger.info("\n" + "=" * 60)
        self.logger.info("ИТОГОВАЯ СТАТИСТИКА")
        self.logger.info("=" * 60)
        self.logger.info(f"Строк: {len(self.processed_data)}")
        self.logger.info(f"Столбцов: {len(self.processed_data.columns)}")
        self.logger.info(f"Памяти: {self.processed_data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        self.logger.info(f"\nТипы данных:\n{self.processed_data.dtypes}")
        self.logger.info(f"\nСтатистика:\n{self.processed_data.describe()}")
        self.logger.info("=" * 60)
        
        return self.processed_data
    
    def save_processed_data(self, output_path: str = 'data/processed_data.pkl') -> None:
        """
        Сохраняет предобработанные данные в pickle формате
        """
        if self.processed_data is None:
            raise ValueError("Нет обработанных данных для сохранения")
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            pickle.dump(self.processed_data, f)
        
        self.logger.info(f"✓ Данные сохранены: {output_path}")
    
    def load_processed_data(self, input_path: str = 'data/processed_data.pkl') -> pd.DataFrame:
        """
        Загружает сохраненные предобработанные данные
        """
        with open(input_path, 'rb') as f:
            self.processed_data = pickle.load(f)
        
        self.logger.info(f"✓ Данные загружены: {input_path}")
        return self.processed_data
    
    def get_data_quality_report(self) -> Dict:
        """
        Генерирует отчет о качестве данных
        """
        if self.processed_data is None:
            raise ValueError("Нет обработанных данных")
        
        df = self.processed_data
        
        report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_mb': df.memory_usage(deep=True).sum() / 1024**2,
            'missing_values': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'data_types': df.dtypes.astype(str).to_dict(),
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
            'date_columns': df.select_dtypes(include=['datetime64']).columns.tolist(),
        }
        
        self.logger.info("\nОтчет о качестве данных:")
        self.logger.info(f"  Всего строк: {report['total_rows']}")
        self.logger.info(f"  Всего столбцов: {report['total_columns']}")
        self.logger.info(f"  Память: {report['memory_mb']:.2f} MB")
        self.logger.info(f"  Дубликатов: {report['duplicate_rows']}")
        
        return report


if __name__ == '__main__':
    # Example usage
    loader = DataLoader('data')
    processed_df = loader.preprocess()
    loader.save_processed_data()
    quality_report = loader.get_data_quality_report()
