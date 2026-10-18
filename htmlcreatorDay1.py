"""
Day 1 (opening night, Oct 20 2026) runner.

Runs htmlcreator.py with "today" pinned to OPENING_NIGHT so index.html shows
opening night's games and odds. The daily GitHub Action runs htmlcreator.py
directly from then on.
"""
import datetime
import runpy

import pandas  # noqa: F401 - load pandas' C extensions against the real date class before patching

OPENING_NIGHT = datetime.date(2026, 10, 20)

class OpeningNightDate(datetime.date):
    @classmethod
    def today(cls):
        return cls(OPENING_NIGHT.year, OPENING_NIGHT.month, OPENING_NIGHT.day)

# htmlcreator.py does `from datetime import date`, so it picks up the pinned date
datetime.date = OpeningNightDate

runpy.run_path('htmlcreator.py', run_name='__main__')
