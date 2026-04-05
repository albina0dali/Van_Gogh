"""
БЛОК 10: Конфигурация и справочники
System configuration and reference data for subsidy scoring
"""

import os
import json
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


# ==================== Справочники (Reference Data) ====================

REGIONS = [
    {'code': 'AKM', 'name': 'Акмолинская область', 'capital': 'Кокшетау'},
    {'code': 'ALM', 'name': 'Алматинская область', 'capital': 'Талдыкорган'},
    {'code': 'ATY', 'name': 'Атырауская область', 'capital': 'Атырау'},
    {'code': 'BAY', 'name': 'Баян-Өлгей область', 'capital': 'Лейпа'},
    {'code': 'KAR', 'name': 'Карагандинская область', 'capital': 'Караганда'},
    {'code': 'KOS', 'name': 'Костанайская область', 'capital': 'Костанай'},
    {'code': 'KHO', 'name': 'Хорезмская область', 'capital': 'Нукус'},
    {'code': 'KYZ', 'name': 'Кызылординская область', 'capital': 'Кызылорда'},
    {'code': 'ZAP', 'name': 'Западно-Казахстанская область', 'capital': 'Уральск'},
    {'code': 'PAV', 'name': 'Павлодарская область', 'capital': 'Павлодар'},
    {'code': 'VOS', 'name': 'Восточно-Казахстанская область', 'capital': 'Усть-Каменогорск'},
    {'code': 'ZHP', 'name': 'Жамбылская область', 'capital': 'Тараз'},
    {'code': 'NUR', 'name': 'Нур-Султан (Астана)', 'capital': 'Нур-Султан'},
    {'code': 'ALM_CITY', 'name': 'Алматы (город)', 'capital': 'Алматы'},
    {'code': 'SHY', 'name': 'Түркістан (город)', 'capital': 'Түркістан'},
]

SUBSIDY_TYPES = [
    {
        'code': 'DEV_LIVESTOCK',
        'name': 'Развитие животноводства',
        'description': 'Субсидия на развитие ферм животноводческого направления',
        'max_amount': 5000000,
        'target_group': 'Животноводы'
    },
    {
        'code': 'DEV_CROP',
        'name': 'Развитие растениеводства',
        'description': 'Субсидия на развитие сельскохозяйственных предприятий растениеводческого профиля',
        'max_amount': 3000000,
        'target_group': 'Растениеводы'
    },
    {
        'code': 'EQUIPMENT',
        'name': 'Приобретение оборудования',
        'description': 'Субсидия на покупку сельскохозяйственной техники и оборудования',
        'max_amount': 10000000,
        'target_group': 'Все производители'
    },
    {
        'code': 'ECO_FARM',
        'name': 'Экологичное земледелие',
        'description': 'Субсидия на переход на органическое/экологичное сельхозпроизводство',
        'max_amount': 2000000,
        'target_group': 'Экологические хозяйства'
    },
    {
        'code': 'INSURANCE',
        'name': 'Страхование урожая',
        'description': 'Компенсация затрат на страховку сельскохозяйственных угодий',
        'max_amount': 1000000,
        'target_group': 'Все производители'
    },
    {
        'code': 'WATER',
        'name': 'Мелиорация и водоснабжение',
        'description': 'Субсидия на проведение работ по улучшению tierra и водоснабжению',
        'max_amount': 7000000,
        'target_group': 'Хозяйства в зонах дефицита воды'
    },
    {
        'code': 'BREEDING',
        'name': 'Племенное разведение',
        'description': 'Субсидия на развитие племенного животноводства',
        'max_amount': 4000000,
        'target_group': 'Племенные фермы'
    },
]

FARM_TYPES = [
    {'code': 'IP', 'name': 'Индивидуальный предприниматель'},
    {'code': 'LLP', 'name': 'ООО'},
    {'code': 'JSC', 'name': 'АО'},
    {'code': 'COOP', 'name': 'Кооператив'},
    {'code': 'STATE', 'name': 'Государственное предприятие'},
    {'code': 'PRIVATE', 'name': 'Частное хозяйство'},
]

DECISION_STATUS = [
    {'code': 'APPROVED', 'name': 'Одобрена', 'color': 'success'},
    {'code': 'REJECTED', 'name': 'Отклонена', 'color': 'danger'},
    {'code': 'UNDER_REVIEW', 'name': 'На рассмотрении', 'color': 'warning'},
    {'code': 'PENDING_DOCS', 'name': 'Ожидание документов', 'color': 'info'},
]


# ==================== Модель конфигурации ====================

class SystemConfig:
    """Класс для управления конфигурацией системы"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.logger = logger
    
    def _load_config(self) -> Dict:
        """Загружает конфигурацию из файла или использует defaults"""
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Ошибка загрузки конфига: {str(e)}")
        
        # Default configuration
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Возвращает конфигурацию по умолчанию"""
        return {
            # API Settings
            'api': {
                'host': os.getenv('API_HOST', '0.0.0.0'),
                'port': int(os.getenv('API_PORT', 5000)),
                'debug': os.getenv('API_DEBUG', 'False').lower() == 'true',
                'log_level': 'INFO',
            },
            
            # Database Settings
            'database': {
                'type': os.getenv('DB_TYPE', 'sqlite'),
                'sqlite': {
                    'path': 'subsidy_scoring.db'
                },
                'postgresql': {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'port': int(os.getenv('DB_PORT', 5432)),
                    'user': os.getenv('DB_USER', 'postgres'),
                    'password': os.getenv('DB_PASSWORD', ''),
                    'database': os.getenv('DB_NAME', 'subsidy_db'),
                }
            },
            
            # Model Settings
            'model': {
                'type': 'xgboost',
                'model_path': 'models/best_model.pkl',
                'threshold_approved': 0.7,
                'threshold_rejected': 0.4,
                'version': '1.0.0',
            },
            
            # Scoring Rules
            'scoring': {
                'min_score': 0,
                'max_score': 100,
                'decision_thresholds': {
                    'approved': 70,
                    'under_review': 40,
                    'rejected': 0
                }
            },
            
            # Reference Data
            'references': {
                'regions': REGIONS,
                'subsidy_types': SUBSIDY_TYPES,
                'farm_types': FARM_TYPES,
                'decision_status': DECISION_STATUS,
            },
            
            # Security
            'security': {
                'secret_key': os.getenv('SECRET_KEY', 'dev-secret-key'),
                'jwt_algorithm': 'HS256',
                'token_expire_hours': 24,
            },
            
            # Feature Configuration
            'features': {
                'required_numeric': [
                    'farm_size_hectares',
                    'annual_revenue',
                    'num_employees',
                    'equipment_value',
                    'debt_amount',
                ],
                'required_categorical': [
                    'region',
                    'farm_type',
                    'subsidy_type',
                ],
            }
        }
    
    def get(self, key: str, default=None):
        """Получить значение конфигурации"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value) -> None:
        """Установить значение конфигурации"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Сохранить конфигурацию в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info(f"✓ Конфигурация сохранена: {self.config_file}")
        except Exception as e:
            logger.error(f"✗ Ошибка сохранения конфига: {str(e)}")
    
    def get_region_by_code(self, code: str) -> Dict:
        """Получить регион по коду"""
        regions = self.get('references.regions', REGIONS)
        for region in regions:
            if region['code'] == code:
                return region
        return {}
    
    def get_subsidy_type_by_code(self, code: str) -> Dict:
        """Получить тип субсидии по коду"""
        types = self.get('references.subsidy_types', SUBSIDY_TYPES)
        for subsidy in types:
            if subsidy['code'] == code:
                return subsidy
        return {}
    
    def validate_application_data(self, data: Dict) -> Tuple[bool, List[str]]:
        """Валидирует данные заявки"""
        errors = []
        
        # Check required fields
        required_numeric = self.get('features.required_numeric', [])
        required_categorical = self.get('features.required_categorical', [])
        
        for field in required_numeric:
            if field not in data:
                errors.append(f"Отсутствует числовое поле: {field}")
            elif not isinstance(data[field], (int, float)):
                errors.append(f"Неверный тип для {field}")
        
        for field in required_categorical:
            if field not in data:
                errors.append(f"Отсутствует категориальное поле: {field}")
        
        return len(errors) == 0, errors


# Экспортируемая функция для быстрого получения конфига
def get_config() -> SystemConfig:
    """Получить глобальный экземпляр конфигурации"""
    if not hasattr(get_config, 'instance'):
        get_config.instance = SystemConfig()
    return get_config.instance


if __name__ == '__main__':
    # Example usage
    config = SystemConfig()
    config.save()
    
    # Test retrieval
    api_host = config.get('api.host')
    regions = config.get('references.regions')
    
    print(f"API Host: {api_host}")
    print(f"Regions: {len(regions)}")
