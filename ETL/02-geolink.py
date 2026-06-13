#!/usr/bin/env python3
import sys
import csv
import requests
import time

def get_cadastral_data(address_string):
    """
    Queries CartoCiudad for the cadastral reference and coordinates.
    Returns a tuple: (ref_catastral, coordinates)
    """
    if not address_string or address_string.strip() == "":
        return "", ""

    url = "https://www.cartociudad.es/geocoder/api/geocoder/candidates"
    params = {
        'q': address_string,
        'limit': 1,
        'municipio_filter': 'Madrid' # Assuming your DB is Madrid-focused per previous context
    }

    try:
        response = requests.get(url, params=params, timeout=10) # 10-second timeout is crucial for ETLs
        response.raise_for_status()
        data = response.json()

        if not data:
            return "", ""

        best_match = data[0]
        
        # Extract Cadastral Reference
        ref_catastral = best_match.get('refCatastral', '')
        
        # Extract Coordinates (Formatting as "lat, lng")
        lat = best_match.get('lat', '')
        lng = best_match.get('lng', '')
        coordenadas = f"{lat}, {lng}" if lat and lng else ""

        return ref_catastral, coordenadas

    except requests.exceptions.RequestException as e:
        # We print to stderr so it shows up cleanly in your cron_errors.log
        print(f"⚠️ API Error for address '{address_string}': {e}", file=sys.stderr)
        return "", ""

def main():
    # 1. Validate arguments passed by the Bash script
    if len(sys.argv) != 3:
        print("Usage: python3 enrich_cadastro.py <input_csv> <output_csv>", file=sys.stderr)
        sys.exit(1)

    input_csv_path = sys.argv[1]
    output_csv_path = sys.argv[2]

    # The new columns we want to append
    new_columns = ['ref_catastral', 'coordenadas']

    print(f"🚀 Starting enrichment process...")
    print(f"📥 Input: {input_csv_path}")
    print(f"📤 Output: {output_csv_path}")

    # 2. Process the CSV
    try:
        with open(input_csv_path, mode='r', encoding='utf-8') as infile, \
             open(output_csv_path, mode='w', encoding='utf-8', newline='') as outfile:
            
            # Use DictReader/DictWriter to safely handle columns by name
            reader = csv.DictReader(infile)
            
            # Check if the expected 'direction' column actually exists
            if 'direction' not in reader.fieldnames:
                print("🚨 ERROR: 'direction' column not found in the input CSV.", file=sys.stderr)
                sys.exit(1)

            # Prepare the output headers (Original headers + our new ones)
            fieldnames = reader.fieldnames + new_columns
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()

            success_count = 0
            row_count = 0

            # 3. Iterate through rows and enrich
            for row in reader:
                row_count += 1
                address = row.get('direction', '')
                
                # Fetch data from API
                ref_catastral, coordenadas = get_cadastral_data(address)
                
                # Append to the row dictionary
                row['ref_catastral'] = ref_catastral
                row['coordenadas'] = coordenadas
                
                # Write the enriched row
                writer.writerow(row)

                if ref_catastral:
                    success_count += 1

                # 🛡️ Politeness Delay: Government APIs will temporarily ban your IP if you slam them.
                # 0.2 seconds guarantees a max of 5 requests per second, which is very safe.
                time.sleep(0.2) 

        print(f"✅ Enrichment complete! Processed {row_count} rows. Found {success_count} cadastral references.")

    except FileNotFoundError:
        print(f"🚨 ERROR: Could not find the input file at {input_csv_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"🚨 UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()