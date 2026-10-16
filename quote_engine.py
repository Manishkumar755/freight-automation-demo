"""
Rate-based freight quote engine (demo).

Rules implemented:
  - Air:      chargeable weight = max(actual kg, volumetric kg); volumetric = L x W x H x pieces / 6000
  - By Road:  price = actual kg x rate, with a minimum charge
  - Sea FCL:  flat rate per container (dimensions do not change the price)

All numbers in rates_sample.csv are SAMPLE values for demo purposes only.
"""
import csv
from dataclasses import dataclass

AIR_VOLUMETRIC_DIVISOR = 6000  # cm3 per kg, standard air volumetric factor
VALID_MODES = ("air", "road", "fcl20", "fcl40")


@dataclass
class Shipment:
    origin: str
    destination: str
    mode: str
    weight_kg: float = 0.0
    length_cm: float = 0.0
    width_cm: float = 0.0
    height_cm: float = 0.0
    pieces: int = 1


def load_rates(path):
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["origin"].strip().upper(),
                   row["destination"].strip().upper(),
                   row["mode"].strip().lower())
            rates[key] = {
                "rate": float(row["rate"]),
                "min_charge": float(row["min_charge"]),
                "currency": row["currency"].strip(),
            }
    return rates


def quote(s, rates):
    if s.mode not in VALID_MODES:
        raise ValueError(f"Unknown mode '{s.mode}'. Use one of {VALID_MODES}.")
    if s.weight_kg < 0 or min(s.length_cm, s.width_cm, s.height_cm) < 0:
        raise ValueError("Weight and dimensions cannot be negative.")
    if s.pieces < 1:
        raise ValueError("Pieces must be at least 1.")

    key = (s.origin.strip().upper(), s.destination.strip().upper(), s.mode)
    r = rates.get(key)
    if r is None:
        return {
            "status": "no_rate",
            "message": f"No sample rate for {key[0]} to {key[1]} ({s.mode}). Route to the ops team.",
        }

    if s.mode.startswith("fcl"):
        return {
            "status": "ok",
            "basis": "flat rate per container",
            "amount": round(r["rate"], 2),
            "currency": r["currency"],
            "note": "SAMPLE rate - demo only",
        }

    volumetric = None
    if s.mode == "air":
        volumetric = s.length_cm * s.width_cm * s.height_cm * s.pieces / AIR_VOLUMETRIC_DIVISOR
        billable = max(s.weight_kg, volumetric)
        basis = "chargeable weight (greater of actual and volumetric)"
    else:
        billable = s.weight_kg
        basis = "actual weight"

    amount = max(billable * r["rate"], r["min_charge"])
    return {
        "status": "ok",
        "basis": basis,
        "actual_kg": round(s.weight_kg, 2),
        "volumetric_kg": round(volumetric, 2) if volumetric is not None else None,
        "billable_kg": round(billable, 2),
        "amount": round(amount, 2),
        "currency": r["currency"],
        "note": "SAMPLE rate - demo only",
    }
