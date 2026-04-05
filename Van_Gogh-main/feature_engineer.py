"""
БЛОК 3: Инженерия признаков (Feature Engineering)
Advanced feature engineering for agricultural subsidy scoring system
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, LabelEncoder
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_classif
import logging
from typing import Dict, List, Tuple
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Класс для инженерии признаков и их трансформации"""
    
    def __init__(self, df: pd.DataFrame, target_col: str = None):
        self.df = df.copy()
        self.target_col = target_col
        self.original_features = list(df.columns)
        self.scaler = StandardScaler()
        self.encoders = {}
        self.selector = None
        self.feature_importance = {}
        self.logger = logger
    
    def create_temporal_features(self) -> pd.DataFrame:
        """
        Рассчитывает историческую динамику и создает временные признаки
        """
        self.logger.info("1. Создание временных признаков...")
        
        df = self.df.copy()
        
        # Find date columns
        date_cols = df.select_dtypes(include=['datetime64']).columns
        
        for date_col in date_cols:
            if pd.notna(df[date_col]).sum() == 0:
                continue
            
            # Extract temporal features
            df[f'{date_col}_year'] = df[date_col].dt.year
            df[f'{date_col}_month'] = df[date_col].dt.month
            df[f'{date_col}_quarter'] = df[date_col].dt.quarter
            df[f'{date_col}_dayofweek'] = df[date_col].dt.dayofweek
            df[f'{date_col}_dayofyear'] = df[date_col].dt.dayofyear
            df[f'{date_col}_week'] = df[date_col].dt.isocalendar().week
            
            # Calculate days since submission
            reference_date = pd.Timestamp.now()
            df[f'{date_col}_days_since'] = (reference_date - df[date_col]).dt.days
            
            self.logger.info(f"  ✓ Обработана дата: {date_col}")
        
        self.df = df
        return df
    
    def create_financial_features(self) -> pd.DataFrame:
        """
        Создает финансовые коэффициенты и интегральные показатели
        """
        self.logger.info("2. Создание финансовых признаков...")
        
        df = self.df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Find potential financial columns
        amount_cols = [col for col in numeric_cols if any(
            term in col.lower() for term in ['сумма', 'amount', 'value', 'стоимость']
        )]
        
        # Create ratios if multiple amount columns exist
        if len(amount_cols) >= 2:
            for i in range(len(amount_cols)):
                for j in range(i+1, len(amount_cols)):
                    col1, col2 = amount_cols[i], amount_cols[j]
                    
                    # Avoid division by zero
                    with np.errstate(divide='ignore', invalid='ignore'):
                        ratio = df[col1] / (df[col2] + 1e-6)
                        ratio = np.where(np.isinf(ratio) | np.isnan(ratio), 0, ratio)
                        df[f'{col1}_to_{col2}_ratio'] = ratio
            
            self.logger.info(f"  ✓ Создано финансовых коэффициентов: {len(amount_cols)}")
        
        self.df = df
        return df
    
    def create_interaction_features(self, top_n_features: int = 5) -> pd.DataFrame:
        """
        Создает признаки взаимодействия между важными переменными
        """
        self.logger.info("3. Создание признаков взаимодействия...")
        
        df = self.df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            self.logger.warning("  Недостаточно числовых столбцов для взаимодействия")
            return df
        
        # Select top features by variance
        top_cols = numeric_cols[:min(top_n_features, len(numeric_cols))]
        
        interaction_count = 0
        for i in range(len(top_cols)):
            for j in range(i+1, len(top_cols)):
                col1, col2 = top_cols[i], top_cols[j]
                
                # Multiplication (synergy)
                df[f'{col1}_x_{col2}'] = df[col1] * df[col2]
                
                # Division (efficiency)
                with np.errstate(divide='ignore', invalid='ignore'):
                    div = df[col1] / (df[col2] + 1e-6)
                    div = np.where(np.isinf(div) | np.isnan(div), 0, div)
                    df[f'{col1}_div_{col2}'] = div
                
                interaction_count += 2
        
        self.logger.info(f"  ✓ Создано признаков взаимодействия: {interaction_count}")
        self.df = df
        return df
    
    def create_geographic_features(self) -> pd.DataFrame:
        """
        Создает географические признаки и паттерны
        """
        self.logger.info("4. Создание географических признаков...")
        
        df = self.df.copy()
        
        # Find region columns
        region_cols = [col for col in df.columns if any(
            term in col.lower() for term in ['регион', 'область', 'region']
        )]
        
        if not region_cols:
            self.logger.warning("  Географические столбцы не найдены")
            return df
        
        for region_col in region_cols:
            # Region frequency encoding
            region_freq = df[region_col].value_counts()
            df[f'{region_col}_frequency'] = df[region_col].map(region_freq)
            
            # Region statistics
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for num_col in numeric_cols[:3]:  # Top 3 numeric
                region_mean = df.groupby(region_col)[num_col].transform('mean')
                df[f'{region_col}_{num_col}_mean'] = region_mean
            
            self.logger.info(f"  ✓ Обработан регион: {region_col}")
        
        self.df = df
        return df
    
    def normalize_numeric_features(self, method: str = 'standard') -> pd.DataFrame:
        """
        Нормализует числовые признаки
        method: 'standard' (StandardScaler) или 'minmax' (MinMaxScaler)
        """
        self.logger.info(f"5. Нормализация числовых признаков (метод: {method})...")
        
        df = self.df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if method == 'standard':
            scaler = StandardScaler()
        else:
            scaler = MinMaxScaler()
        
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        self.scaler = scaler
        
        self.logger.info(f"  ✓ Нормализовано признаков: {len(numeric_cols)}")
        self.df = df
        
        return df
    
    def encode_categorical_features(self, top_n_categories: int = 10) -> pd.DataFrame:
        """
        Кодирует категориальные переменные
        - OneHot для важных переменных
        - Label Encoding для остальных
        """
        self.logger.info("6. Кодирование категориальных признаков...")
        
        df = self.df.copy()
        
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        onehot_count = 0
        label_count = 0
        
        for cat_col in categorical_cols:
            # Skip if too many unique values
            if df[cat_col].nunique() > top_n_categories:
                # Label encoding for high-cardinality
                le = LabelEncoder()
                df[f'{cat_col}_encoded'] = le.fit_transform(df[cat_col].astype(str))
                self.encoders[cat_col] = ('label', le)
                label_count += 1
                self.logger.info(f"  ✓ {cat_col}: Label Encoding ({df[cat_col].nunique()} категорий)")
            else:
                # One-Hot encoding for low-cardinality
                try:
                    dummies = pd.get_dummies(df[cat_col], prefix=cat_col, drop_first=True)
                    df = pd.concat([df, dummies], axis=1)
                    self.encoders[cat_col] = ('onehot', cat_col)
                    onehot_count += len(dummies.columns)
                    self.logger.info(f"  ✓ {cat_col}: One-Hot Encoding ({df[cat_col].nunique()} категорий)")
                except Exception as e:
                    self.logger.warning(f"  ✗ Ошибка при кодировании {cat_col}: {str(e)}")
        
        self.logger.info(f"  Всего кодированных признаков: {onehot_count + label_count}")
        self.df = df
        
        return df
    
    def select_features(self, target_col: str = None, n_features: int = 50) -> pd.DataFrame:
        """
        Выполняет отбор признаков - удаляет малоинформативные
        """
        self.logger.info(f"7. Отбор признаков (top {n_features})...")
        
        df = self.df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Remove constant features (variance = 0)
        selector = VarianceThreshold(threshold=0.0)
        selector.fit(df[numeric_cols])
        
        variance_mask = selector.get_support()
        constant_features = numeric_cols[~variance_mask]
        
        df = df.drop(constant_features, axis=1, errors='ignore')
        
        self.logger.info(f"  ✓ Удалено константных признаков: {len(constant_features)}")
        
        # Feature importance if target available
        if target_col and target_col in df.columns:
            try:
                numeric_cols_filtered = df.select_dtypes(include=[np.number]).columns
                X = df[numeric_cols_filtered].fillna(0)
                y = df[target_col]
                
                # Use SelectKBest
                selector_best = SelectKBest(f_classif, k=min(n_features, len(numeric_cols_filtered)))
                selector_best.fit(X, y)
                
                selected_features = numeric_cols_filtered[selector_best.get_support()].tolist()
                self.feature_importance = dict(zip(
                    selected_features,
                    selector_best.scores_[selector_best.get_support()]
                ))
                
                self.logger.info(f"  ✓ Отобрано информативных признаков: {len(selected_features)}")
                
                # Keep only selected features
                keep_cols = list(df.drop(numeric_cols_filtered, axis=1).columns) + selected_features
                df = df[keep_cols]
            except Exception as e:
                self.logger.warning(f"  ✗ Ошибка при отборе признаков: {str(e)}")
        
        self.df = df
        return df
    
    def create_polynomial_features(self, degree: int = 2, top_n: int = 5) -> pd.DataFrame:
        """
        Создает полиномиальные признаки для топ-N числовых переменных
        """
        self.logger.info(f"8. Создание полиномиальных признаков (степень {degree})...")
        
        df = self.df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Select top features by variance
        top_cols = numeric_cols[:min(top_n, len(numeric_cols))]
        
        poly_count = 0
        for col in top_cols:
            for d in range(2, degree + 1):
                df[f'{col}_pow_{d}'] = df[col] ** d
                poly_count += 1
        
        self.logger.info(f"  ✓ Создано полиномиальных признаков: {poly_count}")
        self.df = df
        
        return df
    
    def get_feature_summary(self) -> Dict:
        """
        Возвращает сводку по признакам
        """
        summary = {
            'total_features': len(self.df.columns),
            'numeric_features': len(self.df.select_dtypes(include=[np.number]).columns),
            'categorical_features': len(self.df.select_dtypes(include=['object']).columns),
            'memory_mb': self.df.memory_usage(deep=True).sum() / 1024**2,
            'missing_values': self.df.isnull().sum().sum(),
            'feature_names': list(self.df.columns)
        }
        
        return summary
    
    def save_transformers(self, output_dir: str = 'models/transformers') -> None:
        """
        Сохраняет трансформеры (scaler, encoders) для использования при обработке новых заявок
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save scaler
        with open(output_path / 'scaler.pkl', 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Save encoders
        with open(output_path / 'encoders.pkl', 'wb') as f:
            pickle.dump(self.encoders, f)
        
        self.logger.info(f"✓ Трансформеры сохранены: {output_dir}")
    
    def fit_transform(self) -> pd.DataFrame:
        """
        Полный конвейер трансформации признаков
        """
        self.logger.info("=" * 60)
        self.logger.info("НАЧАЛО ИНЖЕНЕРИИ ПРИЗНАКОВ")
        self.logger.info("=" * 60)
        
        self.create_temporal_features()
        self.create_financial_features()
        self.create_geographic_features()
        self.create_interaction_features()
        self.create_polynomial_features()
        self.encode_categorical_features()
        self.normalize_numeric_features()
        self.select_features()
        
        summary = self.get_feature_summary()
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("ИТОГИ ИНЖЕНЕРИИ ПРИЗНАКОВ")
        self.logger.info("=" * 60)
        self.logger.info(f"Всего признаков: {summary['total_features']}")
        self.logger.info(f"Числовых: {summary['numeric_features']}")
        self.logger.info(f"Категориальных: {summary['categorical_features']}")
        self.logger.info(f"Память: {summary['memory_mb']:.2f} MB")
        self.logger.info("=" * 60)
        
        return self.df


if __name__ == '__main__':
    # Example usage
    df = pd.read_csv('data/processed_data.csv')
    engineer = FeatureEngineer(df, target_col='статус_заявки')
    df_engineered = engineer.fit_transform()
    engineer.save_transformers()
