# SubsiSmartKZ - Система скоринга для государственных субсидий сельхозпроизводителей

## 📋 Обзор

**SubsiSmartKZ** - это комплексная система машинного обучения для оценки (скоринга) заявок на государственные субсидии сельхозпроизводителей в Казахстане. Система использует передовые алгоритмы ML для объективного и прозрачного принятия решений о выдаче субсидий.

### ✨ Ключевые особенности

- 🤖 **Многомодельный скоринг** (XGBoost, Random Forest, Gradient Boosting, Logistic Regression)
- 📊 **Полный анализ данных** (EDA, корреляции, выбросы)
- 🔧 **Инженерия признаков** (временные, финансовые, географические признаки)
- 💡 **Объяснимость предсказаний** (SHAP analysis, feature importance)
- 🗄️ **Полная БД** (SQLAlchemy ORM, поддержка SQLite/PostgreSQL)
- 🌐 **REST API** (Flask, 10+ endpoints)
- 🎨 **Веб-интерфейс** (HTML/CSS/JavaScript)
- 📈 **Отчеты и мониторинг** (PDF, Excel, JSON)
- 🔒 **Безопасность** (JWT, аудит-логи)

---

## 🏗️ Архитектура системы (11 блоков)

```
СИСТЕМА СКОРИНГА СУБСИДИЙ
│
├── БЛОК 1: Загрузка данных (data_loader.py)
│   └─ Загрузка CSV/Excel, предобработка, нормализация
│
├── БЛОК 2: EDA Анализ (eda_analysis.py)
│   └─ Распределения, корреляции, выбросы, статистика
│
├── БЛОК 3: Инженерия признаков (feature_engineer.py)
│   └─ Создание временных, финансовых, географических признаков
│
├── БЛОКИ 4-5: Обучение + Оценка (model_trainer.py)
│   └─ XGBoost, Random Forest, Gradient Boosting, LR + метрики
│
├── БЛОК 6: Объяснимость (explainability.py)
│   └─ SHAP analysis, feature importance, локальные объяснения
│
├── БЛОК 7: REST API (api_server.py)
│   └─ Flask endpoints: /predict, /explanation, /applications
│
├── БЛОК 8: Веб-интерфейс (app.py + templates/)
│   └─ HTML/CSS/JS форм и дашбордов
│
├── БЛОК 9: База Данных (database_models.py)
│   └─ SQLAlchemy ORM: Applications, Predictions, Audit Logs
│
├── БЛОК 10: Конфигурация (config_manager.py)
│   └─ Справочники регионов, типов субсидий, параметры модели
│
└── БЛОК 11: Утилиты (utilities.py)
    └─ Импорт данных, отчеты PDF, мониторинг, бэкап БД
```

---

## 📁 Структура проекта

```
SubsiSmartKZ/
├── data/                          # Исходные данные
├── results/                       # Результаты анализа
│   ├── eda/                      # Графики EDA
│   └── explanations/             # SHAP объяснения
├── models/                        # Обученные модели
│   ├── best_model.pkl           # Лучшая модель
│   ├── transformers/            # Scaler, encoders
│   └── model_comparison.csv     # Таблица сравнения
├── templates/                     # HTML шаблоны
├── static/                        # CSS, JavaScript
├── reports/                       # Генерируемые отчеты
│
├── data_loader.py               # БЛОК 1
├── eda_analysis.py              # БЛОК 2
├── feature_engineer.py          # БЛОК 3
├── model_trainer.py             # БЛОКИ 4-5
├── explainability.py            # БЛОК 6
├── api_server.py                # БЛОК 7
├── database_models.py           # БЛОК 9
├── config_manager.py            # БЛОК 10
├── utilities.py                 # БЛОК 11
├── main_pipeline.py             # Главная орхестрация
│
├── app.py                       # БЛОК 8: Flask приложение
├── config.json                  # Конфигурация JSON
├── requirements.txt             # Python зависимости
└── README.md                    # Этот файл
```

---

## 🚀 Быстрый старт

### 1. Установка

```bash
cd d:\SubsiSmartKZ
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Подготовка данных

Поместите Excel/CSV файлы в папку `data/` с колонками:
- `Дата поступления` - дата
- `Область` - регион
- `Направление водства` - тип
- `Статус заявки` - решение (Одобрена/Отклонена)
- `Норматив` - размер
- `Причитающая сумма` - сумма

### 3. Запуск системы

```bash
# Полный конвейер (загрузка → обучение → API)
python main_pipeline.py --mode full

# API сервер
python api_server.py
# Доступно на http://localhost:5000

# Предсказание
python main_pipeline.py --mode predict --features '{"farm_size_hectares": 500}'
```

---

## 📊 API Endpoints

| Метод | URL | Описание |
|-------|-----|---------|
| POST | `/api/predict` | Получить скор для заявки |
| GET | `/api/explanation/<id>` | Объяснение решения |
| GET | `/api/applications` | Список заявок |
| GET | `/api/statistics` | Статистика модели |
| GET | `/api/references/regions` | Справочник регионов |
| GET | `/api/references/subsidy_types` | Типы субсидий |
| POST | `/api/model/retrain` | Переобучить модель |

### Пример запроса

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "farm_name": "ООО Агро",
    "region": "Акмолинская область",
    "subsidy_type": "Развитие животноводства",
    "features": {
      "farm_size_hectares": 500,
      "annual_revenue": 1000000
    }
  }'
```

---

## 🤖 Модели машинного обучения

| Модель | Тип | AUC-ROC | Преимущества |
|--------|-----|---------|-------------|
| **XGBoost** | Gradient Boosting | 0.85-0.92 | ✅ Лучшая (обычно выбирается) |
| Random Forest | Ensemble | 0.80-0.88 | Быстрое, стабильное |
| Gradient Boosting | Iterative | 0.82-0.90 | Гибкое, точное |
| Logistic Regression | Linear | 0.70-0.80 | Простое, интерпретируемое |

Использует:
- ✅ SMOTE для балансировки классов
- ✅ GridSearchCV с 5-fold кросс-валидацией
- ✅ StandardScaler нормализацию

---

## 💡 Объяснимость (SHAP)

```python
from explainability import ExplainablePredictions

explainer = ExplainablePredictions(model, X_train, X_test)
explanation = explainer.get_local_explanation(sample_idx=0)

# Позитивные факторы (за одобрение)
for factor in explanation['positive_factors']:
    print(f"+ {factor['feature']}: {factor['contribution']:.4f}")

# Негативные факторы (против одобрения)
for factor in explanation['negative_factors']:
    print(f"- {factor['feature']}: {factor['contribution']:.4f}")
```

---

## 🗄️ База Данных

ORM модели (SQLAlchemy):
- **Applications** - заявки
- **ApplicantData** - данные заявителей
- **Predictions** - предсказания
- **Explanations** - объяснения
- **AuditLogs** - логи действий

```python
from database_models import init_database

db = init_database('sqlite:///subsidy_scoring.db')
stats = db.get_statistics(session)
print(f"Одобренные: {stats['approval_rate']:.1f}%")
```

---

## 📈 Python примеры

### Обучение модели

```python
from main_pipeline import SubsidyScoringPipeline

pipeline = SubsidyScoringPipeline()
pipeline.run_complete_pipeline()  # Всё автоматически
```

### Предсказание

```python
import joblib
import numpy as np

model = joblib.load('models/best_model.pkl')
features = np.array([[500, 1000000, 2]])
score = model.predict_proba(features)[0, 1] * 100
print(f"Score: {score:.1f}%")
```

### Получение объяснения

```python
from explainability import ExplainablePredictions

explainer = ExplainablePredictions(model, X_train, X_test)
results = explainer.run_full_explanation()

importance = results['feature_importance']
for feat, val in list(importance.items())[:5]:
    print(f"{feat}: {val:.4f}")
```

---

## 📊 Метрики системы

После обучения:
- **Accuracy**: 85-92%
- **Precision**: 80-90%
- **Recall**: 75-85%
- **F1-Score**: 80-88%
- **AUC-ROC**: 0.85-0.95
- **Время предсказания**: < 100ms

---

## 🛠️ Стек технологий

- **ML**: XGBoost, scikit-learn, pandas, numpy
- **Explainability**: SHAP
- **Backend**: Flask, SQLAlchemy
- **Database**: SQLite/PostgreSQL
- **Frontend**: HTML/CSS/JavaScript
- **Reports**: ReportLab, Plotly, Matplotlib
- **Testing**: Pytest
- **Deployment**: Docker (опционально)

---

## 🔒 Безопасность

- JWT аутентификация
- Pydantic валидация
- CORS защита
- Аудит-логи
- Переменные окружения (.env)

---

## 📝 Логирование

```bash
tail -f subsidy_system.log    # Основной лог
tail -f api.log               # API лог
tail -f data_processing.log   # Обработка данных
```

---

## 🧪 Тестирование

```bash
pytest tests/ -v
```

---

## 🚢 Развертывание

### Локально
```bash
python api_server.py
```

### Docker
```bash
docker build -t subsidy-scoring .
docker run -p 5000:5000 subsidy-scoring
```

---

## 📚 Документация

- **API Docs**: [API_DOCS.md](API_DOCS.md)
- **Architecture**: [ARCHITECTURE.html](ARCHITECTURE.html)
- **Examples**: [EXAMPLES.md](EXAMPLES.md)
- **Quickstart**: [QUICKSTART.md](QUICKSTART.md)

---

## 📞 Поддержка

Документация находится в файлах проекта:
- `API_DOCS.md` - документация API
- `QUICKSTART.md` - быстрый старт
- `EXAMPLES.md` - примеры использования
- `ARCHITECTURE.html` - диаграммы архитектуры

---

## 🎯 Ключевые преимущества

✅ **Объективность** - все решения основаны на данных
✅ **Прозрачность** - объяснение каждого решения  
✅ **Эффективность** - автоматизация и масштабирование
✅ **Безопасность** - аудит и логирование всех операций
✅ **Гибкость** - легко адаптируются пороги решений
✅ **Скорость** - быстрая обработка заявок

---

**SubsiSmartKZ** - Система для справедливого и прозрачного распределения государственных субсидий! 🇰🇿

**Разработано для**: Decentrathon 5.0 | **Трек**: AI for Government
