"""
四层因果分析引擎
第1层：冲突走向判断（领先指标）
第2层：供给冲击传导（实时指标）
第3层：经济体制判定（组合指标）
第4层：情景推演与操作建议
"""


def _val(indicators, key, field="value"):
    v = indicators.get(key, {}).get(field)
    return v if v is not None else 0


def _pct(indicators, key):
    return _val(indicators, key, "change_pct")


# ── 第3层：经济体制判定 ──────────────────────────────────────

def detect_regime(indicators: dict) -> dict:
    """判定当前经济体制。"""
    brent_chg = _pct(indicators, "brent")
    sp500_chg = _pct(indicators, "sp500")
    us10y_chg = _val(indicators, "us10y", "change")
    gold_chg = _pct(indicators, "gold")
    copper_chg = _pct(indicators, "copper")
    usd_chg = _pct(indicators, "usd_index")
    india_vix = _val(indicators, "india_vix")
    vix = _val(indicators, "vix")
    brent = _val(indicators, "brent")
    ksa_chg = _pct(indicators, "ksa")
    uae_chg = _pct(indicators, "uae")

    regimes = []

    # 滞胀：油涨 + 股跌 + 债收益率涨 + 金涨
    if brent_chg > 3 and sp500_chg < -0.5 and us10y_chg > 0 and gold_chg > 0:
        regimes.append({
            "name": "stagflation", "label": "滞胀",
            "color": "#dc2626",
            "desc": "油价上涨+股市下跌+国债收益率上行+黄金上涨，增长停滞叠加通胀，央行政策空间被压缩",
        })

    # 衰退恐慌：油涨 + 股跌 + 债收益率跌(资金涌入国债) + 金涨
    if brent_chg > 3 and sp500_chg < -0.5 and us10y_chg < 0 and gold_chg > 0:
        regimes.append({
            "name": "recession_fear", "label": "衰退恐慌",
            "color": "#ea580c",
            "desc": "油价上涨+股市下跌+资金涌入国债压低收益率，市场预期经济硬着陆",
        })

    # 全球衰退：铜跌 + 股跌 + 新兴市场恐慌
    if copper_chg < -1.5 and sp500_chg < -0.5 and india_vix > 18:
        regimes.append({
            "name": "global_recession", "label": "全球衰退",
            "color": "#9333ea",
            "desc": "铜价走弱+美股下跌+新兴市场恐慌，工业需求崩塌信号",
        })

    # 美元虹吸：美元涨 + 股跌 + 中东ETF跌
    if usd_chg > 0.3 and sp500_chg < -0.5 and (ksa_chg < -1 or uae_chg < -1):
        regimes.append({
            "name": "usd_siphon", "label": "美元虹吸",
            "color": "#2563eb",
            "desc": "美元走强+美股下跌+中东/新兴市场资金外流，全球资本向美元回流",
        })

    # 正常化：VIX回落 + 油价可控 + 股市涨
    if vix < 20 and brent < 80 and sp500_chg > 0:
        regimes.append({
            "name": "normalization", "label": "正常化",
            "color": "#16a34a",
            "desc": "恐慌消退+能源价格回落+股市企稳，市场回归基本面",
        })

    # 如果没有匹配任何体制
    if not regimes:
        regimes.append({
            "name": "transition", "label": "过渡/混合",
            "color": "#6b7280",
            "desc": "多空信号交织，市场处于体制切换的过渡阶段",
        })

    return regimes[0]  # 返回最优先匹配的体制


# ── 第4层：情景概率 ──────────────────────────────────────────

def estimate_scenarios(indicators: dict, polymarket: list[dict]) -> list[dict]:
    """基于 Polymarket + 军工 + 里亚尔估算三种情景概率。"""

    # 基准：从 Polymarket 获取
    max_ceasefire = 0
    short_ceasefire = 0
    if polymarket:
        probs = [p["probability"] for p in polymarket if p.get("probability") is not None]
        if probs:
            max_ceasefire = max(probs)
            short_ceasefire = min(probs)

    # 情景A：快速停火 (基准=短期停战概率，受里亚尔和军工修正)
    prob_a = short_ceasefire
    irr = _val(indicators, "irr")
    ita_chg = _pct(indicators, "ita")
    if irr > 1500000:  # 里亚尔极度贬值 → 伊朗压力大 → 停火概率上调
        prob_a = min(prob_a + 10, 95)
    if ita_chg > 3:  # 军工大涨 → 聪明钱押注冲突持续 → 停火概率下调
        prob_a = max(prob_a - 5, 0)

    # 情景C：全面升级 (基准15%，受中东ETF和VIX修正)
    prob_c = 15
    ksa_chg = _pct(indicators, "ksa")
    vix = _val(indicators, "vix")
    if ksa_chg < -3:  # 沙特被拖入信号
        prob_c += 10
    if vix > 35:  # 极端恐慌
        prob_c += 5
    if max_ceasefire > 60:  # 市场预期会停，降低升级概率
        prob_c -= 5
    prob_c = max(min(prob_c, 50), 5)

    # 情景B：持久空袭 = 剩余
    prob_b = 100 - prob_a - prob_c
    prob_b = max(prob_b, 0)

    # 归一化
    total = prob_a + prob_b + prob_c
    if total > 0:
        prob_a = round(prob_a / total * 100)
        prob_b = round(prob_b / total * 100)
        prob_c = 100 - prob_a - prob_b

    return [
        {
            "id": "A", "name": "快速停火",
            "desc": "1-2个月内达成停火协议",
            "probability": prob_a, "color": "#22c55e",
        },
        {
            "id": "B", "name": "持久空袭",
            "desc": "空中打击持续3-6个月，不投入地面部队",
            "probability": prob_b, "color": "#f59e0b",
        },
        {
            "id": "C", "name": "全面升级",
            "desc": "地面入侵或沙特等国被拖入，战争扩大化",
            "probability": prob_c, "color": "#ef4444",
        },
    ]


# ── 拐点监控 ──────────────────────────────────────────────

def check_turning_points(indicators: dict, polymarket: list[dict]) -> list[dict]:
    """检测接近触发的拐点信号。"""
    points = []

    max_ceasefire = 0
    if polymarket:
        probs = [p["probability"] for p in polymarket if p.get("probability") is not None]
        if probs:
            max_ceasefire = max(probs)

    vix = _val(indicators, "vix")
    brent = _val(indicators, "brent")
    irr = _val(indicators, "irr")
    ita_chg = _pct(indicators, "ita")

    if max_ceasefire >= 70:
        points.append({
            "signal": f"停战概率达 {max_ceasefire}%",
            "action": "停战交易窗口开启：考虑做空原油、抄底股市",
            "urgency": "high", "color": "#22c55e",
        })
    elif max_ceasefire >= 60:
        points.append({
            "signal": f"停战概率 {max_ceasefire}%，接近70%触发线",
            "action": "准备停战交易预案，关注概率加速上升",
            "urgency": "watch", "color": "#eab308",
        })

    if ita_chg < -3:
        points.append({
            "signal": f"军工ETF回落 {ita_chg}%",
            "action": "聪明钱可能开始撤退，冲突预期降温",
            "urgency": "high", "color": "#22c55e",
        })

    if irr > 1500000:
        points.append({
            "signal": f"里亚尔汇率 {irr:,.0f}，极度贬值",
            "action": "伊朗经济接近崩溃，停火谈判意愿可能上升",
            "urgency": "high", "color": "#f97316",
        })

    if vix < 20:
        points.append({
            "signal": f"VIX回落至 {vix}，恐慌消退",
            "action": "风险偏好恢复，可逐步增配权益类资产",
            "urgency": "high", "color": "#22c55e",
        })
    elif vix > 35:
        points.append({
            "signal": f"VIX飙升至 {vix}，极端恐慌",
            "action": "市场可能超跌，但不宜抄底，等待VIX见顶回落",
            "urgency": "high", "color": "#ef4444",
        })

    if brent < 90:
        points.append({
            "signal": f"Brent回落至 ${brent}，跌破$90",
            "action": "供应恐慌缓解，能源空头可考虑获利了结",
            "urgency": "high", "color": "#22c55e",
        })

    return points


# ── 操作建议 ──────────────────────────────────────────────

def generate_trades(regime: dict, scenarios: list[dict], indicators: dict, polymarket: list[dict]) -> dict:
    """生成操作建议矩阵。"""

    max_ceasefire = 0
    if polymarket:
        probs = [p["probability"] for p in polymarket if p.get("probability") is not None]
        if probs:
            max_ceasefire = max(probs)

    vix = _val(indicators, "vix")
    brent = _val(indicators, "brent")
    regime_name = regime["name"]

    # 确定性方向（不依赖情景）
    confident = [
        {
            "direction": "long", "asset": "黄金",
            "targets": "黄金ETF(518880) / AU9999 / GLD",
            "logic": "三种情景下均受益：避险+通胀对冲，仅快速停火+美元暴涨构成风险",
        },
        {
            "direction": "long", "asset": "能源",
            "targets": "原油ETF / 中国石油 / 中海油 / XLE",
            "logic": "霍尔木兹海峡供应缺口短期难补，油价有支撑",
        },
        {
            "direction": "long", "asset": "军工",
            "targets": "军工ETF(512660) / LMT / RTX / NOC",
            "logic": "全球军费开支结构性上升，不依赖单一冲突",
        },
        {
            "direction": "long", "asset": "农业",
            "targets": "豆粕ETF / 农业ETF / 相关个股",
            "logic": "能源→化肥→粮价传导已启动，且有惯性",
        },
    ]

    # 有条件方向
    conditional = []

    if regime_name in ("stagflation", "recession_fear") and vix > 25:
        conditional.append({
            "direction": "short", "asset": "纳指/成长股",
            "targets": "QQQ Put / IC期货 / 创业板反向",
            "condition": f"当前体制={regime['label']}，VIX={vix}",
            "exit": "停战概率>50%时止损",
        })

    if brent > 100:
        conditional.append({
            "direction": "long", "asset": "航运",
            "targets": "中远海控(601919) / 招商轮船 / ZIM",
            "condition": f"油价>${brent}，运价持续上涨",
            "exit": "停火后运价快速回落",
        })
        conditional.append({
            "direction": "long", "asset": "煤炭",
            "targets": "中国神华 / 煤炭ETF(515220)",
            "condition": f"油价>${brent}，煤炭替代需求上升",
            "exit": "国内调控政策出台",
        })

    if regime_name == "usd_siphon":
        conditional.append({
            "direction": "long", "asset": "美元",
            "targets": "美元ETF / USD多头",
            "condition": "美元虹吸模式确认",
            "exit": "停战+美元回落",
        })

    if regime_name == "stagflation":
        conditional.append({
            "direction": "long", "asset": "通胀保护",
            "targets": "TIP / RINF / 通胀挂钩债券",
            "condition": "滞胀体制下通胀预期持续升温",
            "exit": "油价回落<$80",
        })

    # 拐点交易
    contrarian = []

    if max_ceasefire >= 60:
        contrarian.append({
            "direction": "long", "asset": "抄底中证500",
            "targets": "中证500ETF(510500) / 沪深300ETF",
            "trigger": f"停战概率>{max_ceasefire:.0f}%，突破70%时进场",
        })
        contrarian.append({
            "direction": "short", "asset": "做空原油",
            "targets": "原油Put / 反向原油ETF",
            "trigger": "停战概率从<30%跳升至>50%的那一刻",
        })

    contrarian.append({
        "direction": "long", "asset": "抄底纳斯达克",
        "targets": "QQQ / 纳指ETF / 科技龙头",
        "trigger": "VIX见顶回落破20 + 美联储暗示降息",
    })

    return {
        "confident": confident,
        "conditional": conditional,
        "contrarian": contrarian,
    }


# ── 第1层：关键信号 ──────────────────────────────────────────

def detect_signals(indicators: dict, polymarket: list[dict]) -> list[str]:
    """检测关键市场信号。"""
    signals = []
    vix = _val(indicators, "vix")
    brent = _val(indicators, "brent")
    gold_chg = _pct(indicators, "gold")
    natgas_chg = _pct(indicators, "natgas")
    us10y_chg = _val(indicators, "us10y", "change")
    usd_chg = _pct(indicators, "usd_index")
    sp500_chg = _pct(indicators, "sp500")
    india_vix = _val(indicators, "india_vix")
    copper_chg = _pct(indicators, "copper")
    wheat_chg = _pct(indicators, "wheat")
    ita_chg = _pct(indicators, "ita")
    rinf_chg = _pct(indicators, "rinf")
    irr = _val(indicators, "irr")

    max_ceasefire = 0
    short_ceasefire = 0
    if polymarket:
        probs = [p["probability"] for p in polymarket if p.get("probability") is not None]
        if probs:
            max_ceasefire = max(probs)
            short_ceasefire = min(probs)

    if vix > 30:
        signals.append(f"VIX 突破30 ({vix})，已进入极端恐慌区间")
    elif vix > 25:
        signals.append(f"VIX 处于高位 ({vix})，市场恐慌情绪浓厚")

    if brent > 100:
        signals.append(f"Brent 原油突破 $100/桶 (${brent})，能源供应严重受扰")
    elif brent > 90:
        signals.append(f"Brent 原油高位 (${brent})，霍尔木兹海峡风险持续")

    if natgas_chg > 5:
        signals.append(f"天然气大涨 {natgas_chg}%，LNG运输通道风险加剧")

    if gold_chg > 1:
        signals.append(f"黄金上涨 {gold_chg}%，避险资金持续涌入")

    if us10y_chg > 0 and gold_chg > 0:
        signals.append("黄金涨 + 国债收益率涨 → 滞胀交易逻辑主导")

    if usd_chg > 0.5 and sp500_chg < -1:
        signals.append("美元走强 + 美股下跌 → 典型避险模式")

    if india_vix > 20:
        signals.append(f"印度VIX升至 {india_vix}，亚洲新兴市场恐慌蔓延")

    if copper_chg < -2:
        signals.append(f"铜价下跌 {copper_chg}%，全球经济衰退预期升温")

    if wheat_chg > 3:
        signals.append(f"小麦上涨 {wheat_chg}%，能源成本向粮食传导")

    if ita_chg > 2:
        signals.append(f"军工板块上涨 {ita_chg}%，聪明钱押注冲突持续")

    if rinf_chg > 1:
        signals.append(f"通胀预期ETF上涨 {rinf_chg}%，滞胀担忧加剧")

    if irr > 1000000:
        signals.append(f"伊朗里亚尔汇率 {irr:,.0f}，伊朗经济承压严重")

    if short_ceasefire < 15:
        signals.append(f"短期停战概率极低 ({short_ceasefire}%)，冲突短期难以结束")
    if max_ceasefire > 60:
        signals.append(f"中期停战概率较高 ({max_ceasefire}%)，关注拐点信号")
    elif max_ceasefire < 40:
        signals.append(f"即使中期停战概率也仅 {max_ceasefire}%，市场极度悲观")

    return signals


# ── 风险等级 ──────────────────────────────────────────────

def assess_risk(indicators: dict, polymarket: list[dict]) -> dict:
    vix = _val(indicators, "vix")
    brent = _val(indicators, "brent")
    short_ceasefire = 0
    if polymarket:
        probs = [p["probability"] for p in polymarket if p.get("probability") is not None]
        if probs:
            short_ceasefire = min(probs)

    if vix > 30 and brent > 100 and short_ceasefire < 15:
        return {"level": "extreme", "text": "极高风险", "color": "#dc2626"}
    elif vix > 25 and brent > 90:
        return {"level": "high", "text": "高风险", "color": "#ea580c"}
    elif vix > 20 and brent > 80:
        return {"level": "elevated", "text": "中等偏高", "color": "#ca8a04"}
    else:
        return {"level": "moderate", "text": "风险可控", "color": "#16a34a"}


# ── 主入口 ──────────────────────────────────────────────

def analyze(indicators: dict, polymarket: list[dict]) -> dict:
    """完整的四层分析。"""

    risk = assess_risk(indicators, polymarket)
    regime = detect_regime(indicators)
    scenarios = estimate_scenarios(indicators, polymarket)
    signals = detect_signals(indicators, polymarket)
    turning_points = check_turning_points(indicators, polymarket)
    trades = generate_trades(regime, scenarios, indicators, polymarket)

    return {
        "risk": risk,
        "regime": regime,
        "scenarios": scenarios,
        "signals": signals,
        "turning_points": turning_points,
        "trades": trades,
    }
