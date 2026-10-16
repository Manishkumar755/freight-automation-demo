"""
Rate-based quote engine (demo).

Air: chargeable weight = max(actual kg, volumetric kg), price = billable kg x rate, with a minimum charge.
Sea: flat rate per container from the rate table.

All rates in rates_sample.csv are SAMPLE numbers for demo purposes only.
"""
import csv
from dataclasses import dataclass

AIR_VOLUMETRIC_DIVISOR = 6000  # cm3 per kg (standard air volumetric factor)


@dataclass
class Shipment:
    origin: str
    destination: str
    mode: str                  # "air", "fcl20", "fcl40"
    weight_kg: float = 0.0
    length_cm: float = 0.0
    width_cm: float = 0.0
    height_cm: float = 0.0
    pieces: int = 1


def load_rates(path: str) -> dict:
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["origin"], row["destination"], row["mode"])
            rates[key] = {
                "rate": float(row["rate"]),
                "min_charge": float(row["min_charge"]),
                "currency": row["currency"],
            }
    return rates


def chargeable_weight(s: Shipment) -> float:
    volumetric = s.pieces * s.length_cm * s.width_cm * s.height_cm / AIR_VOLUMETRIC_DIVISOR
    return max(s.weight_kg, volumetric)


def quote(s: Shipment, rates: dict) -> dict:
    key = (s.origin, s.destination, s.mode)
    if key not in rates:
        # Never invent a price. Send it to a human instead.
        return {"status": "manual_review", "reason": f"No rate found for {key}"}

    r = rates[key]
    if s.mode == "air":
        billable = round(chargeable_weight(s), 1)
        amount = max(billable * r["rate"], r["min_charge"])
        basis = f"{billable} kg chargeable x {r['rate']} {r['currency']}/kg (min {r['min_charge']})"
    else:
        amount = r["rate"]
        basis = f"per {s.mode.upper()} container"

    return {
        "status": "quoted",
        "amount": round(amount, 2),
        "currency": r["currency"],
        "basis": basis,
        "note": "Indicative quote. Final rate confirmed by ops team.",
    }


if __name__ == "__main__":
    rates = load_rates("rates_sample.csv")
    demo = Shipment("DEL", "SIN", "air", weight_kg=120, length_cm=100, width_cm=80, height_cm=60, pieces=2)
    print(quote(demo, rates))
    print(quote(Shipment("DEL", "LHR", "air", weight_kg=50), rates))
