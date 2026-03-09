import yfinance as yf

# Symbol mapping with descriptions
SYMBOLS = {
    # -- Core risk indicators --
    "vix": {
        "code": "^VIX",
        "name": "VIX 恐慌指数",
        "unit": "",
        "desc": "衡量美股市场恐慌程度，>25为高恐慌，>30为极端恐慌",
        "group": "core",
    },
    "brent": {
        "code": "BZ=F",
        "name": "Brent 原油",
        "unit": "$",
        "desc": "国际基准油价，霍尔木兹海峡封锁直接推升价格",
        "group": "energy",
    },
    "wti": {
        "code": "CL=F",
        "name": "WTI 原油",
        "unit": "$",
        "desc": "美国基准油价，反映美国本土能源供应压力",
        "group": "energy",
    },
    "natgas": {
        "code": "NG=F",
        "name": "天然气",
        "unit": "$",
        "desc": "霍尔木兹海峡也是LNG运输通道，冲突推升气价",
        "group": "energy",
    },
    "gold": {
        "code": "GC=F",
        "name": "黄金",
        "unit": "$",
        "desc": "核心避险资产，战争恐慌时资金涌入推高金价",
        "group": "safe_haven",
    },
    "usd_index": {
        "code": "DX-Y.NYB",
        "name": "美元指数",
        "unit": "",
        "desc": "美元走强反映全球避险资金回流美元，但压制新兴市场",
        "group": "safe_haven",
    },
    "us10y": {
        "code": "^TNX",
        "name": "10Y美债收益率",
        "unit": "%",
        "desc": "收益率上行=债价下跌，反映市场更担忧通胀而非避险",
        "group": "safe_haven",
    },

    # -- US Stock Indices --
    "sp500": {
        "code": "^GSPC",
        "name": "S&P 500",
        "unit": "",
        "desc": "美股大盘指标，战争引发系统性风险时大幅下跌",
        "group": "us_stocks",
    },
    "dji": {
        "code": "^DJI",
        "name": "道琼斯",
        "unit": "",
        "desc": "蓝筹股指数，受能源成本上升和经济衰退预期拖累",
        "group": "us_stocks",
    },
    "nasdaq": {
        "code": "^IXIC",
        "name": "纳斯达克",
        "unit": "",
        "desc": "科技股指数，对利率和通胀预期最敏感",
        "group": "us_stocks",
    },

    # -- Industrial Metals --
    "copper": {
        "code": "HG=F",
        "name": "铜",
        "unit": "$",
        "desc": "\"铜博士\"，全球经济风向标，下跌反映衰退预期",
        "group": "metals",
    },
    "aluminum": {
        "code": "ALI=F",
        "name": "铝",
        "unit": "$",
        "desc": "工业需求指标，能源成本上升推高铝冶炼成本",
        "group": "metals",
    },

    # -- Grain Prices --
    "wheat": {
        "code": "ZW=F",
        "name": "小麦",
        "unit": "¢",
        "desc": "能源涨价传导至化肥和运输成本，推升粮价",
        "group": "grain",
    },
    "corn": {
        "code": "ZC=F",
        "name": "玉米",
        "unit": "¢",
        "desc": "全球粮食安全指标，油价上涨带动乙醇需求和种植成本",
        "group": "grain",
    },

    # -- Defense & Shipping Stocks --
    "ita": {
        "code": "ITA",
        "name": "美国军工ETF",
        "unit": "$",
        "desc": "iShares军工ETF，战争直接受益板块",
        "group": "sector",
    },
    "lmt": {
        "code": "LMT",
        "name": "洛克希德·马丁",
        "unit": "$",
        "desc": "全球最大军工企业，F-35/导弹防御系统供应商",
        "group": "sector",
    },
    "rtx": {
        "code": "RTX",
        "name": "雷神技术",
        "unit": "$",
        "desc": "导弹/防空系统制造商，冲突升级直接受益",
        "group": "sector",
    },
    "noc": {
        "code": "NOC",
        "name": "诺斯罗普·格鲁曼",
        "unit": "$",
        "desc": "B-21轰炸机/无人机制造商，战时需求激增",
        "group": "sector",
    },
    "zim": {
        "code": "ZIM",
        "name": "ZIM航运",
        "unit": "$",
        "desc": "以色列航运公司，运价上涨直接受益但航线风险大",
        "group": "sector",
    },
    "bdry": {
        "code": "BDRY",
        "name": "干散货航运ETF",
        "unit": "$",
        "desc": "航运运价指数ETF，反映全球海运成本变化",
        "group": "sector",
    },

    # -- Iran / Middle East --
    "irr": {
        "code": "IRR=X",
        "name": "伊朗里亚尔/美元",
        "unit": "",
        "desc": "里亚尔贬值反映伊朗经济压力，数值越大贬值越严重",
        "group": "mideast",
    },
    "ksa": {
        "code": "KSA",
        "name": "沙特ETF",
        "unit": "$",
        "desc": "沙特市场代理指标，沙特被卷入冲突风险的晴雨表",
        "group": "mideast",
    },
    "eis": {
        "code": "EIS",
        "name": "以色列ETF",
        "unit": "$",
        "desc": "以色列市场表现，反映市场对以色列战争风险定价",
        "group": "mideast",
    },
    "uae": {
        "code": "UAE",
        "name": "阿联酋ETF",
        "unit": "$",
        "desc": "阿联酋市场表现，达夫拉空军基地所在国",
        "group": "mideast",
    },

    # -- Volatility / Emerging Markets --
    "india_vix": {
        "code": "^INDIAVIX",
        "name": "印度VIX",
        "unit": "",
        "desc": "亚洲新兴市场恐慌指标，印度是伊朗原油主要买家",
        "group": "em_risk",
    },

    # -- Inflation Expectations --
    "tip": {
        "code": "TIP",
        "name": "TIPS债券ETF",
        "unit": "$",
        "desc": "通胀保值债券，上涨反映市场通胀预期升温",
        "group": "inflation",
    },
    "rinf": {
        "code": "RINF",
        "name": "通胀预期ETF",
        "unit": "$",
        "desc": "直接追踪通胀预期，油价飙升时通常走高",
        "group": "inflation",
    },
}

# Groups for frontend layout
GROUPS = {
    "core": "核心恐慌指标",
    "energy": "能源价格",
    "safe_haven": "避险资产",
    "us_stocks": "美股指数",
    "metals": "工业金属",
    "grain": "粮食价格",
    "sector": "军工 / 航运板块",
    "mideast": "中东 / 伊朗",
    "em_risk": "新兴市场风险",
    "inflation": "通胀预期",
}


def fetch_market_data() -> dict:
    """Fetch latest market data for all tracked symbols."""
    results = {}
    codes = [info["code"] for info in SYMBOLS.values()]

    tickers = yf.Tickers(" ".join(codes))

    for key, info in SYMBOLS.items():
        try:
            ticker = tickers.tickers.get(info["code"])
            if ticker is None:
                ticker = yf.Ticker(info["code"])

            hist = ticker.history(period="5d")
            if hist.empty:
                results[key] = {
                    "name": info["name"],
                    "unit": info["unit"],
                    "desc": info["desc"],
                    "group": info["group"],
                    "value": None,
                    "prev_close": None,
                    "change": None,
                    "change_pct": None,
                }
                continue

            current = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else current
            change = current - prev
            change_pct = (change / prev * 100) if prev != 0 else 0

            results[key] = {
                "name": info["name"],
                "unit": info["unit"],
                "desc": info["desc"],
                "group": info["group"],
                "value": round(current, 2),
                "prev_close": round(prev, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
            }
        except Exception as e:
            results[key] = {
                "name": info["name"],
                "unit": info["unit"],
                "desc": info["desc"],
                "group": info["group"],
                "value": None,
                "prev_close": None,
                "change": None,
                "change_pct": None,
                "error": str(e),
            }

    return results


def fetch_history(symbol_key: str, period: str = "1mo") -> list[dict]:
    """Fetch historical data for a specific symbol."""
    info = SYMBOLS.get(symbol_key)
    if not info:
        return []

    ticker = yf.Ticker(info["code"])
    hist = ticker.history(period=period)

    return [
        {
            "date": idx.strftime("%Y-%m-%d"),
            "close": round(float(row["Close"]), 2),
        }
        for idx, row in hist.iterrows()
    ]
