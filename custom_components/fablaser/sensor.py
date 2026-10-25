"""Capteurs FabLaser."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FabLaserData
from .const import DOMAIN, STATE_OFFLINE, STATES
from .entity import FabLaserEntity


@dataclass(frozen=True, kw_only=True)
class FabLaserSensorDescription(SensorEntityDescription):
    """Description d'un capteur : où lire la valeur, comment la relire après un redémarrage."""

    value_fn: Callable[[FabLaserData], Any]
    restore_attr: str


SENSORS: tuple[FabLaserSensorDescription, ...] = (
    FabLaserSensorDescription(
        key="state",
        translation_key="state",
        device_class=SensorDeviceClass.ENUM,
        options=STATES,
        value_fn=lambda d: d.state,
        restore_attr="state",
    ),
    FabLaserSensorDescription(
        key="progress",
        translation_key="progress",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda d: d.progress,
        restore_attr="progress",
    ),
    FabLaserSensorDescription(
        key="remaining",
        translation_key="remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        value_fn=lambda d: d.remaining_min,
        restore_attr="remaining_min",
    ),
    FabLaserSensorDescription(
        key="duration",
        translation_key="duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        value_fn=lambda d: d.duration_min,
        restore_attr="duration_min",
    ),
    FabLaserSensorDescription(
        key="file",
        translation_key="file",
        value_fn=lambda d: d.file or None,
        restore_attr="file",
    ),
    FabLaserSensorDescription(
        key="error",
        translation_key="error",
        value_fn=lambda d: d.error or None,
        restore_attr="error",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data: FabLaserData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(FabLaserSensor(entry, data, desc) for desc in SENSORS)


class FabLaserSensor(FabLaserEntity, SensorEntity):
    """Un capteur FabLaser."""

    entity_description: FabLaserSensorDescription

    def __init__(
        self, entry: ConfigEntry, data: FabLaserData, description: FabLaserSensorDescription
    ) -> None:
        super().__init__(entry, data, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._data)

    def _restore(self, last) -> None:
        value = last.state
        if value in (None, "unknown", "unavailable", ""):
            return
        attr = self.entity_description.restore_attr
        if attr == "state":
            # après un redémarrage de Home Assistant, on ne sait pas si FabLaser tourne encore
            self._data.state = value if value in STATES else STATE_OFFLINE
        elif attr in ("progress", "remaining_min", "duration_min"):
            try:
                setattr(self._data, attr, float(value))
            except ValueError:
                pass
        else:
            setattr(self._data, attr, str(value))
