# -*- coding: utf-8 -*-
"""cycling_generic: layout-tolerant rows from 中華民國自由車協會 result PDFs.
Names below are placeholders, not riders."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import cycling_generic as G

TITLE = "113年全國自由車公路錦標賽暨菁英排名賽"


def test_start_finish_columns_pick_the_result_time():
    page = [TITLE, "女子青年組 11.2公里個人計時賽", "公告： R1",
            "名次 比賽號碼 姓名 參賽證號 隊名 出發時間 終點時間 加秒 成績 時速 備註",
            "1 304 王小明 10139673112 新社高中 00:02:00 00:18:49.375 00 16:49.375 39.95 km/hr",
            "DNF 316 李小華 10146227985 屏東自由車隊 -"]
    rows = G.parse_dedup([page])
    assert rows[0]["secs"] == 16 * 60 + 49.375 and rows[0]["rank"] == 1
    assert rows[0]["uci"] == "10139673112" and rows[0]["team"] == "新社高中"
    assert rows[0]["category"] == "女子青年組" and rows[0]["gender"] == "F"
    assert rows[1]["status"] == "DNF" and rows[1]["secs"] is None


def test_summary_and_combined_time_pages_are_skipped():
    summary = [TITLE, "總成績表", "姓名 名次 第1名 第2名", "1 2 王小明 陳大文 04:05:13"]
    combined = [TITLE, "男子菁英個人計時及公路賽成績總和", "公告： R6",
                "序號 比賽號碼 姓名 參賽證號 隊名 計時賽成績 公路賽成績 成績總和",
                "1 029 王小明 10005601429 某車隊 00:54:09.193 04:09:07 05:03:16.193"]
    assert G.parse_dedup([summary, combined]) == []


def test_bib_on_its_own_line_and_semicolon_typo():
    page = ["112年全國自由車公路國手選拔賽", "女子菁英組 92公里個人公路賽", "公告： 6",
            "名次 比賽號碼 姓名 參賽證號 隊名 成績", "210", "1 王小美 R112047 某車隊 02:50;22.54"]
    r = G.parse_dedup([page])[0]
    assert (r["rank"], r["bib"], r["time"]) == (1, "210", "02:50:22.54")


def test_glued_overlay_text_is_not_taken_as_a_time():
    page = ["108年全國自由車公路錦標賽暨菁英選拔賽", "男子菁英組 118.9公里個人公路賽", "公告:11",
            "名次 選手號碼選手姓名 英文姓 英文名 UCIID 單位 成績 檢核時間 加秒 時速",
            "40 111 王小明 WANG 15:46.310083232953 個人 2:55:30.490 1:33:02.423 0 40.648"]
    r = G.parse_dedup([page])[0]
    assert r["time"] == "02:55:30.490" and r["team"] == "個人"


def test_stage_time_and_unranked_lap_rows():
    stage = ["113 全國中等學校錦標賽", "Stage 2 賽程 1 距離 3.1 km 開賽時間 8:36:09", "組別 國小四男 日期 6月10日",
             "Rank No. Name TEAM Finish Time Gap 單站積分 上期積分 累計積分",
             "1 306 王小明 某國小 8:42:05.85 05m 56.69s + 00m 0.00s 19 19 38"]
    r = G.parse_dedup([stage])[0]
    assert r["secs"] == 5 * 60 + 56.69 and r["event"] == "Stage 2 3.1km" and r["gender"] == "M"
    laps = ["107年全國自由車少年公路錦標賽", "男子15歲組36.8公里公路賽",
            "排名 號碼＼BIB姓名＼Name 團隊＼Team 成績 Lap 1 Lap 2 時速 備註",
            "0001 0059 王小明 某車隊 001:04:34.81 000:19:54.94 000:15:40.56 34.19",
            "0016 陳大文 某國中 000:09:07.47"]
    rows = G.parse_dedup([laps])
    assert len(rows) == 1 and rows[0]["category"] == "男子15歲組"


def test_selection_rerank_pages_skipped():
    page = ["108年全國自由車公路錦標賽暨菁英選拔賽", "男子菁英組(選拔) 30公里個人計時賽", "公告:1~2",
            "名次 選手號碼選手姓名 英文姓 英文名 UCIID 單位 成績",
            "1 053 王小明 WANG Xiao Ming 10005601429 個人 42:23.125"]
    assert G.parse_dedup([page]) == []
