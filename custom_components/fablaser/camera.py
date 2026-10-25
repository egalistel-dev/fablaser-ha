"""Caméra du plateau FabLaser : la dernière image envoyée par le logiciel."""
from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FabLaserData
from .const import DOMAIN, SIGNAL_IMAGE


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data: FabLaserData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FabLaserCamera(entry, data)])


class FabLaserCamera(Camera):
    """Image de la caméra du plateau. Indisponible tant que FabLaser n'en envoie pas."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "camera"

    def __init__(self, entry: ConfigEntry, data: FabLaserData) -> None:
        super().__init__()
        self._entry = entry
        self._data = data
        self._attr_unique_id = f"{entry.entry_id}_camera"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Egamaker",
            model="FabLaser",
            sw_version=data.version or None,
        )

    @property
    def available(self) -> bool:
        return self._data.image is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        when = self._data.image_time
        return {"image_time": when.isoformat() if when else None}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_IMAGE.format(self._entry.entry_id), self._image_updated
            )
        )

    @callback
    def _image_updated(self) -> None:
        self.async_write_ha_state()

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        return self._data.image
