from pathlib import Path

from quote_engine import Shipment, load_rates, quote

RATES = load_rates(Path(__file__).resolve().parent.parent / "rates_sample.csv")


def test_air_uses_volumetric_when_larger():
    # volumetric = 100*80*60*2/6000 = 160 kg, which is more than actual 120 kg
    r = quote(Shipment("DEL", "SIN", "air", 120, 100, 80, 60, 2), RATES)
    assert r["billable_kg"] == 160.0
    assert r["amount"] == 672.0  # 160 * 4.20


def test_air_uses_actual_when_larger():
    r = quote(Shipment("DEL", "DXB", "air", 200, 10, 10, 10, 1), RATES)
    assert r["billable_kg"] == 200.0


def test_road_min_charge_applies():
    r = quote(Shipment("DEL", "KTM", "road", 10), RATES)
    assert r["amount"] == 25.0  # 10 * 0.35 = 3.5, so the minimum 25 applies


def test_fcl_is_flat_per_container():
    r = quote(Shipment("INNSA", "CNSHA", "fcl40", 9999, 1, 1, 1, 50), RATES)
    assert r["amount"] == 1650.0


def test_no_rate_is_handled_not_crashed():
    r = quote(Shipment("DEL", "LHR", "air", 50), RATES)
    assert r["status"] == "no_rate"


def test_invalid_inputs_rejected():
    for bad in [Shipment("DEL", "SIN", "ship", 10), Shipment("DEL", "SIN", "air", -1), Shipment("DEL", "SIN", "air", 1, pieces=0)]:
        try:
            quote(bad, RATES)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {bad}")
