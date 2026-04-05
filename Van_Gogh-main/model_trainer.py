"""
БЛОК 4-5: Обучение моделей и оценка качества
Model training, optimization, and evaluation for subsidy scoring
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                             roc_auc_score, confusion_matrix, classification_report, 
                             roc_curve, precision_recall_curve, auc)
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
import joblib
import logging
from typing import Dict, Tuple, List
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


class SubsidyModelTrainer:
    """Класс для обучения и оценки моделей скоринга"""
    
    def __init__(self, output_dir: str = 'models'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        self.models = {}
        self.results = {}
        self.best_model = None
        self.best_model_name = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
    
    def prepare_data(self, df: pd.DataFrame, target_col: str, test_size: float = 0.2, 
                    handle_imbalance: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Подготавливает и разбивает данные на train/test
        """
        self.logger.info("\n1. Подготовка данных...")
        
        # Выбор признаков (всё кроме целевой переменной)
        X = df.drop(target_col, axis=1, errors='ignore').select_dtypes(include=[np.number])
        
        # Обработка целевой переменной
        if target_col in df.columns:
            y = df[target_col]
            
            # Кодирование целевой переменной если она категориальная
            if y.dtype == 'object':
                from sklearn.preprocessing import LabelEncoder
                le = LabelEncoder()
                y = le.fit_transform(y)
                self.target_encoder = le
        else:
            raise ValueError(f"Целевой столбец '{target_col}' не найден")
        
        # Разбиение данных
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        self.logger.info(f"  ✓ Разбиение данных:")
        self.logger.info(f"    Train: {len(self.X_train)} образцов ({100-test_size*100:.0f}%)")
        self.logger.info(f"    Test: {len(self.X_test)} образцов ({test_size*100:.0f}%)")
        self.logger.info(f"    Признаков: {self.X_train.shape[1]}")
        
        # Обработка дисбаланса классов
        if handle_imbalance:
            self.logger.info("  ✓ Обработка дисбаланса классов (SMOTE)...")
            smote = SMOTE(random_state=42)
            self.X_train, self.y_train = smote.fit_resample(self.X_train, self.y_train)
            self.logger.info(f"    Train после SMOTE: {len(self.X_train)}")
        
        return self.X_train, self.X_test, self.y_train, self.y_test
    
    def train_logistic_regression(self) -> Tuple[LogisticRegression, Dict]:
        """
        Обучает Logistic Regression
        """
        self.logger.info("\n2a. Обучение Logistic Regression...")
        
        model = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1)
        model.fit(self.X_train, self.y_train)
        
        y_pred = model.predict(self.X_test)
        y_pred_proba = model.predict_proba(self.X_test)[:, 1]
        
        metrics = self._evaluate_model(y_pred, y_pred_proba)
        
        self.models['Logistic Regression'] = model
        self.results['Logistic Regression'] = metrics
        
        self.logger.info(f"  ✓ Обучено успешно")
        
        return model, metrics
    
    def train_random_forest(self) -> Tuple[RandomForestClassifier, Dict]:
        """
        Обучает Random Forest с гиперпараметрической оптимизацией
        """
        self.logger.info("\n2b. Обучение Random Forest...")
        
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        
        # Гиперпараметрическая оптимизация
        param_grid = {
            'max_depth': [10, 15, 20],
            'min_samples_split': [5, 10],
            'min_samples_leaf': [2, 4]
        }
        
        grid_search = GridSearchCV(rf, param_grid, cv=5, n_jobs=-1, verbose=1)
        grid_search.fit(self.X_train, self.y_train)
        
        model = grid_search.best_estimator_
        
        self.logger.info(f"  ✓ Лучшие параметры: {grid_search.best_params_}")
        
        y_pred = model.predict(self.X_test)
        y_pred_proba = model.predict_proba(self.X_test)[:, 1]
        
        metrics = self._evaluate_model(y_pred, y_pred_proba)
        
        self.models['Random Forest'] = model
        self.results['Random Forest'] = metrics
        
        return model, metrics
    
    def train_xgboost(self) -> Tuple[XGBClassifier, Dict]:
        """
        Обучает XGBoost с гиперпараметрической оптимизацией
        """
        self.logger.info("\n2c. Обучение XGBoost...")
        
        xgb = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1,
            eval_metric='logloss'
        )
        
        xgb.fit(self.X_train, self.y_train)
        
        self.logger.info(f"  ✓ Обучено успешно")
        
        y_pred = xgb.predict(self.X_test)
        y_pred_proba = xgb.predict_proba(self.X_test)[:, 1]
        
        metrics = self._evaluate_model(y_pred, y_pred_proba)
        
        self.models['XGBoost'] = xgb
        self.results['XGBoost'] = metrics
        
        return xgb, metrics
    
    def train_gradient_boosting(self) -> Tuple[GradientBoostingClassifier, Dict]:
        """
        Обучает Gradient Boosting
        """
        self.logger.info("\n2d. Обучение Gradient Boosting...")
        
        gb = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        gb.fit(self.X_train, self.y_train)
        
        y_pred = gb.predict(self.X_test)
        y_pred_proba = gb.predict_proba(self.X_test)[:, 1]
        
        metrics = self._evaluate_model(y_pred, y_pred_proba)
        
        self.models['Gradient Boosting'] = gb
        self.results['Gradient Boosting'] = metrics
        
        self.logger.info(f"  ✓ Обучено успешно")
        
        return gb, metrics
    
    def _evaluate_model(self, y_pred, y_pred_proba) -> Dict:
        """
        Вычисляет все метрики качества модели
        """
        metrics = {
            'accuracy': float(accuracy_score(self.y_test, y_pred)),
            'precision': float(precision_score(self.y_test, y_pred, zero_division=0)),
            'recall': float(recall_score(self.y_test, y_pred, zero_division=0)),
            'f1': float(f1_score(self.y_test, y_pred, zero_division=0)),
            'auc_roc': float(roc_auc_score(self.y_test, y_pred_proba)),
        }
        
        return metrics
    
    def cross_validate_best_model(self, cv: int = 5) -> Dict:
        """
        Выполняет кросс-валидацию для лучшей модели
        """
        self.logger.info(f"\n3. Кросс-валидация ({cv}-fold)...")
        
        if not self.best_model:
            raise ValueError("Сначала обучите модели")
        
        scores = cross_val_score(
            self.best_model, 
            self.X_train, 
            self.y_train, 
            cv=StratifiedKFold(n_splits=cv),
            scoring='f1'
        )
        
        cv_results = {
            'mean_f1': float(scores.mean()),
            'std_f1': float(scores.std()),
            'fold_scores': scores.tolist()
        }
        
        self.logger.info(f"  ✓ Средний F1 score: {scores.mean():.4f} (+/- {scores.std():.4f})")
        
        return cv_results
    
    def select_best_model(self) -> str:
        """
        Выбирает лучшую модель на основе F1 score
        """
        self.logger.info("\n4. Выбор лучшей модели...")
        
        best_f1 = -1
        best_model_name = None
        
        for name, metrics in self.results.items():
            f1 = metrics['f1']
            self.logger.info(f"  {name}: F1={f1:.4f}, AUC-ROC={metrics['auc_roc']:.4f}")
            
            if f1 > best_f1:
                best_f1 = f1
                best_model_name = name
        
        self.best_model_name = best_model_name
        self.best_model = self.models[best_model_name]
        
        self.logger.info(f"\n  🏆 Лучшая модель: {best_model_name} (F1={best_f1:.4f})")
        
        return best_model_name
    
    def generate_reports(self) -> None:
        """
        Генерирует отчеты о качестве моделей
        """
        self.logger.info("\n5. Генерация отчетов...")
        
        # Сравнительная таблица
        comparison_df = pd.DataFrame(self.results).T
        comparison_df = comparison_df.sort_values('f1', ascending=False)
        
        self.logger.info(f"\nСравнение моделей:\n{comparison_df}")
        
        # Сохранение отчета
        comparison_df.to_csv(self.output_dir / 'model_comparison.csv')
        
        # JSON отчет
        with open(self.output_dir / 'model_results.json', 'w') as f:
            json.dump({
                'models': self.results,
                'best_model': self.best_model_name
            }, f, indent=4)
        
        # Визуализация
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        metrics_names = ['accuracy', 'precision', 'recall', 'f1', 'auc_roc']
        
        for idx, metric in enumerate(metrics_names[:4]):
            ax = axes.flatten()[idx]
            values = [self.results[model][metric] for model in self.results.keys()]
            ax.bar(self.results.keys(), values)
            ax.set_title(metric.upper(), fontweight='bold')
            ax.set_ylim([0, 1])
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'model_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"  ✓ Отчеты сохранены в {self.output_dir}")
    
    def save_models(self) -> None:
        """
        Сохраняет все обученные модели
        """
        self.logger.info("\n6. Сохранение моделей...")
        
        for name, model in self.models.items():
            filename = self.output_dir / f'{name.lower().replace(" ", "_")}.pkl'
            joblib.dump(model, filename)
            self.logger.info(f"  ✓ {name} → {filename}")
        
        # Сохранить лучшую модель отдельно
        if self.best_model:
            joblib.dump(self.best_model, self.output_dir / 'best_model.pkl')
            self.logger.info(f"  ✓ Лучшая модель → {self.output_dir / 'best_model.pkl'}")
    
    def train_all_models(self) -> Dict:
        """
        Полный конвейер обучения всех моделей
        """
        self.logger.info("=" * 60)
        self.logger.info("НАЧАЛО ОБУЧЕНИЯ МОДЕЛЕЙ")
        self.logger.info("=" * 60)
        
        try:
            self.train_logistic_regression()
        except Exception as e:
            self.logger.error(f"Ошибка Logistic Regression: {str(e)}")
        
        try:
            self.train_random_forest()
        except Exception as e:
            self.logger.error(f"Ошибка Random Forest: {str(e)}")
        
        try:
            self.train_xgboost()
        except Exception as e:
            self.logger.error(f"Ошибка XGBoost: {str(e)}")
        
        try:
            self.train_gradient_boosting()
        except Exception as e:
            self.logger.error(f"Ошибка Gradient Boosting: {str(e)}")
        
        self.select_best_model()
        cv_results = self.cross_validate_best_model()
        self.generate_reports()
        self.save_models()
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("ОБУЧЕНИЕ ЗАВЕРШЕНО")
        self.logger.info("=" * 60)
        
        return self.results


if __name__ == '__main__':
    # Example usage
    df = pd.read_csv('data/engineered_data.csv')
    trainer = SubsidyModelTrainer()
    trainer.prepare_data(df, target_col='status')
    trainer.train_all_models()
