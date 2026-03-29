"""
Демонстрационный скрипт SubsiSmart KZ
Быстрая проверка работоспособности системы
"""

import pandas as pd
from scoring_engine import SubsidyScoring

def quick_demo():
    """Быстрая демонстрация возможностей системы"""
    
    print("="*80)
    print("SubsiSmart KZ - Демонстрация возможностей")
    print("="*80)
    print()
    
    # Загрузка данных
    print("📊 Загрузка демо-данных...")
    try:
        df = pd.read_excel('data/Выгрузка_по_выданным_субсидиям_2025_год__обезлич_.xlsx', 
                          skiprows=4, nrows=1000)  # Загружаем только 1000 строк для демо
        print(f"✓ Загружено {len(df)} записей для демонстрации")
    except FileNotFoundError:
        print("❌ Файл данных не найден!")
        print("   Поместите файл в папку data/")
        return
    
    print()
    
    # Инициализация
    scoring = SubsidyScoring()
    
    # 1. Предобработка
    print("🔧 Предобработка данных...")
    df_processed = scoring.preprocess_data(df)
    print(f"✓ Обработано признаков: {df_processed.shape[1]}")
    print()
    
    # 2. Кластеризация
    print("🎯 K-Means кластеризация...")
    df_processed, cluster_analysis = scoring.create_kmeans_segments(df_processed, n_clusters=4)
    print("✓ Создано 4 кластера")
    print("\nХарактеристики кластеров:")
    print(cluster_analysis)
    print()
    
    # 3. Детектирование аномалий
    print("🚨 Детектирование аномалий...")
    df_processed = scoring.detect_anomalies(df_processed)
    risk_counts = df_processed['Risk_Level'].value_counts()
    print(f"✓ Normal: {risk_counts.get('Normal', 0)}")
    print(f"✓ Medium Risk: {risk_counts.get('Medium Risk', 0)}")
    print(f"✓ High Risk: {risk_counts.get('High Risk', 0)}")
    print()
    
    # 4. Примеры заявок с высоким риском
    print("⚠️  Примеры заявок с высоким риском:")
    high_risk = df_processed[df_processed['Risk_Level'] == 'High Risk'].head(3)
    
    for idx, row in high_risk.iterrows():
        print(f"\n  Заявка №{row['Номер заявки']}")
        print(f"  Область: {row['Область']}")
        print(f"  Норматив: {row['Норматив']:,.0f} тенге")
        print(f"  Причитающая сумма: {row['Причитающая сумма']:,.0f} тенге")
        print(f"  Превышение: {row['Превышение']:,.0f} тенге")
        print(f"  Статус: {row['Статус заявки']}")
    
    print()
    print("="*80)
    print("✅ Демонстрация завершена!")
    print()
    print("Для полного анализа запустите: python scoring_engine.py")
    print("Для веб-интерфейса запустите: python app.py")
    print("="*80)

if __name__ == "__main__":
    quick_demo()
