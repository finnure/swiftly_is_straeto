"""Device tracker platform for swiftly_is_straeto."""

from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_DIRECTION, JSON_VEHICLES
from .coordinator import (
    SwiftlyIsStraetoConfigEntry,
    SwiftlyIsStraetoDataUpdateCoordinator,
)
from .entity import SwiftlyIsStraetoBaseEntity
from .models import Vehicle


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SwiftlyIsStraetoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the swiftly_is_straeto device tracker."""

    coordinator = config_entry.runtime_data
    vehicles = coordinator.data.get("vehicles", [])

    subentry_map: dict[str, list[SensorEntity]] = {}
    for vehicle in vehicles:
        subentry_map.setdefault(vehicle.subentry_id, []).append(
            SwiftlyIsStraetoDeviceTracker(coordinator, vehicle)
        )
    for subentry_id, entities in subentry_map.items():
        async_add_entities(entities, config_subentry_id=subentry_id)

    def _update_entities() -> None:
        """Add new device trackers when new vehicles appear."""
        vehicles = coordinator.data.get("vehicles", [])
        known_ids = {
            e.unique_id for entity_list in subentry_map.values() for e in entity_list
        }
        for vehicle in vehicles:
            if vehicle.get_unique_id("tracker") not in known_ids:
                tracker = SwiftlyIsStraetoDeviceTracker(coordinator, vehicle)
                subentry_map.setdefault(vehicle.subentry_id, []).append(tracker)
                async_add_entities([tracker], config_subentry_id=vehicle.subentry_id)

    config_entry.async_on_unload(coordinator.async_add_listener(_update_entities))


class SwiftlyIsStraetoDeviceTracker(
    CoordinatorEntity[SwiftlyIsStraetoDataUpdateCoordinator],
    SwiftlyIsStraetoBaseEntity,
    TrackerEntity,
):
    """Device tracker entity for swiftly_is_straeto vehicles."""

    _attr_force_update = False
    _attr_translation_key = "vehicle"
    _attr_name = None
    _attr_icon = "mdi:bus-side"

    def __init__(
        self,
        coordinator: SwiftlyIsStraetoDataUpdateCoordinator,
        vehicle: Vehicle,
    ) -> None:
        """Initialize the Tracker."""
        super().__init__(coordinator)
        SwiftlyIsStraetoBaseEntity.__init__(
            self,
            vehicle.route_id,
            vehicle.route_name,
        )
        self._attr_unique_id = vehicle.get_unique_id("tracker")
        self.block_id = vehicle.block_id
        self._attr_name = f"{vehicle.block_id}"

    @property
    def vehicle(self) -> Vehicle | None:
        """Return the vehicle data for this sensor."""
        for v in self.coordinator.data.get(JSON_VEHICLES, []):
            if v.block_id == self.block_id:
                return v
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | float | None]:
        """Return the state attributes."""
        return {
            ATTR_DIRECTION: self.vehicle.location["heading"]
            if self.vehicle and self.vehicle.location
            else None
        }

    @property
    def latitude(self) -> float | None:
        """Return the latitude of the vehicle."""
        return (
            self.vehicle.location["lat"]
            if self.vehicle and self.vehicle.location
            else None
        )

    @property
    def longitude(self) -> float | None:
        """Return the longitude of the vehicle."""
        return (
            self.vehicle.location["lon"]
            if self.vehicle and self.vehicle.location
            else None
        )
