
import streamlit as st
import pandas as pd
from datetime import date
import json

try:
    import yfinance as yf
except Exception:
    yf = None

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:
    gspread = None
    Credentials = None

st.set_page_config(page_title="價差交易紀錄｜Google雲端版", page_icon="📈", layout="wide")

st.markdown("""
<style>
.stApp{background:#F8F5EF;}
[data-testid="stMetric"]{background:#FFFDF8;border:1px solid #E8E0D0;border-radius:18px;padding:16px;box-shadow:0 4px 12px rgba(0,0,0,.05);}
h1,h2,h3{color:#4B443C;}
.stButton>button,.stDownloadButton>button{background:#D9C8A9;color:white;border:none;border-radius:14px;font-weight:700;}
section[data-testid="stSidebar"]{background:#F3EEE4;}
</style>
""", unsafe_allow_html=True)

HOLDINGS_COLS = ["symbol","name","market","currency","shares","avg_cost","price"]
TRADES_COLS = ["date","symbol","name","market","currency","action","qty","price","buy_fee","sell_fee","tax","gross_realized","net_realized","note"]
DAILY_COLS = ["date","total_market_value","total_cost","unrealized_profit","realized_profit","total_profit"]

DEFAULT_HOLDINGS = [
    ["00947","台新臺灣IC設計動能ETF","TW","TWD",1004,25.78,25.78],
    ["SOXQ","Invesco費城半導體ETF","US","USD",2,94.685,94.685],
    ["1310","台苯","TW","TWD",1000,9.52,9.52],
    ["2330","台積電","TW","TWD",530,537.79,1778.5],
    ["00631L","元大台灣50正2","TW","TWD",4070,26.66,38.33],
    ["00830","國泰費城半導體ETF","TW","TWD",1056,81.77,81.77],
    ["2302","麗正","TW","TWD",1000,19.53,19.53],
    ["2337","旺宏","TW","TWD",1000,149.71,149.71],
    ["2408","南亞科","TW","TWD",200,227.32,227.32],
    ["3491","昇達科","TW","TWD",5,1557.2,1557.2],
    ["6116","彩晶","TW","TWD",3000,10.31,10.31],
    ["6558","興能高","TW","TWD",2000,36,36],
    ["6603","富強鑫","TW","TWD",1000,26.64,26.64],
    ["6770","力積電","TW","TWD",1000,63.79,63.79],
    ["NVDA","NVIDIA","US","USD",1,142.95,142.95],
    ["QQQ","Invesco QQQ","US","USD",1.55011,645.15,645.15],
]

def get_sheet():
    if gspread is None or Credentials is None:
        st.error("缺少 gspread/google-auth，請確認 requirements.txt 已上傳。")
        st.stop()
    try:
        info = dict(st.secrets["gcp_service_account"])
        sid = st.secrets["GOOGLE_SHEET_ID"]
    except Exception:
        st.error("尚未設定 Streamlit Secrets：GOOGLE_SHEET_ID 與 [gcp_service_account]。")
        st.stop()
    scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds).open_by_key(sid)

def ws(sheet, title, cols):
    try:
        w = sheet.worksheet(title)
    except Exception:
        w = sheet.add_worksheet(title=title, rows=1000, cols=max(len(cols),10))
        w.update([cols])
    if not w.get_all_values():
        w.update([cols])
    return w

def ws_df(w, cols):
    df = pd.DataFrame(w.get_all_records())
    for c in cols:
        if c not in df.columns:
            df[c] = "" if c in ["date","symbol","name","market","currency","action","note"] else 0.0
    return df[cols]

def save_ws(w, df, cols):
    df = df.copy()
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df = df[cols].fillna("")
    w.clear()
    w.update([cols] + df.astype(str).values.tolist())

def to_num(df, cols):
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df

def norm_holdings(df):
    for c in HOLDINGS_COLS:
        if c not in df.columns:
            df[c] = "" if c in ["symbol","name","market","currency"] else 0.0
    df = df[HOLDINGS_COLS]
    return to_num(df, ["shares","avg_cost","price"])

def norm_trades(df):
    for c in TRADES_COLS:
        if c not in df.columns:
            df[c] = "" if c in ["date","symbol","name","market","currency","action","note"] else 0.0
    df = df[TRADES_COLS]
    return to_num(df, ["qty","price","buy_fee","sell_fee","tax","gross_realized","net_realized"])

def norm_daily(df):
    for c in DAILY_COLS:
        if c not in df.columns:
            df[c] = "" if c == "date" else 0.0
    df = df[DAILY_COLS]
    return to_num(df, ["total_market_value","total_cost","unrealized_profit","realized_profit","total_profit"])

def money(x):
    try: return f"{float(x):,.0f}"
    except Exception: return "0"

def usd_rate_default():
    if yf:
        try:
            h = yf.Ticker("TWD=X").history(period="5d")
            if not h.empty: return float(h["Close"].dropna().iloc[-1])
        except Exception:
            pass
    return 32.0

def fetch_price(symbol, market):
    if yf is None: return None
    s = str(symbol).upper().strip()
    candidates = [s if market == "US" else f"{s}.TW"]
    if market == "TW": candidates.append(f"{s}.TWO")
    for t in candidates:
        try:
            h = yf.Ticker(t).history(period="5d")
            if not h.empty: return float(h["Close"].dropna().iloc[-1])
        except Exception:
            pass
    return None

def is_etf(symbol):
    s = str(symbol).upper()
    return s.startswith(("00","006","007","008","009")) or s in ["QQQ","SMH","SOXQ","VOO","SPY","SOXX"]

def fee_tax(symbol, market, action, qty, price, discount, min_fee):
    amt = float(qty) * float(price)
    bf = sf = tax = 0.0
    if market == "TW" and amt > 0:
        fee = max(round(amt * 0.001425 * discount), int(min_fee))
        if action == "買進": bf = fee
        if action == "賣出":
            sf = fee
            tax = round(amt * (0.001 if is_etf(symbol) else 0.003))
    return bf, sf, tax

def calc_values(h, usd):
    df = h.copy()
    fx = df["currency"].map(lambda x: usd if x == "USD" else 1.0)
    df["market_value"] = df["shares"] * df["price"] * fx
    df["cost_value"] = df["shares"] * df["avg_cost"] * fx
    df["unrealized_profit"] = df["market_value"] - df["cost_value"]
    df["return_rate"] = df["unrealized_profit"] / df["cost_value"].replace(0, pd.NA) * 100
    return df

def realized_total(t):
    return 0.0 if t.empty else float(t["net_realized"].fillna(0).sum())

def add_trade(h, t, d, symbol, name, market, currency, action, qty, price, bf, sf, tax, note):
    symbol = symbol.upper().strip()
    mask = h["symbol"].str.upper().eq(symbol)
    gross = net = 0.0
    qty = float(qty); price = float(price)
    if action == "買進":
        total = qty * price + float(bf)
        if mask.any():
            i = h[mask].index[0]
            oldq = float(h.loc[i,"shares"]); oldc = float(h.loc[i,"avg_cost"])
            newq = oldq + qty
            h.loc[i,"shares"] = newq
            h.loc[i,"avg_cost"] = ((oldq*oldc)+total)/newq if newq else price
            h.loc[i,"price"] = price
            if name: h.loc[i,"name"] = name
        else:
            h = pd.concat([h, pd.DataFrame([{"symbol":symbol,"name":name or symbol,"market":market,"currency":currency,"shares":qty,"avg_cost":total/qty if qty else price,"price":price}])], ignore_index=True)
    elif action == "賣出" and mask.any():
        i = h[mask].index[0]
        oldq = float(h.loc[i,"shares"]); avg = float(h.loc[i,"avg_cost"])
        sellq = min(qty, oldq)
        gross = (price - avg) * sellq
        net = gross - float(sf) - float(tax)
        h.loc[i,"shares"] = oldq - sellq
        h.loc[i,"price"] = price
    row = {"date":d,"symbol":symbol,"name":name or symbol,"market":market,"currency":currency,"action":action,"qty":qty,"price":price,"buy_fee":bf,"sell_fee":sf,"tax":tax,"gross_realized":gross,"net_realized":net,"note":note}
    t = pd.concat([t, pd.DataFrame([row])], ignore_index=True)
    return h, t

def save_daily(daily, h, t, usd):
    v = calc_values(h, usd)
    row = {"date":date.today().isoformat(),"total_market_value":v["market_value"].sum(),"total_cost":v["cost_value"].sum(),"unrealized_profit":v["unrealized_profit"].sum(),"realized_profit":realized_total(t),"total_profit":v["unrealized_profit"].sum()+realized_total(t)}
    if not daily.empty and (daily["date"] == row["date"]).any():
        for k,vv in row.items():
            daily.loc[daily["date"] == row["date"], k] = vv
    else:
        daily = pd.concat([daily, pd.DataFrame([row])], ignore_index=True)
    return daily

sheet = get_sheet()
hws = ws(sheet, "Holdings", HOLDINGS_COLS)
tws = ws(sheet, "Trades", TRADES_COLS)
dws = ws(sheet, "Daily", DAILY_COLS)

holdings = norm_holdings(ws_df(hws, HOLDINGS_COLS))
if holdings.empty:
    holdings = pd.DataFrame(DEFAULT_HOLDINGS, columns=HOLDINGS_COLS)
    save_ws(hws, holdings, HOLDINGS_COLS)
trades = norm_trades(ws_df(tws, TRADES_COLS))
daily = norm_daily(ws_df(dws, DAILY_COLS))

with st.sidebar:
    st.header("設定")
    usd = st.number_input("USD/TWD 匯率", value=float(usd_rate_default()), step=0.01)
    discount = st.number_input("台股手續費折扣", value=0.28, step=0.01)
    min_fee = st.number_input("最低手續費", value=1, step=1)

st.title("📈 價差交易紀錄｜Google Sheets 雲端永久版")
st.caption("新增、修改、刪除與每日紀錄都會同步到 Google Sheets，不怕斷線或 Streamlit 重啟。")

col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 更新最新市價並記錄今日資產", use_container_width=True):
        progress = st.progress(0)
        msg = []
        for i,row in holdings.iterrows():
            p = fetch_price(row["symbol"], row["market"])
            if p:
                holdings.loc[i,"price"] = p
                msg.append(f"✅ {row['symbol']} → {p:.2f}")
            else:
                msg.append(f"⚠️ {row['symbol']} 抓不到，保留 {row['price']}")
            progress.progress((i+1)/len(holdings))
        daily = save_daily(daily, holdings, trades, usd)
        save_ws(hws, holdings, HOLDINGS_COLS)
        save_ws(dws, daily, DAILY_COLS)
        st.success("已同步 Google Sheets")
        st.text("\\n".join(msg))
        st.rerun()

with col2:
    if st.button("📌 只記錄今日資產", use_container_width=True):
        daily = save_daily(daily, holdings, trades, usd)
        save_ws(dws, daily, DAILY_COLS)
        st.success("已記錄到 Google Sheets")
        st.rerun()

dfv = calc_values(holdings, usd)
unreal = dfv["unrealized_profit"].sum()
realized = realized_total(trades)
c1,c2,c3,c4 = st.columns(4)
c1.metric("目前庫存市值", money(dfv["market_value"].sum())+" 元")
c2.metric("未實現損益", money(unreal)+" 元")
c3.metric("已實現損益", money(realized)+" 元")
c4.metric("總損益", money(unreal+realized)+" 元")

tabs = st.tabs(["新增買賣","庫存","交易紀錄","每日資產","損益統計","備份"])

with tabs[0]:
    st.subheader("新增買賣交易")
    with st.form("trade"):
        a,b,c = st.columns(3)
        d = a.date_input("日期", value=date.today())
        action = b.selectbox("動作", ["買進","賣出"])
        symbol = c.text_input("股票代碼", value="00631L").upper()
        d1,d2,d3 = st.columns(3)
        name = d1.text_input("名稱", value="")
        market = d2.selectbox("市場", ["TW","US"])
        currency = d3.selectbox("幣別", ["TWD","USD"])
        e1,e2,e3 = st.columns(3)
        qty = e1.number_input("股數", value=0.0, step=1.0)
        price = e2.number_input("成交價", value=0.0, step=0.01)
        auto = e3.checkbox("自動計算台股手續費/稅", value=True)
        abf, asf, atax = fee_tax(symbol, market, action, qty, price, discount, min_fee)
        f1,f2,f3 = st.columns(3)
        bf = f1.number_input("買進手續費", value=float(abf if auto else 0), step=1.0)
        sf = f2.number_input("賣出手續費", value=float(asf if auto else 0), step=1.0)
        tax = f3.number_input("證交稅/交易稅", value=float(atax if auto else 0), step=1.0)
        note = st.text_area("備註")
        if st.form_submit_button("新增交易並同步 Google Sheets"):
            holdings, trades = add_trade(holdings, trades, d.isoformat(), symbol, name, market, currency, action, qty, price, bf, sf, tax, note)
            daily = save_daily(daily, holdings, trades, usd)
            save_ws(hws, holdings, HOLDINGS_COLS)
            save_ws(tws, trades, TRADES_COLS)
            save_ws(dws, daily, DAILY_COLS)
            st.success("已新增並同步")
            st.rerun()

with tabs[1]:
    st.subheader("目前庫存")
    st.dataframe(dfv[["symbol","name","market","currency","shares","avg_cost","price","market_value","cost_value","unrealized_profit","return_rate"]], use_container_width=True, hide_index=True)
    st.subheader("手動修改庫存")
    edited = st.data_editor(holdings, use_container_width=True, num_rows="dynamic", hide_index=True)
    if st.button("💾 儲存庫存修改到 Google Sheets"):
        edited = norm_holdings(edited)
        save_ws(hws, edited, HOLDINGS_COLS)
        st.success("已儲存")
        st.rerun()

with tabs[2]:
    st.subheader("交易紀錄：可修改 / 刪除")
    manage = trades.copy()
    manage.insert(0, "delete", False)
    for col in ["date","symbol","name","market","currency","action","note"]:
        manage[col] = manage[col].astype(str)
    for col in ["qty","price","buy_fee","sell_fee","tax","gross_realized","net_realized"]:
        manage[col] = pd.to_numeric(manage[col], errors="coerce").fillna(0.0)
    manage["delete"] = manage["delete"].astype(bool)
    edited_t = st.data_editor(manage, use_container_width=True, hide_index=True, num_rows="dynamic")
    if st.button("💾 儲存交易修改 / 刪除到 Google Sheets", use_container_width=True):
        new_t = edited_t.copy()
        if "delete" in new_t.columns:
            new_t = new_t[new_t["delete"] == False].drop(columns=["delete"])
        new_t = norm_trades(new_t)
        save_ws(tws, new_t, TRADES_COLS)
        daily = save_daily(daily, holdings, new_t, usd)
        save_ws(dws, daily, DAILY_COLS)
        st.success("已同步交易修改/刪除")
        st.rerun()

with tabs[3]:
    st.subheader("每日資產紀錄")
    if daily.empty:
        st.info("尚未有每日資產紀錄")
    else:
        show = daily.sort_values("date", ascending=False).copy()
        show["較前次變化"] = show["total_market_value"].diff(-1)
        st.dataframe(show, use_container_width=True, hide_index=True)
        st.line_chart(daily.sort_values("date").set_index("date")[["total_market_value","unrealized_profit","realized_profit","total_profit"]])

with tabs[4]:
    st.subheader("損益統計")
    if trades.empty:
        st.info("尚未有交易紀錄")
    else:
        t = trades.copy()
        t["month"] = pd.to_datetime(t["date"], errors="coerce").dt.to_period("M").astype(str)
        t["year"] = pd.to_datetime(t["date"], errors="coerce").dt.year.astype(str)
        st.write("依股票")
        st.dataframe(t.groupby("symbol")[["gross_realized","buy_fee","sell_fee","tax","net_realized"]].sum().reset_index(), use_container_width=True, hide_index=True)
        st.write("依月份")
        st.dataframe(t.groupby("month")[["gross_realized","buy_fee","sell_fee","tax","net_realized"]].sum().reset_index(), use_container_width=True, hide_index=True)
        st.write("依年度")
        st.dataframe(t.groupby("year")[["gross_realized","buy_fee","sell_fee","tax","net_realized"]].sum().reset_index(), use_container_width=True, hide_index=True)

with tabs[5]:
    backup = {"holdings":holdings.to_dict("records"),"trades":trades.to_dict("records"),"daily":daily.to_dict("records")}
    st.download_button("⬇️ 下載完整 JSON 備份", json.dumps(backup, ensure_ascii=False, indent=2), "價差交易紀錄Google版備份.json", "application/json", use_container_width=True)
