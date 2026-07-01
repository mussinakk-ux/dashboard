
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date
import json
import calendar

try:
    import yfinance as yf
except Exception:
    yf = None

HOLDINGS_FILE = Path("holdings.csv")
TRADES_FILE = Path("trades.csv")
DAILY_FILE = Path("daily_assets.csv")
SETTINGS_FILE = Path("settings.json")

DEFAULT_HOLDINGS = [
    {"symbol":"00947","name":"台新臺灣IC設計動能ETF","market":"TW","currency":"TWD","shares":1004.0,"avg_cost":25.78,"price":25.78},
    {"symbol":"SOXQ","name":"Invesco費城半導體ETF","market":"US","currency":"USD","shares":2.0,"avg_cost":94.685,"price":94.685},
    {"symbol":"1310","name":"台苯","market":"TW","currency":"TWD","shares":1000.0,"avg_cost":9.52,"price":9.52},
    {"symbol":"2330","name":"台積電","market":"TW","currency":"TWD","shares":530.0,"avg_cost":537.79,"price":1778.5},
    {"symbol":"00631L","name":"元大台灣50正2","market":"TW","currency":"TWD","shares":4070.0,"avg_cost":26.66,"price":38.33},
    {"symbol":"00830","name":"國泰費城半導體ETF","market":"TW","currency":"TWD","shares":1056.0,"avg_cost":81.77,"price":81.77},
    {"symbol":"2302","name":"麗正","market":"TW","currency":"TWD","shares":1000.0,"avg_cost":19.53,"price":19.53},
    {"symbol":"2337","name":"旺宏","market":"TW","currency":"TWD","shares":1000.0,"avg_cost":149.71,"price":149.71},
    {"symbol":"2408","name":"南亞科","market":"TW","currency":"TWD","shares":200.0,"avg_cost":227.32,"price":227.32},
    {"symbol":"3491","name":"昇達科","market":"TW","currency":"TWD","shares":5.0,"avg_cost":1557.20,"price":1557.20},
    {"symbol":"6116","name":"彩晶","market":"TW","currency":"TWD","shares":3000.0,"avg_cost":10.31,"price":10.31},
    {"symbol":"6558","name":"興能高","market":"TW","currency":"TWD","shares":2000.0,"avg_cost":36.0,"price":36.0},
    {"symbol":"6603","name":"富強鑫","market":"TW","currency":"TWD","shares":1000.0,"avg_cost":26.64,"price":26.64},
    {"symbol":"6770","name":"力積電","market":"TW","currency":"TWD","shares":1000.0,"avg_cost":63.79,"price":63.79},
    {"symbol":"NVDA","name":"NVIDIA","market":"US","currency":"USD","shares":1.0,"avg_cost":142.95,"price":142.95},
    {"symbol":"QQQ","name":"Invesco QQQ","market":"US","currency":"USD","shares":1.55011,"avg_cost":645.15,"price":645.15},
]

HOLDINGS_COLS = ["symbol","name","market","currency","shares","avg_cost","price"]
TRADES_COLS = ["date","symbol","name","market","currency","action","qty","price","buy_fee","sell_fee","tax","gross_realized","net_realized","note"]
DAILY_COLS = ["date","total_market_value","total_cost","unrealized_profit","realized_profit","total_profit"]

st.set_page_config(page_title="價差交易紀錄｜月曆版", page_icon="🐢", layout="wide")

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"theme":"海龜沙灘版"}

def save_settings(settings):
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")

settings = load_settings()

with st.sidebar:
    st.header("設定")
    theme_choice = st.selectbox("主題配色", ["淡粉色", "海龜沙灘版", "海龜海洋版", "海龜森林版"], index=["淡粉色", "海龜沙灘版", "海龜海洋版", "海龜森林版"].index(settings.get("theme","海龜沙灘版")) if settings.get("theme","海龜沙灘版") in ["淡粉色", "海龜沙灘版", "海龜海洋版", "海龜森林版"] else 1)
    if theme_choice != settings.get("theme"):
        settings["theme"] = theme_choice
        save_settings(settings)
        st.rerun()

theme = settings.get("theme", "海龜沙灘版")

if theme == "海龜森林版":
    css = """
    <style>
    .stApp{background:#EEF5EE;}
    .block-container{padding-top:1rem;padding-bottom:4rem;}
    [data-testid="stMetric"]{background:#F9FCF7;border:1px solid #BFD8BF;border-radius:20px;padding:16px;box-shadow:0 4px 14px rgba(60,100,60,.08);}
    h1,h2,h3{color:#355C3A;}
    p,label,span{color:#3A4D3A;}
    section[data-testid="stSidebar"]{background:#E3EFE3;}
    .stTabs [data-baseweb="tab"]{background:#F9FCF7;border-radius:999px;border:1px solid #BFD8BF;color:#355C3A;}
    .stTabs [aria-selected="true"]{background:#D7E8D7!important;color:#2E4F33!important;}
    .stButton>button,.stDownloadButton>button{background:#5B7F5A;color:white;border:none;border-radius:15px;font-weight:700;}
    .stButton>button:hover,.stDownloadButton>button:hover{background:#466B46;color:white;}
    div[data-testid="stDataFrame"]{background:#F9FCF7;border-radius:16px;}
    .calendar-card{background:#F9FCF7;border:1px solid #BFD8BF;border-radius:16px;padding:10px;min-height:90px;margin:2px;}
    .calendar-empty{background:#E8F1E8;border:1px dashed #BFD8BF;border-radius:16px;padding:10px;min-height:90px;margin:2px;color:#7A947A;}
    .gain{color:#287C4F;font-weight:700;}
    .loss{color:#B85C5C;font-weight:700;}
    .flat{color:#777;font-weight:700;}
    
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-baseweb="select"] > div,
    textarea {
        background:#FFFFFF !important;
        color:#173B35 !important;
        border:2px solid #4F8A8B !important;
        border-radius:14px !important;
        font-weight:700 !important;
        box-shadow:0 2px 8px rgba(0,0,0,.06) !important;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus,
    div[data-testid="stDateInput"] input:focus,
    textarea:focus {
        border:3px solid #2F5D62 !important;
        box-shadow:0 0 0 3px rgba(79,138,139,.18) !important;
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stTextArea"] label {
        font-size:1rem !important;
        font-weight:800 !important;
        color:#2F5D62 !important;
    }
    .trade-card{
        background:rgba(255,255,255,.72);
        border:2px solid rgba(79,138,139,.35);
        border-radius:22px;
        padding:18px;
        margin-bottom:14px;
        box-shadow:0 6px 18px rgba(0,0,0,.06);
    }
    .fee-preview{
        background:#FFFFFF;
        border:2px dashed #4F8A8B;
        border-radius:18px;
        padding:14px;
        margin-top:10px;
        font-weight:800;
        color:#2F5D62;
    }
    .quick-chip{
        display:inline-block;
        background:#FFFFFF;
        border:1px solid #4F8A8B;
        border-radius:999px;
        padding:6px 10px;
        margin:2px;
        color:#2F5D62;
        font-weight:800;
    }

    </style>
    """
elif theme == "海龜海洋版":
    css = """
    <style>
    .stApp{background:#EAF5F5;}
    .block-container{padding-top:1rem;padding-bottom:4rem;}
    [data-testid="stMetric"]{background:#FDFEFE;border:1px solid #B8D8D8;border-radius:20px;padding:16px;box-shadow:0 4px 14px rgba(70,120,125,.08);}
    h1,h2,h3{color:#2F5D62;}
    p,label,span{color:#355C60;}
    section[data-testid="stSidebar"]{background:#DDEFEF;}
    .stTabs [data-baseweb="tab"]{background:#FDFEFE;border-radius:999px;border:1px solid #B8D8D8;color:#2F5D62;}
    .stTabs [aria-selected="true"]{background:#CDE7E7!important;color:#244C50!important;}
    .stButton>button,.stDownloadButton>button{background:#4F8A8B;color:white;border:none;border-radius:15px;font-weight:700;}
    .stButton>button:hover,.stDownloadButton>button:hover{background:#3F7677;color:white;}
    div[data-testid="stDataFrame"]{background:#FDFEFE;border-radius:16px;}
    .calendar-card{background:#FDFEFE;border:1px solid #B8D8D8;border-radius:16px;padding:10px;min-height:90px;margin:2px;}
    .calendar-empty{background:#DFF0F0;border:1px dashed #B8D8D8;border-radius:16px;padding:10px;min-height:90px;margin:2px;color:#78999A;}
    .gain{color:#2F8F70;font-weight:700;}
    .loss{color:#B85C5C;font-weight:700;}
    .flat{color:#777;font-weight:700;}
    
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-baseweb="select"] > div,
    textarea {
        background:#FFFFFF !important;
        color:#173B35 !important;
        border:2px solid #4F8A8B !important;
        border-radius:14px !important;
        font-weight:700 !important;
        box-shadow:0 2px 8px rgba(0,0,0,.06) !important;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus,
    div[data-testid="stDateInput"] input:focus,
    textarea:focus {
        border:3px solid #2F5D62 !important;
        box-shadow:0 0 0 3px rgba(79,138,139,.18) !important;
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stTextArea"] label {
        font-size:1rem !important;
        font-weight:800 !important;
        color:#2F5D62 !important;
    }
    .trade-card{
        background:rgba(255,255,255,.72);
        border:2px solid rgba(79,138,139,.35);
        border-radius:22px;
        padding:18px;
        margin-bottom:14px;
        box-shadow:0 6px 18px rgba(0,0,0,.06);
    }
    .fee-preview{
        background:#FFFFFF;
        border:2px dashed #4F8A8B;
        border-radius:18px;
        padding:14px;
        margin-top:10px;
        font-weight:800;
        color:#2F5D62;
    }
    .quick-chip{
        display:inline-block;
        background:#FFFFFF;
        border:1px solid #4F8A8B;
        border-radius:999px;
        padding:6px 10px;
        margin:2px;
        color:#2F5D62;
        font-weight:800;
    }

    </style>
    """
elif theme == "海龜沙灘版":
    css = """
    <style>
    .stApp{background:#F8F5ED;}
    .block-container{padding-top:1rem;padding-bottom:4rem;}
    [data-testid="stMetric"]{background:#FFFDF8;border:1px solid #D9D1BC;border-radius:20px;padding:16px;box-shadow:0 4px 14px rgba(80,90,70,.08);}
    h1,h2,h3{color:#355C3A;}
    p,label,span{color:#3D4D40;}
    section[data-testid="stSidebar"]{background:#EFE8D8;}
    .stTabs [data-baseweb="tab"]{background:#FFFDF8;border-radius:999px;border:1px solid #D9D1BC;color:#3D4D40;}
    .stTabs [aria-selected="true"]{background:#DDEAD8!important;color:#355C3A!important;}
    .stButton>button,.stDownloadButton>button{background:#6E8B74;color:white;border:none;border-radius:15px;font-weight:700;}
    .stButton>button:hover,.stDownloadButton>button:hover{background:#5B7F5A;color:white;}
    div[data-testid="stDataFrame"]{background:#FFFDF8;border-radius:16px;}
    .calendar-card{background:#FFFDF8;border:1px solid #D9D1BC;border-radius:16px;padding:10px;min-height:90px;margin:2px;}
    .calendar-empty{background:#F2EBDD;border:1px dashed #D9D1BC;border-radius:16px;padding:10px;min-height:90px;margin:2px;color:#9A927E;}
    .gain{color:#2F7D4F;font-weight:700;}
    .loss{color:#B85C5C;font-weight:700;}
    .flat{color:#777;font-weight:700;}
    
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-baseweb="select"] > div,
    textarea {
        background:#FFFFFF !important;
        color:#173B35 !important;
        border:2px solid #4F8A8B !important;
        border-radius:14px !important;
        font-weight:700 !important;
        box-shadow:0 2px 8px rgba(0,0,0,.06) !important;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus,
    div[data-testid="stDateInput"] input:focus,
    textarea:focus {
        border:3px solid #2F5D62 !important;
        box-shadow:0 0 0 3px rgba(79,138,139,.18) !important;
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stTextArea"] label {
        font-size:1rem !important;
        font-weight:800 !important;
        color:#2F5D62 !important;
    }
    .trade-card{
        background:rgba(255,255,255,.72);
        border:2px solid rgba(79,138,139,.35);
        border-radius:22px;
        padding:18px;
        margin-bottom:14px;
        box-shadow:0 6px 18px rgba(0,0,0,.06);
    }
    .fee-preview{
        background:#FFFFFF;
        border:2px dashed #4F8A8B;
        border-radius:18px;
        padding:14px;
        margin-top:10px;
        font-weight:800;
        color:#2F5D62;
    }
    .quick-chip{
        display:inline-block;
        background:#FFFFFF;
        border:1px solid #4F8A8B;
        border-radius:999px;
        padding:6px 10px;
        margin:2px;
        color:#2F5D62;
        font-weight:800;
    }

    </style>
    """
else:
    css = """
    <style>
    .stApp{background:#FFF5F7;}
    .block-container{padding-top:1rem;padding-bottom:4rem;}
    [data-testid="stMetric"]{background:#FFFDFE;border:1px solid #F3C9D2;border-radius:20px;padding:16px;box-shadow:0 4px 14px rgba(177,92,112,.08);}
    h1,h2,h3{color:#6B3F4A;}
    p,label,span{color:#6B4B52;}
    section[data-testid="stSidebar"]{background:#FFECEF;}
    .stTabs [data-baseweb="tab"]{background:#FFFDFE;border-radius:999px;border:1px solid #F3C9D2;color:#6B3F4A;}
    .stTabs [aria-selected="true"]{background:#F8D7DE!important;color:#5A2F3A!important;}
    .stButton>button,.stDownloadButton>button{background:#E7A9B7;color:white;border:none;border-radius:15px;font-weight:700;}
    .stButton>button:hover,.stDownloadButton>button:hover{background:#D98FA0;color:white;}
    div[data-testid="stDataFrame"]{background:#FFFDFE;border-radius:16px;}
    .calendar-card{background:#FFFDFE;border:1px solid #F3C9D2;border-radius:16px;padding:10px;min-height:90px;margin:2px;}
    .calendar-empty{background:#FFF0F3;border:1px dashed #F3C9D2;border-radius:16px;padding:10px;min-height:90px;margin:2px;color:#B78A94;}
    .gain{color:#2F8F5B;font-weight:700;}
    .loss{color:#C05A6A;font-weight:700;}
    .flat{color:#777;font-weight:700;}
    
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-baseweb="select"] > div,
    textarea {
        background:#FFFFFF !important;
        color:#173B35 !important;
        border:2px solid #4F8A8B !important;
        border-radius:14px !important;
        font-weight:700 !important;
        box-shadow:0 2px 8px rgba(0,0,0,.06) !important;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus,
    div[data-testid="stDateInput"] input:focus,
    textarea:focus {
        border:3px solid #2F5D62 !important;
        box-shadow:0 0 0 3px rgba(79,138,139,.18) !important;
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stTextArea"] label {
        font-size:1rem !important;
        font-weight:800 !important;
        color:#2F5D62 !important;
    }
    .trade-card{
        background:rgba(255,255,255,.72);
        border:2px solid rgba(79,138,139,.35);
        border-radius:22px;
        padding:18px;
        margin-bottom:14px;
        box-shadow:0 6px 18px rgba(0,0,0,.06);
    }
    .fee-preview{
        background:#FFFFFF;
        border:2px dashed #4F8A8B;
        border-radius:18px;
        padding:14px;
        margin-top:10px;
        font-weight:800;
        color:#2F5D62;
    }
    .quick-chip{
        display:inline-block;
        background:#FFFFFF;
        border:1px solid #4F8A8B;
        border-radius:999px;
        padding:6px 10px;
        margin:2px;
        color:#2F5D62;
        font-weight:800;
    }

    </style>
    """
st.markdown(css, unsafe_allow_html=True)


CN_MAP = {
    "symbol":"股票代碼","name":"名稱","market":"市場","currency":"幣別",
    "shares":"庫存股數","avg_cost":"平均成本","price":"現價",
    "market_value":"庫存市值","cost_value":"庫存成本","unrealized_profit":"未實現損益",
    "return_rate":"報酬率%","date":"日期","action":"買賣","qty":"股數",
    "buy_fee":"買進手續費","sell_fee":"賣出手續費","tax":"證交稅/交易稅",
    "gross_realized":"已實現毛損益","net_realized":"已實現淨損益","note":"備註",
    "total_market_value":"總市值","total_cost":"總成本","realized_profit":"已實現損益",
    "total_profit":"總損益","daily_change":"每日變化","month":"月份","year":"年度",
    "月初資產":"月初資產","月底資產":"月底資產","月增減":"月增減","月報酬率%":"月報酬率%",
    "月底未實現":"月底未實現","月底已實現":"月底已實現","月底總損益":"月底總損益","紀錄天數":"紀錄天數",
    "delete":"刪除"
}

def zh(df):
    return df.rename(columns={k:v for k,v in CN_MAP.items() if k in df.columns})

def init_files():
    if not HOLDINGS_FILE.exists():
        pd.DataFrame(DEFAULT_HOLDINGS).to_csv(HOLDINGS_FILE, index=False, encoding="utf-8-sig")
    if not TRADES_FILE.exists():
        pd.DataFrame(columns=TRADES_COLS).to_csv(TRADES_FILE, index=False, encoding="utf-8-sig")
    if not DAILY_FILE.exists():
        pd.DataFrame(columns=DAILY_COLS).to_csv(DAILY_FILE, index=False, encoding="utf-8-sig")

def read_csv(path, cols):
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = "" if c in ["date","symbol","name","market","currency","action","note"] else 0.0
    return df[cols]

def save_csv(df, path, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = "" if c in ["date","symbol","name","market","currency","action","note"] else 0.0
    df[cols].to_csv(path, index=False, encoding="utf-8-sig")

def to_num(df, cols):
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df

def normalize_holdings(df):
    df = df.copy()
    for c in HOLDINGS_COLS:
        if c not in df.columns:
            df[c] = "" if c in ["symbol","name","market","currency"] else 0.0
    df = df[HOLDINGS_COLS]
    df = to_num(df, ["shares","avg_cost","price"])
    for c in ["symbol","name","market","currency"]:
        df[c] = df[c].astype(str)
    return df

def normalize_trades(df):
    df = df.copy()
    for c in TRADES_COLS:
        if c not in df.columns:
            df[c] = "" if c in ["date","symbol","name","market","currency","action","note"] else 0.0
    df = df[TRADES_COLS]
    df = to_num(df, ["qty","price","buy_fee","sell_fee","tax","gross_realized","net_realized"])
    for c in ["date","symbol","name","market","currency","action","note"]:
        df[c] = df[c].astype(str)
    return df

def normalize_daily(df):
    df = df.copy()
    for c in DAILY_COLS:
        if c not in df.columns:
            df[c] = "" if c == "date" else 0.0
    df = df[DAILY_COLS]
    df = to_num(df, ["total_market_value","total_cost","unrealized_profit","realized_profit","total_profit"])
    df["date"] = df["date"].astype(str)
    return df

def money(x):
    try:
        return f"{float(x):,.0f}"
    except Exception:
        return "0"

def usd_twd_rate():
    if yf is None:
        return 32.0
    try:
        h = yf.Ticker("TWD=X").history(period="5d")
        if not h.empty:
            return float(h["Close"].dropna().iloc[-1])
    except Exception:
        pass
    return 32.0

def fetch_price(symbol, market):
    if yf is None:
        return None
    s = str(symbol).upper().strip()
    candidates = [s if market == "US" else f"{s}.TW"]
    if market == "TW":
        candidates.append(f"{s}.TWO")
    for t in candidates:
        try:
            h = yf.Ticker(t).history(period="5d")
            if not h.empty:
                return float(h["Close"].dropna().iloc[-1])
        except Exception:
            pass
    return None

def is_etf(symbol):
    s = str(symbol).upper()
    return s.startswith(("00","006","007","008","009")) or s in ["QQQ","SMH","SOXQ","VOO","SPY","SOXX"]

def auto_fee_tax(symbol, market, action, qty, price, discount, min_fee):
    amount = float(qty) * float(price)
    buy_fee = sell_fee = tax = 0.0
    if market == "TW" and amount > 0:
        fee = max(round(amount * 0.001425 * discount), int(min_fee))
        if action == "買進":
            buy_fee = fee
        elif action == "賣出":
            sell_fee = fee
            tax = round(amount * (0.001 if is_etf(symbol) else 0.003))
    return buy_fee, sell_fee, tax

def calc_values(holdings, usd_rate):
    df = normalize_holdings(holdings)
    fx = df["currency"].map(lambda x: usd_rate if x == "USD" else 1.0)
    df["market_value"] = df["shares"] * df["price"] * fx
    df["cost_value"] = df["shares"] * df["avg_cost"] * fx
    df["unrealized_profit"] = df["market_value"] - df["cost_value"]
    df["return_rate"] = df["unrealized_profit"] / df["cost_value"].replace(0, pd.NA) * 100
    return df

def realized_total(trades):
    if trades.empty:
        return 0.0
    return float(pd.to_numeric(trades["net_realized"], errors="coerce").fillna(0).sum())

def add_trade(holdings, trades, d, symbol, name, market, currency, action, qty, price, buy_fee, sell_fee, tax, note):
    holdings = normalize_holdings(holdings)
    trades = normalize_trades(trades)
    symbol = symbol.upper().strip()
    qty = float(qty)
    price = float(price)
    buy_fee = float(buy_fee)
    sell_fee = float(sell_fee)
    tax = float(tax)

    mask = holdings["symbol"].str.upper().eq(symbol)
    gross_realized = 0.0
    net_realized = 0.0

    if action == "買進":
        total_buy_cost = qty * price + buy_fee
        if mask.any():
            i = holdings[mask].index[0]
            old_qty = float(holdings.loc[i, "shares"])
            old_cost = float(holdings.loc[i, "avg_cost"])
            new_qty = old_qty + qty
            new_cost = ((old_qty * old_cost) + total_buy_cost) / new_qty if new_qty else price
            holdings.loc[i, "shares"] = new_qty
            holdings.loc[i, "avg_cost"] = new_cost
            holdings.loc[i, "price"] = price
            if name:
                holdings.loc[i, "name"] = name
            holdings.loc[i, "market"] = market
            holdings.loc[i, "currency"] = currency
        else:
            new_row = {
                "symbol":symbol,"name":name or symbol,"market":market,"currency":currency,
                "shares":qty,"avg_cost":total_buy_cost/qty if qty else price,"price":price
            }
            holdings = pd.concat([holdings, pd.DataFrame([new_row])], ignore_index=True)

    elif action == "賣出":
        if mask.any():
            i = holdings[mask].index[0]
            old_qty = float(holdings.loc[i, "shares"])
            avg_cost = float(holdings.loc[i, "avg_cost"])
            sell_qty = min(qty, old_qty)
            gross_realized = (price - avg_cost) * sell_qty
            net_realized = gross_realized - sell_fee - tax
            holdings.loc[i, "shares"] = old_qty - sell_qty
            holdings.loc[i, "price"] = price
        else:
            st.warning("找不到這檔庫存，已記錄交易但無法更新庫存。")

    new_trade = {
        "date":d,
        "symbol":symbol,
        "name":name or (holdings.loc[holdings["symbol"].str.upper().eq(symbol), "name"].iloc[0] if holdings["symbol"].str.upper().eq(symbol).any() else symbol),
        "market":market,
        "currency":currency,
        "action":action,
        "qty":qty,
        "price":price,
        "buy_fee":buy_fee,
        "sell_fee":sell_fee,
        "tax":tax,
        "gross_realized":gross_realized,
        "net_realized":net_realized,
        "note":note
    }
    trades = pd.concat([trades, pd.DataFrame([new_trade])], ignore_index=True)
    return holdings, trades

def save_daily_snapshot(holdings, trades, usd_rate):
    dfv = calc_values(holdings, usd_rate)
    total_market = dfv["market_value"].sum()
    total_cost = dfv["cost_value"].sum()
    unrealized = dfv["unrealized_profit"].sum()
    realized = realized_total(trades)
    total_profit = unrealized + realized

    daily = normalize_daily(read_csv(DAILY_FILE, DAILY_COLS))
    d = date.today().isoformat()
    row = {
        "date":d,
        "total_market_value":total_market,
        "total_cost":total_cost,
        "unrealized_profit":unrealized,
        "realized_profit":realized,
        "total_profit":total_profit
    }
    if not daily.empty and (daily["date"] == d).any():
        for k,v in row.items():
            daily.loc[daily["date"] == d, k] = v
    else:
        daily = pd.concat([daily, pd.DataFrame([row])], ignore_index=True)
    save_csv(normalize_daily(daily), DAILY_FILE, DAILY_COLS)

def export_backup(holdings, trades, daily):
    return json.dumps({
        "holdings": normalize_holdings(holdings).to_dict("records"),
        "trades": normalize_trades(trades).to_dict("records"),
        "daily": normalize_daily(daily).to_dict("records"),
        "settings": load_settings()
    }, ensure_ascii=False, indent=2)

def import_backup(uploaded_file):
    data = json.load(uploaded_file)
    holdings = normalize_holdings(pd.DataFrame(data.get("holdings", [])))
    trades = normalize_trades(pd.DataFrame(data.get("trades", [])))
    daily = normalize_daily(pd.DataFrame(data.get("daily", [])))
    save_csv(holdings, HOLDINGS_FILE, HOLDINGS_COLS)
    save_csv(trades, TRADES_FILE, TRADES_COLS)
    save_csv(daily, DAILY_FILE, DAILY_COLS)
    if "settings" in data:
        save_settings(data["settings"])


def prepare_trade_daily(trades):
    t = normalize_trades(trades).copy()
    if t.empty:
        return pd.DataFrame()
    t["date_dt"] = pd.to_datetime(t["date"], errors="coerce")
    t = t.dropna(subset=["date_dt"])
    if t.empty:
        return pd.DataFrame()
    g = t.groupby("date").agg(
        gross_realized=("gross_realized","sum"),
        net_realized=("net_realized","sum"),
        buy_fee=("buy_fee","sum"),
        sell_fee=("sell_fee","sum"),
        tax=("tax","sum"),
        trades_count=("symbol","count")
    ).reset_index()
    g["date_dt"] = pd.to_datetime(g["date"], errors="coerce")
    g["year"] = g["date_dt"].dt.year
    g["month_num"] = g["date_dt"].dt.month
    return g.sort_values("date_dt")

def prepare_daily_view(daily):
    d = normalize_daily(daily).copy()
    if d.empty:
        return d
    d["date_dt"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date_dt"]).sort_values("date_dt")
    d["daily_change"] = d["total_market_value"].diff()
    d["month"] = d["date_dt"].dt.to_period("M").astype(str)
    d["year"] = d["date_dt"].dt.year
    d["month_num"] = d["date_dt"].dt.month
    return d

def render_calendar(trades, year, month):
    d = prepare_trade_daily(trades)
    data = {}
    if not d.empty:
        mdf = d[(d["year"] == year) & (d["month_num"] == month)]
        for _, r in mdf.iterrows():
            data[int(r["date_dt"].day)] = r

    st.subheader(f"{year} 年 {month} 月價差月曆")
    week_names = ["一", "二", "三", "四", "五", "六", "日"]
    cols = st.columns(7)
    for i, w in enumerate(week_names):
        cols[i].markdown(f"**{w}**")

    cal = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown('<div class="calendar-empty"></div>', unsafe_allow_html=True)
            elif day in data:
                r = data[day]
                amount = float(r.get("net_realized", 0) or 0)
                cls = "gain" if amount > 0 else "loss" if amount < 0 else "flat"
                sign = "+" if amount > 0 else ""
                cols[i].markdown(f"""
                    <div class="calendar-card">
                        <b>{day}</b><br>
                        <span>價差</span><br>
                        <span class="{cls}">{sign}{money(amount)}</span><br>
                        <small>{int(r.get("trades_count", 0))} 筆交易</small>
                    </div>
                """, unsafe_allow_html=True)
            else:
                cols[i].markdown(f"""
                    <div class="calendar-empty">
                        <b>{day}</b><br><small>無價差</small>
                    </div>
                """, unsafe_allow_html=True)

def monthly_summary(daily):
    d = prepare_daily_view(daily)
    if d.empty:
        return pd.DataFrame()
    rows = []
    for m, g in d.groupby("month"):
        g = g.sort_values("date_dt")
        start = float(g["total_market_value"].iloc[0])
        end = float(g["total_market_value"].iloc[-1])
        change = end - start
        ret = change / start * 100 if start else 0
        rows.append({
            "月份": m,
            "月初資產": start,
            "月底資產": end,
            "月增減": change,
            "月報酬率%": ret,
            "月底未實現": float(g["unrealized_profit"].iloc[-1]),
            "月底已實現": float(g["realized_profit"].iloc[-1]),
            "月底總損益": float(g["total_profit"].iloc[-1]),
            "紀錄天數": len(g)
        })
    return pd.DataFrame(rows).sort_values("月份", ascending=False)

init_files()

with st.sidebar:
    usd_rate = st.number_input("USD/TWD 匯率", value=float(usd_twd_rate()), step=0.01)
    discount = st.number_input("台股手續費折扣", value=0.28, step=0.01, help="2.8折填 0.28；6折填 0.6")
    min_fee = st.number_input("最低手續費", value=1, step=1)

holdings = normalize_holdings(read_csv(HOLDINGS_FILE, HOLDINGS_COLS))
trades = normalize_trades(read_csv(TRADES_FILE, TRADES_COLS))
daily = normalize_daily(read_csv(DAILY_FILE, DAILY_COLS))

st.title("🐢 價差交易紀錄｜月曆版")
st.caption("v3 輸入區強化版｜新增買賣欄位更清楚，保留價差月曆、中文表頭、四種主題。")

colu1, colu2 = st.columns(2)
with colu1:
    if st.button("🔄 更新最新市價並記錄今日資產", use_container_width=True):
        progress = st.progress(0)
        status = []
        for i, row in holdings.iterrows():
            p = fetch_price(row["symbol"], row["market"])
            if p:
                holdings.loc[i, "price"] = p
                status.append(f"✅ {row['symbol']} → {p:.2f}")
            else:
                status.append(f"⚠️ {row['symbol']} 抓不到，保留 {row['price']}")
            progress.progress((i+1)/len(holdings))
        save_csv(holdings, HOLDINGS_FILE, HOLDINGS_COLS)
        save_daily_snapshot(holdings, trades, usd_rate)
        st.success("已更新市價並記錄今日資產")
        st.text("\n".join(status))
        st.rerun()

with colu2:
    if st.button("📌 只記錄今日資產", use_container_width=True):
        save_daily_snapshot(holdings, trades, usd_rate)
        st.success("已記錄今日資產")
        st.rerun()

dfv = calc_values(holdings, usd_rate)
total_market = dfv["market_value"].sum()
unrealized = dfv["unrealized_profit"].sum()
realized = realized_total(trades)
total_profit = unrealized + realized

c1,c2,c3,c4 = st.columns(4)
c1.metric("目前庫存市值", money(total_market) + " 元")
c2.metric("未實現損益", money(unrealized) + " 元")
c3.metric("已實現損益", money(realized) + " 元")
c4.metric("總損益", money(total_profit) + " 元")

tabs = st.tabs(["新增買賣", "庫存", "交易紀錄", "每日資產", "價差月曆", "每月統計", "損益統計", "備份/還原"])

with tabs[0]:
    st.subheader("新增買賣交易")
    st.markdown('<div class="trade-card">', unsafe_allow_html=True)
    st.markdown("#### ⭐ 常用股票")
    qcols = st.columns(6)
    common = [("00631L","元大台灣50正2","TW","TWD"),("2330","台積電","TW","TWD"),("00947","台新IC設計ETF","TW","TWD"),("QQQ","Invesco QQQ","US","USD"),("SMH","VanEck Semiconductor ETF","US","USD"),("NVDA","NVIDIA","US","USD")]
    if "quick_symbol" not in st.session_state:
        st.session_state.quick_symbol = "00631L"
        st.session_state.quick_name = ""
        st.session_state.quick_market = "TW"
        st.session_state.quick_currency = "TWD"
    for idx, (sym0, name0, market0, curr0) in enumerate(common):
        if qcols[idx].button(sym0, use_container_width=True):
            st.session_state.quick_symbol = sym0
            st.session_state.quick_name = name0
            st.session_state.quick_market = market0
            st.session_state.quick_currency = curr0
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="trade-card">', unsafe_allow_html=True)
    with st.form("trade_form"):
        st.markdown("#### 📝 輸入交易資料")
        a,b,c = st.columns(3)
        d = a.date_input("📅 交易日期", value=date.today())
        action = b.selectbox("🟢 買進 / 🔴 賣出", ["買進","賣出"])
        symbol = c.text_input("股票代碼，例如 00631L / 2330 / QQQ / SMH", value=st.session_state.get("quick_symbol","00631L")).upper()

        d1,d2,d3 = st.columns(3)
        name = d1.text_input("股票名稱，可空白", value=st.session_state.get("quick_name",""))
        market = d2.selectbox("市場", ["TW","US"], index=0 if st.session_state.get("quick_market","TW")=="TW" else 1)
        currency = d3.selectbox("幣別", ["TWD","USD"], index=0 if st.session_state.get("quick_currency","TWD")=="TWD" else 1)

        e1,e2,e3 = st.columns(3)
        qty = e1.number_input("請輸入股數", value=0.0, step=1.0)
        price = e2.number_input("請輸入成交價", value=0.0, step=0.01)
        auto_calc = e3.checkbox("✅ 自動計算手續費及證交稅", value=True)

        bf, sf, tx = auto_fee_tax(symbol, market, action, qty, price, discount, min_fee)
        st.markdown(f'<div class="fee-preview">手續費預覽：買進手續費 {money(bf)} ｜ 賣出手續費 {money(sf)} ｜ 證交稅/交易稅 {money(tx)}</div>', unsafe_allow_html=True)

        f1,f2,f3 = st.columns(3)
        buy_fee = f1.number_input("買進手續費", value=float(bf if auto_calc else 0), step=1.0)
        sell_fee = f2.number_input("賣出手續費", value=float(sf if auto_calc else 0), step=1.0)
        tax = f3.number_input("證交稅/交易稅", value=float(tx if auto_calc else 0), step=1.0)

        note = st.text_area("備註，例如：突破賣出、回補、短線價差")
        submitted = st.form_submit_button("✅ 立即新增交易並更新庫存", use_container_width=True)
        if submitted:
            holdings, trades = add_trade(holdings, trades, d.isoformat(), symbol, name, market, currency, action, qty, price, buy_fee, sell_fee, tax, note)
            save_csv(holdings, HOLDINGS_FILE, HOLDINGS_COLS)
            save_csv(trades, TRADES_FILE, TRADES_COLS)
            save_daily_snapshot(holdings, trades, usd_rate)
            st.success("已新增交易，並自動更新庫存與損益")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    st.subheader("目前庫存")
    show = dfv[["symbol","name","market","currency","shares","avg_cost","price","market_value","cost_value","unrealized_profit","return_rate"]]
    st.dataframe(zh(show), use_container_width=True, hide_index=True)
    st.subheader("手動修改庫存")
    edited_display = st.data_editor(zh(holdings), use_container_width=True, num_rows="dynamic", hide_index=True)
    edited = edited_display.rename(columns={v:k for k,v in CN_MAP.items()})
    if st.button("💾 儲存庫存修改"):
        save_csv(normalize_holdings(edited), HOLDINGS_FILE, HOLDINGS_COLS)
        st.success("已儲存庫存")
        st.rerun()

with tabs[2]:
    st.subheader("交易紀錄：可修改 / 刪除")
    st.warning("修改或刪除交易會更新交易紀錄與已實現損益；若該筆已影響庫存，請到庫存頁確認是否也要手動調整。")
    trades_manage = trades.copy()
    trades_manage.insert(0, "delete", False)
    for col in ["date", "symbol", "name", "market", "currency", "action", "note"]:
        trades_manage[col] = trades_manage[col].astype(str)
    for col in ["qty", "price", "buy_fee", "sell_fee", "tax", "gross_realized", "net_realized"]:
        trades_manage[col] = pd.to_numeric(trades_manage[col], errors="coerce").fillna(0.0)
    trades_manage["delete"] = trades_manage["delete"].fillna(False).astype(bool)
    edited_trades_display = st.data_editor(zh(trades_manage), use_container_width=True, hide_index=True, num_rows="dynamic")
    edited_trades = edited_trades_display.rename(columns={v:k for k,v in CN_MAP.items()})
    if st.button("💾 儲存交易修改 / 刪除", use_container_width=True):
        new_trades = edited_trades.copy()
        if "delete" in new_trades.columns:
            new_trades = new_trades[new_trades["delete"] == False].drop(columns=["delete"])
        new_trades = normalize_trades(new_trades)
        save_csv(new_trades, TRADES_FILE, TRADES_COLS)
        save_daily_snapshot(holdings, new_trades, usd_rate)
        st.success("已儲存交易修改 / 刪除")
        st.rerun()

with tabs[3]:
    st.subheader("每日資產紀錄")
    daily = normalize_daily(read_csv(DAILY_FILE, DAILY_COLS))
    if not daily.empty:
        dview = prepare_daily_view(daily)
        daily_show = dview.sort_values("date_dt", ascending=False).copy()
        daily_show["較前次變化"] = daily_show["daily_change"]
        st.dataframe(zh(daily_show.drop(columns=["date_dt","month","year","month_num"], errors="ignore")), use_container_width=True, hide_index=True)
        chart = dview.sort_values("date_dt").set_index("date")
        st.line_chart(chart[["total_market_value","unrealized_profit","realized_profit","total_profit"]])
    else:
        st.info("尚未有每日資產紀錄")

with tabs[4]:
    tview = prepare_trade_daily(trades)
    today = date.today()
    years = [today.year] if tview.empty else sorted(tview["year"].dropna().astype(int).unique().tolist(), reverse=True)
    col_y, col_m = st.columns(2)
    y = col_y.selectbox("年份", years, index=0)
    m = col_m.selectbox("月份", list(range(1,13)), index=today.month-1)
    render_calendar(trades, int(y), int(m))

with tabs[5]:
    st.subheader("每月統計")
    ms = monthly_summary(daily)
    if ms.empty:
        st.info("尚未有每日資產紀錄")
    else:
        st.dataframe(zh(ms), use_container_width=True, hide_index=True)
        st.bar_chart(ms.sort_values("月份").set_index("月份")["月增減"])

with tabs[6]:
    st.subheader("損益統計")
    if not trades.empty:
        t = normalize_trades(trades)
        t["month"] = pd.to_datetime(t["date"], errors="coerce").dt.to_period("M").astype(str)
        t["year"] = pd.to_datetime(t["date"], errors="coerce").dt.year.astype(str)
        st.write("依股票")
        st.dataframe(zh(t.groupby("symbol")[["gross_realized","buy_fee","sell_fee","tax","net_realized"]].sum().reset_index()), use_container_width=True, hide_index=True)
        st.write("依月份")
        st.dataframe(zh(t.groupby("month")[["gross_realized","buy_fee","sell_fee","tax","net_realized"]].sum().reset_index()), use_container_width=True, hide_index=True)
        st.write("依年度")
        st.dataframe(zh(t.groupby("year")[["gross_realized","buy_fee","sell_fee","tax","net_realized"]].sum().reset_index()), use_container_width=True, hide_index=True)
    else:
        st.info("尚未有交易紀錄")

with tabs[7]:
    st.subheader("備份 / 還原")
    st.info("建議每天操作完後，下載一次完整 JSON 備份。若資料遺失，可用匯入備份覆蓋回來。")
    backup_data = export_backup(holdings, trades, daily)
    st.download_button("⬇️ 匯出完整備份 JSON", data=backup_data, file_name=f"價差交易紀錄備份_{date.today().isoformat()}.json", mime="application/json", use_container_width=True)
    uploaded = st.file_uploader("匯入備份 JSON 並覆蓋目前資料", type=["json"])
    if uploaded is not None:
        st.warning("按下方按鈕後，會用備份檔覆蓋目前庫存、交易紀錄、每日資產。")
        if st.button("確認匯入並覆蓋資料", use_container_width=True):
            import_backup(uploaded)
            st.success("已匯入備份並覆蓋資料，請重新整理頁面。")
            st.rerun()
    st.divider()
    st.subheader("單獨下載 CSV")
    st.download_button("⬇️ 下載庫存 CSV", normalize_holdings(holdings).to_csv(index=False).encode("utf-8-sig"), "holdings.csv", "text/csv")
    st.download_button("⬇️ 下載交易 CSV", normalize_trades(trades).to_csv(index=False).encode("utf-8-sig"), "trades.csv", "text/csv")
    st.download_button("⬇️ 下載每日資產 CSV", normalize_daily(daily).to_csv(index=False).encode("utf-8-sig"), "daily_assets.csv", "text/csv")
