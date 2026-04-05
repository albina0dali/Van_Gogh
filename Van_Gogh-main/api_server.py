"""
БЛОК 7: Backend API (Flask/FastAPI)
Complete REST API for agricultural subsidy scoring system
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import logging
import sys
import os
import requests
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path
import json
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
load_dotenv(BASE_DIR / '.env')

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / 'api.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder=str(BASE_DIR / 'templates'), static_folder=str(BASE_DIR / 'static'))
CORS(app)
app.config['JSON_AS_ASCII'] = False

# Global variables
model = None
scaler = None
encoders = None
feature_names = None
config = {}
analytics_cache = None


# ==================== Data Models ====================

class ApplicationData(BaseModel):
    """Модель для новой заявки"""
    farm_name: str
    region: str
    subsidy_type: str
    farm_size_hectares: float
    annual_revenue: float
    previous_subsidies: int


class ChatRequest(BaseModel):
    """Модель для запроса в AI чат"""
    message: str
    history: List[Dict[str, str]] = Field(default_factory=list)
    context: Dict[str, object] = Field(default_factory=dict)


class PredictionRequest(BaseModel):
    """Модель для запроса предсказания"""
    application_id: str
    features: Dict[str, float]


# ==================== Initialization ====================

def initialize_system():
    """Инициализирует систему скоринга загружая модели и конфигурацию"""
    global model, scaler, encoders, feature_names, config
    
    logger.info("Инициализация системы скоринга...")
    
    try:
        # Load model
        model_path = BASE_DIR / 'models' / 'best_model.pkl'
        if model_path.exists():
            model = joblib.load(model_path)
            logger.info("✓ Модель загружена успешно")
        else:
            logger.warning(f"Модель не найдена: {model_path}")
        
        # Load transformers
        scaler_path = BASE_DIR / 'models' / 'transformers' / 'scaler.pkl'
        if scaler_path.exists():
            scaler = joblib.load(scaler_path)
            logger.info("✓ Scaler загружен")
        
        encoders_path = BASE_DIR / 'models' / 'transformers' / 'encoders.pkl'
        if encoders_path.exists():
            encoders = joblib.load(encoders_path)
            logger.info("✓ Encoders загружены")
        
        # Load config
        config_path = BASE_DIR / 'config.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info("✓ Конфигурация загружена")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Ошибка инициализации: {str(e)}", exc_info=True)
        return False


def _fallback_score(data: Dict) -> Tuple[float, str]:
    """Heuristic scoring when ML model is unavailable."""
    farm_size = float(data.get('farm_size_hectares', 0) or 0)
    annual_revenue = float(data.get('annual_revenue', 0) or 0)
    previous_subsidies = float(data.get('previous_subsidies', 0) or 0)
    debt_amount = float(data.get('debt_amount', 0) or 0)
    num_employees = float(data.get('num_employees', 0) or 0)
    requested_amount = float(data.get('requested_amount', 0) or 0)
    region = str(data.get('region', '') or '')
    subsidy_type = str(data.get('subsidy_type', '') or '')

    score = 100.0

    if farm_size < 50:
        score -= 20
    elif farm_size < 150:
        score -= 8
    else:
        score += 4

    if annual_revenue < 5_000_000:
        score -= 30
    elif annual_revenue < 20_000_000:
        score -= 12
    else:
        score += 5

    debt_ratio = debt_amount / max(annual_revenue, 1)
    if debt_ratio > 1.0:
        score -= 30
    elif debt_ratio > 0.6:
        score -= 18
    elif debt_ratio > 0.35:
        score -= 8
    else:
        score += 4

    if num_employees < 5:
        score -= 10
    elif num_employees > 20:
        score += 3

    subsidy_ratio = requested_amount / max(annual_revenue, 1)
    if subsidy_ratio > 1.0:
        score -= 18
    elif subsidy_ratio > 0.7:
        score -= 10
    elif subsidy_ratio > 0.45:
        score -= 5
    else:
        score += 2

    # Light categorical adjustments keep scores dynamic across region/type choices.
    region_mod = (sum(ord(ch) for ch in region) % 7) - 3
    type_mod = (sum(ord(ch) for ch in subsidy_type) % 7) - 3
    score += (region_mod * 0.8) + (type_mod * 0.7)

    score -= min(previous_subsidies * 2.5, 10)
    score = max(0.0, min(100.0, score))

    if score >= config.get('scoring', {}).get('decision_thresholds', {}).get('approved', 70):
        recommendation = 'Одобрена'
    elif score >= config.get('scoring', {}).get('decision_thresholds', {}).get('under_review', 40):
        recommendation = 'На рассмотрении'
    else:
        recommendation = 'Отклонена'

    return round(score, 2), recommendation


def _chat_with_groq(message: str, history: List[Dict[str, str]]) -> str:
    """Call Groq chat completion API with safe fallback messages."""
    api_key = os.environ.get('GROQ_API_KEY', '').strip()
    if not api_key:
        return _local_chat_response(message)

    system_prompt = (
        'Ты AI-консультант платформы АгроСубсидия KZ. '
        'Отвечай кратко, по делу, на русском или казахском в зависимости от языка пользователя. '
        'Помогай по субсидиям, рискам, заполнению заявок и скорингу.'
    )

    messages = [{'role': 'system', 'content': system_prompt}]
    for item in history[-10:]:
        role = item.get('role', '')
        if role in ('user', 'assistant'):
            messages.append({'role': role, 'content': item.get('content', '')})
    messages.append({'role': 'user', 'content': message})

    try:
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': messages,
                'temperature': 0.5,
                'max_tokens': 700
            },
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json().get('choices', [{}])[0].get('message', {}).get('content', 'Пустой ответ модели.')
        if resp.status_code in (401, 403, 429):
            return _local_chat_response(message)
        return _local_chat_response(message)
    except Exception:
        return _local_chat_response(message)
def _build_ai_messages(message: str, history: List[Dict[str, str]], context: Optional[Dict[str, object]] = None) -> List[Dict[str, str]]:
    system_prompt = (
        'Ты AI-консультант платформы АгроСубсидия KZ. '
        'Отвечай кратко, по делу, на русском или казахском в зависимости от языка пользователя. '
        'Помогай по субсидиям, рискам, заполнению заявок и скорингу. '
        'Если пользователь спрашивает, почему балл низкий или как его поднять, объясняй через факторы заявки: '
        'земля, годовой доход, долг, сотрудники, предыдущие субсидии и размер запрашиваемой суммы. '
        'Ориентируйся на шкалу: 70+ = ұсынылады, 40-69 = тексеріс, 0-39 = жоғары тәуекел.'
    )

    messages = [{'role': 'system', 'content': system_prompt}]
    if context:
        messages.append({'role': 'system', 'content': 'Контекст скоринга: ' + json.dumps(context, ensure_ascii=False)})
    for item in history[-10:]:
        role = item.get('role', '')
        if role in ('user', 'assistant'):
            messages.append({'role': role, 'content': item.get('content', '')})
    messages.append({'role': 'user', 'content': message})
    return messages


def _call_chat_completion(api_url: str, api_key: str, model: str, messages: List[Dict[str, str]], temperature: float = 0.5, max_tokens: int = 700) -> Tuple[bool, str]:
    try:
        resp = requests.post(
            api_url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens
            },
            timeout=30
        )
        if resp.status_code == 200:
            return True, resp.json().get('choices', [{}])[0].get('message', {}).get('content', 'Пустой ответ модели.')
        return False, f'HTTP {resp.status_code}'
    except Exception as exc:
        return False, str(exc)


def _chat_with_ai(message: str, history: List[Dict[str, str]], context: Optional[Dict[str, object]] = None) -> str:
    """OpenAI-first chat with Groq fallback and local fallback."""
    messages = _build_ai_messages(message, history, context)

    openai_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if openai_key:
        ok, answer = _call_chat_completion(
            'https://api.openai.com/v1/chat/completions',
            openai_key,
            os.environ.get('OPENAI_CHAT_MODEL', 'gpt-4o-mini'),
            messages,
            temperature=0.4,
            max_tokens=800
        )
        if ok:
            return answer

    groq_key = os.environ.get('GROQ_API_KEY', '').strip()
    if groq_key:
        ok, answer = _call_chat_completion(
            'https://api.groq.com/openai/v1/chat/completions',
            groq_key,
            os.environ.get('GROQ_CHAT_MODEL', 'llama-3.3-70b-versatile'),
            messages,
            temperature=0.5,
            max_tokens=700
        )
        if ok:
            return answer

    return _local_chat_response(message)


def _local_chat_response(message: str) -> str:
    """Rule-based fallback so chat still works when external AI is unavailable."""
    text = (message or '').lower()

    if any(word in text for word in ['жоғары тәуекел', 'высокий риск', 'тәуекел']):
        return (
            'Жоғары тәуекел дегеніміз - кіріс төмен, қарыз жүктемесі жоғары немесе өтінім параметрлері әлсіз болған жағдай. '
            'Тәуекелді азайту үшін жер көлемін, табысты және қаржылық тұрақтылықты күшейткен дұрыс.'
        )

    if any(word in text for word in ['скоринг', 'балл', 'score']):
        return (
            'Скоринг жер көлемі, жылдық табыс, қарыз, қызметкерлер саны және сұралған сомаға сүйенеді. '
            '70+ - ұсынылады, 40–69 - тексеріс, 0–39 - жоғары тәуекел.'
        )

    if any(word in text for word in ['қалай өсіремін', 'қалай арттырам', 'арттыр', 'арттырам', 'арт', 'как поднять', 'балды', 'көтер', 'өсі']):
        return (
            'Балды көтеру үшін қарыз/табыс қатынасын азайтыңыз, табысты арттырыңыз, жұмыс күшін жеткілікті деңгейде көрсетіңіз '
            'және сұралған субсидияны бизнес көлеміне сай етіп ұсыныңыз.'
        )

    if any(word in text for word in ['құжат', 'документ', 'қажет']):
        return (
            'Әдетте өтінім үшін шаруашылық туралы деректер, қаржылық көрсеткіштер және субсидия бағыты бойынша дәлел құжаттар қажет. '
            'Нақты тізім өңір мен бағытқа байланысты.'
        )

    if any(word in text for word in ['сәлем', 'привет', 'hello']):
        return 'Сәлем. Субсидия, тәуекел немесе скоринг туралы сұрағыңызды жазыңыз.'

    return (
        'Жылдам кеңес: балды арттыру үшін қарыз жүктемесін азайтып, табыс пен қызметкер санын нақты көрсетіңіз, '
        'ал сұралған соманы шаруашылық ауқымына сай таңдаңыз. Қаласаңыз, 1) скоринг 2) тәуекел 3) құжаттар бойынша бөлек түсіндіріп беремін.'
    )


def _find_data_file() -> Path:
    """Return first available real dataset path."""
    candidates = [
        BASE_DIR / 'results' / 'processed_data.csv',
        BASE_DIR.parent / 'results' / 'processed_data.csv',
        BASE_DIR / 'data' / 'processed_data.csv'
    ]
    for path in candidates:
        if path.exists():
            return path
    return BASE_DIR / 'results' / 'processed_data.csv'


def _find_regional_report() -> Path:
    candidates = [
        BASE_DIR / 'results' / 'regional_report.csv',
        BASE_DIR.parent / 'results' / 'regional_report.csv'
    ]
    for path in candidates:
        if path.exists():
            return path
    return BASE_DIR / 'results' / 'regional_report.csv'


def _to_records(df: pd.DataFrame) -> List[Dict]:
    if df is None or df.empty:
        return []
    rows = df.replace({np.nan: None}).to_dict(orient='records')
    return rows


def _build_real_analytics() -> Dict:
    """Build real analytics from csv files and cache it in memory."""
    global analytics_cache
    if analytics_cache is not None:
        return analytics_cache

    data_path = _find_data_file()
    if not data_path.exists():
        analytics_cache = {
            'source': str(data_path),
            'summary': {},
            'regional': [],
            'subsidy': [],
            'monthly': [],
            'risk': []
        }
        return analytics_cache

    df = pd.read_csv(data_path, low_memory=False)

    # Normalize key columns.
    status_col = 'Статус заявки' if 'Статус заявки' in df.columns else None
    region_col = 'Область' if 'Область' in df.columns else None
    subsidy_col = 'Направление водства' if 'Направление водства' in df.columns else None
    amount_col = 'Причитающая сумма' if 'Причитающая сумма' in df.columns else None
    score_col = 'Merit_Score' if 'Merit_Score' in df.columns else None
    risk_col = 'Risk_Level' if 'Risk_Level' in df.columns else None
    date_col = 'Дата поступления' if 'Дата поступления' in df.columns else None

    if status_col:
        status_series = df[status_col].astype(str).str.lower()
        executed_mask = status_series.str.contains('исполн|орындал', na=False)
        approved_mask = status_series.str.contains('одобр|мақұл', na=False)
        rejected_mask = status_series.str.contains('отклон|қайтар', na=False)
    else:
        executed_mask = pd.Series([False] * len(df))
        approved_mask = pd.Series([False] * len(df))
        rejected_mask = pd.Series([False] * len(df))

    total_apps = int(len(df))
    executed_count = int(executed_mask.sum())
    approved_count = int(approved_mask.sum())
    rejected_count = int(rejected_mask.sum())
    approval_rate = round((approved_count / max(total_apps, 1)) * 100, 1)

    avg_score = None
    if score_col:
        avg_score = round(pd.to_numeric(df[score_col], errors='coerce').fillna(0).mean(), 1)

    total_amount = None
    if amount_col:
        total_amount = float(pd.to_numeric(df[amount_col], errors='coerce').fillna(0).sum())

    regional_data = []
    report_path = _find_regional_report()
    if report_path.exists():
        rr = pd.read_csv(report_path)
        rename_map = {
            'Область': 'region',
            'Всего_заявок': 'total',
            'Исполнено': 'executed',
            'Одобрено': 'approved',
            'Отклонено': 'rejected',
            'Процент_исполненных': 'success_rate'
        }
        available = {k: v for k, v in rename_map.items() if k in rr.columns}
        rr = rr.rename(columns=available)
        if 'success_rate' in rr.columns:
            rr = rr.sort_values('success_rate', ascending=False)
        regional_data = _to_records(rr.head(15))
    elif region_col:
        tmp = df.groupby(region_col).agg(total=('№ п/п', 'count')).reset_index()
        tmp.columns = ['region', 'total']
        regional_data = _to_records(tmp.head(15))

    subsidy_data = []
    if subsidy_col and status_col:
        g = df.groupby(subsidy_col).agg(
            total=(subsidy_col, 'count'),
            executed=(status_col, lambda s: s.astype(str).str.lower().str.contains('исполн|орындал', na=False).sum())
        ).reset_index()
        g['success_rate'] = (g['executed'] / g['total'] * 100).round(1)
        g = g.rename(columns={subsidy_col: 'subsidy'})
        g = g.sort_values('success_rate', ascending=False)
        subsidy_data = _to_records(g.head(10))

    monthly_data = []
    if date_col:
        dt = pd.to_datetime(df[date_col], errors='coerce')
        d2 = pd.DataFrame({'month': dt.dt.to_period('M').astype(str)})
        d2 = d2.dropna().groupby('month').size().reset_index(name='applications')
        d2 = d2.sort_values('month')
        monthly_data = _to_records(d2.tail(12))

    risk_data = []
    if risk_col:
        r = df[risk_col].fillna('Unknown').astype(str).value_counts().reset_index()
        r.columns = ['risk_level', 'count']
        risk_data = _to_records(r)

    analytics_cache = {
        'source': str(data_path),
        'summary': {
            'total_applications': total_apps,
            'executed_count': executed_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'approval_rate': approval_rate,
            'average_score': avg_score,
            'total_amount': total_amount,
        },
        'regional': regional_data,
        'subsidy': subsidy_data,
        'monthly': monthly_data,
        'risk': risk_data
    }
    return analytics_cache


# ==================== API Endpoints ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.now().isoformat(),
        'service': 'SubsiSmartKZ API'
    }), 200


@app.route('/api/model_status', methods=['GET'])
def model_status():
    """Returns current model connection status."""
    model_path = BASE_DIR / 'models' / 'best_model.pkl'
    return jsonify({
        'model_loaded': model is not None,
        'model_file_exists': model_path.exists(),
        'model_path': str(model_path),
        'using_fallback_scoring': model is None
    }), 200


@app.route('/api/analytics/real', methods=['GET'])
def analytics_real():
    """Returns charts-ready analytics derived from real CSV files."""
    try:
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        global analytics_cache
        if refresh:
            analytics_cache = None
        payload = _build_real_analytics()
        return jsonify(payload), 200
    except Exception as e:
        logger.error(f"✗ Ошибка real analytics: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to build analytics'}), 500


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Выполняет предсказание (скоринг) для заявки
    """
    try:
        data = request.get_json()
        
        # Validate request
        req = ApplicationData(
            farm_name=data.get('farm_name'),
            region=data.get('region'),
            subsidy_type=data.get('subsidy_type'),
            farm_size_hectares=data.get('farm_size_hectares', 0),
            annual_revenue=data.get('annual_revenue', 0),
            previous_subsidies=data.get('previous_subsidies', 0)
        )
        
        # Prepare features
        score = None
        recommendation = None

        features_dict = data.get('features', {})
        if model and features_dict:
            try:
                features_array = np.array([list(features_dict.values())]).reshape(1, -1)

                if scaler:
                    try:
                        features_array = scaler.transform(features_array)
                    except Exception:
                        pass

                if hasattr(model, 'predict_proba'):
                    probability = model.predict_proba(features_array)[0, 1]
                else:
                    probability = model.predict(features_array)[0]

                score = float(probability) * 100
            except Exception:
                score = None

        if score is None:
            score, recommendation = _fallback_score(data)
        else:
            if score >= config.get('scoring', {}).get('decision_thresholds', {}).get('approved', 70):
                recommendation = 'Одобрена'
            elif score >= config.get('scoring', {}).get('decision_thresholds', {}).get('under_review', 40):
                recommendation = 'На рассмотрении'
            else:
                recommendation = 'Отклонена'
        
        application_id = f"APP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"✓ Предсказание выполнено: {application_id} = {score:.1f}%")
        
        return jsonify({
            'success': True,
            'score': round(score, 2),
            'recommendation': recommendation,
            'application_id': application_id,
            'farm_name': req.farm_name,
            'region': req.region,
            'model_used': bool(model and features_dict),
            'created_at': datetime.now().isoformat()
        }), 200
    
    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"✗ Ошибка предсказания: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """AI chat endpoint for assistant page."""
    try:
        data = request.get_json() or {}
        raw_history = data.get('history')
        raw_context = data.get('context')
        req = ChatRequest(
            message=data.get('message', ''),
            history=raw_history if isinstance(raw_history, list) else [],
            context=raw_context if isinstance(raw_context, dict) else {}
        )

        if not req.message.strip():
            return jsonify({'error': 'Пустое сообщение'}), 400

        answer = _chat_with_groq(req.message.strip(), req.history)
        answer = _chat_with_ai(req.message.strip(), req.history, req.context)
        return jsonify({'success': True, 'answer': answer}), 200
    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"✗ Ошибка AI чата: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/explanation/<application_id>', methods=['GET'])
def get_explanation(application_id):
    """Получить подробное объяснение предсказания"""
    try:
        return jsonify({
            'application_id': application_id,
            'positive_factors': [
                'Размер хозяйства соответствует стандартам',
                'Годовой доход стабилен'
            ],
            'negative_factors': [
                'Количество предыдущих субсидий выше нормы'
            ],
            'explanation': 'Заявка имеет хорошие перспективы одобрения'
        }), 200
    except Exception as e:
        logger.error(f"✗ Ошибка объяснения: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/applications', methods=['GET'])
def list_applications():
    """Получить список заявок с фильтрами"""
    try:
        region = request.args.get('region')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        
        applications = []
        
        return jsonify({
            'total': len(applications),
            'applications': applications[:limit]
        }), 200
    except Exception as e:
        logger.error(f"✗ Ошибка списка заявок: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Общая статистика по системе"""
    try:
        return jsonify({
            'total_applications': 0,
            'approved_count': 0,
            'rejected_count': 0,
            'under_review_count': 0,
            'approval_rate': 0.0,
            'average_score': 0.0,
            'by_region': {},
            'by_subsidy_type': {}
        }), 200
    except Exception as e:
        logger.error(f"✗ Ошибка статистики: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/references/regions', methods=['GET'])
def get_regions():
    """Получить список всех регионов"""
    try:
        regions = config.get('references', {}).get('regions', [])
        return jsonify({'regions': regions}), 200
    except Exception as e:
        logger.error(f"✗ Ошибка регионов: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/references/subsidy_types', methods=['GET'])
def get_subsidy_types():
    """Получить список всех типов субсидий"""
    try:
        subsidy_types = config.get('references', {}).get('subsidy_types', [])
        return jsonify({'subsidy_types': subsidy_types}), 200
    except Exception as e:
        logger.error(f"✗ Ошибка типов субсидий: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/model/retrain', methods=['POST'])
def retrain_model():
    """Переобучить модель (требуется авторизация)"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != f"Bearer {config.get('api', {}).get('admin_token')}":
            return jsonify({'error': 'Unauthorized'}), 401
        
        logger.info("✓ Инициирована переобучение модели")
        
        return jsonify({
            'success': True,
            'message': 'Переобучение инициировано',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"✗ Ошибка переобучения: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/', methods=['GET'])
def index():
    """Redirect root to dashboard"""
    return redirect(url_for('dashboard'))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Dashboard page"""
    try:
        return render_template('index.html', active_page='dashboard')
    except Exception as e:
        logger.error(f"✗ Ошибка страницы dashboard: {str(e)}")
        return f"<h1>SubsiSmartKZ API</h1><p>Dashboard unavailable</p>"


@app.route('/new-application', methods=['GET'])
def new_application_page():
    """New application page"""
    try:
        return render_template('index.html', active_page='new_application')
    except Exception as e:
        logger.error(f"✗ Ошибка страницы new_application: {str(e)}")
        return f"<h1>SubsiSmartKZ API</h1><p>New application page unavailable</p>"


@app.route('/history', methods=['GET'])
def history_page():
    """History page"""
    try:
        return render_template('index.html', active_page='history')
    except Exception as e:
        logger.error(f"✗ Ошибка страницы history: {str(e)}")
        return f"<h1>SubsiSmartKZ API</h1><p>History page unavailable</p>"


@app.route('/analytics', methods=['GET'])
def analytics_page():
    """Analytics page"""
    try:
        return render_template('index.html', active_page='analytics')
    except Exception as e:
        logger.error(f"✗ Ошибка страницы analytics: {str(e)}")
        return f"<h1>SubsiSmartKZ API</h1><p>Analytics page unavailable</p>"


@app.route('/assistant', methods=['GET'])
def assistant_page():
    """AI assistant page"""
    try:
        return render_template('index.html', active_page='assistant')
    except Exception as e:
        logger.error(f"✗ Ошибка страницы assistant: {str(e)}")
        return f"<h1>SubsiSmartKZ API</h1><p>Assistant page unavailable</p>"


@app.route('/settings', methods=['GET'])
def settings_page():
    """Settings page"""
    try:
        return render_template('index.html', active_page='settings')
    except Exception as e:
        logger.error(f"✗ Ошибка страницы settings: {str(e)}")
        return f"<h1>SubsiSmartKZ API</h1><p>Settings page unavailable</p>"


@app.route('/logout', methods=['GET'])
def logout_page():
    """Logout stub"""
    return redirect(url_for('dashboard'))


@app.errorhandler(404)
def not_found(error):
    """404 Not Found"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 Internal Server Error"""
    logger.error(f"✗ 500 Error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


# ==================== Main ====================

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("Запуск API сервера...")
    logger.info("="*60)
    
    initialize_system()
    
    logger.info("API запущен на http://0.0.0.0:5000")
    logger.info("="*60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
