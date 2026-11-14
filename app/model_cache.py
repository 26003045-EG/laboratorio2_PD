import os
import threading
import time
import mlflow
from mlflow.tracking import MlflowClient

MODEL_NAME = os.getenv('MODEL_NAME', 'NovaMercadoVentas')
ALIAS = 'champion'

class ModelCache:
    def __init__(self):
        self.lock = threading.Lock()
        self.model = None
        self.version = None
        self.checked = 0
        self.available = False

    def refresh(self, force=False):
        with self.lock:
            if not force and time.monotonic() - self.checked < 15:
                return
            self.checked = time.monotonic()
            try:
                mlflow.set_tracking_uri(os.environ['MLFLOW_TRACKING_URI'])
                client = MlflowClient()
                mv = client.get_model_version_by_alias(MODEL_NAME, ALIAS)
                if self.model is None or self.version != str(mv.version):
                    new_model = mlflow.sklearn.load_model(f'models:/{MODEL_NAME}/{mv.version}')
                    self.model = new_model
                    self.version = str(mv.version)
                self.available = True
            except Exception:
                self.available = False
                # Never discard an already loaded model during MLflow outage.

cache = ModelCache()
