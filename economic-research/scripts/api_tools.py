#!/usr/bin/env python3
"""
Economic Research Agent — API Tools for querying US government data sources.
Each function fetches data from a free public API and returns structured JSON.

Usage:
  python api_tools.py fred --cities "Austin,Raleigh" --metric unemployment
  python api_tools.py bls --cities "Austin,Raleigh" --metric wages
  python api_tools.py census --states "Texas,North Carolina" --metric education
  python api_tools.py hud --cities "Austin,Raleigh" --metric fmr
  python api_tools.py eia --states "Texas,North Carolina" --metric electricity
  python api_tools.py tax --states "Texas,North Carolina"
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime


def _api_get(url: str, headers: dict = None) -> dict:
    """Simple GET request returning JSON."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}


# ============================================================
# FRED — Federal Reserve Economic Data (St. Louis Fed)
# ============================================================

# Common MSA codes for unemployment series
FRED_MSA_CODES = {
    "Austin": "AUST448", "Raleigh": "RALE937", "San Francisco": "SANF806",
    "Dallas": "DALL148", "Denver": "DENN508", "Seattle": "SEAT653",
    "Atlanta": "ATLA013", "Charlotte": "CHAL837", "Phoenix": "PHOE429",
    "Nashville": "NASH947", "Portland": "PORT741", "Boston": "BOST725",
    "Chicago": "CHIC917", "Houston": "HOUS448", "Miami": "MIAM412",
    "New York": "NEWY636", "Los Angeles": "LOSA706", "Washington": "WASH511",
    "Minneapolis": "MINN927", "Detroit": "DETR426", "Tampa": "TAMP412",
    "Columbus": "COLU839", "Indianapolis": "INDI918", "San Antonio": "SANA448",
    "Pittsburgh": "PITT942", "Cleveland": "CLEV839", "Kansas City": "KANS729",
    "Salt Lake City": "SALT849", "Richmond": "RICH951", "Bellevue": "SEAT653",
}

FRED_SERIES_SUFFIXES = {
    "unemployment": "UR",
    "gdp": "NGMP",  # Nominal GDP
    "building_permits": "BP1FH",
}


def fred_query(cities: list[str], metric: str = "unemployment") -> list[dict]:
    """Fetch regional macro stats from FRED API."""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        return [{"error": "FRED_API_KEY not set. Register at: https://fredaccount.stlouisfed.org/login/secure/apikeys"}]

    suffix = FRED_SERIES_SUFFIXES.get(metric, "UR")
    results = []

    for city in cities:
        city_clean = city.split(",")[0].strip()
        code = FRED_MSA_CODES.get(city_clean)

        if not code:
            # Search FRED for the series
            search_url = f"https://api.stlouisfed.org/fred/series/search?search_text={urllib.parse.quote(city_clean + ' ' + metric)}&api_key={api_key}&file_type=json&limit=3"
            search_data = _api_get(search_url)
            if "seriess" in search_data and search_data["seriess"]:
                series_id = search_data["seriess"][0]["id"]
            else:
                results.append({"city": city_clean, "error": "No series found"})
                continue
        else:
            series_id = f"{code}{suffix}"

        # Fetch observations
        obs_url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&limit=13"
        obs_data = _api_get(obs_url)

        if "observations" in obs_data and obs_data["observations"]:
            obs = obs_data["observations"]
            latest = obs[0]
            historical = [{"date": o["date"], "value": o["value"]} for o in obs[:12]]

            results.append({
                "city": city_clean,
                "metric": metric,
                "latest_value": latest["value"],
                "latest_date": latest["date"],
                "historical": historical,
                "series_id": series_id,
                "source": f"FRED API (https://api.stlouisfed.org/fred/series/observations?series_id={series_id})"
            })
        else:
            results.append({"city": city_clean, "error": f"No data for series {series_id}", "api_response": obs_data.get("error", "")})

    return results


# ============================================================
# BLS — Bureau of Labor Statistics
# ============================================================

# State FIPS codes for BLS queries
STATE_FIPS = {
    "Alabama": "01", "Alaska": "02", "Arizona": "04", "Arkansas": "05",
    "California": "06", "Colorado": "08", "Connecticut": "09", "Delaware": "10",
    "Florida": "12", "Georgia": "13", "Hawaii": "15", "Idaho": "16",
    "Illinois": "17", "Indiana": "18", "Iowa": "19", "Kansas": "20",
    "Kentucky": "21", "Louisiana": "22", "Maine": "23", "Maryland": "24",
    "Massachusetts": "25", "Michigan": "26", "Minnesota": "27", "Mississippi": "28",
    "Missouri": "29", "Montana": "30", "Nebraska": "31", "Nevada": "32",
    "New Hampshire": "33", "New Jersey": "34", "New Mexico": "35", "New York": "36",
    "North Carolina": "37", "North Dakota": "38", "Ohio": "39", "Oklahoma": "40",
    "Oregon": "41", "Pennsylvania": "42", "Rhode Island": "44", "South Carolina": "45",
    "South Dakota": "46", "Tennessee": "47", "Texas": "48", "Utah": "49",
    "Vermont": "50", "Virginia": "51", "Washington": "53", "West Virginia": "54",
    "Wisconsin": "55", "Wyoming": "56",
}


def bls_query(cities: list[str] = None, states: list[str] = None, metric: str = "wages") -> list[dict]:
    """Fetch BLS data — wages, employment, labor force."""
    api_key = os.getenv("BLS_API_KEY", "")  # BLS works without key (10 queries/day limit)

    headers = {"Content-Type": "application/json"}
    base_url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

    # For state-level queries, use LAUS (Local Area Unemployment Statistics)
    regions = states or cities or []
    results = []

    for region in regions:
        region_clean = region.strip()
        fips = STATE_FIPS.get(region_clean)

        if not fips:
            results.append({"region": region_clean, "error": "State not found in FIPS lookup"})
            continue

        # LAUS series: LASST{FIPS}0000000000003 = unemployment rate
        # OEWS series for wages: OEUS{FIPS}00000000000000{measure}
        if metric == "unemployment":
            series_id = f"LASST{fips}0000000000003"
        elif metric == "wages":
            # All occupations, all industries, median hourly wage
            series_id = f"OEUS{fips}000000000000000413"
        elif metric == "labor_force":
            series_id = f"LASST{fips}0000000000006"
        else:
            series_id = f"LASST{fips}0000000000003"

        payload = json.dumps({
            "seriesid": [series_id],
            "startyear": str(datetime.now().year - 2),
            "endyear": str(datetime.now().year),
            "registrationkey": api_key
        }).encode()

        req = urllib.request.Request(base_url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())

            if data.get("Results", {}).get("series"):
                series_data = data["Results"]["series"][0]["data"]
                if series_data:
                    latest = series_data[0]
                    results.append({
                        "region": region_clean,
                        "metric": metric,
                        "latest_value": latest["value"],
                        "latest_period": f"{latest['year']}-{latest['period']}",
                        "series_id": series_id,
                        "source": f"BLS API (https://api.bls.gov/publicAPI/v2/timeseries/data/{series_id})"
                    })
                else:
                    results.append({"region": region_clean, "error": "No data returned"})
            else:
                results.append({"region": region_clean, "error": "BLS API returned no series", "message": data.get("message", "")})
        except Exception as e:
            results.append({"region": region_clean, "error": str(e)})

    return results


# ============================================================
# Census Bureau — Education & Demographics
# ============================================================

def census_query(states: list[str], metric: str = "education") -> list[dict]:
    """Fetch Census ACS data — education, demographics."""
    api_key = os.getenv("CENSUS_API_KEY")
    if not api_key:
        return [{"error": "CENSUS_API_KEY not set. Register at: https://api.census.gov/data/key_signup.html"}]

    results = []
    # ACS 5-Year estimates — education attainment
    # B15003: Educational Attainment for Population 25+
    # _001E = total, _022E = bachelor's, _023E = master's, _025E = doctorate
    variables = "B15003_001E,B15003_022E,B15003_023E,B15003_025E"

    for state in states:
        state_clean = state.strip()
        fips = STATE_FIPS.get(state_clean)
        if not fips:
            results.append({"state": state_clean, "error": "State not found"})
            continue

        url = f"https://api.census.gov/data/2022/acs/acs5?get={variables}&for=state:{fips}&key={api_key}"
        data = _api_get(url)

        if isinstance(data, list) and len(data) > 1:
            row = data[1]
            total = int(row[0]) if row[0] else 1
            bachelors = int(row[1]) if row[1] else 0
            masters = int(row[2]) if row[2] else 0
            doctorate = int(row[3]) if row[3] else 0

            results.append({
                "state": state_clean,
                "total_25_plus": total,
                "bachelors": bachelors,
                "masters": masters,
                "doctorate": doctorate,
                "bachelors_pct": f"{bachelors/total*100:.1f}%",
                "advanced_degree_pct": f"{(masters+doctorate)/total*100:.1f}%",
                "source": f"Census ACS 5-Year 2022 (https://api.census.gov/data/2022/acs/acs5)"
            })
        else:
            results.append({"state": state_clean, "error": "No Census data returned", "raw": data})

    return results


# ============================================================
# HUD — Housing & Urban Development
# ============================================================

def hud_query(cities: list[str] = None, states: list[str] = None, metric: str = "fmr") -> list[dict]:
    """Fetch HUD Fair Market Rent or income limits."""
    api_key = os.getenv("HUD_API_KEY")
    if not api_key:
        return [{"error": "HUD_API_KEY not set. Register at: https://www.huduser.gov/portal/dataset/fmr-api.html"}]

    headers = {"Authorization": f"Bearer {api_key}"}
    results = []
    regions = states or []

    for region in regions:
        region_clean = region.strip()
        fips = STATE_FIPS.get(region_clean)
        if not fips:
            results.append({"region": region_clean, "error": "State not found"})
            continue

        if metric == "fmr":
            url = f"https://www.huduser.gov/hudapi/public/fmr/statedata/{fips}"
        elif metric == "income_limits":
            url = f"https://www.huduser.gov/hudapi/public/il/statedata/{fips}"
        else:
            url = f"https://www.huduser.gov/hudapi/public/fmr/statedata/{fips}"

        data = _api_get(url, headers=headers)

        if "error" not in data:
            results.append({
                "region": region_clean,
                "metric": metric,
                "data": data.get("data", data),
                "source": f"HUD API ({url})"
            })
        else:
            results.append({"region": region_clean, "error": data.get("error", "Unknown error")})

    return results


# ============================================================
# EIA — Energy Information Administration
# ============================================================

def eia_query(states: list[str], metric: str = "electricity") -> list[dict]:
    """Fetch EIA state electricity rates."""
    api_key = os.getenv("EIA_API_KEY")
    if not api_key:
        return [{"error": "EIA_API_KEY not set. Register at: https://www.eia.gov/opendata/register.php"}]

    results = []
    # State electricity price series: ELEC.PRICE.{STATE}-ALL.M
    state_abbrevs = {
        "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
        "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
        "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
        "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
        "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
        "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
        "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
        "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
        "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
        "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
        "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
        "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
        "Wisconsin": "WI", "Wyoming": "WY",
    }

    for state in states:
        state_clean = state.strip()
        abbrev = state_abbrevs.get(state_clean)
        if not abbrev:
            results.append({"state": state_clean, "error": "State abbreviation not found"})
            continue

        # EIA API v2
        url = f"https://api.eia.gov/v2/electricity/retail-sales/data/?api_key={api_key}&frequency=monthly&data[0]=price&facets[stateid][]={abbrev}&sort[0][column]=period&sort[0][direction]=desc&length=12"
        data = _api_get(url)

        if "response" in data and "data" in data["response"]:
            rows = data["response"]["data"]
            if rows:
                latest = rows[0]
                results.append({
                    "state": state_clean,
                    "metric": "electricity_price_cents_per_kwh",
                    "latest_value": latest.get("price"),
                    "latest_period": latest.get("period"),
                    "sector": latest.get("sectorName", "All"),
                    "historical": [{"period": r["period"], "price": r.get("price")} for r in rows[:6]],
                    "source": f"EIA API v2 (https://api.eia.gov/v2/electricity/retail-sales/)"
                })
            else:
                results.append({"state": state_clean, "error": "No EIA data returned"})
        else:
            results.append({"state": state_clean, "error": data.get("error", "Unknown EIA error")})

    return results


# ============================================================
# Tax Foundation — State Tax Rates (web scraping fallback)
# ============================================================

# Hardcoded 2024 rates from Tax Foundation (updated annually)
STATE_TAX_RATES = {
    "Alabama": {"corporate": 6.5, "individual_top": 5.0}, "Alaska": {"corporate": 9.4, "individual_top": 0},
    "Arizona": {"corporate": 4.9, "individual_top": 2.5}, "Arkansas": {"corporate": 5.3, "individual_top": 4.4},
    "California": {"corporate": 8.84, "individual_top": 13.3}, "Colorado": {"corporate": 4.4, "individual_top": 4.4},
    "Connecticut": {"corporate": 7.5, "individual_top": 6.99}, "Delaware": {"corporate": 8.7, "individual_top": 6.6},
    "Florida": {"corporate": 5.5, "individual_top": 0}, "Georgia": {"corporate": 5.75, "individual_top": 5.49},
    "Idaho": {"corporate": 5.8, "individual_top": 5.8}, "Illinois": {"corporate": 9.5, "individual_top": 4.95},
    "Indiana": {"corporate": 4.9, "individual_top": 3.05}, "Iowa": {"corporate": 8.4, "individual_top": 5.7},
    "Kansas": {"corporate": 4.0, "individual_top": 5.7}, "Kentucky": {"corporate": 5.0, "individual_top": 4.0},
    "Louisiana": {"corporate": 7.5, "individual_top": 4.25}, "Maryland": {"corporate": 8.25, "individual_top": 5.75},
    "Massachusetts": {"corporate": 8.0, "individual_top": 9.0}, "Michigan": {"corporate": 6.0, "individual_top": 4.25},
    "Minnesota": {"corporate": 9.8, "individual_top": 9.85}, "Mississippi": {"corporate": 5.0, "individual_top": 5.0},
    "Missouri": {"corporate": 4.0, "individual_top": 4.8}, "Nevada": {"corporate": 0, "individual_top": 0},
    "New Hampshire": {"corporate": 7.5, "individual_top": 0}, "New Jersey": {"corporate": 11.5, "individual_top": 10.75},
    "New York": {"corporate": 7.25, "individual_top": 10.9}, "North Carolina": {"corporate": 2.5, "individual_top": 4.5},
    "Ohio": {"corporate": 0, "individual_top": 3.5}, "Oregon": {"corporate": 7.6, "individual_top": 9.9},
    "Pennsylvania": {"corporate": 8.99, "individual_top": 3.07}, "South Carolina": {"corporate": 5.0, "individual_top": 6.4},
    "Tennessee": {"corporate": 6.5, "individual_top": 0}, "Texas": {"corporate": 0, "individual_top": 0},
    "Utah": {"corporate": 4.65, "individual_top": 4.65}, "Virginia": {"corporate": 6.0, "individual_top": 5.75},
    "Washington": {"corporate": 0, "individual_top": 0}, "Wisconsin": {"corporate": 7.9, "individual_top": 7.65},
}


def tax_query(states: list[str]) -> list[dict]:
    """Fetch state tax rates from local lookup (Tax Foundation data)."""
    results = []
    for state in states:
        state_clean = state.strip()
        rates = STATE_TAX_RATES.get(state_clean)
        if rates:
            results.append({
                "state": state_clean,
                "corporate_tax_rate": f"{rates['corporate']}%",
                "individual_top_rate": f"{rates['individual_top']}%",
                "source": "Tax Foundation 2024 State Tax Data (https://taxfoundation.org/data/all/state/)"
            })
        else:
            results.append({"state": state_clean, "error": "State not in tax lookup table"})
    return results


# ============================================================
# CLI Interface
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Economic Research API Tools")
    parser.add_argument("source", choices=["fred", "bls", "census", "hud", "eia", "tax"],
                        help="Data source to query")
    parser.add_argument("--cities", type=str, default="", help="Comma-separated city names")
    parser.add_argument("--states", type=str, default="", help="Comma-separated state names")
    parser.add_argument("--metric", type=str, default="", help="Metric to fetch")

    args = parser.parse_args()

    cities = [c.strip() for c in args.cities.split(",") if c.strip()] if args.cities else []
    states = [s.strip() for s in args.states.split(",") if s.strip()] if args.states else []

    if args.source == "fred":
        results = fred_query(cities, args.metric or "unemployment")
    elif args.source == "bls":
        results = bls_query(cities=cities, states=states, metric=args.metric or "wages")
    elif args.source == "census":
        results = census_query(states, args.metric or "education")
    elif args.source == "hud":
        results = hud_query(cities=cities, states=states, metric=args.metric or "fmr")
    elif args.source == "eia":
        results = eia_query(states, args.metric or "electricity")
    elif args.source == "tax":
        results = tax_query(states)
    else:
        results = [{"error": f"Unknown source: {args.source}"}]

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
