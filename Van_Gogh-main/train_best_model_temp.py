from pathlib import Path
from data_loader import DataLoader
from feature_engineer import FeatureEngineer
from model_trainer import SubsidyModelTrainer

base = Path(__file__).resolve().parent

loader = DataLoader(str(base / 'data'))
df = loader.preprocess()

target_cols = [c for c in df.columns if any(k in c.lower() for k in ['статус', 'status', 'decision'])]
if not target_cols:
    raise RuntimeError('Target column not found after preprocessing')
target_col = target_cols[0]

engineer = FeatureEngineer(df, target_col=target_col)
df_engineered = engineer.fit_transform()
engineer.save_transformers(str(base / 'models' / 'transformers'))

trainer = SubsidyModelTrainer(output_dir=str(base / 'models'))
trainer.prepare_data(df_engineered, target_col=target_col)
trainer.train_all_models()

print('BEST_MODEL_READY', str(base / 'models' / 'best_model.pkl'))