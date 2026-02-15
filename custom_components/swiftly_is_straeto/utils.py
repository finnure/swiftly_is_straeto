"""Utility functions for Swiftly IS Straeto integration."""

from homeassistant.config_entries import ConfigEntry

from .const import CONF_ROUTE, CONF_STOPS


def get_subentry_data(
    entry: ConfigEntry,
) -> tuple[list[str], dict[str, list[str]]]:
    """Get subentry data from a config entry."""
    subentries = entry.subentries
    routeSubentryMapping: dict[str, str] = {}
    routes: list[str] = []
    stops: dict[str, list[str]] = {}
    if subentries:
        for subentry_id, subentry in subentries.items():
            route = subentry.data.get(CONF_ROUTE)
            routeSubentryMapping[route] = subentry_id
            if route and route not in routes:
                routes.append(route)
            for stop in subentry.data.get(CONF_STOPS, []):
                if stop not in stops:
                    stops[stop] = [route]
                else:
                    stops[stop].append(route)
    return routes, stops, routeSubentryMapping
