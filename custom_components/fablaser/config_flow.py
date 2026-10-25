"""Assistant d'ajout de FabLaser : crée le webhook et affiche son adresse."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME, CONF_WEBHOOK_ID
from homeassistant.helpers.network import NoURLAvailableError, get_url

from .const import DOMAIN


class FabLaserConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ajout de l'appareil FabLaser."""

    VERSION = 1

    def __init__(self) -> None:
        self._name = "FabLaser"
        self._webhook_id = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._name = user_input[CONF_NAME]
            self._webhook_id = webhook.async_generate_id()
            await self.async_set_unique_id(self._webhook_id)
            return await self.async_step_url()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_NAME, default="FabLaser"): str}),
        )

    async def async_step_url(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=self._name, data={CONF_WEBHOOK_ID: self._webhook_id}
            )
        path = webhook.async_generate_path(self._webhook_id)
        try:
            url = get_url(self.hass, allow_external=False) + path
        except NoURLAvailableError:
            url = "http://ADRESSE-DE-HOME-ASSISTANT:8123" + path
        return self.async_show_form(
            step_id="url", description_placeholders={"url": url}
        )
