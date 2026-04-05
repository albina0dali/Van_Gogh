import pandas as pd

df = pd.read_excel('data/Выгрузка_по_выданным_субсидиям_2025_год__обезлич_.xlsx')

print("=" * 60)
print("РЕГИОНЫ (Область)")
print("=" * 60)
regions = sorted(df['Область'].unique())
for r in regions:
    print(f"  '{r}',")

print("\n" + "=" * 60)
print("НАПРАВЛЕНИЯ ЖИВОТНОВОДСТВА")
print("=" * 60)
directions = sorted(df['Направление водства'].unique())
for d in directions:
    print(f"  '{d}',")

print("\n" + "=" * 60)
print("ТИПЫ СУБСИДИРОВАНИЯ (первые 12)")
print("=" * 60)
subsidies = sorted(df['Наименование субсидирования'].unique())[:12]
for s in subsidies:
    # Сокращаем длинное название
    short = s[:60] + "..." if len(s) > 60 else s
    print(f"  '{s}',")
