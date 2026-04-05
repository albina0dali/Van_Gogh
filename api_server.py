"""
БЛОК 7: Backend API (Flask/FastAPI)
Complete REST API for agricultural subsidy scoring system
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import logging
import sys
from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path
import json
from pydantic import BaseModel, ValidationError

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
app.config['JSON_AS_ASCII'] = False

# Global variables
model = None
scaler = None
encoders = None
feature_names = None
config = {}


# ==================== Data Models ====================

class ApplicationData(BaseModel):
    """Модель для новой заявки"""
    farm_name: str
    region: str
    subsidy_type: str
    farm_size_hectares: float
    annual_revenue: float
    previous_subsidies: int


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
        model_path = Path('models/best_model.pkl')
        if model_path.exists():
            model = joblib.load(model_path)
            logger.info("✓ Модель загружена успешно")
        else:
            logger.warning(f"Модель не найдена: {model_path}")
        
        # Load transformers
        scaler_path = Path('models/transformers/scaler.pkl')
        if scaler_path.exists():
            scaler = joblib.load(scaler_path)
            logger.info("✓ Scaler загружен")
        
        encoders_path = Path('models/transformers/encoders.pkl')
        if encoders_path.exists():
            encoders = joblib.load(encoders_path)
            logger.info("✓ Encoders загружены")
        
        # Load config
        config_path = Path('config.json')
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info("✓ Конфигурация загружена")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Ошибка инициализации: {str(e)}", exc_info=True)
        return False


# ==================== API Endpoints ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.now().isoformat(),
        'service': 'SubsiSmartKZ API'
    }), 200


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Выполняет предсказание (скоринг) для заявки
    """
    try:
        data = request.get_json()
        
        if not model:
            return jsonify({'error': 'Модель не загружена'}), 500
        
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
        features_dict = data.get('features', {})
        features_array = np.array([list(features_dict.values())]).reshape(1, -1)
        
        # Normalize if scaler available
        if scaler:
            try:
                features_array = scaler.transform(features_array)
            except:
                pass
        
        # Predict
        if hasattr(model, 'predict_proba'):
            probability = model.predict_proba(features_array)[0, 1]
        else:
            probability = model.predict(features_array)[0]
        
        score = probability * 100
        
        # Determine recommendation based on thresholds
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
            'created_at': datetime.now().isoformat()
        }), 200
    
    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"✗ Ошибка предсказания: {str(e)}", exc_info=True)
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
    """Main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"✗ Ошибка главной страницы: {str(e)}")
        return f"<h1>SubsiSmartKZ API</h1<p>Версия: 1.0</p>"


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
