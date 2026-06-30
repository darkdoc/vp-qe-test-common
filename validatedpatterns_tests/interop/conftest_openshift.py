import os

import pytest
from kubernetes import config
from kubernetes.config.config_exception import ConfigException
from openshift.dynamic import DynamicClient


@pytest.fixture
def openshift_dyn_client(request):
    env_var = request.param

    kubeconfig = os.getenv(env_var)
    if not kubeconfig:
        pytest.fail(f"Environment variable '{env_var}' is not set.")

    if not os.path.isfile(kubeconfig):
        pytest.fail(f"Kubeconfig file '{kubeconfig}' does not exist.")

    try:
        return DynamicClient(client=config.new_client_from_config(kubeconfig))
    except ConfigException as exc:
        pytest.fail(f"Failed to load kubeconfig '{kubeconfig}': {exc}")
