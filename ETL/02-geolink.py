#!/usr/bin/env python3
"""
02-geolink.py - Robust Geo-Link Enrichment for Tenants Union ETL

Combines:
- Proven two-stage lookup strategy (full address → strict comma-parsed fallback)
- Automated exponential backoff retry loop for resilient API network handling
- Intelligent comma-boundary address parsing for Spanish data
- Robust geocoded address sanitation to completely strip out municipal noise
- Automatic formatting and appending of unit tracking tokens (Floor + Door)
"""

import sys
import csv
import requests
import time
import logging

# =============================================================================
# CONFIGURATION
# =============================================================================
API_URL = "https://www.cartociudad.es/geocoder/api/geocoder/candidates"
API_TIMEOUT = 10
RATE_LIMIT_SLEEP = 0.2

# Resilience / Retry Configurations
MAX_RETRIES = 3            # Total attempts per API request phase
RETRY_BACKOFF_BASE = 1.5   # Base multiplier for exponential sleep delays

# Column matching criteria (case-insensitive)
ADDRESS_FIELDS = ['address_full_google', 'direction', 'direccion', 'address', 'calle']
CITY_FIELDS = ['address_city', 'city', 'municipio', 'ciudad', 'poblacion']
FLOOR_FIELDS = ['address_floor', 'floor', 'piso', 'planta']
DOOR_FIELDS = ['address_door', 'door', 'puerta', 'mano']

# New columns added by this transform
NEW_COLUMNS = ['ref_catastral', 'coordenadas', 'geocoded_address']

# =============================================================================
# LOGGING SETUP
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def clean_address_string(address_string):
    """Normalizes whitespace and expands common Spanish street abbreviations."""
    if not address_string:
        return ""
    text = " ".join(str(address_string).split())
    lower = text.lower()
    if lower.startswith("c. "):
        text = "Calle " + text[3:]
    elif lower.startswith("c/"):
        text = "Calle " + text[2:]
    return text.strip()


def extract_street_and_number(full_address):
    """Parses the full address using comma boundaries to isolate 'Street, Number'."""
    if not full_address:
        return ""
    parts = [p.strip() for p in str(full_address).split(',') if p.strip()]
    if not parts:
        return ""

    street = clean_address_string(parts[0])

    if len(parts) > 1:
        second = parts[1]
        first_token = second.split()[0] if second.split() else ""
        if any(char.isdigit() for char in first_token):
            return f"{street}, {first_token}"

    return street


def find_best_column(fieldnames, candidates):
    """Case-insensitive search for the best matching column name."""
    if not fieldnames:
        return None
    lower_fields = {f.lower(): f for f in fieldnames}
    for candidate in candidates:
        if candidate.lower() in lower_fields:
            return lower_fields[candidate.lower()]
    return None


def sanitize_geocoded_base(geocoded_str):
    """
    Strips out trailing city, postal codes, and provincial/country indicators 
    returned by the geocoder API to isolate the pure street address line.
    """
    if not geocoded_str:
        return ""
        
    parts = [p.strip() for p in geocoded_str.split(',') if p.strip()]
    if not parts:
        return ""
        
    street_line = parts[0]
    
    if len(parts) > 1:
        second_part = parts[1]
        first_token = second_part.split()[0] if second_part.split() else ""
        
        if any(char.isdigit() for char in first_token) and len(first_token) < 5:
            return f"{street_line}, {first_token}"
            
    return street_line


def get_cadastral_data(address_string, municipality="Madrid"):
    """
    Queries CartoCiudad and returns (ref_catastral, coordenadas, geocoded_address).
    Features an exponential backoff retry system to handle transient drops/rate limits.
    """
    if not address_string or len(address_string) < 5:
        return "", "", ""

    params = {
        'q': address_string,
        'limit': 1
    }
    if municipality:
        params['municipio_filter'] = str(municipality).strip()

    # Loop through execution retry budget
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(API_URL, params=params, timeout=API_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if data and isinstance(data, list) and len(data) > 0:
                best = data[0]
                
                ref_catastral = (best.get('refCatastral') or '').strip()
                lat = best.get('lat') or ''
                lng = best.get('lng') or ''
                
                raw_geo_addr = best.get('address') or best.get('portalAddress') or ""
                geocoded_address = sanitize_geocoded_base(str(raw_geo_addr))
                coordenadas = f"{lat}, {lng}" if lat and lng else ""
                
                return ref_catastral, coordenadas, geocoded_address
            else:
                # API responded with 200 OK but an empty array (Genuine zero match found)
                return "", "", ""

        except (requests.exceptions.RequestException, Exception) as e:
            if attempt == MAX_RETRIES:
                logging.warning(f"❌ API permanently failed after {MAX_RETRIES} attempts for '{address_string}': {e}")
            else:
                # Exponential backoff formula calculation: e.g., 1.5s, 3.0s
                sleep_time = RETRY_BACKOFF_BASE * attempt
                logging.info(f"⏳ Retry block triggered (Attempt {attempt}/{MAX_RETRIES} failed: {e}). Retrying in {sleep_time}s...")
                time.sleep(sleep_time)

    return "", "", ""


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def main():
    if len(sys.argv) < 3:
        logging.error("Missing arguments.")
        print("Usage: python3 02-geolink.py <input_csv> <output_csv>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    logging.info("🚀 Starting Geo-Link Enrichment (Resilient Network Topology Ingestion)")

    try:
        with open(input_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            if not reader.fieldnames:
                logging.error("CSV has no headers.")
                sys.exit(1)

            addr_col = find_best_column(reader.fieldnames, ADDRESS_FIELDS)
            city_col = find_best_column(reader.fieldnames, CITY_FIELDS)
            floor_col = find_best_column(reader.fieldnames, FLOOR_FIELDS)
            door_col = find_best_column(reader.fieldnames, DOOR_FIELDS)

            logging.info(f"🎯 Address column: {addr_col or 'NOT FOUND'}")
            logging.info(f"🌆 City column:    {city_col or 'NOT FOUND (defaulting to Madrid)'}")
            logging.info(f"🏢 Unit tracking:  Floor={floor_col or 'None'}, Door={door_col or 'None'}")

            rows = list(reader)

        total = len(rows)
        success = 0
        fallback_used = 0

        output_fieldnames = [f for f in reader.fieldnames if f not in NEW_COLUMNS] + NEW_COLUMNS

        with open(output_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()

            for idx, row in enumerate(rows, 1):
                raw_address = row.get(addr_col, '') if addr_col else ''
                city = row.get(city_col, 'Madrid') if city_col else 'Madrid'
                if not city or not str(city).strip():
                    city = 'Madrid'

                # === STAGE 1: Try full cleaned address ===
                clean_full = clean_address_string(raw_address)
                ref_cat, coords, geocoded = get_cadastral_data(clean_full, city)

                # === STAGE 2: Fallback to strict comma-parsed address ===
                if not ref_cat and raw_address:
                    parsed = extract_street_and_number(raw_address)
                    if parsed and parsed != clean_full:
                        logging.info(f"⚠️  Row {idx}: Full address gave no result. Trying comma-parsed: '{parsed}'")
                        ref_cat, coords, geocoded = get_cadastral_data(parsed, city)
                        if ref_cat:
                            fallback_used += 1

                # === STAGE 3: Append Floor + Door Info to Pure Base Address ===
                if geocoded:
                    floor_val = str(row.get(floor_col, '')).strip() if floor_col else ''
                    door_val = str(row.get(door_col, '')).strip() if door_col else ''
                    
                    if floor_val and floor_val.isdigit() and len(floor_val) <= 2:
                        floor_val = f"{floor_val}º"
                    
                    unit_parts = [p for p in [floor_val, door_val] if p]
                    if unit_parts:
                        unit_str = " ".join(unit_parts)
                        geocoded = f"{geocoded}, {unit_str}"

                # Write results
                row['ref_catastral'] = ref_cat
                row['coordenadas'] = coords
                row['geocoded_address'] = geocoded

                output_row = {k: row.get(k, '') for k in output_fieldnames}
                writer.writerow(output_row)

                if ref_cat:
                    success += 1

                if idx % 20 == 0 or idx == total:
                    logging.info(f"⏳ Processed {idx}/{total} | Success: {success} | Fallback used: {fallback_used}")

                time.sleep(RATE_LIMIT_SLEEP)

        logging.info("=" * 60)
        logging.info(f"✅ Enrichment completed successfully!")
        logging.info(f"   Total records processed: {total}")
        logging.info(f"   Successful hits:         {success}")
        logging.info(f"   Sanitized Output File:   {output_path}")
        logging.info("=" * 60)

    except Exception as e:
        logging.critical(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()