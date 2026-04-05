"""
БЛОК 2: Разведочный анализ данных (EDA)
Comprehensive exploratory data analysis of agricultural subsidy data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
from typing import Dict, List
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats

logger = logging.getLogger(__name__)

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class ExploratoryDataAnalysis:
    """Класс для разведочного анализа данных о субсидиях"""
    
    def __init__(self, df: pd.DataFrame, output_dir: str = 'results/eda'):
        self.df = df.copy()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        self.report = {}
    
    def analyze_target_distribution(self) -> Dict:
        """
        Анализирует распределение целевой переменной (статус заявки)
        """
        self.logger.info("\n1. Анализ распределения целевой переменной...")
        
        # Поиск столбца статуса
        status_cols = [col for col in self.df.columns 
                      if any(term in col.lower() for term in ['статус', 'status', 'decision'])]
        
        if not status_cols:
            self.logger.warning("Столбец статуса не найден")
            return {}
        
        status_col = status_cols[0]
        
        # Análisis
        distribution = self.df[status_col].value_counts()
        distribution_pct = self.df[status_col].value_counts(normalize=True) * 100
        
        # Check for class imbalance
        class_balance = distribution.min() / distribution.max() * 100
        imbalance_level = "Сильный перекос" if class_balance < 20 else (
            "Умеренный перекос" if class_balance < 40 else "Сбалансирован"
        )
        
        result = {
            'status_column': status_col,
            'distribution': distribution.to_dict(),
            'distribution_pct': distribution_pct.to_dict(),
            'class_imbalance_pct': class_balance,
            'imbalance_level': imbalance_level
        }
        
        self.logger.info(f"✓ Столбец статуса: {status_col}")
        self.logger.info(f"  Распределение:\n{distribution}")
        self.logger.info(f"  Уровень дисбаланса: {imbalance_level} ({class_balance:.1f}%)")
        
        # Визуализация
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        distribution.plot(kind='bar', ax=axes[0], color='steelblue')
        axes[0].set_title('Распределение классов', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('Количество')
        axes[0].tick_params(axis='x', rotation=45)
        
        distribution_pct.plot(kind='pie', ax=axes[1], autopct='%1.1f%%')
        axes[1].set_title('Процент классов', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '01_target_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.report['target_distribution'] = result
        return result
    
    def analyze_correlation(self) -> Dict:
        """
        Строит корреляционную матрицу для всех числовых признаков
        """
        self.logger.info("\n2. Анализ корреляций...")
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            self.logger.warning("Недостаточно числовых столбцов для анализа корреляций")
            return {}
        
        correlation_matrix = self.df[numeric_cols].corr()
        
        # Find strong correlations
        strong_corr = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                if abs(correlation_matrix.iloc[i, j]) > 0.7:
                    strong_corr.append({
                        'var1': correlation_matrix.columns[i],
                        'var2': correlation_matrix.columns[j],
                        'correlation': correlation_matrix.iloc[i, j]
                    })
        
        self.logger.info(f"✓ Числовые столбцы: {len(numeric_cols)}")
        self.logger.info(f"  Сильные корреляции (|r| > 0.7): {len(strong_corr)}")
        for corr in strong_corr[:5]:  # Show top 5
            self.logger.info(f"    {corr['var1']} ↔ {corr['var2']}: {corr['correlation']:.3f}")
        
        # Visualization
        plt.figure(figsize=(12, 10))
        sns.heatmap(correlation_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                    center=0, square=True, linewidths=1)
        plt.title('Матрица корреляций', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / '02_correlation_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.report['correlation'] = {
            'matrix': correlation_matrix.to_dict(),
            'strong_correlations': strong_corr
        }
        return self.report['correlation']
    
    def analyze_outliers(self) -> Dict:
        """
        Создает боксплоты для выявления выбросов по ключевым признакам
        """
        self.logger.info("\n3. Анализ выбросов...")
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            self.logger.warning("Нет числовых столбцов для анализа выбросов")
            return {}
        
        # Select top numeric columns
        numeric_cols = numeric_cols[:min(6, len(numeric_cols))]
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        outliers_summary = {}
        
        for idx, col in enumerate(numeric_cols):
            if idx < len(axes):
                # Box plot
                sns.boxplot(data=self.df, y=col, ax=axes[idx], color='lightblue')
                axes[idx].set_title(f'Выбросы: {col}', fontweight='bold')
                
                # Calculate outliers (IQR method)
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                outlier_count = ((self.df[col] < Q1 - 1.5*IQR) | 
                                (self.df[col] > Q3 + 1.5*IQR)).sum()
                
                outliers_summary[col] = {
                    'outlier_count': int(outlier_count),
                    'outlier_pct': float((outlier_count / len(self.df)) * 100)
                }
                
                self.logger.info(f"  {col}: {outlier_count} выбросов ({outliers_summary[col]['outlier_pct']:.2f}%)")
        
        # Hide unused subplots
        for idx in range(len(numeric_cols), len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / '03_outliers_boxplot.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.report['outliers'] = outliers_summary
        return outliers_summary
    
    def analyze_by_groups(self) -> Dict:
        """
        Анализирует распределение по регионам и типам субсидий
        """
        self.logger.info("\n4. Анализ по группам (регионы, типы)...")
        
        # Find grouping columns
        region_cols = [col for col in self.df.columns 
                      if any(term in col.lower() for term in ['регион', 'область', 'region'])]
        type_cols = [col for col in self.df.columns 
                    if any(term in col.lower() for term in ['тип', 'направ', 'type', 'category'])]
        
        results = {}
        
        # By region
        if region_cols:
            region_col = region_cols[0]
            region_stats = self.df[region_col].value_counts().head(10)
            results['top_regions'] = region_stats.to_dict()
            
            fig, ax = plt.subplots(figsize=(12, 6))
            region_stats.plot(kind='barh', ax=ax, color='steelblue')
            ax.set_title(f'Топ-10 регионов по количеству заявок', fontweight='bold')
            ax.set_xlabel('Количество заявок')
            plt.tight_layout()
            plt.savefig(self.output_dir / '04_top_regions.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"✓ Топ регионов:\n{region_stats}")
        
        # By type
        if type_cols:
            type_col = type_cols[0]
            type_stats = self.df[type_col].value_counts()
            results['subsidy_types'] = type_stats.to_dict()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            type_stats.plot(kind='barh', ax=ax, color='coral')
            ax.set_title(f'Распределение по типам субсидий', fontweight='bold')
            ax.set_xlabel('Количество')
            plt.tight_layout()
            plt.savefig(self.output_dir / '04_subsidy_types.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"✓ Типы субсидий:\n{type_stats}")
        
        self.report['group_analysis'] = results
        return results
    
    def analyze_statistics_by_status(self) -> Dict:
        """
        Рассчитывает базовую статистику по группам (получившие/не получившие субсидию)
        """
        self.logger.info("\n5. Базовая статистика по статусу...")
        
        status_cols = [col for col in self.df.columns 
                      if any(term in col.lower() for term in ['статус', 'status'])]
        
        if not status_cols:
            return {}
        
        status_col = status_cols[0]
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        result = {}
        
        for status in self.df[status_col].unique():
            subset = self.df[self.df[status_col] == status]
            stats = subset[numeric_cols].describe().to_dict()
            result[str(status)] = stats
            
            self.logger.info(f"\n{status}:")
            self.logger.info(f"  Количество: {len(subset)}")
            for col in numeric_cols[:3]:  # Show first 3
                self.logger.info(f"  {col}: mean={subset[col].mean():.2f}, std={subset[col].std():.2f}")
        
        self.report['statistics_by_status'] = result
        return result
    
    def generate_html_report(self) -> None:
        """
        Генерирует HTML отчет со всеми анализами
        """
        self.logger.info("\n6. Генерация HTML отчета...")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EDA Report - Agricultural Subsidy System</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background-color: #ecf0f1; border-radius: 5px; }}
                .metric-label {{ font-size: 12px; color: #7f8c8d; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                img {{ max-width: 100%; height: auto; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .report-generated {{ color: #7f8c8d; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Отчет Разведочного Анализа Данных (EDA)</h1>
                <p>Система скоринга субсидий для сельхозпроизводителей Казахстана</p>
                
                <h2>📈 Распределение целевой переменной</h2>
                <img src="01_target_distribution.png" alt="Target Distribution">
                
                <h2>🔗 Корреляционная матрица</h2>
                <img src="02_correlation_matrix.png" alt="Correlation Matrix">
                
                <h2>📊 Анализ выбросов</h2>
                <img src="03_outliers_boxplot.png" alt="Outliers">
                
                <h2>🌍 Анализ по регионам и типам</h2>
                <img src="04_top_regions.png" alt="Top Regions">
                <img src="04_subsidy_types.png" alt="Subsidy Types">
                
                <h2>📋 Основные метрики</h2>
                <div>
                    <div class="metric">
                        <div class="metric-label">Всего строк</div>
                        <div class="metric-value">{len(self.df):,}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Всего признаков</div>
                        <div class="metric-value">{len(self.df.columns)}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Числовые столбцы</div>
                        <div class="metric-value">{len(self.df.select_dtypes(include=[np.number]).columns)}</div>
                    </div>
                </div>
                
                <div class="report-generated">
                    Отчет сгенерирован: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """
        
        report_path = self.output_dir / 'EDA_Report.html'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"✓ HTML отчет сохранен: {report_path}")
    
    def run_full_analysis(self) -> Dict:
        """
        Запускает полный EDA анализ
        """
        self.logger.info("=" * 60)
        self.logger.info("НАЧАЛО РАЗВЕДОЧНОГО АНАЛИЗА ДАННЫХ (EDA)")
        self.logger.info("=" * 60)
        
        self.analyze_target_distribution()
        self.analyze_correlation()
        self.analyze_outliers()
        self.analyze_by_groups()
        self.analyze_statistics_by_status()
        self.generate_html_report()
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("EDA АНАЛИЗ ЗАВЕРШЕН")
        self.logger.info("=" * 60)
        
        return self.report


if __name__ == '__main__':
    # Example usage
    df = pd.read_csv('data/processed_data.csv')
    eda = ExploratoryDataAnalysis(df)
    report = eda.run_full_analysis()
