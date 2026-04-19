"""Test 06: Cross-table consistency."""

import os
import pandas as pd

from src.utils import OUTPUT_DIR


def _load(name):
    return pd.read_csv(os.path.join(OUTPUT_DIR, name))


def test_table3a_has_25_rows():
    assert len(_load("table_3a.csv")) == 25


def test_table3b_has_25_rows():
    assert len(_load("table_3b.csv")) == 25


def test_table3a_3b_same_countries():
    t3a = _load("table_3a.csv")
    t3b = _load("table_3b.csv")
    assert list(t3a["Country"]) == list(t3b["Country"])


def test_tableA1_has_85_rows():
    assert len(_load("table_a1.csv")) == 85


def test_tableA2_has_85_rows():
    assert len(_load("table_a2.csv")) == 85


def test_table3a_rank3_equals_rank4():
    t3a = _load("table_3a.csv")
    assert (t3a["Rank_3"] == t3a["Rank_4"]).all()


def test_delta_computation():
    t3a = _load("table_3a.csv")
    for _, row in t3a.iterrows():
        expected = row["Rank_1"] - row["Rank_3"]
        assert row["Delta"] == expected, f"{row['Country']}: Delta mismatch"
