"""
SubsiSmart KZ - AI-скоринг для государственных субсидий Казахстана
Версия 2.0 — Merit-based scoring с explainability
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


# Приоритеты направлений (по гос. стратегии АПК Казахстана)
DIRECTION_PRIORITY = {
    'Субсидирование в скотоводстве': 1.0,
    'Субсидирование в овцеводстве': 0.9,
    'Субсидирование в коневодстве': 0.85,
    'Субсидирование в верблюдоводстве': 0.85,
    'Субсидирование в козоводстве': 0.8,
    'Субсидирование затрат по искусственному осеменению': 0.75,
    'Субсидирование в птицеводстве': 0.7,
    'Субсидирование в пчеловодстве': 0.65,
    'Субсидирование в свиноводстве': 0.6,
}


class SubsidyScoring:
    """
    AI-система merit-based скоринга заявок на субсидии.
    
    Логика: вместо 'кто первый подал' — оцениваем реальную
    эффективность хозяйства по историческим данным.
    """

    def __init__(self):
        self.label_encoders = {}
        self.kmeans_model = None
        self.scaler = StandardScaler()
        self.merit_scaler = MinMaxScaler(feature_range=(0, 100))
        self.df_full = None  # полный датасет для истории

    # ─────────────────────────────────────────────
    # 1. ПРЕДОБРАБОТКА
    # ─────────────────────────────────────────────
    def preprocess_data(self, df):
        df = df.copy()
        df = df.drop(['Unnamed: 2', 'Unnamed: 3'], axis=1, errors='ignore')
        df = df.dropna(subset=['Дата поступления', 'Область',
                                'Направление водства', 'Статус заявки'])

        # Парсим дату
        df['Дата поступления'] = pd.to_datetime(
            df['Дата поступления'], format='%d.%m.%Y %H:%M:%S', errors='coerce'
        )
        df = df.dropna(subset=['Дата поступления'])

        # Признаки из даты
        df['Месяц']       = df['Дата поступления'].dt.month
        df['День_недели'] = df['Дата поступления'].dt.dayofweek
        df['Час']         = df['Дата поступления'].dt.hour
        df['Квартал']     = df['Дата поступления'].dt.quarter

        # Кол-во голов скота = Причитающая сумма / Норматив
        df['Норматив'] = pd.to_numeric(df['Норматив'], errors='coerce').fillna(0)
        df['Причитающая сумма'] = pd.to_numeric(
            df['Причитающая сумма'], errors='coerce').fillna(0)

        df['Кол_голов'] = np.where(
            df['Норматив'] > 0,
            (df['Причитающая сумма'] / df['Норматив']).round(0),
            0
        )

        # Кодирование категорий
        for feat in ['Область', 'Направление водства', 'Статус заявки']:
            le = LabelEncoder()
            df[f'{feat}_encoded'] = le.fit_transform(df[feat].astype(str))
            self.label_encoders[feat] = le

        self.df_full = df.copy()
        return df

    # ─────────────────────────────────────────────
    # 2. ИСТОРИЯ ЗАЯВИТЕЛЯ (по Акимату как прокси)
    # ─────────────────────────────────────────────
    def build_applicant_history(self, df):
        """
        Строим профиль каждого заявителя на основе его истории.
        Используем Акимат + Район хозяйства как идентификатор.
        """
        df['applicant_id'] = (
            df['Акимат'].astype(str) + '|' +
            df['Район хозяйства'].astype(str)
        )

        history = df.groupby('applicant_id').agg(
            total_apps        = ('Статус заявки', 'count'),
            executed_count    = ('Статус заявки', lambda x: (x == 'Исполнена').sum()),
            approved_count    = ('Статус заявки', lambda x: (x == 'Одобрена').sum()),
            rejected_count    = ('Статус заявки', lambda x: (x == 'Отклонена').sum()),
            withdrawn_count   = ('Статус заявки', lambda x: (x == 'Отозвано').sum()),
            avg_amount        = ('Причитающая сумма', 'mean'),
            total_amount      = ('Причитающая сумма', 'sum'),
            avg_heads         = ('Кол_голов', 'mean'),
        ).reset_index()

        # Процент успешных заявок
        history['success_rate'] = (
            (history['executed_count'] + history['approved_count']) /
            history['total_apps'] * 100
        ).round(1)

        # Процент отклонённых
        history['rejection_rate'] = (
            history['rejected_count'] / history['total_apps'] * 100
        ).round(1)

        df = df.merge(history, on='applicant_id', how='left')
        return df, history

    # ─────────────────────────────────────────────
    # 3. MERIT-BASED СКОРИНГ (0–100, выше = лучше)
    # ─────────────────────────────────────────────
    def calculate_merit_score(self, df):
        """
        Merit Score показывает, насколько заявитель
        заслуживает субсидии на основе данных.

        Компоненты:
          A. История успеха       (0–40 баллов)
          B. Масштаб хозяйства    (0–25 баллов)
          C. Приоритет направления(0–20 баллов)
          D. Опыт (кол-во заявок) (0–15 баллов)
          E. Штраф за отказы      (0 до -20 баллов)
        """
        df = df.copy()

        # A. История успеха (0–40)
        df['score_history'] = (df['success_rate'].fillna(0) / 100 * 40).round(2)

        # B. Масштаб хозяйства — нормализуем кол-во голов (0–25)
        max_heads = df['avg_heads'].quantile(0.95)  # отсекаем выбросы сверху
        df['heads_capped'] = df['avg_heads'].clip(upper=max_heads)
        df['score_scale'] = (
            df['heads_capped'] / max_heads * 25
        ).fillna(0).round(2)

        # C. Приоритет направления (0–20)
        df['direction_priority'] = df['Направление водства'].map(
            DIRECTION_PRIORITY).fillna(0.5)
        df['score_direction'] = (df['direction_priority'] * 20).round(2)

        # D. Опыт заявителя (0–15)
        max_apps = df['total_apps'].quantile(0.95)
        df['score_experience'] = (
            df['total_apps'].clip(upper=max_apps) / max_apps * 15
        ).fillna(0).round(2)

        # E. Штраф за отказы (0 до -20)
        df['score_penalty'] = -(df['rejection_rate'].fillna(0) / 100 * 20).round(2)

        # Итоговый Merit Score
        df['Merit_Score'] = (
            df['score_history'] +
            df['score_scale'] +
            df['score_direction'] +
            df['score_experience'] +
            df['score_penalty']
        ).clip(0, 100).round(1)

        return df

    # ─────────────────────────────────────────────
    # 4. EXPLAINABILITY — почему такой скор
    # ─────────────────────────────────────────────
    def explain_score(self, row):
        """
        Возвращает человекочитаемое объяснение скора.
        """
        reasons = []

        # История
        if row.get('score_history', 0) >= 30:
            reasons.append(f"✅ Жоғары орындалу тарихы ({row.get('success_rate', 0):.0f}%)")
        elif row.get('score_history', 0) >= 15:
            reasons.append(f"🟡 Орташа орындалу тарихы ({row.get('success_rate', 0):.0f}%)")
        else:
            reasons.append(f"🔴 Төмен орындалу тарихы ({row.get('success_rate', 0):.0f}%)")

        # Масштаб
        if row.get('score_scale', 0) >= 18:
            reasons.append(f"✅ Ірі шаруашылық (~{row.get('avg_heads', 0):.0f} бас)")
        elif row.get('score_scale', 0) >= 8:
            reasons.append(f"🟡 Орта шаруашылық (~{row.get('avg_heads', 0):.0f} бас)")
        else:
            reasons.append(f"⚪ Кіші шаруашылық (~{row.get('avg_heads', 0):.0f} бас)")

        # Направление
        prio = row.get('direction_priority', 0)
        if prio >= 0.9:
            reasons.append(f"✅ Жоғары басымдықты бағыт (скотоводство/овцеводство)")
        elif prio >= 0.7:
            reasons.append(f"🟡 Орташа басымдықты бағыт")
        else:
            reasons.append(f"⚪ Стандартты бағыт")

        # Штраф
        if row.get('score_penalty', 0) < -10:
            reasons.append(
                f"🔴 Бұрын {row.get('rejected_count', 0)} рет қабылданбаған өтінім бар"
            )
        elif row.get('score_penalty', 0) < -5:
            reasons.append(
                f"🟡 Бірнеше қабылданбаған өтінім бар"
            )

        # Тәжірибе
        if row.get('total_apps', 0) >= 5:
            reasons.append(f"✅ Тәжірибелі өтініш беруші ({row.get('total_apps', 0)} өтінім)")

        return ' | '.join(reasons)

    # ─────────────────────────────────────────────
    # 5. АНОМАЛИИ — исправленная логика
    # ─────────────────────────────────────────────
    def detect_anomalies(self, df):
        """
        Аномалии определяем только по статистике ВНУТРИ направления,
        используя только 3-sigma по нормализованной сумме на голову.
        НЕ используем соотношение сумма/норматив (оно всегда большое).
        """
        df = df.copy()
        df['Risk_Level'] = 'Normal'
        df['risk_reasons'] = ''

        for direction in df['Направление водства'].unique():
            mask = df['Направление водства'] == direction
            subset = df[mask].copy()

            if len(subset) < 10:
                continue

            # Аномалия по сумме на голову
            amount_per_head = subset['Причитающая сумма'] / subset['Кол_голов'].replace(0, np.nan)
            amount_per_head = amount_per_head.fillna(0)

            mean_aph = amount_per_head.mean()
            std_aph  = amount_per_head.std()

            if std_aph > 0:
                threshold_high = mean_aph + 3 * std_aph
                threshold_med  = mean_aph + 2 * std_aph

                high_mask = mask & (
                    subset['Причитающая сумма'].div(
                        subset['Кол_голов'].replace(0, np.nan)
                    ).fillna(0) > threshold_high
                ).reindex(df.index, fill_value=False)

                med_mask = mask & (
                    subset['Причитающая сумма'].div(
                        subset['Кол_голов'].replace(0, np.nan)
                    ).fillna(0) > threshold_med
                ).reindex(df.index, fill_value=False) & ~high_mask

                df.loc[high_mask, 'Risk_Level'] = 'High Risk'
                df.loc[high_mask, 'risk_reasons'] = 'Бас басына сумма нормадан 3σ жоғары'
                df.loc[med_mask, 'Risk_Level'] = 'Medium Risk'
                df.loc[med_mask, 'risk_reasons'] = 'Бас басына сумма нормадан 2σ жоғары'

        # Нулевая сумма при ненулевом нормативе
        zero_mask = (df['Причитающая сумма'] == 0) & (df['Норматив'] > 0)
        df.loc[zero_mask, 'Risk_Level'] = 'Medium Risk'
        df.loc[zero_mask, 'risk_reasons'] = 'Норматив бар, бірақ сумма нөл'

        return df

    # ─────────────────────────────────────────────
    # 6. K-MEANS КЛАСТЕРИЗАЦИЯ
    # ─────────────────────────────────────────────
    def create_kmeans_segments(self, df, n_clusters=4):
        features = df[['Норматив', 'Причитающая сумма', 'Кол_голов']].copy().fillna(0)
        features_scaled = self.scaler.fit_transform(features)

        self.kmeans_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['Кластер'] = self.kmeans_model.fit_predict(features_scaled)

        # Даём читаемые названия кластерам по среднему размеру хозяйства
        cluster_means = df.groupby('Кластер')['Кол_голов'].mean().sort_values()
        labels = ['🟢 Кіші', '🔵 Орташа', '🟡 Ірі', '🔴 Мега']
        cluster_label_map = {
            cid: labels[i] for i, cid in enumerate(cluster_means.index)
        }
        df['Кластер_атауы'] = df['Кластер'].map(cluster_label_map)

        cluster_analysis = df.groupby('Кластер_атауы').agg({
            'Норматив':          'mean',
            'Причитающая сумма': 'mean',
            'Кол_голов':         'mean',
            'Merit_Score':       'mean',
            'Статус заявки':     'count',
        }).round(1)

        return df, cluster_analysis

    # ─────────────────────────────────────────────
    # 7. SHORTLIST — топ кандидаты для комиссии
    # ─────────────────────────────────────────────
    def generate_shortlist(self, df, top_n=20, direction=None, region=None):
        """
        Формирует список лучших кандидатов для рассмотрения комиссией.
        Фильтрует только текущие заявки (Получена / Одобрена).
        """
        # Берём только активные заявки
        active_statuses = ['Получена', 'Одобрена', 'Сформировано поручение']
        candidates = df[df['Статус заявки'].isin(active_statuses)].copy()

        if direction:
            candidates = candidates[candidates['Направление водства'] == direction]
        if region:
            candidates = candidates[candidates['Область'] == region]

        # Сортируем по Merit Score
        candidates = candidates.sort_values('Merit_Score', ascending=False)

        cols = [
            'Номер заявки', 'Дата поступления', 'Область',
            'Район хозяйства', 'Направление водства',
            'Норматив', 'Причитающая сумма', 'Кол_голов',
            'Merit_Score', 'score_history', 'score_scale',
            'score_direction', 'score_experience', 'score_penalty',
            'success_rate', 'total_apps', 'rejected_count',
            'Risk_Level', 'Explainability', 'Кластер_атауы'
        ]
        cols = [c for c in cols if c in candidates.columns]

        return candidates[cols].head(top_n)

    # ─────────────────────────────────────────────
    # 8. РЕГИОНАЛЬНЫЙ ОТЧЁТ
    # ─────────────────────────────────────────────
    def regional_report(self, df):
        regional_stats = df.groupby('Область').agg(
            Всего_заявок            = ('Статус заявки', 'count'),
            Исполнено               = ('Статус заявки', lambda x: (x == 'Исполнена').sum()),
            Одобрено                = ('Статус заявки', lambda x: (x == 'Одобрена').sum()),
            Отклонено               = ('Статус заявки', lambda x: (x == 'Отклонена').sum()),
            Общая_сумма             = ('Причитающая сумма', 'sum'),
            Средняя_сумма           = ('Причитающая сумма', 'mean'),
            Средний_Merit_Score     = ('Merit_Score', 'mean'),
        ).round(1)

        regional_stats['Процент_исполненных'] = (
            regional_stats['Исполнено'] / regional_stats['Всего_заявок'] * 100
        ).round(1)

        return regional_stats.sort_values('Средний_Merit_Score', ascending=False)

    # ─────────────────────────────────────────────
    # 9. ПОЛНЫЙ ПАЙПЛАЙН
    # ─────────────────────────────────────────────
    def run_full_pipeline(self, df):
        print("🔧 Шаг 1: Предобработка данных...")
        df = self.preprocess_data(df)
        print(f"   ✓ {len(df):,} записей обработано")

        print("📊 Шаг 2: Построение истории заявителей...")
        df, history = self.build_applicant_history(df)
        print(f"   ✓ {len(history):,} уникальных заявителей")

        print("🎯 Шаг 3: Merit-based скоринг...")
        df = self.calculate_merit_score(df)
        print(f"   ✓ Merit Score: мин={df['Merit_Score'].min():.1f}, "
              f"макс={df['Merit_Score'].max():.1f}, "
              f"среднее={df['Merit_Score'].mean():.1f}")

        print("🔍 Шаг 4: Explainability...")
        df['Explainability'] = df.apply(self.explain_score, axis=1)
        print("   ✓ Объяснения сформированы для каждой заявки")

        print("🚨 Шаг 5: Детектирование аномалий...")
        df = self.detect_anomalies(df)
        risk_counts = df['Risk_Level'].value_counts()
        print(f"   ✓ Normal: {risk_counts.get('Normal', 0):,}")
        print(f"   ✓ Medium Risk: {risk_counts.get('Medium Risk', 0):,}")
        print(f"   ✓ High Risk: {risk_counts.get('High Risk', 0):,}")

        print("🔵 Шаг 6: K-Means кластеризация...")
        df, cluster_analysis = self.create_kmeans_segments(df)
        print("   ✓ 4 кластера создано")

        return df, cluster_analysis

    def generate_full_report(self, df):
        return {
            'total_applications':   int(len(df)),
            'status_distribution':  df['Статус заявки'].value_counts().to_dict(),
            'total_subsidy_amount': float(df['Причитающая сумма'].sum()),
            'average_subsidy':      float(df['Причитающая сумма'].mean()),
            'high_risk_count':      int((df['Risk_Level'] == 'High Risk').sum()),
            'medium_risk_count':    int((df['Risk_Level'] == 'Medium Risk').sum()),
            'avg_merit_score':      float(df['Merit_Score'].mean()),
            'regions_count':        int(df['Область'].nunique()),
            'directions_count':     int(df['Направление водства'].nunique()),
        }


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    import os
    print("=" * 70)
    print("SubsiSmart KZ v2.0 — Merit-based AI скоринг субсидий")
    print("=" * 70)

    scoring = SubsidyScoring()

    fname = os.listdir('data')[0]
    print(f"\n📂 Загрузка: {fname}")
    df = pd.read_excel(f'data/{fname}', skiprows=4)
    print(f"✓ Загружено {len(df):,} строк\n")

    df, cluster_analysis = scoring.run_full_pipeline(df)

    print("\n📋 Кластеры:")
    print(cluster_analysis)

    print("\n🏆 ТОП-10 кандидатов для субсидии:")
    shortlist = scoring.generate_shortlist(df, top_n=10)
    if len(shortlist) > 0:
        print(shortlist[['Номер заявки', 'Область', 'Направление водства',
                          'Merit_Score', 'Explainability']].to_string())
    else:
        print("   Активных заявок не найдено")

    print("\n🗺️ Региональный отчёт:")
    reg = scoring.regional_report(df)
    print(reg[['Всего_заявок', 'Процент_исполненных',
               'Средний_Merit_Score', 'Общая_сумма']].head(10))

    report = scoring.generate_full_report(df)
    print("\n" + "=" * 70)
    print("ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 70)
    print(f"Всего заявок:           {report['total_applications']:,}")
    print(f"Общая сумма субсидий:   {report['total_subsidy_amount']:,.0f} тг")
    print(f"Средняя субсидия:       {report['average_subsidy']:,.0f} тг")
    print(f"Средний Merit Score:    {report['avg_merit_score']:.1f}/100")
    print(f"High Risk заявок:       {report['high_risk_count']:,} "
          f"({report['high_risk_count']/report['total_applications']*100:.1f}%)")
    print(f"Medium Risk заявок:     {report['medium_risk_count']:,}")
    print(f"Регионов:               {report['regions_count']}")

    os.makedirs('results', exist_ok=True)
    df.to_csv('results/processed_data.csv', index=False, encoding='utf-8-sig')
    scoring.regional_report(df).to_csv(
        'results/regional_report.csv', encoding='utf-8-sig')
    scoring.generate_shortlist(df, top_n=50).to_csv(
        'results/shortlist.csv', index=False, encoding='utf-8-sig')
    print("\n✅ Нәтижелер results/ папкасына сақталды")


if __name__ == "__main__":
    main()
