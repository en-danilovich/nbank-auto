"""
Generates an importable Kibana 7.17 saved-objects NDJSON dashboard for the
NBank log-analytics homework (Kibana-only questions: Q11, Q12, Q16, Q17).

Self-contained: it ships its own data view (title "filebeat-*") with the
`username` and `amount` runtime fields baked in, so no manual field setup is
needed before import.

Run:  python _build_kibana_dashboard.py
Out:  kibana-nbank-dashboard.ndjson  (Stack Management -> Saved Objects -> Import)
"""
import json
import os

IP_ID = "nbank-logs"  # single consolidated data-view id

USERNAME_SCRIPT = (
    "String m = params._source.message;\n"
    "if (m != null) {\n"
    "  def g = grok(\"user '%{DATA:u}'\").extract(m);\n"
    "  if (g != null) { emit(g.u); }\n"
    "  else {\n"
    "    def g2 = grok(\"user='%{DATA:u}'\").extract(m);\n"
    "    if (g2 != null) { emit(g2.u); }\n"
    "    else {\n"
    # "Unauthorized transfer/deposit access by 'X'": username after "by '"
    "      def g3 = grok(\"by '%{DATA:u}'\").extract(m);\n"
    "      if (g3 != null) { emit(g3.u); }\n"
    "    }\n"
    "  }\n"
    "}"
)

AMOUNT_SCRIPT = (
    "String m = params._source.message;\n"
    "if (m != null) {\n"
    "  def g = grok(\"amount=%{NUMBER:a}\").extract(m);\n"
    "  if (g != null) { emit(Double.parseDouble(g.a)); }\n"
    "}"
)

RUNTIME_FIELD_MAP = {
    "username": {"type": "keyword", "script": {"source": USERNAME_SCRIPT}},
    "amount": {"type": "double", "script": {"source": AMOUNT_SCRIPT}},
}


def search_source(query=""):
    return json.dumps({
        "query": {"query": query, "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    })


def metric_avg(vid, title, field, query):
    vis_state = {
        "title": title,
        "type": "metric",
        "aggs": [
            {"id": "1", "enabled": True, "type": "avg", "schema": "metric",
             "params": {"field": field}},
        ],
        "params": {
            "addTooltip": True, "addLegend": False, "type": "metric",
            "metric": {
                "percentageMode": False, "useRanges": False,
                "colorSchema": "Green to Red", "metricColorMode": "None",
                "colorsRange": [{"from": 0, "to": 10000}],
                "labels": {"show": True}, "invertColors": False,
                "style": {"bgFill": "#000", "bgColor": False, "labelColor": False,
                          "subText": "", "fontSize": 36},
            },
        },
    }
    return viz(vid, title, vis_state, query)


def metric_count(vid, title, query):
    vis_state = {
        "title": title,
        "type": "metric",
        "aggs": [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
        ],
        "params": {
            "addTooltip": True, "addLegend": False, "type": "metric",
            "metric": {
                "percentageMode": False, "useRanges": False,
                "colorSchema": "Green to Red", "metricColorMode": "None",
                "colorsRange": [{"from": 0, "to": 10000}],
                "labels": {"show": True}, "invertColors": False,
                "style": {"bgFill": "#000", "bgColor": False, "labelColor": False,
                          "subText": "", "fontSize": 36},
            },
        },
    }
    return viz(vid, title, vis_state, query)


def table_terms(vid, title, field, query, size=10):
    vis_state = {
        "title": title,
        "type": "table",
        "aggs": [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {"id": "2", "enabled": True, "type": "terms", "schema": "bucket",
             "params": {"field": field, "orderBy": "1", "order": "desc",
                        "size": size, "otherBucket": False, "missingBucket": False,
                        "missingBucketLabel": "Missing"}},
        ],
        "params": {
            "perPage": 10, "showPartialRows": False, "showMetricsAtAllLevels": False,
            "showTotal": False, "totalFunc": "sum", "percentageCol": "",
            "sort": {"columnIndex": None, "direction": None},
        },
    }
    return viz(vid, title, vis_state, query)


def table_filters(vid, title, filters):
    """filters: list of (label, kql)"""
    vis_state = {
        "title": title,
        "type": "table",
        "aggs": [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {"id": "2", "enabled": True, "type": "filters", "schema": "bucket",
             "params": {"filters": [
                 {"input": {"query": kql, "language": "kuery"}, "label": label}
                 for (label, kql) in filters
             ]}},
        ],
        "params": {
            "perPage": 10, "showPartialRows": False, "showMetricsAtAllLevels": False,
            "showTotal": False, "totalFunc": "sum", "percentageCol": "",
            "sort": {"columnIndex": 1, "direction": "desc"},
        },
    }
    return viz(vid, title, vis_state, "")


def table_datehist(vid, title, query, interval="h"):
    vis_state = {
        "title": title,
        "type": "table",
        "aggs": [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {"id": "2", "enabled": True, "type": "date_histogram", "schema": "bucket",
             "params": {"field": "@timestamp", "useNormalizedEsInterval": True,
                        "interval": interval, "drop_partials": False,
                        "min_doc_count": 1, "extended_bounds": {}}},
        ],
        "params": {
            "perPage": 24, "showPartialRows": False, "showMetricsAtAllLevels": False,
            "showTotal": True, "totalFunc": "sum", "percentageCol": "",
            "sort": {"columnIndex": None, "direction": None},
        },
    }
    return viz(vid, title, vis_state, query)


def markdown(vid, title, md):
    vis_state = {
        "title": title,
        "type": "markdown",
        "aggs": [],
        "params": {"fontSize": 12, "openLinksInNewTab": True, "markdown": md},
    }
    # markdown has no index reference
    return {
        "id": vid,
        "type": "visualization",
        "attributes": {
            "title": title,
            "visState": json.dumps(vis_state),
            "uiStateJSON": "{}",
            "description": "",
            "version": 1,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"}, "filter": []})
            },
        },
        "references": [],
    }


def viz(vid, title, vis_state, query):
    return {
        "id": vid,
        "type": "visualization",
        "attributes": {
            "title": title,
            "visState": json.dumps(vis_state),
            "uiStateJSON": "{}",
            "description": "",
            "version": 1,
            "kibanaSavedObjectMeta": {"searchSourceJSON": search_source(query)},
        },
        "references": [
            {"name": "kibanaSavedObjectMeta.searchSourceJSON.index",
             "type": "index-pattern", "id": IP_ID},
        ],
    }


# ---- data view (index pattern) with runtime fields baked in ----------------
index_pattern = {
    "id": IP_ID,
    "type": "index-pattern",
    "attributes": {
        "title": "filebeat-*",
        "timeFieldName": "@timestamp",
        "fields": "[]",
        "runtimeFieldMap": json.dumps(RUNTIME_FIELD_MAP),
    },
    "references": [],
}

# ---- visualizations --------------------------------------------------------
visualizations = [
    metric_avg("nbank-avg-transfer-success", "Q16 — Средняя сумма успешного перевода",
               "amount", 'message : "Transfer successful"'),
    metric_avg("nbank-avg-transfer-request", "Q16 — Средняя сумма (все запросы перевода)",
               "amount", 'message : "Transfer request"'),
    metric_count("nbank-cnt-transfer-failed", "Кол-во неуспешных переводов",
                 'message : "Transfer failed"'),
    table_terms("nbank-top-logins", "Q11 — Топ пользователей по логинам",
                "username", 'message : "Login successful for user"'),
    table_terms("nbank-top-profile", "Q12 — Топ по обновлениям профиля",
                "username", 'message : "Profile updated for user"'),
    table_terms("nbank-top-active", "Q16 — Самые активные пользователи (по всем событиям)",
                "username", ""),
    table_filters("nbank-error-reasons", "Q16 — Причины ошибок (частота)", [
        ("Invalid name format", 'message : "Invalid name format from user"'),
        ("Transfer failed (insufficient/invalid)", 'message : "Transfer failed"'),
        ("Unauthorized transfer", 'message : "Unauthorized transfer access by"'),
    ]),
    table_terms("nbank-top-unauth", "Q17 — Пользователи с ошибками перевода (unauthorized)",
                "username", 'message : "Unauthorized transfer access by"'),
    # ---- Q18: ошибки во времени (есть ли >3 подряд) -----------------------
    table_datehist("nbank-q18-errors", "Q18 — Ошибки во времени (по часам)",
                   'error.message : * or message : "Exception"', interval="h"),
    markdown("nbank-q18-note", "Q18 — Вывод", (
        "### Q18 — Падало ли создание пользователя >3 раз подряд?\n\n"
        "**Нет.** Отдельной лог-строки \"создание пользователя упало\" в приложении нет "
        "(создание логируется как `Admin request: create user 'X'`).\n\n"
        "Единственные ошибки в логах — это **стартовые** ошибки подключения к БД "
        "(`Connection to postgres:5432 refused`, Flyway/Hikari при загрузке контекста), "
        "т.е. ретраи на старте пода, а **не** падения отдельных запросов на создание.\n\n"
        "Соседняя таблица показывает ошибки по часам — кластеров из >3 подряд "
        "падений создания пользователя нет."
    )),
    # ---- Q19: метрики vs логи ---------------------------------------------
    metric_count("nbank-q19-logins-log", "Q19 — Логинов в ЛОГАХ (Login successful)",
                 'message : "Login successful for user"'),
    markdown("nbank-q19-note", "Q19 — Сопоставление метрик и логов", (
        "### Q19 — Есть ли рост, не отражённый в логах?\n\n"
        "Сравни **одно и то же событие** в двух системах за один период:\n\n"
        "- **Grafana (сырой счётчик):** `sum(user_login_total)` — считает **с момента "
        "последнего перезапуска** пода backend.\n"
        "- **Kibana (логи):** число строк `Login successful for user` (см. панель слева) — "
        "**сохраняются между перезапусками**.\n\n"
        "**Они не совпадают:** счётчик Prometheus **сбросился** при рестарте "
        "(`restartCount=1`), поэтому его сырое значение меньше числа строк в логах. "
        "Это и есть «рост метрики, не отражённый 1:1 в логах»: для корректного счёта за "
        "период нужен `increase(metric[24h])` (reset-safe), а логи остаются источником "
        "истины по фактическим событиям."
    )),
]

# ---- dashboard layout ------------------------------------------------------
# 24-wide grid
layout = [
    ("nbank-avg-transfer-success", 0, 0, 8, 8),
    ("nbank-avg-transfer-request", 8, 0, 8, 8),
    ("nbank-cnt-transfer-failed", 16, 0, 8, 8),
    ("nbank-top-logins", 0, 8, 8, 13),
    ("nbank-top-profile", 8, 8, 8, 13),
    ("nbank-top-active", 16, 8, 8, 13),
    ("nbank-error-reasons", 0, 21, 12, 12),
    ("nbank-top-unauth", 12, 21, 12, 12),
    ("nbank-q18-errors", 0, 33, 12, 12),
    ("nbank-q18-note", 12, 33, 12, 12),
    ("nbank-q19-logins-log", 0, 45, 8, 8),
    ("nbank-q19-note", 8, 45, 16, 8),
]

panels = []
references = []
for i, (vid, x, y, w, h) in enumerate(layout, start=1):
    pidx = str(i)
    panels.append({
        "version": "7.17.3",
        "type": "visualization",
        "gridData": {"x": x, "y": y, "w": w, "h": h, "i": pidx},
        "panelIndex": pidx,
        "embeddableConfig": {"enhancements": {}},
        "panelRefName": f"panel_{pidx}",
    })
    references.append({"name": f"panel_{pidx}", "type": "visualization", "id": vid})

dashboard = {
    "id": "nbank-kibana-analytics",
    "type": "dashboard",
    "attributes": {
        "title": "NBank — Log Analytics (Kibana)",
        "hits": 0,
        "description": "Ответы по логам: Q11 логины, Q12 профиль, Q16 активность/сумма/ошибки, Q17 ошибки переводов.",
        "panelsJSON": json.dumps(panels),
        "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
        "version": 1,
        "timeRestore": True,
        "timeTo": "now",
        "timeFrom": "now-24h",
        "refreshInterval": {"pause": True, "value": 0},
        "kibanaSavedObjectMeta": {
            "searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"}, "filter": []})
        },
    },
    "references": references,
}

# ---- write NDJSON ----------------------------------------------------------
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "kibana-nbank-dashboard.ndjson")
objects = [index_pattern] + visualizations + [dashboard]
with open(out_path, "w", encoding="utf-8") as f:
    for obj in objects:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    # trailing summary line that Kibana's import tolerates
    f.write(json.dumps({"exportedCount": len(objects),
                        "missingRefCount": 0, "missingReferences": []}) + "\n")

print(f"wrote {out_path} ({len(objects)} objects)")
