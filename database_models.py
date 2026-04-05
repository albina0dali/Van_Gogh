"""
БЛОК 9: База данных и ORM (SQLAlchemy)
Database schema and ORM models for subsidy scoring system
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Boolean, Text, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
from typing import Optional, List
import logging
import os

logger = logging.getLogger(__name__)

# Создание базы данных
Base = declarative_base()


# ==================== Enums ====================

class DecisionStatus(enum.Enum):
    """Статусы решения по заявке"""
    PENDING = "pending"           # Ожидание рассмотрения
    UNDER_REVIEW = "under_review" # На рассмотрении
    APPROVED = "approved"         # Одобрена
    REJECTED = "rejected"         # Отклонена
    PENDING_DOCS = "pending_docs" # Ожидание документов


class ApplicationStatus(enum.Enum):
    """Статусы заявки в системе"""
    DRAFT = "draft"               # Черновик
    SUBMITTED = "submitted"       # Подана
    PROCESSING = "processing"     # Обработка
    COMPLETED = "completed"       # Завершена
    CANCELLED = "cancelled"       # Отменена


# ==================== Models ====================

class Application(Base):
    """Модель заявки на субсидию"""
    
    __tablename__ = 'applications'
    
    id = Column(String(50), primary_key=True)
    farm_name = Column(String(255), nullable=False, index=True)
    organization_id = Column(String(50), nullable=True)
    region = Column(String(100), nullable=False, index=True)
    farm_type = Column(String(50), nullable=False)
    subsidy_type = Column(String(100), nullable=False, index=True)
    
    # Статусы
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.DRAFT)
    decision = Column(Enum(DecisionStatus), nullable=True)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    decision_date = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Финансовые сведения
    requested_amount = Column(Float, nullable=True)  # Запрашиваемая сумма
    approved_amount = Column(Float, default=0)        # Одобренная сумма
    
    # Связи
    applicant_data = relationship("ApplicantData", back_populates="application", uselist=False)
    predictions = relationship("Prediction", back_populates="application")
    explanations = relationship("Explanation", back_populates="application")
    audit_logs = relationship("AuditLog", back_populates="application")
    
    def __repr__(self):
        return f"<Application(id={self.id}, farm={self.farm_name}, status={self.status})>"


class ApplicantData(Base):
    """Модель данных заявителя"""
    
    __tablename__ = 'applicant_data'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(String(50), ForeignKey('applications.id'), nullable=False, unique=True)
    
    # Информация о хозяйстве
    farm_size_hectares = Column(Float, nullable=True)
    land_ownership_type = Column(String(50), nullable=True)  # собственность/аренда
    
    # Финансовые показатели
    annual_revenue = Column(Float, nullable=True)
    annual_profit = Column(Float, nullable=True)
    debt_amount = Column(Float, nullable=True)
    equipment_value = Column(Float, nullable=True)
    
    # Персонал
    num_employees = Column(Integer, nullable=True)
    num_full_time = Column(Integer, nullable=True)
    
    # История
    years_in_operation = Column(Integer, nullable=True)
    previous_subsidies = Column(Integer, default=0)
    previous_subsidy_amount = Column(Float, default=0)
    
    # Сертификаты и разрешения
    has_tax_registration = Column(Boolean, default=False)
    has_environmental_permit = Column(Boolean, default=False)
    has_veterinary_cert = Column(Boolean, default=False)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь
    application = relationship("Application", back_populates="applicant_data")
    
    def __repr__(self):
        return f"<ApplicantData(app_id={self.application_id}, farm_size={self.farm_size_hectares})>"


class Prediction(Base):
    """Модель предсказания модели"""
    
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(String(50), ForeignKey('applications.id'), nullable=False)
    
    # Результаты модели
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20), nullable=False)
    score = Column(Float, nullable=False)  # Score 0-100
    confidence = Column(Float, nullable=True)  # Confidence 0-1
    
    # Класс предсказания
    predicted_class = Column(Enum(DecisionStatus), nullable=False)
    
    # Служебная информация
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processing_time_ms = Column(Integer, nullable=True)  # Время обработки в мс
    
    # Связь
    application = relationship("Application", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction(app_id={self.application_id}, score={self.score}, class={self.predicted_class})>"


class Explanation(Base):
    """Модель объяснения решения"""
    
    __tablename__ = 'explanations'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(String(50), ForeignKey('applications.id'), nullable=False, unique=True)
    
    # SHAP значения (сохраняем как JSON)
    shap_values = Column(Text, nullable=True)  # JSON
    
    # Top факторы
    top_positive_factors = Column(Text, nullable=True)  # JSON list
    top_negative_factors = Column(Text, nullable=True)  # JSON list
    
    # Текстовое объяснение
    explanation_text = Column(Text, nullable=True)  # Human-readable explanation
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь
    application = relationship("Application", back_populates="explanations")
    
    def __repr__(self):
        return f"<Explanation(app_id={self.application_id})>"


class AuditLog(Base):
    """Модель аудит-лога"""
    
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(String(50), ForeignKey('applications.id'), nullable=False)
    
    # Информация об изменении
    action = Column(String(50), nullable=False)  # created, updated, predicted, reviewed, etc.
    changed_fields = Column(Text, nullable=True)  # JSON
    old_values = Column(Text, nullable=True)      # JSON
    new_values = Column(Text, nullable=True)      # JSON
    
    # Кто совершил действие
    actor = Column(String(100), nullable=True)  # username or system
    actor_role = Column(String(50), nullable=True)  # admin, reviewer, system, etc.
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(45), nullable=True)
    details = Column(Text, nullable=True)
    
    # Связь
    application = relationship("Application", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(app_id={self.application_id}, action={self.action}, time={self.created_at})>"


# ==================== Database Manager ====================

class DatabaseManager:
    """Класс для управления БД"""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Инициализирует подключение к БД
        db_url: строка подключения (например: sqlite:///subsidy.db)
        """
        
        if db_url is None:
            # Использовать SQLite по умолчанию
            db_path = os.getenv('DATABASE_URL', 'sqlite:///subsidy_scoring.db')
            db_url = db_path
        
        self.engine = create_engine(db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.logger = logger
    
    def create_all_tables(self):
        """Создает все таблицы в БД"""
        try:
            Base.metadata.create_all(self.engine)
            self.logger.info("✓ Все таблицы созданы успешно")
        except Exception as e:
            self.logger.error(f"✗ Ошибка создания таблиц: {str(e)}")
            raise
    
    def drop_all_tables(self):
        """Удаляет все таблицы (используется для тестирования)"""
        try:
            Base.metadata.drop_all(self.engine)
            self.logger.info("✓ Все таблицы удалены")
        except Exception as e:
            self.logger.error(f"✗ Ошибка удаления таблиц: {str(e)}")
            raise
    
    def get_session(self):
        """Получить новую сессию"""
        return self.Session()
    
    def add_application(self, session, application: Application) -> bool:
        """Добавить новую заявку"""
        try:
            session.add(application)
            session.commit()
            self.logger.info(f"✓ Заявка добавлена: {application.id}")
            return True
        except Exception as e:
            session.rollback()
            self.logger.error(f"✗ Ошибка добавления заявки: {str(e)}")
            return False
    
    def get_application(self, session, app_id: str) -> Optional[Application]:
        """Получить заявку по ID"""
        try:
            return session.query(Application).filter(Application.id == app_id).first()
        except Exception as e:
            self.logger.error(f"✗ Ошибка получения заявки: {str(e)}")
            return None
    
    def get_applications_by_region(self, session, region: str, limit: int = 100) -> List[Application]:
        """Получить заявки по региону"""
        try:
            return session.query(Application).filter(
                Application.region == region
            ).order_by(Application.created_at.desc()).limit(limit).all()
        except Exception as e:
            self.logger.error(f"✗ Ошибка получения заявок: {str(e)}")
            return []
    
    def update_application_decision(self, session, app_id: str, 
                                   decision: DecisionStatus, amount: float = 0) -> bool:
        """Обновить решение по заявке"""
        try:
            app = session.query(Application).filter(Application.id == app_id).first()
            if app:
                app.decision = decision
                app.decision_date = datetime.utcnow()
                if amount > 0:
                    app.approved_amount = amount
                session.commit()
                self.logger.info(f"✓ Решение по заявке обновлено: {app_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            self.logger.error(f"✗ Ошибка обновления решения: {str(e)}")
            return False
    
    def get_statistics(self, session) -> dict:
        """Получить статистику"""
        try:
            total_apps = session.query(Application).count()
            approved = session.query(Application).filter(
                Application.decision == DecisionStatus.APPROVED
            ).count()
            rejected = session.query(Application).filter(
                Application.decision == DecisionStatus.REJECTED
            ).count()
            
            return {
                'total_applications': total_apps,
                'approved': approved,
                'rejected': rejected,
                'approval_rate': (approved / total_apps * 100) if total_apps > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"✗ Ошибка получения статистики: {str(e)}")
            return {}


# ==================== Экспортируемые функции ====================

def init_database(db_url: Optional[str] = None) -> DatabaseManager:
    """Инициализировать БД и создать все таблицы"""
    manager = DatabaseManager(db_url)
    manager.create_all_tables()
    return manager


if __name__ == '__main__':
    # Example usage
    db = init_database()
    
    # Create a test application
    session = db.get_session()
    
    test_app = Application(
        id='APP_TEST_001',
        farm_name='ООО Агро-Тест',
        region='Акмолинская область',
        farm_type='LLP',
        subsidy_type='DEV_LIVESTOCK'
    )
    
    db.add_application(session, test_app)
    session.close()
    
    logger.info("✓ Test successful")
