"""
Testing Guide for SubsiSmartKZ System
Быстрая проверка всех компонентов
"""

import logging
from pathlib import Path

# Configure logging with UTF-8 encoding for Windows
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def test_imports():
    """Проверить импорт всех модулей"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Импорт модулей")
    logger.info("="*60)
    
    try:
        from data_loader import DataLoader
        logger.info("✓ data_loader.py")
        
        from eda_analysis import ExploratoryDataAnalysis
        logger.info("✓ eda_analysis.py")
        
        from feature_engineer import FeatureEngineer
        logger.info("✓ feature_engineer.py")
        
        # Правильно закрыть БД перед удалением
        import os
        import time
        time.sleep(0.1)
        
        try:
            os.remove('test_subsidy.db')
        except OSError:
            pass  # Файл может быть заблокирован
        from explainability import ExplainablePredictions
        logger.info("✓ explainability.py")
        
        from api_server import app
        logger.info("✓ api_server.py")
        
        from database_models import init_database, Application
        logger.info("✓ database_models.py")
        
        from config_manager import SystemConfig
        logger.info("✓ config_manager.py")
        
        from utilities import (DataImportUtility, ReportGenerator, 
                             ModelMonitor, DatabaseBackup)
        logger.info("✓ utilities.py")
        
        from main_pipeline import SubsidyScoringPipeline
        logger.info("✓ main_pipeline.py")
        
        logger.info("\n✅ ВСЕ МОДУЛИ ИМПОРТИРОВАНЫ УСПЕШНО")
        return True
    
    except Exception as e:
        logger.error(f"❌ ОШИБКА ИМПОРТА: {str(e)}")
        return False


def test_config():
    """Проверить конфигурацию"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Конфигурация")
    logger.info("="*60)
    
    try:
        from config_manager import SystemConfig
        
        config = SystemConfig()
        
        # Проверить регионы
        regions = config.get('references.regions', [])
        logger.info(f"✓ Регионы загружены: {len(regions)} регионов")
        
        # Проверить типы субсидий
        subsidy_types = config.get('references.subsidy_types', [])
        logger.info(f"✓ Типы субсидий: {len(subsidy_types)} типов")
        
        # Проверить модель
        model_path = config.get('model.model_path')
        logger.info(f"✓ Путь модели: {model_path}")
        
        logger.info("\n✅ КОНФИГУРАЦИЯ РАБОТАЕТ")
        return True
    
    except Exception as e:
        logger.error(f"❌ ОШИБКА КОНФИГУРАЦИИ: {str(e)}")
        return False


def test_database():
    """Проверить базу данных"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: База данных")
    logger.info("="*60)
    
    try:
        from database_models import init_database, Application
        from datetime import datetime
        
        # Инициализировать БД
        db = init_database('sqlite:///test_subsidy.db')
        logger.info("✓ База данных инициализирована")
        
        # Создать тестовую заявку
        session = db.get_session()
        
        test_app = Application(
            id='TEST_APP_001',
            farm_name='ООО Тестовое Хозяйство',
            region='Акмолинская область',
            farm_type='LLP',
            subsidy_type='DEV_LIVESTOCK'
        )
        
        success = db.add_application(session, test_app)
        
        if success:
            logger.info("✓ Заявка добавлена в БД")
            
            # Получить заявку
            retrieved_app = db.get_application(session, 'TEST_APP_001')
            if retrieved_app:
                logger.info(f"✓ Заявка найдена: {retrieved_app.farm_name}")
            else:
                logger.error("✗ Не удалось получить заявку")
                return False
        
        session.close()
        
        # Удалить тестовую БД
        import os
        os.remove('test_subsidy.db')
        
        logger.info("\n✅ БД РАБОТАЕТ КОРРЕКТНО")
        return True
    
    except Exception as e:
        logger.error(f"❌ ОШИБКА БД: {str(e)}")
        return False


def test_api():
    """Проверить API endpoints"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: REST API")
    logger.info("="*60)
    
    try:
        from api_server import app
        
        # Создать тестовый клиент
        client = app.test_client()
        
        # Тест /health
        response = client.get('/api/health')
        if response.status_code == 200:
            logger.info("✓ GET /api/health - ОК")
        else:
            logger.error(f"✗ GET /api/health - {response.status_code}")
            return False
        
        # Тест /references/regions
        response = client.get('/api/references/regions')
        if response.status_code == 200:
            logger.info("✓ GET /api/references/regions - ОК")
        else:
            logger.error(f"✗ GET /api/references/regions - {response.status_code}")
            return False
        
        # Тест /references/subsidy_types
        response = client.get('/api/references/subsidy_types')
        if response.status_code == 200:
            logger.info("✓ GET /api/references/subsidy_types - ОК")
        else:
            logger.error(f"✗ GET /api/references/subsidy_types - {response.status_code}")
            return False
        
        logger.info("\n✅ API ENDPOINTS РАБОТАЮТ")
        return True
    
    except Exception as e:
        logger.error(f"❌ ОШИБКА API: {str(e)}")
        return False


def test_utilities():
    """Проверить утилиты"""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Утилиты")
    logger.info("="*60)
    
    try:
        from utilities import TestUtilities, ReportGenerator, ModelMonitor
        
        # Тест создания примера заявки
        app_data = TestUtilities.create_sample_application()
        logger.info(f"✓ Тестовая заявка создана: {app_data['farm_name']}")
        
        # Тест создания признаков
        features = TestUtilities.create_sample_features()
        logger.info(f"✓ Тестовые признаки созданы: {len(features)} признаков")
        
        # Тест мониторинга
        monitor = ModelMonitor()
        monitor.log_prediction({'score': 75.5, 'recommendation': 'Одобрена'})
        logger.info("✓ Предсказание залогировано")
        
        stats = monitor.get_model_statistics()
        if stats:
            logger.info(f"✓ Статистика получена: {stats.get('total_predictions', 0)} предсказаний")
        
        logger.info("\n✅ УТИЛИТЫ РАБОТАЮТ")
        return True
    
    except Exception as e:
        logger.error(f"❌ ОШИБКА УТИЛИТ: {str(e)}")
        return False


def test_config_json():
    """Проверить config.json"""
    logger.info("\n" + "="*60)
    logger.info("TEST 6: config.json")
    logger.info("="*60)
    
    try:
        import json
        
        config_path = Path('config.json')
        
        if not config_path.exists():
            logger.error("✗ config.json не найден")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logger.info("✓ config.json загружен")
        logger.info(f"  - API: {config['api']['host']}:{config['api']['port']}")
        logger.info(f"  - Database type: {config['database']['type']}")
        logger.info(f"  - Model: {config['model']['type']}")
        logger.info(f"  - Regions: {len(config['references']['regions'])}")
        logger.info(f"  - Subsidy types: {len(config['references']['subsidy_types'])}")
        
        logger.info("\n✅ CONFIG.JSON В ПОРЯДКЕ")
        return True
    
    except Exception as e:
        logger.error(f"❌ ОШИБКА CONFIG: {str(e)}")
        return False


def run_all_tests():
    """Запустить все тесты"""
    logger.info("\n")
    logger.info("╔" + "="*58 + "╗")
    logger.info("║" + "  ТЕСТИРОВАНИЕ СИСТЕМЫ СКОРИНГА СУБСИДИЙ  ".center(58) + "║")
    logger.info("╚" + "="*58 + "╝")
    
    results = {
        'Импорт модулей': test_imports(),
        'Конфигурация': test_config(),
        'База данных': test_database(),
        'REST API': test_api(),
        'Утилиты': test_utilities(),
        'config.json': test_config_json(),
    }
    
    # Итоги
    logger.info("\n" + "="*60)
    logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
    logger.info("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("="*60)
    logger.info(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        logger.info("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ")
        return True
    else:
        logger.error(f"\n⚠️  {total - passed} тестов не пройдено")
        return False


if __name__ == '__main__':
    import sys
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
