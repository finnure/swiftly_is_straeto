"""DataUpdateCoordinator for Swiftly integration."""

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import _LOGGER, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import SwiftlyAPIClient
from .const import DEFAULT_UPDATE_TIME, JSON_PREDICTIONS_DATA, JSON_VEHICLES
from .models import CoordinatorData, Prediction, Vehicle
from .utils import get_subentry_data

type SwiftlyIsStraetoConfigEntry = ConfigEntry[SwiftlyIsStraetoDataUpdateCoordinator]


class SwiftlyIsStraetoDataUpdateCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Class to manage fetching Swiftly IS Straeto data from API."""

    config_entry: SwiftlyIsStraetoConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SwiftlyIsStraetoConfigEntry,
        api_client: SwiftlyAPIClient,
    ) -> None:
        """Initialize Swiftly IS Straeto data updater."""
        self.api_client = api_client
        self.config_entry = config_entry
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="Swiftly IS Straeto Data Coordinator",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_TIME),
        )

    async def _get_stop_predictions(
        self, stops: dict[str, list[str]], route_subentry_mapping: dict[str, str]
    ) -> list[Prediction]:
        """Fetch predictions for monitored stops."""
        predictions: list[Prediction] = []
        for stop, routes in stops.items():
            prediction = await self.api_client.get_predictions(stop, routes)
            prediction_data = prediction.get(JSON_PREDICTIONS_DATA, [])
            for item in prediction_data:
                predictions.extend([Prediction(item, route_subentry_mapping)])
        return predictions

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch vehicle and prediction data for monitored routes and stops every DEFAULT_UPDATE_TIME seconds."""
        routes, stops, route_subentry_mapping = get_subentry_data(self.config_entry)

        vehicles = (
            await self.api_client.get_vehicles(route=routes, verbose=True)
            if routes
            else {}
        )
        predictions = (
            await self._get_stop_predictions(stops, route_subentry_mapping)
            if stops
            else []
        )

        return CoordinatorData(
            vehicles=[
                Vehicle(vehicle, route_subentry_mapping)
                for vehicle in vehicles.get(JSON_VEHICLES, [])
            ],
            predictions=predictions,
        )
