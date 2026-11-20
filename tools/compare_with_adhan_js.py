"""Cross-check our calculation against the independent `adhan` JS library
(batikata/adhan, widely used, includes the Egyptian method).

Run from repo root after `npm install` in tools/js-compare:
    PYTHONPATH=src python3 tools/compare_with_adhan_js.py

Prints per-prayer differences in minutes; PASS if all within 2 minutes.
"""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from isma_adhan.prayer_times import PRAYERS, PrayerTimeCalculator  # noqa: E402

JS = r"""
const adhan = require('adhan');
const coords = new adhan.Coordinates(30.0444, 31.2357);
const params = adhan.CalculationMethod.Egyptian();
params.madhab = adhan.Madhab.Shafi;
const out = {};
for (const d of ['2026-01-15','2026-04-15','2026-07-15','2026-10-15','2026-11-20','2026-06-21','2026-12-21']) {
  const [y,m,dd] = d.split('-').map(Number);
  const t = new adhan.PrayerTimes(coords, new Date(y, m-1, dd, 12, 0, 0), params);
  out[d] = {
    fajr: t.fajr, sunrise: t.sunrise, dhuhr: t.dhuhr,
    asr: t.asr, maghrib: t.maghrib, isha: t.isha
  };
}
console.log(JSON.stringify(out));
"""


def main() -> int:
    import os

    env = dict(os.environ, TZ="Africa/Cairo")  # the JS lib uses the system timezone
    proc = subprocess.run(
        ["node", "-e", JS],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent / "js-compare",
        env=env,
    )
    if proc.returncode != 0:
        print(proc.stderr)
        return 1
    ref = json.loads(proc.stdout)
    calc = PrayerTimeCalculator(30.0444, 31.2357)
    worst = 0.0
    ok = True
    for d, ref_times in ref.items():
        y, m, dd = map(int, d.split("-"))
        ours = calc.for_date(date(y, m, dd)).times
        for p in PRAYERS:
            # the JS lib emits UTC ISO strings; compare absolute instants
            ref_dt = ref_times[p].replace("Z", "+00:00")
            from datetime import datetime

            ref_dt = datetime.fromisoformat(ref_dt)
            diff = abs((ours[p] - ref_dt).total_seconds()) / 60.0
            worst = max(worst, diff)
            flag = "" if diff <= 2 else "  <-- OFF"
            if diff > 2:
                ok = False
            print(f"{d} {p:8s} ours={ours[p].strftime('%H:%M')} ref={ref_dt.astimezone(ours[p].tzinfo).strftime('%H:%M')} diff={diff:.1f} min{flag}")
    print(f"\nworst diff: {worst:.1f} min -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
