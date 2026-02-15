"""Base entity for Straeto route."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class SwiftlyIsStraetoBaseEntity(Entity):
    """Base entity for all Swiftly IS Straeto entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        route_id: str,
        route_name: str,
    ) -> None:
        """Initialize base entity."""
        self.route_id = route_id
        self.route_name = route_name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for the route."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.route_id)},
            name=self.route_name,
            manufacturer="Strætó Bs.",
            model="Rauntíma gögn frá Swiftly",
        )
