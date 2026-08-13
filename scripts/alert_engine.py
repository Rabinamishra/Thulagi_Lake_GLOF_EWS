from dataclasses import dataclass, field
from typing import List


# ============================================================
# INPUT DATA STRUCTURES
# ============================================================

@dataclass
class RainfallInput:
    daily_mm: float
    rainfall_3day_mm: float
    rainfall_7day_mm: float
    historical_7day_percentile: float


@dataclass
class LakeAreaInput:
    latest_area_km2: float
    previous_area_km2: float
    years_between_observations: float


@dataclass
class SimulatedWaterLevelInput:
    current_level_m: float
    change_10hr_m: float
    latest_rate_m_per_hr: float
    latest_acceleration_m_per_hr2: float
    trend: str


# ============================================================
# ALERT RESULT
# ============================================================

@dataclass
class AlertResult:
    level: str
    score: int
    max_score: int

    rainfall_score: int
    rainfall_status: str

    lake_growth_score: int
    lake_growth_status: str

    primary_drivers: List[str] = field(default_factory=list)


# ============================================================
# OPERATIONAL EXTENSION RESULT
# ============================================================

@dataclass
class OperationalExtensionResult:
    hypothetical_score: int
    hypothetical_max: int
    hypothetical_level: str

    water_level_score: int
    water_level_status: str


# ============================================================
# PROTOTYPE ALERT ENGINE
# ============================================================

def run_alert_engine(
    rainfall: RainfallInput,
    lake: LakeAreaInput,
    water: SimulatedWaterLevelInput,
) -> AlertResult:

    # --------------------------------------------------------
    # RAINFALL SCORE
    # --------------------------------------------------------
    #
    # Prototype rainfall logic:
    # >= 95th percentile = 2
    # >= 80th percentile = 1
    # otherwise = 0
    #
    # The rainfall score is based primarily on the historical
    # 7-day percentile.
    # --------------------------------------------------------

    percentile = rainfall.historical_7day_percentile

    if percentile >= 95:
        rainfall_score = 2
        rainfall_status = (
            f"HIGH - {percentile:.2f}th historical percentile "
            f"(7-day rainfall)"
        )

    elif percentile >= 80:
        rainfall_score = 1
        rainfall_status = (
            f"MODERATE - {percentile:.2f}th historical percentile "
            f"(7-day rainfall)"
        )

    else:
        rainfall_score = 0
        rainfall_status = (
            f"BASELINE - {percentile:.2f}th historical percentile "
            f"(7-day rainfall)"
        )


    # --------------------------------------------------------
    # LAKE AREA SCORE
    # --------------------------------------------------------
    #
    # Calculate percentage change between observations.
    #
    # The current prototype deliberately uses conservative
    # thresholds because satellite-derived lake-area changes
    # can also reflect acquisition date and extraction
    # uncertainty.
    # --------------------------------------------------------

    if lake.previous_area_km2 <= 0:
        raise ValueError(
            "Previous lake area must be greater than zero."
        )

    lake_change_percent = (
        (lake.latest_area_km2 - lake.previous_area_km2)
        / lake.previous_area_km2
    ) * 100


    if lake_change_percent >= 5:
        lake_growth_score = 2
        lake_growth_status = (
            f"HIGH GROWTH ({lake_change_percent:+.2f}%)"
        )

    elif lake_change_percent >= 2:
        lake_growth_score = 1
        lake_growth_status = (
            f"MODERATE GROWTH ({lake_change_percent:+.2f}%)"
        )

    else:
        lake_growth_score = 0

        if lake_change_percent > 0:
            lake_growth_status = (
                f"LOW/NO SIGNIFICANT GROWTH "
                f"({lake_change_percent:+.2f}%)"
            )
        else:
            lake_growth_status = (
                f"NO GROWTH ({lake_change_percent:+.2f}%)"
            )


    # --------------------------------------------------------
    # TOTAL PROTOTYPE SCORE
    # --------------------------------------------------------

    score = rainfall_score + lake_growth_score
    max_score = 4


    # --------------------------------------------------------
    # ALERT LEVEL
    # --------------------------------------------------------
    #
    # 0-1 = NORMAL
    # 2-3 = WATCH
    # 4   = ALERT
    # --------------------------------------------------------

    if score >= 4:
        level = "ALERT"

    elif score >= 2:
        level = "WATCH"

    else:
        level = "NORMAL"


    # --------------------------------------------------------
    # PRIMARY DRIVERS
    # --------------------------------------------------------

    drivers = []


    if rainfall_score > 0:
        drivers.append(
            f"Rainfall: {rainfall_status}"
        )


    if lake_growth_score > 0:
        drivers.append(
            f"Lake area: {lake_growth_status}"
        )


    # --------------------------------------------------------
    # If there are no elevated indicators
    # --------------------------------------------------------

    if not drivers:
        drivers.append(
            "No individual indicator elevated above baseline."
        )


    return AlertResult(
        level=level,
        score=score,
        max_score=max_score,

        rainfall_score=rainfall_score,
        rainfall_status=rainfall_status,

        lake_growth_score=lake_growth_score,
        lake_growth_status=lake_growth_status,

        primary_drivers=drivers,
    )


# ============================================================
# OPERATIONAL EXTENSION DEMO
# ============================================================
#
# IMPORTANT:
# Water level does NOT contribute to the main prototype
# alert score.
#
# This function demonstrates separately how telemetry could
# eventually be incorporated after proper calibration.
# ============================================================

def demo_operational_extension(
    result: AlertResult,
    water: SimulatedWaterLevelInput,
) -> OperationalExtensionResult:

    # --------------------------------------------------------
    # Water-level contribution
    # --------------------------------------------------------

    rate = water.latest_rate_m_per_hr

    if rate >= 0.15:
        water_level_score = 2
        water_level_status = (
            f"Rapid rise (+{rate:.3f} m/hr)"
        )

    elif rate >= 0.05:
        water_level_score = 1
        water_level_status = (
            f"Elevated rise (+{rate:.3f} m/hr)"
        )

    else:
        water_level_score = 0

        if rate > 0:
            water_level_status = (
                f"Low rise (+{rate:.3f} m/hr)"
            )
        elif rate < 0:
            water_level_status = (
                f"Falling ({rate:.3f} m/hr)"
            )
        else:
            water_level_status = "Stable"


    # --------------------------------------------------------
    # Hypothetical combined score
    # --------------------------------------------------------

    hypothetical_score = (
        result.score + water_level_score
    )

    hypothetical_max = 6


    if hypothetical_score >= 5:
        hypothetical_level = "ALERT"

    elif hypothetical_score >= 3:
        hypothetical_level = "WATCH"

    else:
        hypothetical_level = "NORMAL"


    return OperationalExtensionResult(
        hypothetical_score=hypothetical_score,
        hypothetical_max=hypothetical_max,
        hypothetical_level=hypothetical_level,

        water_level_score=water_level_score,
        water_level_status=water_level_status,
    )