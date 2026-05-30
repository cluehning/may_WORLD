"""
Real-data loaders for the Global Crisis & Conflict Map.

Sources used:
- Country list: datasets/country-codes
- Terrorism / violence proxy: World Bank PV.EST
- Humanitarian pressure: World Bank / IDMC
    - VC.IDP.TOCV = total displaced by conflict and violence
    - VC.IDP.NWCV = new displacement associated with conflict and violence
- Conflict: World Bank VC.BTL.DETH
- Refugee outflow: World Bank / UNHCR SM.POP.RHCR.EO
- Trade pressure: World Bank GC.TAX.IMPT.ZS
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd
import requests

COUNTRY_CODES_URL = (
    "https://raw.githubusercontent.com/datasets/country-codes/master/data/country-codes.csv"
)

WORLD_BANK_API = "https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=20000"

REQUEST_TIMEOUT = 30


# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------

def normalize(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    if s.dropna().empty:
        return pd.Series(np.nan, index=series.index)
    s_min = s.min()
    s_max = s.max()
    if pd.isna(s_min) or pd.isna(s_max) or s_min == s_max:
        return pd.Series(0.0, index=series.index)
    return (s - s_min) / (s_max - s_min)


def safe_log1p(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    return np.log1p(s.clip(lower=0))


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "GlobalCrisisConflictMap/1.0 (+Dash app)"
        }
    )
    return session


# ------------------------------------------------------------
# 1. Full country list (ISO3)
# ------------------------------------------------------------

def load_country_list() -> pd.DataFrame:
    df = pd.read_csv(COUNTRY_CODES_URL)

    df = df[
        [
            "ISO3166-1-Alpha-3",
            "official_name_en",
            "Region Name",
        ]
    ].rename(
        columns={
            "ISO3166-1-Alpha-3": "iso3",
            "official_name_en": "country",
            "Region Name": "region",
        }
    )

    df = df.dropna(subset=["iso3", "country"]).copy()
    df["iso3"] = df["iso3"].astype(str).str.upper().str.strip()
    df["region"] = df["region"].fillna("Unknown")

    # Keep one row per ISO3
    df = df.drop_duplicates(subset=["iso3"], keep="first").reset_index(drop=True)
    return df


# ------------------------------------------------------------
# 2. Generic World Bank helper
# ------------------------------------------------------------


def _fetch_world_bank_indicator(indicator_code: str) -> pd.DataFrame:
    url = WORLD_BANK_API.format(indicator=indicator_code)

    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    payload = resp.json()

    if isinstance(payload, dict) and "message" in payload:
        raise ValueError(f"World Bank API error for {indicator_code}: {payload}")

    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        raise ValueError(f"No usable data returned for {indicator_code}")

    records = payload[1]
    df = pd.DataFrame(records)

    if df.empty:
        raise ValueError(f"Empty dataset for {indicator_code}")

    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError(f"Unexpected World Bank response for {indicator_code}")

    records = payload[1]
    if not isinstance(records, list):
        raise ValueError(f"Unexpected record structure for {indicator_code}")

    df = pd.DataFrame(records)
    required = {"countryiso3code", "date", "value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for {indicator_code}: {missing}")

    df = df[["countryiso3code", "date", "value"]].copy()
    df = df.rename(columns={"countryiso3code": "iso3"})
    df["iso3"] = df["iso3"].astype(str).str.upper().str.strip()
    df["date"] = pd.to_numeric(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Keep only proper ISO3 rows; regional aggregates typically won't survive merge with country list,
    # but we filter obvious non-country blanks here.
    df = df[df["iso3"].str.len() == 3]
    df = df.dropna(subset=["date", "value"])

    # Latest non-null value per country
    df = (
        df.sort_values(["iso3", "date"], ascending=[True, False])
          .drop_duplicates(subset=["iso3"], keep="first")
          .reset_index(drop=True)
    )
    return df


# ------------------------------------------------------------
# 3. Terrorism / violence proxy
#    World Bank PV.EST: Political Stability and Absence of Violence/Terrorism
# ------------------------------------------------------------

def load_terrorism_data():
    """
    Proxy for violence / instability risk:
    Internally displaced persons (conflict & violence)
    """
    df = _fetch_world_bank_indicator("VC.IDP.NWCV")

    df = df.rename(columns={
        "value": "violence_displacement",
        "date": "terrorism_year"
    })

    # higher displacement = higher risk
    df["terrorism_score"] = normalize(safe_log1p(df["violence_displacement"]))

    return df[["iso3", "violence_displacement", "terrorism_year", "terrorism_score"]]


# ------------------------------------------------------------
# 4. Humanitarian pressure
#    Composite of:
#    - VC.IDP.TOCV = total displaced by conflict and violence
#    - VC.IDP.NWCV = new displacement associated with conflict and violence
# ------------------------------------------------------------


def load_humanitarian_data():
    """
    Uses ONLY working IDP indicator:
    VC.IDP.NWCV (new displacement due to conflict & violence)
    """

    df = _fetch_world_bank_indicator("VC.IDP.NWCV")

    df = df.rename(columns={
        "value": "idp_new_conflict",
        "date": "idp_year"
    })

    # use log to avoid extreme values dominating
    df["humanitarian_score"] = normalize(
        safe_log1p(df["idp_new_conflict"])
    )

    return df[
        [
            "iso3",
            "idp_new_conflict",
            "idp_year",
            "humanitarian_score",
        ]
    ]


# ------------------------------------------------------------
# 5. Armed conflict
#    VC.BTL.DETH = battle-related deaths
# ------------------------------------------------------------

def load_conflict_data() -> pd.DataFrame:
    df = _fetch_world_bank_indicator("VC.BTL.DETH").rename(
        columns={"value": "battle_deaths", "date": "conflict_year"}
    )
    df["conflict_score"] = normalize(safe_log1p(df["battle_deaths"]))
    return df[["iso3", "battle_deaths", "conflict_year", "conflict_score"]]


# ------------------------------------------------------------
# 6. Refugee outflow / displacement pressure
#    SM.POP.RHCR.EO = Refugees under UNHCR mandate by country/territory of origin
# ------------------------------------------------------------

def load_refugee_outflow_data() -> pd.DataFrame:
    df = _fetch_world_bank_indicator("SM.POP.RHCR.EO").rename(
        columns={"value": "refugees_origin", "date": "refugee_year"}
    )
    df["refugee_outflow_score"] = normalize(safe_log1p(df["refugees_origin"]))
    return df[["iso3", "refugees_origin", "refugee_year", "refugee_outflow_score"]]


# ------------------------------------------------------------
# 7. Trade / tariff pressure
#    GC.TAX.IMPT.ZS = customs + import duties (% of tax revenue)
# ------------------------------------------------------------

def load_tariff_data() -> pd.DataFrame:
    df = _fetch_world_bank_indicator("GC.TAX.IMPT.ZS").rename(
        columns={"value": "customs_duties_pct_tax", "date": "tariff_year"}
    )
    df["tariff_score"] = normalize(df["customs_duties_pct_tax"])
    return df[["iso3", "customs_duties_pct_tax", "tariff_year", "tariff_score"]]


# ------------------------------------------------------------
# Optional helper: build one combined dataframe from all sources
# ------------------------------------------------------------

def build_master_dataframe() -> pd.DataFrame:
    base = load_country_list()

    dfs = [
        load_terrorism_data(),
        load_humanitarian_data(),
        load_conflict_data(),
        load_refugee_outflow_data(),
        load_tariff_data(),
    ]

    df = base.copy()
    for d in dfs:
        df = df.merge(d, on="iso3", how="left")

    score_cols = [
        "terrorism_score",
        "humanitarian_score",
        "conflict_score",
        "refugee_outflow_score",
        "tariff_score",
    ]

    # Leave truly missing data as NaN first; app can decide how to render/fill.
    for col in score_cols:
        if col not in df.columns:
            df[col] = np.nan

    return df
