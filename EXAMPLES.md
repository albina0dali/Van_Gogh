# Примеры использования SubsiSmart KZ

## Сценарий 1: Консольный анализ полного датасета

```bash
# Запуск полного анализа
python scoring_engine.py
```

**Выход:**
```
================================================================================
SubsiSmart KZ - AI-скоринг для государственных субсидий
================================================================================

📊 Загрузка данных...
✓ Загружено записей: 36651

🔧 Этап 1: Предобработка данных...
✓ Данные обработаны: 36651 записей
✓ Добавлено признаков из даты: Месяц, День недели, Час, Квартал
✓ Закодированы категории: Область, Направление водства, Статус заявки

🎯 Этап 2: Сегментация заявителей (K-Means)...
✓ Создано 4 кластера по признакам: Норматив и Причитающая сумма

📈 Характеристики кластеров:
[таблица с характеристиками]

🚨 Этап 3: Детектирование аномалий...
✓ Анализ рисков завершен:
  - Normal: 33450
  - Medium Risk: 2309
  - High Risk: 892

🗺️  Этап 4: Региональный анализ...
📊 ТОП-10 регионов по проценту исполненных заявок:
[таблица с регионами]

⚠️  Этап 5: Расчет общего risk score...
✓ Risk score рассчитан для всех заявок

================================================================================
ИТОГОВЫЙ ОТЧЕТ
================================================================================
Всего заявок: 36,651
Общая сумма субсидий: 139,384,738,000.00 тенге
Средняя субсидия: 3,801,413.25 тенге
Заявок с высоким риском: 892
Количество регионов: 18
Направлений деятельности: 9
================================================================================

💾 Сохранение результатов...
✓ Результаты сохранены в папку 'results/'

✅ Анализ завершен успешно!
```

---

## Сценарий 2: Быстрая демонстрация (первые 1000 записей)

```bash
# Запуск демо
python demo.py
```

**Использование:** Для быстрой проверки работоспособности системы без полной обработки датасета.

---

## Сценарий 3: Запуск веб-интерфейса

```bash
# Запуск Flask сервера
python app.py
```

**Выход:**
```
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.100:5000
```

**Затем:**
1. Откройте браузер
2. Перейдите на http://localhost:5000
3. Интерактивная работа с дашбордом

---

## Сценарий 4: Использование как библиотеки

```python
from scoring_engine import SubsidyScoring
import pandas as pd

# Инициализация
scoring = SubsidyScoring()

# Загрузка своих данных
df = pd.read_excel('my_data.xlsx')

# Обработка
df_processed = scoring.preprocess_data(df)
df_processed, clusters = scoring.create_kmeans_segments(df_processed)
df_processed = scoring.detect_anomalies(df_processed)
df_processed = scoring.calculate_risk_score(df_processed)

# Получение отчетов
regional_report = scoring.regional_report(df_processed)
full_report = scoring.generate_full_report(df_processed)

# Работа с результатами
high_risk = df_processed[df_processed['Risk_Level'] == 'High Risk']
print(f"Найдено заявок с высоким риском: {len(high_risk)}")
```

---

## Сценарий 5: API запросы

### Получение статистики

```python
import requests

# Dashboard stats
response = requests.get('http://localhost:5000/api/dashboard_stats')
stats = response.json()

print(f"Всего заявок: {stats['total_applications']}")
print(f"Заявок с высоким риском: {stats['high_risk_count']}")
print(f"Процент исполненных: {stats['executed_percent']}%")
```

### Поиск заявок с высоким риском

```python
import requests

params = {
    'risk_level': 'High Risk',
    'region': 'Алматинская область',
    'limit': 100
}

response = requests.get(
    'http://localhost:5000/api/search_applications',
    params=params
)

applications = response.json()

for app in applications[:5]:
    print(f"\nЗаявка №{app['Номер заявки']}")
    print(f"Область: {app['Область']}")
    print(f"Risk Score: {app['Risk_Score']}")
    print(f"Превышение: {app['Причитающая сумма'] - app['Норматив']:,.0f} тенге")
```

### Региональный анализ

```python
import requests
import pandas as pd

response = requests.get('http://localhost:5000/api/regional_analysis')
data = response.json()

df = pd.DataFrame(data)
print("\nТОП-5 регионов по проценту исполнения:")
print(df[['region', 'executed_percent']].head())
```

---

## Сценарий 6: Фильтрация в веб-интерфейсе

### Шаги:
1. Откройте http://localhost:5000
2. Прокрутите до раздела "Заявки с высоким риском"
3. Выберите фильтры:
   - **Регион**: "Алматинская область"
   - **Уровень риска**: "High Risk"
   - **Статус**: "Исполнена"
4. Таблица автоматически обновится

**Результат:** Список заявок, которые были исполнены, но имеют высокий риск (возможное мошенничество или ошибки).

---

## Сценарий 7: Экспорт результатов

```python
from scoring_engine import SubsidyScoring
import pandas as pd

# Обработка данных
scoring = SubsidyScoring()
df = pd.read_excel('data/Выгрузка_по_выданным_субсидиям_2025_год__обезлич_.xlsx', skiprows=4)
df_processed = scoring.preprocess_data(df)
df_processed, _ = scoring.create_kmeans_segments(df_processed)
df_processed = scoring.detect_anomalies(df_processed)
df_processed = scoring.calculate_risk_score(df_processed)

# Экспорт только заявок с высоким риском
high_risk = df_processed[df_processed['Risk_Level'] == 'High Risk']
high_risk.to_excel('results/high_risk_applications.xlsx', index=False)

# Экспорт по региону
almaty = df_processed[df_processed['Область'] == 'Алматинская область']
almaty.to_excel('results/almaty_applications.xlsx', index=False)

print("✓ Файлы экспортированы")
```

---

## Сценарий 8: Мониторинг в реальном времени

```python
import time
import requests

def monitor_high_risk():
    """Мониторинг количества заявок с высоким риском"""
    
    while True:
        response = requests.get('http://localhost:5000/api/dashboard_stats')
        stats = response.json()
        
        high_risk = stats['high_risk_count']
        total = stats['total_applications']
        percent = (high_risk / total) * 100
        
        print(f"\r[{time.strftime('%H:%M:%S')}] High Risk: {high_risk} ({percent:.2f}%)", end='')
        
        time.sleep(60)  # Обновление каждую минуту

# Запуск
monitor_high_risk()
```

---

## Сценарий 9: Создание кастомного отчета

```python
from scoring_engine import SubsidyScoring
import pandas as pd
import matplotlib.pyplot as plt

# Обработка
scoring = SubsidyScoring()
df = pd.read_excel('data/Выгрузка_по_выданным_субсидиям_2025_год__обезлич_.xlsx', skiprows=4)
df_processed = scoring.preprocess_data(df)
df_processed = scoring.detect_anomalies(df_processed)

# Кастомный анализ: заявки по дням недели
daily_analysis = df_processed.groupby('День_недели').agg({
    'Номер заявки': 'count',
    'Причитающая сумма': 'sum',
    'Risk_Score': 'mean'
})

days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
daily_analysis.index = [days[i] for i in daily_analysis.index]

# Визуализация
fig, ax = plt.subplots(figsize=(10, 6))
daily_analysis['Номер заявки'].plot(kind='bar', ax=ax, color='#2ecc71')
ax.set_title('Количество заявок по дням недели')
ax.set_xlabel('День недели')
ax.set_ylabel('Количество заявок')
plt.tight_layout()
plt.savefig('results/daily_analysis.png', dpi=300)
print("✓ График сохранен в results/daily_analysis.png")
```

---

## Сценарий 10: Интеграция с другими системами

```python
import requests
import json

class SubsiSmartClient:
    """Клиент для интеграции SubsiSmart KZ с другими системами"""
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
    
    def get_high_risk_applications(self, region=None, limit=100):
        """Получить заявки с высоким риском"""
        params = {'risk_level': 'High Risk', 'limit': limit}
        if region:
            params['region'] = region
        
        response = requests.get(f'{self.base_url}/api/search_applications', params=params)
        return response.json()
    
    def send_alert(self, application):
        """Отправить уведомление о подозрительной заявке"""
        # Интеграция с системой уведомлений
        alert_data = {
            'type': 'high_risk_application',
            'application_id': application['Номер заявки'],
            'region': application['Область'],
            'risk_score': application['Risk_Score'],
            'amount': application['Причитающая сумма']
        }
        
        # Отправка в систему мониторинга (пример)
        # requests.post('https://monitoring.gov.kz/alerts', json=alert_data)
        
        return alert_data
    
    def generate_report_for_region(self, region):
        """Сгенерировать отчет для конкретного региона"""
        apps = self.get_high_risk_applications(region=region)
        
        report = {
            'region': region,
            'high_risk_count': len(apps),
            'total_risk_amount': sum(app['Причитающая сумма'] for app in apps),
            'applications': apps
        }
        
        return report

# Использование
client = SubsiSmartClient()

# Получить заявки с высоким риском для Алматинской области
apps = client.get_high_risk_applications(region='Алматинская область')
print(f"Найдено заявок с высоким риском: {len(apps)}")

# Отправить алерты для топ-10 заявок
for app in apps[:10]:
    alert = client.send_alert(app)
    print(f"Алерт отправлен для заявки №{alert['application_id']}")

# Сгенерировать отчет
report = client.generate_report_for_region('Алматинская область')
with open('results/almaty_risk_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
```

---

## Полезные команды

### Установка
```bash
# Быстрая установка
./setup.sh

# Или вручную
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Запуск
```bash
# Консольный анализ
python scoring_engine.py

# Демо (быстро)
python demo.py

# Веб-интерфейс
python app.py
```

### Тестирование
```bash
# Проверка API
curl http://localhost:5000/api/dashboard_stats

# Проверка с фильтрами
curl "http://localhost:5000/api/search_applications?risk_level=High%20Risk&limit=10"
```

### Экспорт
```bash
# Результаты сохраняются автоматически в папку results/
ls -lh results/
# processed_data.csv
# regional_report.csv
```

---

## Часто задаваемые вопросы (FAQ)

**Q: Сколько времени занимает обработка полного датасета?**
A: ~30-60 секунд на обычном компьютере (36,651 записей)

**Q: Можно ли использовать свои данные?**
A: Да, просто замените файл в папке data/ на свой (с такой же структурой)

**Q: Как настроить пороги риска?**
A: Отредактируйте метод `detect_anomalies()` в `scoring_engine.py`, измените коэффициент 3 в `mean + 3 * std`

**Q: Можно ли добавить новые признаки?**
A: Да, добавьте их в метод `preprocess_data()` в классе `SubsidyScoring`

**Q: Как экспортировать данные в Excel?**
A: Используйте `df.to_excel('filename.xlsx', index=False)` после обработки

---

Все эти сценарии и примеры помогут вам максимально эффективно использовать SubsiSmart KZ! 🌾
