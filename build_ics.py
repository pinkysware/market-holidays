# -*- coding: utf-8 -*-
"""
生成交易所非交易日 ICS 日历，供 iPhone 日历订阅。

输出（英文文件名，避免 URL 编码问题）：
  cn-market-closed.ics   A股非交易日（法定休市 + 全部周末）
  cn-holidays-only.ics   A股法定休市（仅工作日，精简版）
  us-market-closed.ics   美股非交易日（NYSE 休市 + 全部周末）
  us-early-close.ics     美股提前收盘日（当天仍开盘）

美股休市日按 NYSE 规则算法生成，可自动延伸多年（已用 2026/2027 官方数据校验通过）。
A股休市日来自沪深北交易所年度通知，需人工按年更新（一般 11–12 月公布次年安排）。
"""

import os
from datetime import date, timedelta

OUT = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# A 股：沪深北交易所公布的休市区间（闭区间）
# 2026 年数据来源：三大交易所 2025-12-22 发布的《2026年部分节假日休市安排》
# 次年安排通常在当年 11–12 月公布，届时在此追加
# ============================================================
CN_CLOSED_RANGES = {
    2026: [
        ("元旦", date(2026, 1, 1), date(2026, 1, 3)),
        ("春节", date(2026, 2, 15), date(2026, 2, 23)),
        ("清明节", date(2026, 4, 4), date(2026, 4, 6)),
        ("劳动节", date(2026, 5, 1), date(2026, 5, 5)),
        ("端午节", date(2026, 6, 19), date(2026, 6, 21)),
        ("中秋节", date(2026, 9, 25), date(2026, 9, 27)),
        ("国庆节", date(2026, 10, 1), date(2026, 10, 7)),
    ],
}
# 交易所单独点名的周末休市日（国务院调休补班，但 A 股照常休市）
CN_WEEKEND_EXTRA = {
    2026: [date(2026, 1, 4), date(2026, 2, 14), date(2026, 2, 28),
           date(2026, 5, 9), date(2026, 9, 20), date(2026, 10, 10)],
}

# ============================================================
# 美股：按 NYSE 规则算法生成
# ============================================================
def easter(y):
    """Anonymous Gregorian algorithm，返回复活节（周日）"""
    a = y % 19
    b, c = divmod(y, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(y, month, day + 1)


def nth_weekday(y, m, weekday, n):
    """第 n 个 weekday（周一=0）；n=-1 表示最后一个"""
    if n > 0:
        d = date(y, m, 1)
        off = (weekday - d.weekday()) % 7
        return d + timedelta(days=off + 7 * (n - 1))
    # 最后一个：取该月最后一天，往前回退到目标星期
    import calendar
    d = date(y, m, calendar.monthrange(y, m)[1])
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def observe(d):
    """NYSE 调休：周六 → 前一个周五；周日 → 后一个周一；圣诞节周六特例 → 前一个周五"""
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def nyse_holidays(y):
    """返回 [(date, 名称)]，NYSE 全年休市日"""
    h = []
    # 元旦：落周日则补 1/2 周一；落周六不调休（12/31 周五正常开市）
    nya = date(y, 1, 1)
    h.append((observe(nya) if nya.weekday() == 6 else nya, "元旦 New Year's Day"))
    h.append((nth_weekday(y, 1, 0, 3), "马丁·路德·金日 MLK Day"))
    h.append((nth_weekday(y, 2, 0, 3), "总统日 Washington's Birthday"))
    h.append((easter(y) - timedelta(days=2), "耶稣受难日 Good Friday"))
    h.append((nth_weekday(y, 5, 0, -1), "阵亡将士纪念日 Memorial Day"))
    h.append((observe(date(y, 6, 19)), "六月节 Juneteenth"))
    h.append((observe(date(y, 7, 4)), "独立日 Independence Day"))
    h.append((nth_weekday(y, 9, 0, 1), "劳动节 Labor Day"))
    tg = nth_weekday(y, 11, 3, 4)
    h.append((tg, "感恩节 Thanksgiving"))
    h.append((observe(date(y, 12, 25)), "圣诞节 Christmas"))
    return h


def nyse_early_closes(y):
    """提前收盘（美东 13:00）。仅含规则明确的两类：感恩节次日、平安夜（若当天为工作日且未休市）"""
    closed = {d for d, _ in nyse_holidays(y)}
    out = []
    tg = nth_weekday(y, 11, 3, 4)
    after_tg = tg + timedelta(days=1)
    if after_tg.weekday() < 5 and after_tg not in closed:
        out.append((after_tg, "感恩节次日提前收盘 13:00 ET"))
    xmas_eve = date(y, 12, 24)
    if xmas_eve.weekday() < 5 and xmas_eve not in closed:
        out.append((xmas_eve, "平安夜提前收盘 13:00 ET"))
    return out
# 注：独立日前一天（多为 7/3）NYSE 亦常提前收盘，但各年公告不一（2026 官方未列），
#     需要的话在 nyse_early_closes 里补一条即可。


# ============================================================
# ICS 输出
# ============================================================
def fold(line):
    b = line.encode("utf-8")
    if len(b) <= 73:
        return line
    out, cur = [], b""
    for ch in line:
        e = ch.encode("utf-8")
        if len(cur) + len(e) > 73:
            out.append(cur)
            cur = b" " + e
        else:
            cur += e
    out.append(cur)
    return "\r\n".join(x.decode("utf-8") for x in out)


def esc(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def allday(uid, d, summary):
    end = d + timedelta(days=1)
    return "\r\n".join([
        "BEGIN:VEVENT", "UID:%s" % uid, "DTSTAMP:20260907T120000Z",
        fold("SUMMARY:%s" % esc(summary)),
        "DTSTART;VALUE=DATE:%s" % d.strftime("%Y%m%d"),
        "DTEND;VALUE=DATE:%s" % end.strftime("%Y%m%d"),
        "TRANSP:TRANSPARENT", "END:VEVENT",
    ])


def write_ics(name, calname, events):
    body = ["BEGIN:VCALENDAR", "VERSION:2.0",
            "PRODID:-//WorkBuddy//Market Holidays//CN", "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH", fold("X-WR-CALNAME:%s" % calname),
            "X-WR-TIMEZONE:Asia/Shanghai", "REFRESH-INTERVAL;VALUE=DURATION:P1D"]
    body += events + ["END:VCALENDAR"]
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(body) + "\r\n")
    print("%-26s %4d events" % (name, len(events)))


def daterange(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


# ---------------- A 股 ----------------
cn_years = sorted(CN_CLOSED_RANGES)
hol = {}
for y in cn_years:
    for nm, a, b in CN_CLOSED_RANGES[y]:
        for d in daterange(a, b):
            hol[d] = nm

a, b = date(cn_years[0], 1, 1), date(cn_years[-1], 12, 31)
ev_full, ev_slim = [], []
for d in daterange(a, b):
    if d in hol:
        ev_full.append(allday("cn-h-%s" % d.strftime("%Y%m%d"), d, "%s休市" % hol[d]))
        if d.weekday() < 5:
            ev_slim.append(allday("cnh-%s" % d.strftime("%Y%m%d"), d, "%s休市" % hol[d]))
    elif d.weekday() >= 5:
        ev_full.append(allday("cn-w-%s" % d.strftime("%Y%m%d"), d, "周末休市"))
write_ics("cn-market-closed.ics", "A股非交易日", ev_full)
write_ics("cn-holidays-only.ics", "A股法定休市", ev_slim)

# ---------------- 美股（2026–2030） ----------------
US_FROM, US_TO = 2026, 2030
us = {}
for y in range(US_FROM, US_TO + 1):
    us.update(dict(nyse_holidays(y)))

ev3 = []
for d in daterange(date(US_FROM, 1, 1), date(US_TO, 12, 31)):
    if d in us:
        ev3.append(allday("us-h-%s" % d.strftime("%Y%m%d"), d, "美股休市 · %s" % us[d]))
    elif d.weekday() >= 5:
        ev3.append(allday("us-w-%s" % d.strftime("%Y%m%d"), d, "周末休市"))
write_ics("us-market-closed.ics", "美股非交易日", ev3)

ev4 = []
for y in range(US_FROM, US_TO + 1):
    for d, nm in nyse_early_closes(y):
        ev4.append(allday("use-%s" % d.strftime("%Y%m%d"), d, "美股提前收盘 · %s" % nm))
write_ics("us-early-close.ics", "美股提前收盘", ev4)

# ---------------- 自检 ----------------
print()
for y in cn_years:
    n = sum(1 for d in daterange(date(y, 1, 1), date(y, 12, 31)) if d.weekday() < 5 and d not in hol)
    print("A股 %d 交易日: %d" % (y, n))
for y in range(US_FROM, US_TO + 1):
    n = sum(1 for d in daterange(date(y, 1, 1), date(y, 12, 31)) if d.weekday() < 5 and d not in us)
    print("美股 %d 交易日: %d" % (y, n))
