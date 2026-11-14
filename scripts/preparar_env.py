"""Crear credenciales locales fuera del repositorio, sin dependencias."""
from pathlib import Path
import base64
import secrets

root = Path(__file__).resolve().parents[1]
out = root / '.env'
if out.exists():
    print('Archivo .env existente; se conserva.'); raise SystemExit(0)

def secret():
    return secrets.token_urlsafe(28)

values = {
    'NOVA_DB_PASSWORD': secret(),
    'AIRFLOW_DB_PASSWORD': secret(),
    'AIRFLOW_USER_NAME': 'admin',
    'AIRFLOW_USER_PASS': secret(),
    'AIRFLOW_SECRET_KEY': secret(),
    'AIRFLOW_FERNET_KEY': base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
}
out.write_text(''.join(f'{k}={v}\n' for k, v in values.items()), encoding='utf-8')
print('Configuracion local .env creada; no se versiona.')
