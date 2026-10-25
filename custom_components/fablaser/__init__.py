"""Intégration FabLaser : reçoit l'état du logiciel de gravure par un webhook Home Assistant."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aiohttp import web

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    EVENT_JOB_FINISHED,
    EVENT_JOB_STARTED,
    FINISHED_STATES,
    MAX_IMAGE_BYTES,
    SIGNAL_IMAGE,
    SIGNAL_UPDATE,
    STATE_OFFLINE,
    STATE_RUNNING,
    STATES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "camera"]


@dataclass
class FabLaserData:
    """Dernier état connu de FabLaser."""

    state: str = STATE_OFFLINE
    progress: float | None = None
    remaining_min: float | None = None
    duration_min: float | None = None
    file: str = ""
    error: str = ""
    version: str = ""
    machine: str = ""
    connected: bool = False
    image: bytes | None = None
    image_time: datetime | None = None

    def update(self, payload: dict[str, Any]) -> None:
        """Applique un message reçu ; les champs absents ne changent pas."""
        state = payload.get("state")
        if isinstance(state, str) and state in STATES:
            self.state = state
        if "progress" in payload:
            self.progress = _number(payload["progress"])
        if "remaining_min" in payload:
            self.remaining_min = _number(payload["remaining_min"])
        if "duration_min" in payload:
            self.duration_min = _number(payload["duration_min"])
        if "file" in payload:
            self.file = str(payload["file"] or "")
        if "error" in payload:
            self.error = str(payload["error"] or "")
        if "version" in payload:
            self.version = str(payload["version"] or "")
        if "machine" in payload:
            self.machine = str(payload["machine"] or "")
        if "connected" in payload:
            self.connected = bool(payload["connected"])
        if self.state == STATE_OFFLINE:
            self.connected = False
            self.remaining_min = None


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Crée l'appareil FabLaser et enregistre son webhook."""
    data = FabLaserData()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = data

    async def _handle(
        hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        if request.content_type == "image/jpeg":
            # Image de la caméra du plateau : le corps est le JPEG brut
            image = await request.read()
            if len(image) > MAX_IMAGE_BYTES or image[:2] != b"\xff\xd8":
                return web.Response(status=400, text="JPEG de 2 Mo au plus attendu")
            data.image = image
            data.image_time = dt_util.utcnow()
            async_dispatcher_send(hass, SIGNAL_IMAGE.format(entry.entry_id))
            return web.Response(status=200, text="ok")
        try:
            payload = await request.json()
        except ValueError:
            return web.Response(status=400, text="JSON attendu")
        if not isinstance(payload, dict):
            return web.Response(status=400, text="objet JSON attendu")

        previous = data.state
        data.update(payload)
        if data.state != previous:
            fields = {
                "entry_id": entry.entry_id,
                "name": entry.title,
                "file": data.file,
                "progress": data.progress,
                "duration_min": data.duration_min,
                "error": data.error,
                "machine": data.machine,
            }
            if data.state == STATE_RUNNING and previous != STATE_RUNNING:
                hass.bus.async_fire(EVENT_JOB_STARTED, fields)
            elif data.state in FINISHED_STATES and previous in (
                STATE_RUNNING,
                "pause",
            ):
                hass.bus.async_fire(EVENT_JOB_FINISHED, {**fields, "result": data.state})
        async_dispatcher_send(hass, SIGNAL_UPDATE.format(entry.entry_id))
        # La caméra est éteinte ou FabLaser s'est fermé : on n'affiche plus une image périmée
        if (payload.get("camera") is False or data.state == STATE_OFFLINE) and data.image is not None:
            data.image = None
            data.image_time = None
            async_dispatcher_send(hass, SIGNAL_IMAGE.format(entry.entry_id))
        return web.Response(status=200, text="ok")

    webhook.async_register(
        hass,
        DOMAIN,
        entry.title,
        entry.data[CONF_WEBHOOK_ID],
        _handle,
        allowed_methods=["POST"],
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Retire le webhook et les entités."""
    webhook.async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
