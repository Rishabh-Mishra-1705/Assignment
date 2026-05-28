"""
Travel Parser
=============
Handles Concur / corporate travel CSV exports.

Common format:
  TravelerName, FromAirport, ToAirport, FlightClass, TravelDate, Distance_km, Hotel_Nights

Challenges:
  - Distance often missing → need to estimate or flag
  - Airport codes (LHR, JFK) instead of city names
  - Mixed hotel + flight rows in same file
  - Flight class impacts emission factor significantly (business = 3x economy)

Airport distances: We use a simplified lookup for common routes.
In production this would call an aviation distance API.
"""

import io
import pandas as pd
from ..normalizers.unit_normalizer import normalize_unit, get_emission_factor
from ..normalizers.date_normalizer import normalize_date
from ..validators.record_validator import validate_record

# Sample airport-to-city mapping (expand in production)
AIRPORT_TO_CITY = {
    'LHR': 'London, UK',     'LGW': 'London Gatwick, UK',
    'JFK': 'New York, USA',  'EWR': 'Newark, USA',   'LAX': 'Los Angeles, USA',
    'CDG': 'Paris, France',  'ORY': 'Paris Orly, France',
    'FRA': 'Frankfurt, Germany', 'MUC': 'Munich, Germany',
    'DXB': 'Dubai, UAE',     'SIN': 'Singapore',
    'HND': 'Tokyo Haneda, Japan', 'NRT': 'Tokyo Narita, Japan',
    'BOM': 'Mumbai, India',  'DEL': 'Delhi, India',
    'SYD': 'Sydney, Australia', 'MEL': 'Melbourne, Australia',
    'ORD': 'Chicago, USA',   'SFO': 'San Francisco, USA',
}

# Approximate great-circle distances for common routes (km)
# In production: use haversine formula with airport coordinates DB
ROUTE_DISTANCES = {
    ('LHR', 'JFK'): 5570, ('JFK', 'LHR'): 5570,
    ('LHR', 'DXB'): 5500, ('DXB', 'LHR'): 5500,
    ('FRA', 'JFK'): 6200, ('JFK', 'FRA'): 6200,
    ('LHR', 'SIN'): 10840, ('SIN', 'LHR'): 10840,
    ('LHR', 'BOM'): 7190, ('BOM', 'LHR'): 7190,
}

HEADER_MAP = {
    'travelername': 'traveler_name',
    'employeename': 'traveler_name',
    'fromairport': 'from_airport',
    'origin': 'from_airport',
    'toairport': 'to_airport',
    'destination': 'to_airport',
    'flightclass': 'flight_class',
    'class': 'flight_class',
    'traveldate': 'travel_date',
    'departuredate': 'travel_date',
    'distance': 'distance_km',
    'distancekm': 'distance_km',
    'distancemiles': 'distance_miles',
    'hotelnights': 'hotel_nights',
    'nightsstayed': 'hotel_nights',
    'hotelname': 'hotel_name',
    'cost': 'cost_amount',
    'totalcost': 'cost_amount',
    'currency': 'currency',
    'transporttype': 'transport_type',
    'mode': 'transport_type',
}


def _estimate_distance(from_code: str, to_code: str) -> tuple[float | None, bool]:
    """Returns (distance_km, is_estimated). is_estimated=True means flag for review."""
    key = (from_code.upper(), to_code.upper())
    dist = ROUTE_DISTANCES.get(key)
    if dist:
        return dist, False
    # Unknown route — return None to trigger suspicious flag
    return None, True


def parse_travel_csv(file_bytes: bytes) -> tuple[list[dict], list[dict]]:
    records = []
    errors = []

    try:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8', sep=None, engine='python')
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding='latin-1', sep=None, engine='python')
    except Exception as e:
        return [], [{'row': 0, 'error': f'Failed to read CSV: {str(e)}'}]

    df.columns = [c.strip().lower().replace(' ', '').replace('_', '') for c in df.columns]
    df.rename(columns={k: v for k, v in HEADER_MAP.items() if k in df.columns}, inplace=True)

    for idx, row in df.iterrows():
        row_num = idx + 2
        try:
            transport_type = str(row.get('transport_type', 'FLIGHT')).upper()
            raw_date = str(row.get('travel_date', ''))
            activity_date = normalize_date(raw_date, source_hint='TRAVEL')

            # ── Handle flight records ──────────────────────────────────────────
            if 'from_airport' in row and pd.notna(row.get('from_airport')):
                from_code = str(row['from_airport']).strip().upper()
                to_code = str(row.get('to_airport', '')).strip().upper()
                flight_class = str(row.get('flight_class', 'ECONOMY')).upper()

                # Resolve distance
                if pd.notna(row.get('distance_km')):
                    dist_km = float(row['distance_km'])
                    is_estimated = False
                elif pd.notna(row.get('distance_miles')):
                    dist_km, _ = normalize_unit(float(row['distance_miles']), 'MI')
                    is_estimated = False
                else:
                    dist_km, is_estimated = _estimate_distance(from_code, to_code)

                if dist_km is None:
                    errors.append({'row': row_num, 'error': f'Unknown route {from_code}→{to_code}, distance missing'})
                    continue

                ef = get_emission_factor('AIR_TRAVEL', flight_class)
                emissions = dist_km * ef

                from_city = AIRPORT_TO_CITY.get(from_code, from_code)
                to_city = AIRPORT_TO_CITY.get(to_code, to_code)

                record = {
                    'scope': 'SCOPE_3',
                    'activity_type': 'AIR_TRAVEL',
                    'description': f"{from_city} → {to_city} ({flight_class}) | {row.get('traveler_name', '')}",
                    'quantity': dist_km,
                    'unit': 'km',
                    'raw_date': raw_date,
                    'normalized_quantity': dist_km,
                    'normalized_unit': 'km',
                    'activity_date': activity_date,
                    'emission_factor': ef,
                    'estimated_emission_kgco2e': emissions,
                    'location': f"{from_code} → {to_code}",
                    'cost_amount': float(row['cost_amount']) if pd.notna(row.get('cost_amount')) else None,
                    'currency': str(row.get('currency', 'USD')),
                    'row_number': row_num,
                    'suspicious_flag': is_estimated,
                    'suspicious_reason': 'Distance estimated from route lookup' if is_estimated else '',
                }

            # ── Handle hotel records ───────────────────────────────────────────
            elif pd.notna(row.get('hotel_nights')):
                nights = float(row['hotel_nights'])
                ef = get_emission_factor('HOTEL_STAY')
                emissions = nights * ef

                record = {
                    'scope': 'SCOPE_3',
                    'activity_type': 'HOTEL_STAY',
                    'description': f"{row.get('hotel_name', 'Unknown Hotel')} | {row.get('traveler_name', '')}",
                    'quantity': nights,
                    'unit': 'nights',
                    'raw_date': raw_date,
                    'normalized_quantity': nights,
                    'normalized_unit': 'nights',
                    'activity_date': activity_date,
                    'emission_factor': ef,
                    'estimated_emission_kgco2e': emissions,
                    'location': str(row.get('location', '')),
                    'cost_amount': float(row['cost_amount']) if pd.notna(row.get('cost_amount')) else None,
                    'currency': str(row.get('currency', 'USD')),
                    'row_number': row_num,
                }
            else:
                errors.append({'row': row_num, 'error': 'Row is neither flight nor hotel — skipped'})
                continue

            record, warnings = validate_record(record)
            if warnings and not record.get('suspicious_flag'):
                record['suspicious_flag'] = True
                record['suspicious_reason'] = '; '.join(warnings)

            records.append(record)

        except Exception as e:
            errors.append({'row': row_num, 'error': str(e)})

    return records, errors