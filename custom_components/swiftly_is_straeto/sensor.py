"""Swiftly IS Straeto vehicle sensors."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import JSON_PREDICTIONS, JSON_VEHICLES
from .coordinator import (
    SwiftlyIsStraetoConfigEntry,
    SwiftlyIsStraetoDataUpdateCoordinator,
)
from .entity import SwiftlyIsStraetoBaseEntity
from .models import Prediction, Vehicle


@dataclass(frozen=True, kw_only=True)
class VehicleSensorEntityDescription(SensorEntityDescription):
    """Describes Vehicle sensor entity."""

    value_fn: Callable[[Vehicle], datetime | StateType]


VEHICLE_SENSORS: tuple[VehicleSensorEntityDescription, ...] = (
    VehicleSensorEntityDescription(
        key="schedule_adherence_seconds",
        translation_key="schedule_adherence_seconds",
        name="Frávik",
        icon="mdi:clock-time-three-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda vehicle: vehicle.schedule_adherence,
        suggested_display_precision=0,
    ),
    VehicleSensorEntityDescription(
        key="next_stop_name",
        translation_key="next_stop_name",
        name="Næsta stopp",
        icon="mdi:bus-stop-uncovered",
        value_fn=lambda vehicle: vehicle.next_stop_name,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwiftlyIsStraetoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up available vehicle and prediction sensors."""
    coordinator = entry.runtime_data
    vehicles = coordinator.data.get(JSON_VEHICLES, [])
    predictions = coordinator.data.get(JSON_PREDICTIONS, [])

    subentry_map: dict[str, list[SensorEntity]] = {}

    for vehicle in vehicles:
        subentry_map.setdefault(vehicle.subentry_id, []).extend(
            SwiftlyIsStraetoVehicleSensor(coordinator, description, vehicle)
            for description in VEHICLE_SENSORS
        )

    for prediction in predictions:
        subentry_map.setdefault(prediction.subentry_id, []).append(
            SwiftlyIsStraetoPredictionSensor(coordinator, prediction)
        )

    # Add all entities to Home Assistant, attaching them to the correct subentry
    for subentry_id, entities in subentry_map.items():
        async_add_entities(entities, config_subentry_id=subentry_id)

    def _update_entities() -> None:
        """Add new vehicle and prediction sensors when new data appears."""
        vehicles = coordinator.data.get(JSON_VEHICLES, [])
        predictions = coordinator.data.get(JSON_PREDICTIONS, [])
        known_ids = {
            e.unique_id for entity_list in subentry_map.values() for e in entity_list
        }
        for vehicle in vehicles:
            if vehicle.get_unique_id("schedule_adherence_seconds") not in known_ids:
                sensors = [
                    SwiftlyIsStraetoVehicleSensor(coordinator, description, vehicle)
                    for description in VEHICLE_SENSORS
                ]
                subentry_map.setdefault(vehicle.subentry_id, []).extend(sensors)
                async_add_entities(sensors, config_subentry_id=vehicle.subentry_id)
        for prediction in predictions:
            if prediction.unique_id not in known_ids:
                sensor = SwiftlyIsStraetoPredictionSensor(coordinator, prediction)
                subentry_map.setdefault(prediction.subentry_id, []).append(sensor)
                async_add_entities(
                    [sensor],
                    config_subentry_id=prediction.subentry_id,
                )

    entry.async_on_unload(coordinator.async_add_listener(_update_entities))


class SwiftlyIsStraetoVehicleSensor(
    CoordinatorEntity[SwiftlyIsStraetoDataUpdateCoordinator],
    SwiftlyIsStraetoBaseEntity,
    SensorEntity,
):
    """Sensor for a Swiftly IS Straeto vehicle on a route."""

    entity_description: VehicleSensorEntityDescription

    def __init__(
        self,
        coordinator: SwiftlyIsStraetoDataUpdateCoordinator,
        description: VehicleSensorEntityDescription,
        vehicle: Vehicle,
    ) -> None:
        """Initialize the Swiftly IS Straeto vehicle sensor."""
        super().__init__(coordinator)
        SwiftlyIsStraetoBaseEntity.__init__(
            self,
            vehicle.route_id,
            vehicle.route_name,
        )
        self.block_id = vehicle.block_id
        self.entity_description = description
        self._attr_unique_id = vehicle.get_unique_id(description.key)
        self._attr_name = f"{vehicle.block_id} {description.name}"

    @property
    def vehicle(self) -> Vehicle | None:
        """Return the vehicle data for this sensor."""
        for v in self.coordinator.data.get(JSON_VEHICLES, []):
            if v.block_id == self.block_id:
                return v
        return None

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        return bool(self.vehicle)

    @property
    def native_value(self) -> datetime | StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.vehicle) if self.vehicle else None

    @property
    def extra_state_attributes(self) -> dict[str, str | int]:
        """Return the state attributes of the sensor."""
        return self.vehicle.extra_state_attributes if self.vehicle else {}


class SwiftlyIsStraetoPredictionSensor(
    CoordinatorEntity[SwiftlyIsStraetoDataUpdateCoordinator],
    SwiftlyIsStraetoBaseEntity,
    SensorEntity,
):
    """Sensor for a Swiftly IS Straeto prediction for a stop on a route."""

    def __init__(
        self,
        coordinator: SwiftlyIsStraetoDataUpdateCoordinator,
        data: Prediction,
    ) -> None:
        """Initialize the Swiftly IS Straeto prediction sensor."""
        super().__init__(coordinator)
        SwiftlyIsStraetoBaseEntity.__init__(
            self,
            data.route_id,
            data.route_name,
        )
        self.stop_id = data.stop_id
        self.route_id = data.route_id
        self._attr_name = f"{data.stop_name} -> {data.headsign}"
        self._attr_unique_id = data.unique_id
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_translation_key = "predicted_arrival_time"

    @property
    def prediction(self) -> Prediction | None:
        """Return the prediction data for this sensor."""
        for p in self.coordinator.data.get(JSON_PREDICTIONS, []):
            if p.stop_id == self.stop_id and p.route_id == self.route_id:
                return p
        return None

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        return bool(self.prediction)

    @property
    def native_value(self) -> datetime | StateType:
        """Return the state of the sensor."""
        return self.prediction.arrival_time if self.prediction else None

    @property
    def extra_state_attributes(self) -> dict[str, str | int]:
        """Return the state attributes of the sensor."""
        return self.prediction.extra_state_attributes if self.prediction else {}
