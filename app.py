"""
SubsiSmart KZ - Веб-интерфейс
Flask приложение для визуализации и интерактивного анализа
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from scoring_engine import SubsidyScoring
import json
import os

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Глобальные переменные для хранения данных
scoring_system = None
df_processed = None

def initialize_system():
    """Инициализация системы скоринга"""
    global scoring_system, df_processed
    
    if scoring_system is None:
        scoring_system = SubsidyScoring()
        
        # Проверяем наличие файла данных
        data_file = 'data/Выгрузка_по_выданным_субсидиям_2025_год__обезлич_.xlsx'
        if os.path.exists(data_file):
            df = pd.read_excel(data_file, skiprows=4)
            df_processed = scoring_system.preprocess_data(df)
            df_processed, _ = scoring_system.create_kmeans_segments(df_processed)
            df_processed = scoring_system.detect_anomalies(df_processed)
            df_processed = scoring_system.calculate_risk_score(df_processed)

@app.route('/')
def index():
    """Главная страница"""
    initialize_system()
    return render_template('index.html')

@app.route('/api/dashboard_stats')
def dashboard_stats():
    """API для получения статистики дашборда"""
    initialize_system()
    
    if df_processed is None:
        return jsonify({'error': 'Данные не загружены'}), 500
    
    stats = {
        'total_applications': int(len(df_processed)),
        'total_amount': float(df_processed['Причитающая сумма'].sum()),
        'avg_amount': float(df_processed['Причитающая сумма'].mean()),
        'high_risk_count': int((df_processed['Risk_Level'] == 'High Risk').sum()),
        'executed_percent': float((df_processed['Статус заявки'] == 'Исполнена').sum() / len(df_processed) * 100),
        'approved_percent': float((df_processed['Статус заявки'] == 'Одобрена').sum() / len(df_processed) * 100),
        'rejected_percent': float((df_processed['Статус заявки'] == 'Отклонена').sum() / len(df_processed) * 100),
    }
    
    return jsonify(stats)

@app.route('/api/regional_analysis')
def regional_analysis():
    """API для регионального анализа"""
    initialize_system()
    
    if df_processed is None:
        return jsonify({'error': 'Данные не загружены'}), 500
    
    regional_report = scoring_system.regional_report(df_processed)
    
    # Преобразуем в формат для графика
    data = []
    for region, row in regional_report.head(10).iterrows():
        data.append({
            'region': region,
            'total': int(row['Всего заявок']),
            'executed_percent': float(row['Процент исполненных']),
            'approved_percent': float(row['Процент одобренных']),
            'rejected_percent': float(row['Процент отклоненных']),
            'total_amount': float(row['Общая сумма субсидий'])
        })
    
    return jsonify(data)

@app.route('/api/cluster_analysis')
def cluster_analysis():
    """API для анализа кластеров"""
    initialize_system()
    
    if df_processed is None:
        return jsonify({'error': 'Данные не загружены'}), 500
    
    # Статистика по кластерам
    cluster_stats = df_processed.groupby('Кластер').agg({
        'Норматив': 'mean',
        'Причитающая сумма': 'mean',
        'Статус заявки': 'count'
    }).reset_index()
    
    cluster_stats.columns = ['cluster', 'avg_normativ', 'avg_amount', 'count']
    
    return jsonify(cluster_stats.to_dict('records'))

@app.route('/api/risk_distribution')
def risk_distribution():
    """API для распределения рисков"""
    initialize_system()
    
    if df_processed is None:
        return jsonify({'error': 'Данные не загружены'}), 500
    
    risk_dist = df_processed['Risk_Level'].value_counts().to_dict()
    
    data = [
        {'level': 'Normal', 'count': risk_dist.get('Normal', 0)},
        {'level': 'Medium Risk', 'count': risk_dist.get('Medium Risk', 0)},
        {'level': 'High Risk', 'count': risk_dist.get('High Risk', 0)}
    ]
    
    return jsonify(data)

@app.route('/api/monthly_trend')
def monthly_trend():
    """API для анализа трендов по месяцам"""
    initialize_system()
    
    if df_processed is None:
        return jsonify({'error': 'Данные не загружены'}), 500
    
    monthly_data = df_processed.groupby('Месяц').agg({
        'Номер заявки': 'count',
        'Причитающая сумма': 'sum'
    }).reset_index()
    
    monthly_data.columns = ['month', 'applications', 'total_amount']
    
    months_ru = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    
    monthly_data['month_name'] = monthly_data['month'].map(months_ru)
    
    return jsonify(monthly_data.to_dict('records'))

@app.route('/api/direction_analysis')
def direction_analysis():
    """API для анализа по направлениям"""
    initialize_system()
    
    if df_processed is None:
        return jsonify({'error': 'Данные не загружены'}), 500
    
    direction_stats = df_processed.groupby('Направление водства').agg({
        'Номер заявки': 'count',
        'Причитающая сумма': 'sum',
        'Risk_Score': 'mean'
    }).reset_index()
    
    direction_stats.columns = ['direction', 'count', 'total_amount', 'avg_risk_score']
    direction_stats = direction_stats.sort_values('total_amount', ascending=False).head(8)
    
    return jsonify(direction_stats.to_dict('records'))

@app.route('/api/search_applications')
def search_applications():
    """API для поиска заявок"""
    initialize_system()
    
    if df_processed is None:
        return jsonify({'error': 'Данные не загружены'}), 500
    
    # Параметры фильтрации
    region = request.args.get('region', None)
    risk_level = request.args.get('risk_level', None)
    status = request.args.get('status', None)
    limit = int(request.args.get('limit', 50))
    
    df_filtered = df_processed.copy()
    
    if region:
        df_filtered = df_filtered[df_filtered['Область'] == region]
    
    if risk_level:
        df_filtered = df_filtered[df_filtered['Risk_Level'] == risk_level]
    
    if status:
        df_filtered = df_filtered[df_filtered['Статус заявки'] == status]
    
    # Сортируем по Risk Score
    df_filtered = df_filtered.sort_values('Risk_Score', ascending=False).head(limit)
    
    # Выбираем нужные колонки
    result = df_filtered[[
        'Номер заявки', 'Дата поступления', 'Область', 'Направление водства',
        'Статус заявки', 'Норматив', 'Причитающая сумма', 'Risk_Level', 'Risk_Score', 'Кластер'
    ]].copy()
    
    # Преобразуем дату в строку
    result['Дата поступления'] = result['Дата поступления'].astype(str)
    
    return jsonify(result.to_dict('records'))

@app.route('/api/filters')
def get_filters():
    """API для получения списка фильтров"""
    initialize_system()
    
    if df_processed is None:
        return jsonify({'error': 'Данные не загружены'}), 500
    
    filters = {
        'regions': sorted(df_processed['Область'].unique().tolist()),
        'risk_levels': ['Normal', 'Medium Risk', 'High Risk'],
        'statuses': sorted(df_processed['Статус заявки'].unique().tolist()),
        'directions': sorted(df_processed['Направление водства'].unique().tolist())
    }
    
    return jsonify(filters)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
