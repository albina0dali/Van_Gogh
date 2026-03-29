# API Документация SubsiSmart KZ

## Обзор

SubsiSmart KZ предоставляет REST API для интеграции с другими системами.

**Base URL**: `http://localhost:5000`

---

## Endpoints

### 1. Dashboard Statistics
Получение общей статистики по заявкам

**GET** `/api/dashboard_stats`

**Response**:
```json
{
  "total_applications": 36651,
  "total_amount": 139384738000.0,
  "avg_amount": 3801413.25,
  "high_risk_count": 892,
  "executed_percent": 57.3,
  "approved_percent": 20.8,
  "rejected_percent": 7.9
}
```

---

### 2. Regional Analysis
Анализ по регионам с процентом исполнения заявок

**GET** `/api/regional_analysis`

**Response**:
```json
[
  {
    "region": "Алматинская область",
    "total": 5432,
    "executed_percent": 62.5,
    "approved_percent": 18.3,
    "rejected_percent": 8.2,
    "total_amount": 18500000000.0
  },
  ...
]
```

---

### 3. Cluster Analysis
Статистика по кластерам K-Means

**GET** `/api/cluster_analysis`

**Response**:
```json
[
  {
    "cluster": 0,
    "avg_normativ": 15000.5,
    "avg_amount": 2500000.0,
    "count": 9823
  },
  ...
]
```

---

### 4. Risk Distribution
Распределение заявок по уровням риска

**GET** `/api/risk_distribution`

**Response**:
```json
[
  {
    "level": "Normal",
    "count": 33450
  },
  {
    "level": "Medium Risk",
    "count": 2309
  },
  {
    "level": "High Risk",
    "count": 892
  }
]
```

---

### 5. Monthly Trend
Динамика заявок по месяцам

**GET** `/api/monthly_trend`

**Response**:
```json
[
  {
    "month": 1,
    "month_name": "Январь",
    "applications": 5234,
    "total_amount": 18500000000.0
  },
  ...
]
```

---

### 6. Direction Analysis
Анализ по направлениям субсидирования

**GET** `/api/direction_analysis`

**Response**:
```json
[
  {
    "direction": "Субсидирование в скотоводстве",
    "count": 12450,
    "total_amount": 45600000000.0,
    "avg_risk_score": 12.5
  },
  ...
]
```

---

### 7. Search Applications
Поиск и фильтрация заявок

**GET** `/api/search_applications`

**Query Parameters**:
- `region` (optional): Фильтр по области
- `risk_level` (optional): Фильтр по уровню риска (Normal, Medium Risk, High Risk)
- `status` (optional): Фильтр по статусу заявки
- `limit` (optional, default=50): Максимальное количество результатов

**Example**:
```
GET /api/search_applications?region=Алматинская%20область&risk_level=High%20Risk&limit=10
```

**Response**:
```json
[
  {
    "Номер заявки": 1300100258072,
    "Дата поступления": "2025-01-21",
    "Область": "Алматинская область",
    "Направление водства": "Субсидирование в скотоводстве",
    "Статус заявки": "Исполнена",
    "Норматив": 15000,
    "Причитающая сумма": 4635000,
    "Risk_Level": "High Risk",
    "Risk_Score": 65,
    "Кластер": 2
  },
  ...
]
```

---

### 8. Available Filters
Получение списка доступных значений для фильтров

**GET** `/api/filters`

**Response**:
```json
{
  "regions": [
    "Алматинская область",
    "Акмолинская область",
    ...
  ],
  "risk_levels": [
    "Normal",
    "Medium Risk",
    "High Risk"
  ],
  "statuses": [
    "Исполнена",
    "Одобрена",
    "Отклонена",
    ...
  ],
  "directions": [
    "Субсидирование в скотоводстве",
    "Субсидирование в растениеводстве",
    ...
  ]
}
```

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 400 | Неверные параметры запроса |
| 500 | Внутренняя ошибка сервера (данные не загружены) |

**Пример ошибки**:
```json
{
  "error": "Данные не загружены"
}
```

---

## Примеры использования

### Python
```python
import requests

# Получение статистики
response = requests.get('http://localhost:5000/api/dashboard_stats')
stats = response.json()
print(f"Всего заявок: {stats['total_applications']}")

# Поиск заявок с высоким риском
params = {
    'risk_level': 'High Risk',
    'limit': 100
}
response = requests.get('http://localhost:5000/api/search_applications', params=params)
applications = response.json()
print(f"Найдено заявок: {len(applications)}")
```

### JavaScript (Fetch API)
```javascript
// Получение регионального анализа
fetch('http://localhost:5000/api/regional_analysis')
  .then(response => response.json())
  .then(data => {
    console.log('Топ регион:', data[0].region);
    console.log('Процент исполнения:', data[0].executed_percent);
  });

// Фильтрация заявок
const params = new URLSearchParams({
  region: 'Алматинская область',
  risk_level: 'High Risk',
  limit: 50
});

fetch(`http://localhost:5000/api/search_applications?${params}`)
  .then(response => response.json())
  .then(data => console.log('Заявки:', data));
```

### cURL
```bash
# Получение статистики
curl http://localhost:5000/api/dashboard_stats

# Поиск заявок
curl "http://localhost:5000/api/search_applications?risk_level=High%20Risk&limit=10"
```

---

## Ограничения

- API работает только при запущенном веб-сервере (`python app.py`)
- Все даты возвращаются в формате ISO 8601 (YYYY-MM-DD)
- Числовые значения округляются для удобства отображения
- Максимальный limit для `/api/search_applications` не ограничен, но рекомендуется ≤1000

---

## CORS

По умолчанию CORS не настроен. Для использования API из браузерных приложений на других доменах, добавьте Flask-CORS:

```python
# В app.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
```

```bash
pip install flask-cors
```
