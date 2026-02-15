"""Config flow for the Swiftly IS Straeto integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_API_KEY, CONF_DEVICE, CONF_URL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import InvalidRequestError, SwiftlyAPIClient, UnauthorizedError
from .const import (
    CONF_ROUTE,
    CONF_ROUTE_NAME,
    CONF_ROUTES,
    CONF_STOPS,
    CONF_USER,
    DOMAIN,
    JSON_AGENCY_KEY,
    JSON_DIRECTIONS,
    JSON_ID,
    JSON_NAME,
    JSON_TITLE,
)
from .models import ConfigFlowData, Route, RouteStop, StraetoSubentryData

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): str})


def _filter_routes(hass: HomeAssistant, routes: list[Route]) -> list[Route]:
    """Filter routes that are already configured."""
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    existing_route_ids = {
        subentry.data.get(CONF_ROUTE) for subentry in entry.subentries.values()
    }
    return [route for route in routes if route[JSON_ID] not in existing_route_ids]


def _get_client(hass: HomeAssistant, api_key: str) -> SwiftlyAPIClient:
    """Create and return a SwiftlyAPIClient."""
    session = async_get_clientsession(hass)
    return SwiftlyAPIClient(api_key, session)


async def _validate_input(hass: HomeAssistant, data: dict[str, str]) -> ConfigFlowData:
    """Validate the user input allows us to connect."""

    client = _get_client(hass, data[CONF_API_KEY])
    info = await client.get_agency_info()
    return ConfigFlowData(
        title=info.get(JSON_NAME, "Swiftly IS Straeto"),
        id=info.get(JSON_AGENCY_KEY),
        url=info.get(CONF_URL),
        api_key=data[CONF_API_KEY],
        routes=await client.get_routes(),
    )


async def _get_routes(client: SwiftlyAPIClient) -> list[Route]:
    """Get available routes."""
    route_data = await client.get_routes()
    return route_data.get(CONF_ROUTES, [])


async def _get_route_stops(
    client: SwiftlyAPIClient, route_id: str
) -> tuple[str, list[RouteStop]]:
    """Get stops for a given route."""
    route_data = await client.get_routes([route_id], verbose=True)
    return (
        route_data.get(CONF_ROUTES, [])[0].get(JSON_NAME),
        [
            RouteStop(
                route_id,
                direction[JSON_ID],
                direction[JSON_TITLE],
                stop,
            )
            for route in route_data.get(CONF_ROUTES, [])
            for direction in route.get(JSON_DIRECTIONS, [])
            for stop in direction.get(CONF_STOPS, [])
        ],
    )


class SwiftlyIsStraetoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Swiftly IS Straeto."""

    VERSION = 1

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry):
        """Return subentries supported by this integration."""
        return {CONF_DEVICE: SwiftlyIsStraetoSubentryFlowHandler}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for API key and validate."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                data = await _validate_input(self.hass, user_input)
            except InvalidRequestError as err:
                _LOGGER.error("Invalid request: %s", err)
                errors["base"] = "cannot_connect"
            except UnauthorizedError as err:
                _LOGGER.error("Unauthorized: %s", err)
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            if not errors:
                unique_id = data.get(JSON_ID)
                await self.async_set_unique_id(str(unique_id))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=data.get(JSON_TITLE), data=data)

        return self.async_show_form(
            step_id=CONF_USER, data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class SwiftlyIsStraetoSubentryFlowHandler(ConfigSubentryFlow):
    """Handle a subentry flow for Swiftly IS Straeto."""

    _subentry_data: StraetoSubentryData
    _client: SwiftlyAPIClient

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Step 1: Select a route from available routes."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._subentry_data = StraetoSubentryData(route=user_input[CONF_ROUTE])
            return await self.async_step_stops()

        parent_entry = self._get_entry()
        self._client = _get_client(self.hass, parent_entry.data[CONF_API_KEY])
        routes = await _get_routes(self._client)
        routes = _filter_routes(self.hass, routes)
        data_schema = vol.Schema(
            {
                vol.Required(CONF_ROUTE): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(
                                value=route[JSON_ID], label=route[JSON_NAME]
                            )
                            for route in routes
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id=CONF_USER, data_schema=data_schema, errors=errors, last_step=False
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle reconfiguration of a subentry."""
        reconfigure_subentry = self._get_reconfigure_subentry()
        self._subentry_data = StraetoSubentryData(
            route=reconfigure_subentry.data.get(CONF_ROUTE),
            route_name=reconfigure_subentry.data.get(CONF_ROUTE_NAME),
            stops=reconfigure_subentry.data.get(CONF_STOPS, []),
        )
        return await self.async_step_stops()

    async def async_step_stops(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Step 2: Optionally select stops from the chosen route."""

        errors: dict[str, str] = {}
        route = self._subentry_data[CONF_ROUTE]
        if user_input is not None:
            self._subentry_data[CONF_STOPS] = user_input.get(CONF_STOPS, [])
            if self.source == SOURCE_RECONFIGURE:
                return await self.async_step_save_changes()
            return self.async_create_entry(
                title=f"{self._subentry_data[CONF_ROUTE_NAME]}",
                data=self._subentry_data,
            )

        parent_entry = self._get_entry()
        self._client = _get_client(self.hass, parent_entry.data[CONF_API_KEY])
        (route_name, route_stops) = await _get_route_stops(self._client, route)
        self._subentry_data[CONF_ROUTE_NAME] = route_name
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_STOPS, default=self._subentry_data.get(CONF_STOPS, [])
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=stop.stop_id, label=str(stop))
                            for stop in route_stops
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                        multiple=True,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id=CONF_STOPS, data_schema=data_schema, errors=errors, last_step=True
        )

    async def async_step_save_changes(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle saving changes to a subentry."""
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        return self.async_update_and_abort(
            entry,
            subentry,
            title=f"{self._subentry_data[CONF_ROUTE_NAME]}",
            data=self._subentry_data,
        )
