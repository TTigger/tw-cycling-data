# -*- coding: utf-8 -*-
import irunner_crawl


def test_event_date_from_page_header():
    html = ("<h1 class='h3'>2026 Gravel Fundo</h1><div class='mt-2'>"
            "<i class='fa fa-calendar me-2'></i>2026/01/25</div>")
    assert irunner_crawl.event_date(html) == "2026-01-25"
    assert irunner_crawl.event_date("<p>no date</p>") is None
