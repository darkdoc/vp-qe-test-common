import base64
import fileinput
import logging

import requests
from ocp_resources.secret import Secret
from requests import RequestException
from urllib3.exceptions import InsecureRequestWarning, ProtocolError
from openshift.dynamic import DynamicClient

from . import __loggername__

logger = logging.getLogger(__loggername__)

# Duplicated in layered-zero-trust, but not used anywhere
# def load_yaml_file(file_path):
#     """
#     Load and parse the yaml file
#     :param file_path: (str) file path
#     :return: (dict) yaml_config_obj in the form of Python dict
#     """
#     yaml_config_obj = None
#     with open(file_path, "r") as yfh:
#         try:
#             yaml_config_obj = yaml.load(yfh, Loader=yaml.FullLoader)
#         except Exception as ex:
#             raise yaml.YAMLError("YAML Syntax Error:\n %s" % ex)
#         logger.info("Yaml Config : %s", yaml_config_obj)
#     return yaml_config_obj


def get_long_live_bearer_token(
    openshift_dyn_client: DynamicClient,
    namespace: str = "default",
    sub_string: str = "default-token",
) -> str:
    """
    Return the decoded bearer token from the service account secret whose
    name contains ``sub_string``.
    """
    try:
        matching_secrets = [
            secret
            for secret in Secret.get(
                dyn_client=openshift_dyn_client,
                namespace=namespace,
            )
            if sub_string in secret.instance.metadata.name
        ]
    except ProtocolError as exc:
        # See https://github.com/kubernetes-client/python/issues/1225
        raise RuntimeError(
            f"Failed to retrieve secrets from namespace '{namespace}'."
        ) from exc

    if len(matching_secrets) != 1:
        raise RuntimeError(
            f"Expected exactly one secret matching '{sub_string}' "
            f"in namespace '{namespace}', found {len(matching_secrets)}."
        )

    try:
        token = matching_secrets[0].instance.data.token
    except AttributeError as exc:
        raise RuntimeError(
            f"Secret '{matching_secrets[0].instance.metadata.name}' "
            "does not contain a service account token."
        ) from exc

    return base64.b64decode(token).decode()


def get_site_response(site_url: str, bearer_token: str) -> requests.Response:
    """
    Return the HTTP response from the site API.
    """
    headers = {"Authorization": f"Bearer {bearer_token}"}

    # Suppress only the warning about verify=False.
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    try:
        return requests.get(
            site_url,
            headers=headers,
            verify=False,
        )
    except RequestException:
        raise RuntimeError(f"Failed to connect to '{site_url}'.") from None


# Used in mcg, IE, QNA-chat-amd, zero-trust, omnicloud as a service, netapp-dr-starterkit
def modify_file_content(file_name, orig_content, new_content):

    with open(file_name, "r") as frb:
        logger.debug(f"Current content : {frb.readlines()}")

    with fileinput.FileInput(file_name, inplace=True, backup=".bak") as file:
        for line in file:
            print(
                line.replace(
                    orig_content,
                    new_content,
                ),
                end="",
            )

    with open(file_name, "r") as fra:
        contents = fra.readlines()
        logger.debug(f"Modified content : {contents}")

    return contents
