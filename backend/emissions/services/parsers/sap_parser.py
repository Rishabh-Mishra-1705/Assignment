"""
SAP Parser
==========
Parses SAP flat-file / CSV exports into normalized EmissionRecord dicts.

Real SAP exports often contain:
  - German column headers (Materialnummer, Menge, Einheit, Buchungsdatum)
  - Plant codes instead of location names
  - Material codes instead of fuel types
  - Compact dates (YYYYMMDD)
  - Units like 'L', 'GAL', 'M3', 'KG'

This parser handles two scenarios:
  A) German-header SAP export (Materialnummer, Werk, Menge, ...)
  B) English-header SAP export (MaterialCode, PlantCode, Quantity, ...)

We map both to an internal canonical dict, then hand off to normalizers.
"""

import io
import pandas as pd
from ..normalizers.unit_normalizer import normalize_unit, get_emission_factor, EMISSION_FACTORS
from ..normalizers.date_normalizer import normalize_date
from ..validators.record_validator import validate_record

# ── Column mapping: German SAP headers → canonical internal names ──────────────
GERMAN_TO_CANONICAL = {
    'materialnummer': 'material_code',
    'materialtext':   'material_description',
    'werk':           'plant_code',
    'menge':          'quantity',
    'mengeneinheit':  'unit',
    'buchungsdatum':  'posting_date',
    'belegart':       'document_type',
    'lieferant':      'supplier',
    'betrag':         'cost_amount',
    'währung':        'currency',
    'belegnummer':    'reference_id',
}

# ── English SAP headers ────────────────────────────────────────────────────────
ENGLISH_TO_CANONICAL = {
    'materialcode':   'material_code',
    'materialdescription': 'material_description',
    'plantcode':      'plant_code',
    'quantity':       'quantity',
    'unit':           'unit',
    'postingdate':    'posting_date',
    'documenttype':   'document_type',
    'supplier':       'supplier',
    'amount':         'cost_amount',
    'currency':       'currency',
    'documentnumber': 'reference_id',
}

# ── SAP material codes → activity types ───────────────────────────────────────
MATERIAL_TO_ACTIVITY = {
    'DIESEL':   ('DIESEL_COMBUSTION', 'SCOPE_1'),
    'HEL':      ('DIESEL_COMBUSTION', 'SCOPE_1'),   # "Heizöl EL" (heating oil)
    'ERDGAS':   ('NATURAL_GAS',       'SCOPE_1'),
    'NATGAS':   ('NATURAL_GAS',       'SCOPE_1'),
    'FUELOIL':  ('FUEL_OIL',          'SCOPE_1'),
    'HEIZÖL':   ('FUEL_OIL',          'SCOPE_1'),
    'BENZIN':   ('DIESEL_COMBUSTION', 'SCOPE_1'),   # Petrol mapped to diesel for simplicity
    'GASOLINE': ('DIESEL_COMBUSTION', 'SCOPE_1'),
}


def _normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Lowercases and strips headers, then maps them to canonical names.
    Supports both German and English SAP exports.
    """
    df.columns = [c.strip().lower().replace(' ', '').replace('-', '') for c in df.columns]
    # Try German mapping first, then English
    rename = {}
    for col in df.columns:
        if col in GERMAN_TO_CANONICAL:
            rename[col] = GERMAN_TO_CANONICAL[col]
        elif col in ENGLISH_TO_CANONICAL:
            rename[col] = ENGLISH_TO_CANONICAL[col]
    return df.rename(columns=rename)


def parse_sap_csv(file_bytes: bytes) -> tuple[list[dict], list[dict]]:
    """
    Main entry point. Parses raw SAP CSV bytes.

    Returns:
        (records, errors)
        records: list of dicts ready to create EmissionRecord objects
        errors:  list of {'row': int, 'error': str}
    """
    records = []
    errors = []

    # SAP exports often use latin-1 encoding due to German characters
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding='latin-1', sep=None, engine='python')
    except Exception as e:
        return [], [{'row': 0, 'error': f'Failed to read CSV: {str(e)}'}]

    df = _normalize_headers(df)

    # Verify required columns exist
    required = ['material_code', 'quantity', 'unit', 'posting_date']
    missing = [c for c in required if c not in df.columns]
    if missing:
        return [], [{'row': 0, 'error': f'Missing required columns: {missing}'}]

    for idx, row in df.iterrows():
        row_num = idx + 2  # +2 because 1-indexed and header row
        try:
            raw_material = str(row.get('material_code', '')).strip().upper()
            activity_type, scope = MATERIAL_TO_ACTIVITY.get(
                raw_material,
                ('DIESEL_COMBUSTION', 'SCOPE_1')   # Default for unknown SAP fuel codes
            )

            raw_qty = float(row['quantity'])
            raw_unit = str(row['unit']).strip()
            norm_qty, norm_unit = normalize_unit(raw_qty, raw_unit)
            raw_date = str(row['posting_date'])
            activity_date = normalize_date(raw_date, source_hint='SAP')

            emission_factor = get_emission_factor(activity_type)
            estimated_emission = (norm_qty * emission_factor) if emission_factor else None

            record = {
                'scope': scope,
                'activity_type': activity_type,
                'description': str(row.get('material_description', '')),
                'quantity': raw_qty,
                'unit': raw_unit,
                'raw_date': raw_date,
                'normalized_quantity': norm_qty,
                'normalized_unit': norm_unit,
                'activity_date': activity_date,
                'emission_factor': emission_factor,
                'estimated_emission_kgco2e': estimated_emission,
                'location': str(row.get('plant_code', '')),
                'supplier': str(row.get('supplier', '')),
                'cost_amount': float(row['cost_amount']) if pd.notna(row.get('cost_amount')) else None,
                'currency': str(row.get('currency', '')),
                'reference_id': str(row.get('reference_id', '')),
                'row_number': row_num,
            }

            # Validate and flag suspicious records
            record, warnings = validate_record(record)
            if warnings:
                record['suspicious_flag'] = True
                record['suspicious_reason'] = '; '.join(warnings)

            records.append(record)

        except Exception as e:
            errors.append({'row': row_num, 'error': str(e)})

    return records, errors