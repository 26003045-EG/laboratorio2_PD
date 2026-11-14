"""Validaci?n reproducible con los mismos c?lculos del entrenamiento."""
import json
import os
from pathlib import Path
import pandas as pd


def evaluar():
    root = Path(__file__).resolve().parents[1]
    os.environ.setdefault('DATA_DIR', str(root / 'data/entrada'))
    from app.data import catalogs
    from training.evaluation import evaluate
    df = pd.read_csv(Path(os.environ['DATA_DIR']) / 'historico_ventas.csv', parse_dates=['fecha'])
    _, _, _, result = evaluate(df, catalogs()[2])
    target = root / 'evidencias/validacion_actual.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == '__main__':
    evaluar()
