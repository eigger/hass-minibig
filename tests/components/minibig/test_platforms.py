"""Entity registry lookup shared by the real HA platform tests."""

from homeassistant.helpers import entity_registry as er

from .conftest import ADDRESS


def entity_id(hass, domain, key):
    return er.async_get(hass).async_get_entity_id(domain, "minibig", f"{ADDRESS}_{key}")
