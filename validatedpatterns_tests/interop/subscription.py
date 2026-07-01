import logging


from ocp_resources.subscription import Subscription
from openshift.dynamic.exceptions import NotFoundError
from openshift.dynamic import DynamicClient

from . import __loggername__

logger = logging.getLogger(__loggername__)


def assert_subscription_status(
    openshift_dyn_client: DynamicClient, expected_subs: dict[str, list[str]]
):
    """
    Assert if the expected subs are present in the given namespaces of the cluster, reached with dynamic client

    :param openshift_dyn_client: The openshift DynamicClient to connect to the cluster
    :param expected_subs: A dict of the expected subscriptions with the list of namespaces to expect them in
    """
    missing_subs = []
    unhealthy_subs = []
    missing_installplans = []
    upgrades_pending = []

    for subscription in expected_subs.keys():
        for namespace in expected_subs[subscription]:
            try:
                subs = Subscription.get(
                    dyn_client=openshift_dyn_client,
                    name=subscription,
                    namespace=namespace,
                )
                sub = next(subs)
            except NotFoundError:
                missing_subs.append(f"{subscription} in {namespace} namespace")
                continue

            if sub.instance.status.state == "UpgradePending":
                upgrades_pending.append(
                    f"{sub.instance.metadata.name} in {sub.instance.metadata.namespace} namespace"
                )

            if sub.instance.status.conditions[0].status != "False":
                unhealthy_subs.append(
                    f"{sub.instance.metadata.name} in {sub.instance.metadata.namespace} namespace"
                )

            if not sub.instance.status.installPlanRef:
                missing_installplans.append(
                    f"{sub.instance.metadata.name} in {sub.instance.metadata.namespace} namespace"
                )

    if upgrades_pending:
        logger.warning(
            f"WARNING: The following subscriptions are in UpgradePending state: {upgrades_pending}"
        )

    errors = []

    if missing_subs:
        errors.append(f"Missing subscriptions: {', '.join(missing_subs)}")

    if unhealthy_subs:
        errors.append(f"Unhealthy subscriptions: {', '.join(unhealthy_subs)}")

    if missing_installplans:
        errors.append(f"Missing install plans: {', '.join(missing_installplans)}")

    assert not errors, (
        "Subscription status check failed:\n"
        + "\n".join(errors)
    )