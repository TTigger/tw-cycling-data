# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import merge


def test_keeps_dnf_dns_rows_without_time():
    assert merge.should_drop_zero_time({"status": "DNF", "finish_seconds": None}) is False
    assert merge.should_drop_zero_time({"status": "DNS", "finish_seconds": 0}) is False


def test_drops_zero_time_noise_without_status():
    assert merge.should_drop_zero_time({"status": None, "finish_seconds": 0}) is True
    assert merge.should_drop_zero_time({"status": None, "finish_seconds": -5}) is True


def test_keeps_normal_finisher():
    assert merge.should_drop_zero_time({"status": "FIN", "finish_seconds": 2858}) is False
    assert merge.should_drop_zero_time({"status": None, "finish_seconds": 2858}) is False


def test_criterium_prefix_discovered():
    assert "criterium_" in merge.SOURCE_PREFIXES
