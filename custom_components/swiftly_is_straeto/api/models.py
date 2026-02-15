"""Data models for Swiftly API."""

from typing import TypedDict


class JSONLocation(TypedDict):
    """Data model for JSONVehicle location."""

    lat: float
    lon: float
    time: int
    speed: float
    heading: float


class JSONVehicle(TypedDict):
    """Data model for JSONVehicleDetailData vehicles."""

    id: str
    routeId: str
    routeShortName: str
    routeName: str
    headsign: str
    vehicleType: str
    loc: JSONLocation
    schAdhSecs: float
    schAdhStr: str
    headwaySecs: float
    scheduledHeadwaySecs: float
    previousVehicleId: str
    previousVehicleSchAdhSecs: float
    previousVehicleSchAdhStr: str
    oaOptimalDepartureTimeEpochMsecs: int | None
    oaOptimalDepartureTimeStr: str | None
    layoverDepTime: int | None
    layoverDepTimeStr: str | None
    serviceDate: str
    blockAssignmentInfo: str
    isPredictable: bool
    tripShortName: str
    tripPattern: str
    layover: bool
    isAtStop: bool
    isAtWaitStop: bool
    nextStopPathIndex: int
    nextStopId: str
    nextStopName: str
    stopScheduleTimeEpochMsecs: int | None
    stopScheduleTimeStr: str | None
    distanceAlongStopPath: float
    stopPathIndex: int
    gtfsStopSequence: int
    serviceId: str
    isAddedService: bool
    isOnDetour: bool
    inYard: bool
    directionId: str
    tripId: str
    blockId: str


class JSONVehicleDetailData(TypedDict):
    """Data model for JSONVehicleDetailResponse data."""

    vehicles: list[JSONVehicle]
    agencyKey: str


class JSONVehicleDetailResponse(TypedDict):
    """Data model for get_vehicles response."""

    data: JSONVehicleDetailData
    route: str
    success: bool


class JSONStop(TypedDict):
    """Data model for JSONDirection stops."""

    id: str
    name: str
    lat: float
    lon: float
    code: int


class JSONDirection(TypedDict):
    """Data model for JSONRoute directions."""

    id: str
    title: str
    headsigns: list[str]
    stops: list[JSONStop]


class JSONShapeLocs(TypedDict):
    """Data model for JSONShape locations."""

    lat: float
    lon: float


class JSONShape(TypedDict):
    """Data model for JSONRoute shapes."""

    tripPatternId: str
    shapeId: str
    directionId: str
    headsign: str
    locs: list[JSONShapeLocs]


class JSONExtent(TypedDict):
    """Data model for JSONRoute extent."""

    minLat: float
    minLon: float
    maxLat: float
    maxLon: float


class JSONRoute(TypedDict):
    """Data model for JSONRouteData routes."""

    id: str
    name: str
    shortName: str
    longName: str
    color: str
    type: str
    directions: list[JSONDirection] | None
    shapes: list[JSONShape] | None
    extent: JSONExtent | None


class JSONRouteData(TypedDict):
    """Data model for JSONRouteResponse data."""

    routes: list[JSONRoute]
    agencyKey: str


class JSONRouteResponse(TypedDict):
    """Data model for get_routes response."""

    data: JSONRouteData
    success: bool
    route: str


class JSONPrediction(TypedDict):
    """Data model for JSONPredictionDestination predictions."""

    time: int
    sec: int
    min: int
    departure: bool
    blockId: str
    vehicleId: str
    tripId: str


class JSONPredictionDestination(TypedDict):
    """Data model for JSONPredictionData destinations."""

    directionId: str
    headsign: str
    predictions: list[JSONPrediction]


class JSONPredictionData(TypedDict):
    """Data model for JSONPredictionResponseData predictionsData."""

    routeShortName: str
    routeName: str
    routeId: str
    stopId: str
    stopName: str
    stopCode: int
    destinations: list[JSONPredictionDestination]


class JSONPredictionResponseData(TypedDict):
    """Data model for JSONPredictionResponse data."""

    agencyKey: str
    predictionsData: list[JSONPredictionData]


class JSONPredictionResponse(TypedDict):
    """Data model for get_predictions response."""

    data: JSONPredictionResponseData
    success: bool
    route: str


class JSONInfoData(TypedDict):
    """Data model for JSONInfoResponse data."""

    agencyKey: str
    name: str
    url: str
    timezone: str
    extent: JSONExtent


class JSONInfoResponse(TypedDict):
    """Data model for get_agency_info response."""

    data: JSONInfoData
    success: bool
    route: str
