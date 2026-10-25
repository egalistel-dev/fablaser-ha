"""Capteurs binaires FabLaser."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FabLaserData
from .const import DOMAIN, STATE_PAUSED, STATE_RUNNING
from .entity import FabLaserEntity


@dataclass(frozen=True, kw_only=True)
class FabLaserBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[FabLaserData], bool]


BINARY_SENSORS: tuple[FabLaserBinaryDescription, ...] = (
    FabLaserBinaryDescription(
        key="running",
        translation_key="running",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.state in (STATE_RUNNING, STATE_PAUSED),
    ),
    FabLaserBinaryDescription(
        key="connected",
        translation_key="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda d: d.connected,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data: FabLaserData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(FabLaserBinary(entry, data, desc) for desc in BINARY_SENSORS)


class FabLaserBinary(FabLaserEntity, BinarySensorEntity):
    """Un capteur binaire FabLaser."""

    entity_description: FabLaserBinaryDescription

    def __init__(
        self, entry: ConfigEntry, data: FabLaserData, description: FabLaserBinaryDescription
    ) -> None:
        super().__init__(entry, data, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self._data)
