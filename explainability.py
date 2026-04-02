"""
БЛОК 6: Объяснимость предсказаний (XAI - Explainable AI)
SHAP and feature importance analysis for model interpretability
"""

import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import logging
import json
from pathlib import Path
import joblib

logger = logging.getLogger(__name__)


class ExplainablePredictions:
    """Класс для генерации объяснений предсказаний моделей"""
    
    def __init__(self, model, X_train: pd.DataFrame, X_test: pd.DataFrame = None, 
                 feature_names: List[str] = None, output_dir: str = 'results/explanations'):
        self.model = model
        self.X_train = X_train
        self.X_test = X_test if X_test is not None else X_train.head(100)
        self.feature_names = feature_names or list(X_train.columns)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        self.explainer = None
        self.shap_values = None
    
    def initialize_shap_explainer(self) -> None:
        """
        Инициализирует SHAP explainer
        """
        self.logger.info("1. Инициализация SHAP Explainer...")
        
        try:
            # Try TreeExplainer for tree-based models
            if hasattr(self.model, 'predict_proba'):
                # Use KernelExplainer for more compatibility
                self.explainer = shap.KernelExplainer(
                    self.model.predict_proba,
                    shap.sample(self.X_train, 100)
                )
            else:
                self.explainer = shap.KernelExplainer(
                    self.model.predict,
                    shap.sample(self.X_train, 100)
                )
            
            self.logger.info("  ✓ SHAP Explainer инициализирован успешно")
        
        except Exception as e:
            self.logger.error(f"  ✗ Ошибка SHAP: {str(e)}")
            self.explainer = None
    
    def calculate_shap_values(self) -> None:
        """
        Рассчитывает SHAP values для тестовых примеров
        """
        self.logger.info("\n2. Расчет SHAP values...")
        
        if self.explainer is None:
            self.logger.warning("  Explainer не инициализирован")
            return
        
        try:
            self.shap_values = self.explainer.shap_values(self.X_test)
            self.logger.info("  ✓ SHAP values рассчитаны успешно")
        except Exception as e:
            self.logger.error(f"  ✗ Ошибка расчета SHAP: {str(e)}")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Получает feature importance из модели или SHAP values
        """
        self.logger.info("\n3. Расчет Feature Importance...")
        
        importance = {}
        
        # Метод 1: Из модели (если поддерживается)
        if hasattr(self.model, 'feature_importances_'):
            try:
                importance = dict(zip(
                    self.feature_names,
                    self.model.feature_importances_
                ))
                self.logger.info("  ✓ Feature importance из модели")
            except Exception as e:
                self.logger.warning(f"  ✗ Ошибка: {str(e)}")
        
        # Метод 2: Из SHAP values
        if self.shap_values is not None:
            try:
                # For binary classification
                if isinstance(self.shap_values, list):
                    shap_val = np.abs(self.shap_values[1]).mean(axis=0)
                else:
                    shap_val = np.abs(self.shap_values).mean(axis=0)
                
                importance = dict(zip(self.feature_names, shap_val))
                self.logger.info("  ✓ Feature importance из SHAP")
            except Exception as e:
                self.logger.warning(f"  ✗ Ошибка SHAP: {str(e)}")
        
        # Сортировка по важности
        importance = dict(sorted(importance.items(), 
                                key=lambda x: abs(x[1]), 
                                reverse=True))
        
        self.logger.info(f"  Топ-5 признаков:")
        for i, (feat, imp) in enumerate(list(importance.items())[:5], 1):
            self.logger.info(f"    {i}. {feat}: {imp:.4f}")
        
        return importance
    
    def get_local_explanation(self, sample_idx: int, top_n: int = 5) -> Dict:
        """
        Получает локальное объяснение для конкретного примера
        Возвращает top-5 позитивных и негативных факторов
        """
        self.logger.info(f"\n4. Локальное объяснение для примера #{sample_idx}...")
        
        explanation = {
            'sample_id': sample_idx,
            'positive_factors': [],
            'negative_factors': [],
            'feature_contributions': {}
        }
        
        try:
            if self.shap_values is not None:
                # Get SHAP values for binary classification
                if isinstance(self.shap_values, list):
                    shap_val = self.shap_values[1][sample_idx]
                else:
                    shap_val = self.shap_values[sample_idx]
                
                # Combine with feature values
                contributions = []
                for feat_idx, feat_name in enumerate(self.feature_names):
                    try:
                        feat_value = self.X_test.iloc[sample_idx, feat_idx]
                        shap_contribution = float(shap_val[feat_idx])
                        
                        contributions.append({
                            'feature': feat_name,
                            'value': float(feat_value),
                            'contribution': shap_contribution
                        })
                    except:
                        pass
                
                # Sort by absolute contribution
                contributions = sorted(contributions, 
                                     key=lambda x: abs(x['contribution']), 
                                     reverse=True)
                
                # Top positive (push towards approval)
                explanation['positive_factors'] = [c for c in contributions[:top_n] 
                                                  if c['contribution'] > 0]
                
                # Top negative (push towards rejection)
                explanation['negative_factors'] = [c for c in contributions[:top_n] 
                                                  if c['contribution'] < 0]
                
                explanation['feature_contributions'] = contributions[:top_n*2]
        
        except Exception as e:
            self.logger.error(f"  ✗ Ошибка: {str(e)}")
        
        return explanation
    
    def generate_explanation_text(self, explanation: Dict, lang: str = 'ru') -> str:
        """
        Генерирует понятное текстовое объяснение на русском языке
        """
        text = f"\n📋 ОБЪЯСНЕНИЕ РЕШЕНИЯ (Пример #{explanation['sample_id']})\n"
        text += "=" * 60 + "\n\n"
        
        # Позитивные факторы
        if explanation['positive_factors']:
            text += "✅ ПОЗИТИВНЫЕ ФАКТОРЫ (за одобрение):\n"
            for i, factor in enumerate(explanation['positive_factors'], 1):
                impact = "СИЛЬНОЕ" if abs(factor['contribution']) > 0.1 else "СРЕДНЕЕ"
                text += f"  {i}. {factor['feature']}: {factor['value']:.2f}\n"
                text += f"     └─ Влияние: +{factor['contribution']:.4f} ({impact})\n\n"
        
        # Негативные факторы
        if explanation['negative_factors']:
            text += "\n❌ НЕГАТИВНЫЕ ФАКТОРЫ (против одобрения):\n"
            for i, factor in enumerate(explanation['negative_factors'], 1):
                impact = "СИЛЬНОЕ" if abs(factor['contribution']) > 0.1 else "СРЕДНЕЕ"
                text += f"  {i}. {factor['feature']}: {factor['value']:.2f}\n"
                text += f"     └─ Влияние: {factor['contribution']:.4f} ({impact})\n\n"
        
        text += "=" * 60 + "\n"
        
        return text
    
    def visualize_global_explanation(self) -> None:
        """
        Визуализирует глобальное объяснение (importantes признаки)
        """
        self.logger.info("\n5. Визуализация глобального объяснения...")
        
        try:
            importance = self.get_feature_importance()
            
            if not importance:
                self.logger.warning("  Нет данных для визуализации")
                return
            
            # Top 15 features
            top_features = dict(list(importance.items())[:15])
            
            fig, ax = plt.subplots(figsize=(10, 6))
            features = list(top_features.keys())
            values = list(top_features.values())
            
            ax.barh(features, values, color='steelblue')
            ax.set_xlabel('Важность', fontweight='bold')
            ax.set_title('Top-15 Наиболее важных признаков', fontweight='bold')
            ax.invert_yaxis()
            
            plt.tight_layout()
            plt.savefig(self.output_dir / '01_feature_importance.png', 
                       dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info("  ✓ График сохранен")
        
        except Exception as e:
            self.logger.error(f"  ✗ Ошибка визуализации: {str(e)}")
    
    def visualize_local_explanation(self, sample_idx: int) -> None:
        """
        Визуализирует локальное объяснение (waterfall chart)
        """
        self.logger.info(f"\n6. Визуализация локального объяснения (примера #{sample_idx})...")
        
        try:
            explanation = self.get_local_explanation(sample_idx, top_n=5)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            contributions = explanation['feature_contributions'][:10]
            features = [c['feature'] for c in contributions]
            values = [c['contribution'] for c in contributions]
            colors = ['green' if v > 0 else 'red' for v in values]
            
            ax.barh(features, values, color=colors)
            ax.set_xlabel('Вклад в решение', fontweight='bold')
            ax.set_title(f'Факторы, влияющие на решение (Пример #{sample_idx})', 
                        fontweight='bold')
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
            ax.invert_yaxis()
            
            plt.tight_layout()
            plt.savefig(self.output_dir / f'02_local_explanation_{sample_idx}.png',
                       dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info("  ✓ График сохранен")
        
        except Exception as e:
            self.logger.error(f"  ✗ Ошибка визуализации: {str(e)}")
    
    def generate_html_report(self, explanations: List[Dict]) -> None:
        """
        Генерирует HTML отчет с объяснениями
        """
        self.logger.info("\n7. Генерация HTML отчета...")
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Model Explanations Report</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1000px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }
                h1 { color: #2c3e50; border-bottom: 3px solid #3498db; }
                .explanation { margin: 20px 0; padding: 15px; background-color: #ecf0f1; border-radius: 5px; border-left: 4px solid #3498db; }
                .positive { color: #27ae60; font-weight: bold; }
                .negative { color: #e74c3c; font-weight: bold; }
                img { max-width: 100%; height: auto; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Отчет об объяснении решений</h1>
        """
        
        # Add explanations
        for exp in explanations[:10]:  # First 10
            html += f"""
                <div class="explanation">
                    <h3>Пример #{exp['sample_id']}</h3>
                    <p><span class="positive">✅ Позитивные факторы:</span>
            """
            
            for factor in exp['positive_factors'][:3]:
                html += f"<br>  - {factor['feature']}: {factor['value']:.2f}"
            
            html += "</p><p>"
            html += f"""<span class="negative">❌ Негативные факторы:</span>"""
            
            for factor in exp['negative_factors'][:3]:
                html += f"<br>  - {factor['feature']}: {factor['value']:.2f}"
            
            html += "</p></div>"
        
        html += """
            </div>
        </body>
        </html>
        """
        
        report_path = self.output_dir / 'explanations_report.html'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info(f"  ✓ Отчет сохранен: {report_path}")
    
    def run_full_explanation(self) -> Dict[str, any]:
        """
        Запускает полный процесс объяснения
        """
        self.logger.info("=" * 60)
        self.logger.info("НАЧАЛО АНАЛИЗА ОБЪЯСНИМОСТИ ПРЕДСКАЗАНИЙ")
        self.logger.info("=" * 60)
        
        self.initialize_shap_explainer()
        self.calculate_shap_values()
        importance = self.get_feature_importance()
        self.visualize_global_explanation()
        
        # Generate explanations for top 10 samples
        explanations = []
        for i in range(min(10, len(self.X_test))):
            exp = self.get_local_explanation(i, top_n=5)
            explanations.append(exp)
            self.visualize_local_explanation(i)
        
        self.generate_html_report(explanations)
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("АНАЛИЗ ОБЪЯСНИМОСТИ ЗАВЕРШЕН")
        self.logger.info("=" * 60)
        
        return {
            'feature_importance': importance,
            'explanations': explanations
        }


if __name__ == '__main__':
    # Example usage
    model = joblib.load('models/best_model.pkl')
    X_train = pd.read_csv('data/X_train.csv')
    X_test = pd.read_csv('data/X_test.csv')
    
    explainer = ExplainablePredictions(model, X_train, X_test)
    results = explainer.run_full_explanation()
