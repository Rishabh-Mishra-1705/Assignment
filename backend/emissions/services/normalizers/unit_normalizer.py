"""
Unit Normalizer
===============
Converts all incoming quantity units to canonical internal units:

  Fuel / liquid  →  liters (L)
  Electricity    →  kilowatt-hours (kWh)
  Mass           →  kilograms (kg)
  Distance       →  kilometers (km)

We centralize this so parsers never duplicate conversion logic.
Each entry in CONVERSION_FACTORS maps:
    source_unit → (canonical_unit, multiplier)
"""

CONVERSION_FACTORS = {
    # ── Fuel / Liquid ──────────────────────────────────────────────────────────
    'L':      ('L', 1.0),
    'LITER':  ('L', 1.0),
    'LITERS': ('L', 1.0),
    'LITRE':  ('L', 1.0),
    'LITRES': ('L', 1.0),
    'GAL':    ('L', 3.78541),    # US gallon
    'GALLON': ('L', 3.78541),
    'GALLONS':('L', 3.78541),
    'UKGAL':  ('L', 4.54609),    # Imperial gallon
    'M3':     ('L', 1000.0),     # Cubic meters → liters
    'CBM':    ('L', 1000.0),

    # ── Electricity ────────────────────────────────────────────────────────────
    'KWH':    ('kWh', 1.0),
    'KILOWATT-HOUR': ('kWh', 1.0),
    'MWH':    ('kWh', 1000.0),
    'MEGAWATT-HOUR': ('kWh', 1000.0),
    'GWH':    ('kWh', 1_000_000.0),

    # ── Mass ───────────────────────────────────────────────────────────────────
    'KG':     ('kg', 1.0),
    'KILOGRAM': ('kg', 1.0),
    'KILOGRAMS': ('kg', 1.0),
    'G':      ('kg', 0.001),
    'T':      ('kg', 1000.0),    # Metric ton
    'MT':     ('kg', 1000.0),
    'TONNE':  ('kg', 1000.0),
    'LB':     ('kg', 0.453592),
    'LBS':    ('kg', 0.453592),
    'POUND':  ('kg', 0.453592),
    'POUNDS': ('kg', 0.453592),

    # ── Distance ───────────────────────────────────────────────────────────────
    'KM':     ('km', 1.0),
    'KILOMETER': ('km', 1.0),
    'KILOMETERS': ('km', 1.0),
    'MI':     ('km', 1.60934),
    'MILE':   ('km', 1.60934),
    'MILES':  ('km', 1.60934),
    'NM':     ('km', 1.852),     # Nautical miles (aviation)
}

# Default emission factors (kgCO2e per normalized unit)
# Source: DEFRA 2023 / GHG Protocol
EMISSION_FACTORS = {
    'DIESEL_COMBUSTION': 2.68,          # kgCO2e per liter of diesel
    'NATURAL_GAS': 2.04,                # kgCO2e per kg
    'FUEL_OIL': 2.96,                   # kgCO2e per liter
    'ELECTRICITY_PURCHASED': 0.233,     # kgCO2e per kWh (UK grid average 2023)
    'AIR_TRAVEL_ECONOMY': 0.151,        # kgCO2e per passenger-km
    'AIR_TRAVEL_BUSINESS': 0.429,       # kgCO2e per passenger-km
    'AIR_TRAVEL_FIRST': 0.604,          # kgCO2e per passenger-km
    'HOTEL_STAY': 31.0,                 # kgCO2e per room-night
    'GROUND_TRANSPORT': 0.089,          # kgCO2e per km (average car)
}


def normalize_unit(quantity: float, unit: str) -> tuple[float, str]:
    """
    Converts a quantity from its source unit to the canonical unit.

    Returns:
        (normalized_quantity, canonical_unit)

    Raises:
        ValueError if the unit is unrecognized.
    """
    key = unit.strip().upper().replace(' ', '-')
    if key not in CONVERSION_FACTORS:
        raise ValueError(f"Unrecognized unit: '{unit}'. Cannot normalize.")
    canonical_unit, factor = CONVERSION_FACTORS[key]
    return round(quantity * factor, 6), canonical_unit


def get_emission_factor(activity_type: str, flight_class: str = 'ECONOMY') -> float | None:
    """
    Returns the kgCO2e emission factor for a given activity type.
    """
    if activity_type == 'AIR_TRAVEL':
        key = f'AIR_TRAVEL_{flight_class.upper()}'
        return EMISSION_FACTORS.get(key, EMISSION_FACTORS['AIR_TRAVEL_ECONOMY'])
    return EMISSION_FACTORS.get(activity_type)