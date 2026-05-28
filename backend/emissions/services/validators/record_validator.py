"""
Record Validator
================
Runs business-rule checks on a normalized record dict BEFORE it is saved.
Returns (record_dict, list_of_warning_strings).

Suspicious flags do NOT block saving — they trigger the review queue.
Hard errors raise exceptions and prevent saving.
"""

from datetime import date


# Thresholds — document these in DECISIONS.md
SUSPICIOUS_THRESHOLDS = {
    'DIESEL_COMBUSTION':     {'max_liters': 50_000,  'min_liters': 0.1},
    'NATURAL_GAS':           {'max_kg': 100_000,     'min_kg': 0.1},
    'ELECTRICITY_PURCHASED': {'max_kwh': 500_000,    'min_kwh': 1.0},
    'AIR_TRAVEL':            {'max_km': 20_000,      'min_km': 50},
    'HOTEL_STAY':            {'max_nights': 365,     'min_nights': 1},
}


def validate_record(record: dict) -> tuple[dict, list[str]]:
    warnings = []
    activity_type = record.get('activity_type', '')
    norm_qty = record.get('normalized_quantity', 0)
    norm_unit = record.get('normalized_unit', '')
    activity_date = record.get('activity_date')

    # ── Negative or zero values ────────────────────────────────────────────────
    if norm_qty < 0:
        warnings.append(f"Negative quantity: {norm_qty}")
    elif norm_qty == 0:
        warnings.append("Zero quantity — possible meter error or duplicate")

    # ── Future dates ───────────────────────────────────────────────────────────
    if activity_date and isinstance(activity_date, date):
        if activity_date > date.today():
            warnings.append(f"Future date: {activity_date} — likely data entry error")

    # ── Very old dates (pre-2010 for a modern ESG platform) ────────────────────
    if activity_date and isinstance(activity_date, date):
        if activity_date.year < 2010:
            warnings.append(f"Very old date: {activity_date} — verify correct year")

    # ── Activity-specific range checks ────────────────────────────────────────
    thresholds = SUSPICIOUS_THRESHOLDS.get(activity_type, {})
    for key, limit in thresholds.items():
        direction, unit_label = key.split('_', 1)  # 'max' / 'min', 'liters' etc.
        if direction == 'max' and norm_qty > limit:
            warnings.append(f"Unusually high {activity_type}: {norm_qty} {norm_unit} (limit: {limit})")
        elif direction == 'min' and 0 < norm_qty < limit:
            warnings.append(f"Unusually low {activity_type}: {norm_qty} {norm_unit}")

    # ── Missing emission factor ────────────────────────────────────────────────
    if record.get('emission_factor') is None:
        warnings.append("No emission factor available — CO2e cannot be calculated")

    return record, warnings