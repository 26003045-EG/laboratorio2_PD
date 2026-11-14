import pytest
from mlflow.exceptions import MlflowException
from mlflow.protos.databricks_pb2 import RESOURCE_DOES_NOT_EXIST, INTERNAL_ERROR
from training.train import champion, register


def test_ausente_es_distinto_de_fallo():
    class Client:
        error = RESOURCE_DOES_NOT_EXIST
        def get_model_version_by_alias(self, *args):
            raise MlflowException('prueba', error_code=self.error)
    client = Client()
    assert champion(client) is None
    client.error = INTERNAL_ERROR
    with pytest.raises(MlflowException):
        champion(client)
