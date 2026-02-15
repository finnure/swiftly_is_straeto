"""The Swiftly IS Straeto integration."""

from __future__ import annotations

from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SwiftlyAPIClient
from .coordinator import (
    SwiftlyIsStraetoConfigEntry,
    SwiftlyIsStraetoDataUpdateCoordinator,
)

_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.DEVICE_TRACKER]


async def async_setup_entry(
    hass: HomeAssistant, entry: SwiftlyIsStraetoConfigEntry
) -> bool:
    """Set up Swiftly IS Straeto from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    session = async_get_clientsession(hass)
    api_client = SwiftlyAPIClient(api_key, session)
    coordinator = SwiftlyIsStraetoDataUpdateCoordinator(hass, entry, api_client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: SwiftlyIsStraetoConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
