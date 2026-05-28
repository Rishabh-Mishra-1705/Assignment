"""
Utility Parser
==============
Handles electricity bill CSVs from utility providers.

Common formats:
  - MeterID, ConsumptionKWh, BillingStart, BillingEnd, Tariff, Cost
  - AccountNumber, ReadingDate, PreviousReading, CurrentReading, Unit

Key challenges:
  - Billing periods span multiple calendar months (tricky for monthly reporting)
  - Units can be kWh, MWh, or even kVAh (we reject kVAh — needs manual review)
  - Duplicate rows from estimated vs actual readings

We always use BillingEnd as the canonical activity_date.
"""

import io
import pandas as pd
from ..normalizers.unit_normalizer import normalize_unit, get_emission_factor
from ..normalizers.date_normalizer import normalize_date
from ..validators.record_validator import validate_record

HEADER_MAP = {
    'meterid': 'meter_id',
    'meteridentifier': 'meter_id',
    'accountnumber': 'meter_id',
    'consumptionkwh': 'quantity',
    'consumption': 'quantity',
    'usage': 'quantity',
    'previousreading': 'prev_reading',
    'currentreading': 'curr_reading',
    'unit': 'unit',
    'units': 'unit',
    'billingstart': 'billing_start',
    'billingend': 'billing_end',
    'billdate': 'billing_end',
    'readingdate': 'billing_end',
    'tariff': 'tariff',
    'totalcost': 'cost_amount',
    'cost': 'cost_amount',
    'amount': 'cost_amount',
    'currency': 'currency',
    'site': 'location',
    'location': 'location',
    'address': 'location',
}


def parse_utility_csv(file_bytes: bytes) -> tuple[list[dict], list[dict]]:
    records = []
    errors = []

    try:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8', sep=None, engine='python')
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding='latin-1', sep=None, engine='python')
    except Exception as e:
        return [], [{'row': 0, 'error': f'Failed to read CSV: {str(e)}'}]

    # Normalize headers
    df.columns = [c.strip().lower().replace(' ', '').replace('_', '') for c in df.columns]
    df.rename(columns={k: v for k, v in HEADER_MAP.items() if k in df.columns}, inplace=True)

    # If consumption not direct, compute from meter readings
    if 'quantity' not in df.columns and 'curr_reading' in df.columns and 'prev_reading' in df.columns:
        df['quantity'] = df['curr_reading'] - df['prev_reading']

    required = ['quantity', 'billing_end']
    missing = [c for c in required if c not in df.columns]
    if missing:
        return [], [{'row': 0, 'error': f'Missing required columns after mapping: {missing}'}]

    # Default unit to kWh if not present (most utility CSVs omit it)
    if 'unit' not in df.columns:
        df['unit'] = 'kWh'

    for idx, row in df.iterrows():
        row_num = idx + 2
        try:
            raw_qty = float(row['quantity'])
            raw_unit = str(row.get('unit', 'kWh')).strip()
            norm_qty, norm_unit = normalize_unit(raw_qty, raw_unit)
            raw_date = str(row['billing_end'])
            activity_date = normalize_date(raw_date, source_hint='UTILITY')

            emission_factor = get_emission_factor('ELECTRICITY_PURCHASED')
            estimated_emission = norm_qty * emission_factor

            record = {
                'scope': 'SCOPE_2',
                'activity_type': 'ELECTRICITY_PURCHASED',
                'description': f"Meter: {row.get('meter_id', 'Unknown')} | Tariff: {row.get('tariff', 'N/A')}",
                'quantity': raw_qty,
                'unit': raw_unit,
                'raw_date': raw_date,
                'normalized_quantity': norm_qty,
                'normalized_unit': norm_unit,
                'activity_date': activity_date,
                'emission_factor': emission_factor,
                'estimated_emission_kgco2e': estimated_emission,
                'location': str(row.get('location', '')),
                'cost_amount': float(row['cost_amount']) if pd.notna(row.get('cost_amount')) else None,
                'currency': str(row.get('currency', 'USD')),
                'reference_id': str(row.get('meter_id', '')),
                'row_number': row_num,
            }

            record, warnings = validate_record(record)
            if warnings:
                record['suspicious_flag'] = True
                record['suspicious_reason'] = '; '.join(warnings)

            records.append(record)

        except Exception as e:
            errors.append({'row': row_num, 'error': str(e)})

    return records, errors