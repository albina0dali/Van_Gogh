"""
Main Pipeline Script
Comprehensive orchestration of all system blocks
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Import all modules
from data_loader import DataLoader
from eda_analysis import ExploratoryDataAnalysis
from feature_engineer import FeatureEngineer
from model_trainer import SubsidyModelTrainer
from explainability import ExplainablePredictions
from config_manager import SystemConfig
from database_models import init_database
from utilities import (DataImportUtility, ReportGenerator, 
                      ModelMonitor, DatabaseBackup)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('subsidy_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SubsidyScoringPipeline:
    """Главный конвейер всей системы скоринга"""
    
    def __init__(self):
        self.logger = logger
        self.config = SystemConfig()
        self.start_time = datetime.now()
        
        self.logger.info("=" * 80)
        self.logger.info("ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ СКОРИНГА СУБСИДИЙ")
        self.logger.info("=" * 80)
    
    def run_complete_pipeline(self):
        """
        Запускает полный конвейер: от загрузки данных до обучения модели
        """
        try:
            # Блок 0: Инициализация БД
            self.logger.info("\n[БЛОК 0] Инициализация базы данных...")
            self._init_database()
            
            # Блоки 1-2: Загрузка и EDA
            self.logger.info("\n[БЛОКИ 1-2] Загрузка и анализ данных...")
            df_processed = self._load_and_analyze_data()
            
            if df_processed is None or len(df_processed) == 0:
                self.logger.error("✗ Не удалось загрузить данные")
                return False
            
            # Блок 3: Feature Engineering
            self.logger.info("\n[БЛОК 3] Инженерия признаков...")
            df_engineered = self._engineer_features(df_processed)
            
            # Блоки 4-5: Обучение и оценка
            self.logger.info("\n[БЛОКИ 4-5] Обучение и оценка моделей...")
            self._train_and_evaluate(df_engineered)
            
            # Блок 6: Объяснимость
            self.logger.info("\n[БЛОК 6] Анализ объяснимости...")
            self._generate_explanations()
            
            self._print_summary()
            return True
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка в конвейере: {str(e)}", exc_info=True)
            return False
    
    def run_prediction_only(self, features_dict: dict):
        """
        Запускает только предсказание на новых данных
        """
        try:
            self.logger.info("\n[ПРЕДСКАЗАНИЕ] Загрузка модели и выполнение предсказания...")
            
            import joblib
            import numpy as np
            
            # Загрузка модели
            model = joblib.load(self.config.get('model.model_path'))
            
            # Загрузка трансформеров
            try:
                scaler = joblib.load('models/transformers/scaler.pkl')
            except:
                scaler = None
            
            # Подготовка признаков
            features_array = np.array([list(features_dict.values())]).reshape(1, -1)
            
            if scaler:
                features_array = scaler.transform(features_array)
            
            # Предсказание
            if hasattr(model, 'predict_proba'):
                probability = model.predict_proba(features_array)[0, 1]
            else:
                probability = model.predict(features_array)[0]
            
            score = probability * 100
            
            self.logger.info(f"✓ Предсказание: {score:.1f}%")
            return score
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка предсказания: {str(e)}")
            return None
    
    def _init_database(self):
        """Инициализация БД"""
        try:
            db_url = self.config.get('database.sqlite.path', 'subsidy_scoring.db')
            db_url = f'sqlite:///{db_url}'
            db = init_database(db_url)
            self.logger.info(f"✓ База данных инициализирована")
            return db
        except Exception as e:
            self.logger.error(f"✗ Ошибка БД: {str(e)}")
            return None
    
    def _load_and_analyze_data(self):
        """Загружает и анализирует данные"""
        try:
            # Загрузка
            loader = DataLoader('data')
            df = loader.preprocess()
            
            if df is None or len(df) == 0:
                return None
            
            # EDA
            eda = ExploratoryDataAnalysis(df, 'results/eda')
            eda.run_full_analysis()
            
            return df
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка загрузки данных: {str(e)}")
            return None
    
    def _engineer_features(self, df):
        """Инженерия признаков"""
        try:
            # Определить целевой столбец
            target_cols = [col for col in df.columns 
                          if any(term in col.lower() for term in ['статус', 'status', 'decision'])]
            target_col = target_cols[0] if target_cols else None
            
            engineer = FeatureEngineer(df, target_col)
            df_engineered = engineer.fit_transform()
            engineer.save_transformers()
            
            return df_engineered
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка инженерии признаков: {str(e)}")
            return df
    
    def _train_and_evaluate(self, df):
        """Обучение и оценка моделей"""
        try:
            # Определить целевой столбец
            target_cols = [col for col in df.columns 
                          if any(term in col.lower() for term in ['статус', 'status', 'decision'])]
            target_col = target_cols[0] if target_cols else None
            
            if not target_col:
                self.logger.warning("⚠ Целевой столбец не найден")
                return
            
            trainer = SubsidyModelTrainer()
            trainer.prepare_data(df, target_col)
            trainer.train_all_models()
        
        except Exception as e:
            self.logger.error(f"✗ Ошибка обучения: {str(e)}")
    
    def _generate_explanations(self):
        """Генерирует объяснения"""
        try:
            import joblib
            import pandas as pd
            
            model = joblib.load('models/best_model.pkl')
            X_train = pd.read_csv('data/processed_data.csv').iloc[:100]
            X_test = pd.read_csv('data/processed_data.csv').iloc[100:110]
            
            explainer = ExplainablePredictions(model, X_train, X_test)
            explainer.run_full_explanation()
        
        except Exception as e:
            self.logger.warning(f"⚠ Ошибка объяснимости (non-critical): {str(e)}")
    
    def _print_summary(self):
        """Выводит сводку"""
        elapsed = datetime.now() - self.start_time
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("СВОДКА ВЫПОЛНЕНИЯ")
        self.logger.info("=" * 80)
        self.logger.info(f"Время выполнения: {elapsed}")
        self.logger.info(f"Завершено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("\n✓ Система успешно инициализирована!")
        self.logger.info("=" * 80)


def main():
    """Главная функция"""
    
    parser = argparse.ArgumentParser(description='Subsidy Scoring System')
    parser.add_argument('--mode', choices=['full', 'predict', 'api'], 
                       default='full', help='Режим работы')
    parser.add_argument('--data-dir', default='data', help='Путь к папке данных')
    parser.add_argument('--features', type=str, help='JSON с признаками для предсказания')
    
    args = parser.parse_args()
    
    pipeline = SubsidyScoringPipeline()
    
    if args.mode == 'full':
        success = pipeline.run_complete_pipeline()
        sys.exit(0 if success else 1)
    
    elif args.mode == 'predict':
        if not args.features:
            print("Error: --features required for predict mode")
            sys.exit(1)
        
        import json
        features = json.loads(args.features)
        score = pipeline.run_prediction_only(features)
        print(f"Score: {score:.1f}%")
    
    elif args.mode == 'api':
        from api_server import app
        app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
