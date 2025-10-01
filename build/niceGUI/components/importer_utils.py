# build/niceGUI/components/importer_utils.py

import pandas as pd
import re
from datetime import date, datetime
from typing import Optional, Dict, Any

from api.validate import validator


def parse_date(date_str: str) -> Optional[str]:
    """Safely parses a date string from multiple formats."""
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date().isoformat()
        except (ValueError, TypeError):
            continue
    return None


def short_address(address: Optional[str]) -> str:
    """Return only 'street name + house number' from a full address.

    Rules:
    - If the first comma-separated token already contains a trailing number
      (e.g. "Calle Santa Fe 3"), return it trimmed to that last number.
    - Otherwise, append the first subsequent token that is a clean house
      number (e.g. "10" or "10B"). Tokens like "1º", "Bajo", "Izq" are ignored.
    - As a last resort, return the first token (street name) as-is.
    """
    if not address:
        return ""
    parts = [p.strip() for p in str(address).split(",") if p.strip()]
    if not parts:
        return ""

    first = parts[0]
    # If first token ends with a number (optionally followed by one letter), keep up to it.
    m_first = re.search(r"(\d+[A-Za-z]?)\s*$", first)
    if m_first:
        return first[: m_first.end()].strip()

    # Else, find the first subsequent token that is a clean house number like '10' or '10B'
    for token in parts[1:]:
        m_num = re.match(r"^(\d+[A-Za-z]?)$", token.replace(" ", ""))
        if m_num:
            return f"{first} {m_num.group(1)}"

    return first


def transform_and_validate_row(row: pd.Series) -> Optional[Dict[str, Any]]:
    """
    Transforms a single CSV row into a structured dictionary and validates it.
    Returns the structured record or None if the row is invalid.
    """
    try:
        get_val = lambda index: row.get(index, "").strip()
        nombre = get_val(0).strip('<>"')
        if not nombre:
            return None

        # --- Data Extraction ---
        full_address = ", ".join(
            filter(
                None,
                [
                    get_val(9),
                    get_val(10),
                    get_val(11),
                    get_val(12),
                    get_val(14),
                    get_val(13),
                ],
            )
        )
        final_address = re.sub(r"\s*,\s*", ", ", full_address).strip(" ,")
        cuota_str = get_val(23) or get_val(24) or get_val(25)
        cuota_match = re.search(r"(\d+[\.,]?\d*)\s*€\s*(mes|año)", cuota_str)
        iban_raw = get_val(26).replace(" ", "")

        # --- Data Structuring ---
        record = {
            "afiliada": {
                "nombre": nombre,
                "apellidos": f"{get_val(2)} {get_val(3)}".strip(),
                "genero": get_val(4),
                "fecha_nac": parse_date(get_val(5)),
                "cif": get_val(6).upper(),
                "telefono": get_val(7),
                "email": get_val(8),
                "fecha_alta": date.today().isoformat(),
                "regimen": get_val(17),
                "estado": "Alta",
                "piso_id": None,
            },
            "piso": {
                "direccion": final_address,
                "municipio": get_val(13),
                "cp": int(get_val(14)) if get_val(14).isdigit() else None,
                "n_personas": int(get_val(15)) if get_val(15).isdigit() else None,
                "inmobiliaria": get_val(18),
                "propiedad": get_val(20),
                "prop_vertical": get_val(21),
                "fecha_firma": parse_date(get_val(16)),
                "bloque_id": None,
            },
            "bloque": {"direccion": short_address(final_address)},
            "facturacion": {
                "cuota": (
                    float(cuota_match.group(1).replace(",", "."))
                    if cuota_match
                    else 0.0
                ),
                "periodicidad": (
                    12 if cuota_match and cuota_match.group(2) == "año" else 1
                ),
                "forma_pago": "Domiciliación" if iban_raw else "Otro",
                "iban": iban_raw.upper() if iban_raw else None,
                "afiliada_id": None,
            },
            "meta": {
                "bloque": None,
                "bloque_manual": None,
                "nif_exists": False,
                "piso_exists": False,
            },
        }

        # --- Validation ---
        is_valid_afiliada, err_afiliada = validator.validate_record(
            "afiliadas", record["afiliada"]
        )
        is_valid_piso, err_piso = validator.validate_record("pisos", record["piso"])
        is_valid_bloque, err_bloque = validator.validate_record(
            "bloques", record["bloque"]
        )
        is_valid_facturacion, err_facturacion = validator.validate_record(
            "facturacion", record["facturacion"]
        )

        record["validation"] = {
            "is_valid": is_valid_afiliada
            and is_valid_piso
            and is_valid_bloque
            and is_valid_facturacion,
            "errors": err_afiliada + err_piso + err_bloque + err_facturacion,
            "warnings": [],
        }
        return record

    except Exception:
        return None
