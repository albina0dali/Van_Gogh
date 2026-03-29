"""
SubsiSmart KZ - AI-скоринг для государственных субсидий Казахстана
Автор: Команда разработки SubsiSmart KZ
Дата: Март 2025
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class SubsidyScoring:
    """Класс для AI-скоринга заявок на субсидии"""
    
    def __init__(self):
        self.label_encoders = {}
        self.kmeans_model = None
        self.scaler = StandardScaler()
        
    def preprocess_data(self, df):
        """
        Функция предобработки данных
        
        Преобразует дату в признаки (месяц, день недели),
        кодирует 'Область' и 'Направление водства' через LabelEncoder
        """
        # Создаем копию датафрейма
        df_processed = df.copy()
        
        # Удаляем пустые столбцы
        df_processed = df_processed.drop(['Unnamed: 2', 'Unnamed: 3'], axis=1, errors='ignore')
        
        # Удаляем строки с NaN
        df_processed = df_processed.dropna(subset=['Дата поступления', 'Область', 
                                                     'Направление водства', 'Статус заявки'])
        
        # Преобразование даты
        df_processed['Дата поступления'] = pd.to_datetime(df_processed['Дата поступления'], 
                                                           format='%d.%m.%Y %H:%M:%S', 
                                                           errors='coerce')
        
        # Извлекаем признаки из даты
        df_processed['Месяц'] = df_processed['Дата поступления'].dt.month
        df_processed['День_недели'] = df_processed['Дата поступления'].dt.dayofweek
        df_processed['Час'] = df_processed['Дата поступления'].dt.hour
        df_processed['Квартал'] = df_processed['Дата поступления'].dt.quarter
        
        # Кодирование категориальных признаков
        categorical_features = ['Область', 'Направление водства', 'Статус заявки']
        
        for feature in categorical_features:
            le = LabelEncoder()
            df_processed[f'{feature}_encoded'] = le.fit_transform(df_processed[feature].astype(str))
            self.label_encoders[feature] = le
        
        return df_processed
    
    def create_kmeans_segments(self, df, n_clusters=4):
        """
        Создает модель K-Means для сегментации заявителей на группы
        по признакам 'Норматив' и 'Причитающая сумма'
        """
        # Подготовка данных для кластеризации
        features_for_clustering = df[['Норматив', 'Причитающая сумма']].copy()
        
        # Удаляем строки с NaN
        features_for_clustering = features_for_clustering.dropna()
        
        # Стандартизация данных
        features_scaled = self.scaler.fit_transform(features_for_clustering)
        
        # Обучение модели K-Means
        self.kmeans_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = self.kmeans_model.fit_predict(features_scaled)
        
        # Добавляем кластеры в датафрейм
        df.loc[features_for_clustering.index, 'Кластер'] = clusters
        
        # Анализ кластеров
        cluster_analysis = df.groupby('Кластер').agg({
            'Норматив': ['mean', 'median', 'std'],
            'Причитающая сумма': ['mean', 'median', 'std'],
            'Статус заявки': lambda x: (x == 'Исполнена').sum() / len(x) * 100
        }).round(2)
        
        return df, cluster_analysis
    
    def detect_anomalies(self, df):
        """
        Проверка на аномалии: если 'Причитающая сумма' превышает 'Норматив' 
        более чем на 3 стандартных отклонения в рамках одной категории,
        помечает заявку как 'High Risk'
        """
        # Создаем колонку для рисков
        df['Risk_Level'] = 'Normal'
        
        # Вычисляем разницу между причитающей суммой и нормативом
        df['Превышение'] = df['Причитающая сумма'] - df['Норматив']
        
        # Группируем по направлению и вычисляем статистику
        for direction in df['Направление водства'].unique():
            mask = df['Направление водства'] == direction
            subset = df[mask]
            
            if len(subset) > 1:
                mean_excess = subset['Превышение'].mean()
                std_excess = subset['Превышение'].std()
                
                # Если превышение больше 3 стандартных отклонений
                threshold = mean_excess + 3 * std_excess
                high_risk_mask = (df['Направление водства'] == direction) & (df['Превышение'] > threshold)
                df.loc[high_risk_mask, 'Risk_Level'] = 'High Risk'
                
                # Дополнительная проверка: слишком большая причитающая сумма относительно норматива
                ratio_threshold = 3  # Если сумма в 3+ раза больше норматива
                ratio_mask = (df['Направление водства'] == direction) & \
                            (df['Причитающая сумма'] > df['Норматив'] * ratio_threshold)
                df.loc[ratio_mask, 'Risk_Level'] = 'High Risk'
        
        # Проверка на нулевую причитающую сумму при ненулевом нормативе
        zero_sum_mask = (df['Причитающая сумма'] == 0) & (df['Норматив'] > 0)
        df.loc[zero_sum_mask, 'Risk_Level'] = 'Medium Risk'
        
        return df
    
    def regional_report(self, df):
        """
        Выводит отчет: какие регионы имеют самый высокий процент 'Исполненных' заявок
        """
        # Группируем по областям
        regional_stats = df.groupby('Область').agg({
            'Статус заявки': [
                'count',
                lambda x: (x == 'Исполнена').sum(),
                lambda x: (x == 'Исполнена').sum() / len(x) * 100,
                lambda x: (x == 'Одобрена').sum() / len(x) * 100,
                lambda x: (x == 'Отклонена').sum() / len(x) * 100
            ],
            'Причитающая сумма': ['sum', 'mean']
        }).round(2)
        
        # Переименовываем колонки
        regional_stats.columns = [
            'Всего заявок', 
            'Исполнено', 
            'Процент исполненных',
            'Процент одобренных',
            'Процент отклоненных',
            'Общая сумма субсидий',
            'Средняя сумма'
        ]
        
        # Сортируем по проценту исполненных заявок
        regional_stats = regional_stats.sort_values('Процент исполненных', ascending=False)
        
        return regional_stats
    
    def calculate_risk_score(self, df):
        """
        Вычисляет общий risk score для каждой заявки
        на основе нескольких факторов
        """
        df['Risk_Score'] = 0
        
        # Фактор 1: Аномальное превышение суммы
        df.loc[df['Risk_Level'] == 'High Risk', 'Risk_Score'] += 50
        df.loc[df['Risk_Level'] == 'Medium Risk', 'Risk_Score'] += 25
        
        # Фактор 2: Статус заявки
        df.loc[df['Статус заявки'] == 'Отклонена', 'Risk_Score'] += 30
        df.loc[df['Статус заявки'] == 'Отозвано', 'Risk_Score'] += 20
        
        # Фактор 3: Необычное время подачи (ночное время)
        df.loc[(df['Час'] >= 0) & (df['Час'] <= 6), 'Risk_Score'] += 10
        
        # Фактор 4: Очень большая причитающая сумма (топ 5%)
        threshold_95 = df['Причитающая сумма'].quantile(0.95)
        df.loc[df['Причитающая сумма'] > threshold_95, 'Risk_Score'] += 15
        
        return df
    
    def generate_full_report(self, df):
        """
        Генерирует полный отчет по всем метрикам
        """
        report = {
            'total_applications': len(df),
            'status_distribution': df['Статус заявки'].value_counts().to_dict(),
            'total_subsidy_amount': df['Причитающая сумма'].sum(),
            'average_subsidy': df['Причитающая сумма'].mean(),
            'high_risk_applications': (df['Risk_Level'] == 'High Risk').sum(),
            'regions_count': df['Область'].nunique(),
            'directions_count': df['Направление водства'].nunique(),
        }
        
        return report


def main():
    """Основная функция для демонстрации работы системы"""
    
    print("="*80)
    print("SubsiSmart KZ - AI-скоринг для государственных субсидий")
    print("="*80)
    print()
    
    # Инициализация системы скоринга
    scoring = SubsidyScoring()
    
    # Загрузка данных
    print("📊 Загрузка данных...")
    df = pd.read_excel('data/Выгрузка_по_выданным_субсидиям_2025_год__обезлич_.xlsx', skiprows=4)
    print(f"✓ Загружено записей: {len(df)}")
    print()
    
    # 1. Предобработка данных
    print("🔧 Этап 1: Предобработка данных...")
    df_processed = scoring.preprocess_data(df)
    print(f"✓ Данные обработаны: {len(df_processed)} записей")
    print(f"✓ Добавлено признаков из даты: Месяц, День недели, Час, Квартал")
    print(f"✓ Закодированы категории: Область, Направление водства, Статус заявки")
    print()
    
    # 2. Кластеризация K-Means
    print("🎯 Этап 2: Сегментация заявителей (K-Means)...")
    df_processed, cluster_analysis = scoring.create_kmeans_segments(df_processed, n_clusters=4)
    print("✓ Создано 4 кластера по признакам: Норматив и Причитающая сумма")
    print("\n📈 Характеристики кластеров:")
    print(cluster_analysis)
    print()
    
    # 3. Детектирование аномалий
    print("🚨 Этап 3: Детектирование аномалий...")
    df_processed = scoring.detect_anomalies(df_processed)
    risk_counts = df_processed['Risk_Level'].value_counts()
    print(f"✓ Анализ рисков завершен:")
    print(f"  - Normal: {risk_counts.get('Normal', 0)}")
    print(f"  - Medium Risk: {risk_counts.get('Medium Risk', 0)}")
    print(f"  - High Risk: {risk_counts.get('High Risk', 0)}")
    print()
    
    # 4. Региональный отчет
    print("🗺️  Этап 4: Региональный анализ...")
    regional_report = scoring.regional_report(df_processed)
    print("\n📊 ТОП-10 регионов по проценту исполненных заявок:")
    print(regional_report.head(10))
    print()
    
    # 5. Расчет risk score
    print("⚠️  Этап 5: Расчет общего risk score...")
    df_processed = scoring.calculate_risk_score(df_processed)
    print(f"✓ Risk score рассчитан для всех заявок")
    print(f"\nСтатистика Risk Score:")
    print(df_processed['Risk_Score'].describe())
    print()
    
    # 6. Полный отчет
    print("📋 Этап 6: Генерация итогового отчета...")
    full_report = scoring.generate_full_report(df_processed)
    print("\n" + "="*80)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("="*80)
    print(f"Всего заявок: {full_report['total_applications']:,}")
    print(f"Общая сумма субсидий: {full_report['total_subsidy_amount']:,.2f} тенге")
    print(f"Средняя субсидия: {full_report['average_subsidy']:,.2f} тенге")
    print(f"Заявок с высоким риском: {full_report['high_risk_applications']}")
    print(f"Количество регионов: {full_report['regions_count']}")
    print(f"Направлений деятельности: {full_report['directions_count']}")
    print("\nРаспределение по статусам:")
    for status, count in full_report['status_distribution'].items():
        print(f"  {status}: {count:,}")
    print("="*80)
    
    # Сохраняем обработанные данные
    print("\n💾 Сохранение результатов...")
    df_processed.to_csv('results/processed_data.csv', index=False, encoding='utf-8-sig')
    regional_report.to_csv('results/regional_report.csv', encoding='utf-8-sig')
    print("✓ Результаты сохранены в папку 'results/'")
    print()
    print("✅ Анализ завершен успешно!")
    

if __name__ == "__main__":
    main()
