from types import SimpleNamespace
from app import model_cache as module


def test_conserva_modelo_y_recupera(monkeypatch):
    cache = module.ModelCache()
    state = {'version': '1', 'fail': False}
    class Client:
        def get_model_version_by_alias(self, *args):
            if state['fail']:
                raise ConnectionError('MLflow no disponible')
            return SimpleNamespace(version=state['version'])
    monkeypatch.setattr(module, 'MlflowClient', Client)
    monkeypatch.setattr(module.mlflow.sklearn, 'load_model', lambda uri: uri)
    monkeypatch.setenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
    cache.refresh(True)
    original = cache.model
    state['fail'] = True
    cache.refresh(True)
    assert cache.model == original and cache.version == '1' and not cache.available
    state.update(fail=False, version='2')
    cache.refresh(True)
    assert cache.available and cache.version == '2' and cache.model != original
