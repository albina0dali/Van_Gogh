# Van_Gogh

Система ML-скоринга заявок на субсидии с API, пайплайном обучения и демо-интерфейсом.

## Возможности

- Оценка заявок и формирование short-list
- Обучение и переобучение моделей
- Объяснимость предсказаний
- Генерация отчетов по регионам
- Веб-интерфейс для просмотра результатов

## Основные Компоненты

- API: `api_server.py`
- Скоринг: `scoring_engine.py`
- Пайплайн: `main_pipeline.py`
- Обучение: `model_trainer.py`
- Демо: `demo.py`, `templates/index.html`

## Быстрый Старт

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main_pipeline.py
python api_server.py
```

## Структура

```text
.
|- api_server.py
|- main_pipeline.py
|- model_trainer.py
|- scoring_engine.py
|- data/
|- results/
|- templates/
|- metrics/
|- ARCHITECTURE.html
`- PRESENTATION.md
```

## Документация

- Архитектура: `ARCHITECTURE.html`
- Презентация: `PRESENTATION.md`

Главная страница GitHub поддерживается этим файлом `README.md`.
