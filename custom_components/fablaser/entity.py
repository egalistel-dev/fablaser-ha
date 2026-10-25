"""Entité de base FabLaser."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity

from . import FabLaserData
from .const import DOMAIN, SIGNAL_UPDATE


class FabLaserEntity(RestoreEntity):
    """Entité alimentée par les messages du webhook, qui garde sa valeur après un redémarrage."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, data: FabLaserData, key: str) -> None:
        self._entry = entry
        self._data = data
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Egamaker",
            model="FabLaser",
            sw_version=data.version or None,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None:
            self._restore(last)
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE.format(self._entry.entry_id), self.async_write_ha_state
            )
        )

    def _restore(self, last) -> None:
        """Reprend la dernière valeur connue (à surcharger)."""
