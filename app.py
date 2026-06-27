
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date
import json

try:
    import yfinance as yf
except Exception:
    yf = None

HOLDINGS_FILE = Path("holdings.csv")
TRADES_FILE = Path("trades.csv")
DAILY_FILE = Path("daily_assets.csv")

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

st.set_page_config(page_title="價差交易紀錄簡易版 v1.1", page_icon="📈", layout="wide")

st.markdown("""
<style>
.stApp{background:#F8F5EF;}
[data-testid="stMetric"]{background:#FFFDF8;border:1px solid #E8E0D0;border-radius:18px;padding:16px;box-shadow:0 4px 12px rgba(0,0,0,.05);}
h1,h2,h3{color:#4B443C;}
.stButton>button,.stDownloadButton>button{background:#D9C8A9;color:white;border:none;border-radius:14px;font-weight:700;}
section[data-testid="stSidebar"]{background:#F3EEE4;}
</style>
""", unsafe_allow_html=True)

def init_files():
    if not HOLDINGS_FILE.exists():
        pd.DataFrame(DEFAULT_HOLDINGS).to_csv(HOLDINGS_FILE, index=False, encoding="utf-8-sig")
    if not TRADES_FILE.exists():
        pd.DataFrame(columns=[
            "date","symbol","name","market","currency","action","qty","price","buy_fee","sell_fee","tax",
            "gross_realized","net_realized","note"
        ]).to_csv(TRADES_FILE, index=False, encoding="utf-8-sig")
    if not DAILY_FILE.exists():
        pd.DataFrame(columns=[
            "date","total_market_value","total_cost","unrealized_profit",
            "realized_profit","total_profit"
        ]).to_csv(DAILY_FILE, index=False, encoding="utf-8-sig")

def read_csv(path):
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(path)

def save_csv(df, path):
    df.to_csv(path, index=False, encoding="utf-8-sig")

def normalize_trades(trades):
    needed = {
        "date":"",
        "symbol":"",
        "name":"",
        "market":"TW",
        "currency":"TWD",
        "action":"買進",
        "qty":0.0,
        "price":0.0,
        "buy_fee":0.0,
        "sell_fee":0.0,
        "tax":0.0,
        "gross_realized":0.0,
        "net_realized":0.0,
        "note":""
    }
    for col, default in needed.items():
        if col not in trades.columns:
            trades[col] = default
    return trades[list(needed.keys())]

def normalize_holdings(holdings):
    needed = {
        "symbol":"",
        "name":"",
        "market":"TW",
        "currency":"TWD",
        "shares":0.0,
        "avg_cost":0.0,
        "price":0.0
    }
    for col, default in needed.items():
        if col not in holdings.columns:
            holdings[col] = default
    return holdings[list(needed.keys())]

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

def yf_symbol(symbol, market):
    s = str(symbol).upper().strip()
    if market == "US":
        return s
    return f"{s}.TW"

def fetch_price(symbol, market):
    if yf is None:
        return None
    s = str(symbol).upper().strip()
    candidates = [yf_symbol(s, market)]
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
    df = holdings.copy()
    df = normalize_holdings(df)
    fx = df["currency"].map(lambda x: usd_rate if x == "USD" else 1.0)
    df["market_value"] = df["shares"] * df["price"] * fx
    df["cost_value"] = df["shares"] * df["avg_cost"] * fx
    df["unrealized_profit"] = df["market_value"] - df["cost_value"]
    df["return_rate"] = df["unrealized_profit"] / df["cost_value"].replace(0, pd.NA) * 100
    return df

def realized_total(trades):
    if trades.empty:
        return 0.0
    return float(trades["net_realized"].fillna(0).sum())

def apply_single_trade(holdings, trade):
    symbol = str(trade.get("symbol","")).upper().strip()
    action = trade.get("action","買進")
    name = trade.get("name","")
    market = trade.get("market","TW")
    currency = trade.get("currency","TWD")
    qty = float(trade.get("qty",0) or 0)
    price = float(trade.get("price",0) or 0)
    buy_fee = float(trade.get("buy_fee",0) or 0)
    sell_fee = float(trade.get("sell_fee",0) or 0)
    tax = float(trade.get("tax",0) or 0)

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

    return holdings, gross_realized, net_realized

def add_trade(holdings, trades, d, symbol, name, market, currency, action, qty, price, buy_fee, sell_fee, tax, note):
    temp_trade = {
        "date":d,
        "symbol":symbol.upper().strip(),
        "name":name,
        "market":market,
        "currency":currency,
        "action":action,
        "qty":qty,
        "price":price,
        "buy_fee":buy_fee,
        "sell_fee":sell_fee,
        "tax":tax,
        "gross_realized":0.0,
        "net_realized":0.0,
        "note":note
    }
    holdings, gross, net = apply_single_trade(holdings, temp_trade)
    temp_trade["gross_realized"] = gross
    temp_trade["net_realized"] = net
    if not temp_trade["name"]:
        match = holdings[holdings["symbol"].str.upper().eq(temp_trade["symbol"])]
        temp_trade["name"] = match["name"].iloc[0] if not match.empty else temp_trade["symbol"]
    trades = pd.concat([trades, pd.DataFrame([temp_trade])], ignore_index=True)
    return holdings, trades

def rebuild_holdings_from_trades(original_holdings, trades):
    # 用目前庫存當初始資料會造成重複計算，所以這裡改用「交易前基礎庫存」欄位不可得的簡化邏輯：
    # 若要完全重算，請先在庫存頁手動整理基礎庫存，再修改/刪除交易後，系統會根據交易紀錄損益重新計算已實現損益。
    # 為避免誤改既有持股，這個函式只重算交易的 gross/net，不自動覆蓋庫存。
    holdings = original_holdings.copy()
    trades = trades.copy()
    for idx, tr in trades.iterrows():
        sym = str(tr.get("symbol","")).upper().strip()
        action = tr.get("action","買進")
        qty = float(tr.get("qty",0) or 0)
        price = float(tr.get("price",0) or 0)
        sell_fee = float(tr.get("sell_fee",0) or 0)
        tax = float(tr.get("tax",0) or 0)
        if action == "賣出":
            mask = holdings["symbol"].str.upper().eq(sym)
            if mask.any():
                avg_cost = float(holdings.loc[mask, "avg_cost"].iloc[0])
                gross = (price - avg_cost) * qty
                net = gross - sell_fee - tax
                trades.loc[idx, "gross_realized"] = gross
                trades.loc[idx, "net_realized"] = net
    return holdings, trades

def save_daily_snapshot(holdings, trades, usd_rate):
    dfv = calc_values(holdings, usd_rate)
    total_market = dfv["market_value"].sum()
    total_cost = dfv["cost_value"].sum()
    unrealized = dfv["unrealized_profit"].sum()
    realized = realized_total(trades)
    total_profit = unrealized + realized

    daily = read_csv(DAILY_FILE)
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
    save_csv(daily, DAILY_FILE)

init_files()

with st.sidebar:
    st.header("設定")
    usd_rate = st.number_input("USD/TWD 匯率", value=float(usd_twd_rate()), step=0.01)
    discount = st.number_input("台股手續費折扣", value=0.28, step=0.01, help="2.8折填 0.28；6折填 0.6")
    min_fee = st.number_input("最低手續費", value=1, step=1)

holdings = normalize_holdings(read_csv(HOLDINGS_FILE))
trades = normalize_trades(read_csv(TRADES_FILE))
daily = read_csv(DAILY_FILE)

st.title("📈 價差交易紀錄簡易版 v1.1")
st.caption("本版只修改交易紀錄：可修改交易、刪除交易，並重新計算已實現損益。")

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
        save_csv(holdings, HOLDINGS_FILE)
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
total_cost = dfv["cost_value"].sum()
unrealized = dfv["unrealized_profit"].sum()
realized = realized_total(trades)
total_profit = unrealized + realized

c1,c2,c3,c4 = st.columns(4)
c1.metric("目前庫存市值", money(total_market) + " 元")
c2.metric("未實現損益", money(unrealized) + " 元")
c3.metric("已實現損益", money(realized) + " 元")
c4.metric("總損益", money(total_profit) + " 元")

tabs = st.tabs(["新增買賣", "庫存", "交易紀錄", "每日資產", "損益統計", "備份"])

with tabs[0]:
    st.subheader("新增買賣交易")
    with st.form("trade_form"):
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
        auto_calc = e3.checkbox("自動計算台股手續費/稅", value=True)

        bf, sf, tx = auto_fee_tax(symbol, market, action, qty, price, discount, min_fee)
        f1,f2,f3 = st.columns(3)
        buy_fee = f1.number_input("買進手續費", value=float(bf if auto_calc else 0), step=1.0)
        sell_fee = f2.number_input("賣出手續費", value=float(sf if auto_calc else 0), step=1.0)
        tax = f3.number_input("證交稅/交易稅", value=float(tx if auto_calc else 0), step=1.0)

        note = st.text_area("備註")
        submitted = st.form_submit_button("新增交易並更新庫存")

        if submitted:
            holdings, trades = add_trade(
                holdings, trades, d.isoformat(), symbol, name, market, currency,
                action, qty, price, buy_fee, sell_fee, tax, note
            )
            save_csv(holdings, HOLDINGS_FILE)
            save_csv(trades, TRADES_FILE)
            save_daily_snapshot(holdings, trades, usd_rate)
            st.success("已新增交易，並自動更新庫存與損益")
            st.rerun()

with tabs[1]:
    st.subheader("目前庫存")
    show = dfv.copy()
    show = show[["symbol","name","market","currency","shares","avg_cost","price","market_value","cost_value","unrealized_profit","return_rate"]]
    st.dataframe(show, use_container_width=True, hide_index=True)

    st.subheader("手動修改庫存")
    edited = st.data_editor(holdings, use_container_width=True, num_rows="dynamic", hide_index=True)
    if st.button("💾 儲存庫存修改"):
        save_csv(normalize_holdings(edited), HOLDINGS_FILE)
        st.success("已儲存庫存")
        st.rerun()

with tabs[2]:
    st.subheader("交易紀錄：可修改 / 刪除")
    st.warning("提醒：修改或刪除交易後，會更新交易紀錄與已實現損益。若該筆已影響庫存，請確認庫存頁是否也需要手動調整。")

    trades_manage = trades.copy()
    trades_manage.insert(0, "delete", False)

    edited_trades = st.data_editor(
        trades_manage,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "delete": st.column_config.CheckboxColumn("刪除"),
            "date": st.column_config.TextColumn("日期"),
            "symbol": st.column_config.TextColumn("股票代碼"),
            "name": st.column_config.TextColumn("名稱"),
            "market": st.column_config.SelectboxColumn("市場", options=["TW","US"]),
            "currency": st.column_config.SelectboxColumn("幣別", options=["TWD","USD"]),
            "action": st.column_config.SelectboxColumn("動作", options=["買進","賣出"]),
            "qty": st.column_config.NumberColumn("股數"),
            "price": st.column_config.NumberColumn("成交價"),
            "buy_fee": st.column_config.NumberColumn("買進手續費"),
            "sell_fee": st.column_config.NumberColumn("賣出手續費"),
            "tax": st.column_config.NumberColumn("證交稅/交易稅"),
            "gross_realized": st.column_config.NumberColumn("已實現毛損益"),
            "net_realized": st.column_config.NumberColumn("已實現淨損益"),
            "note": st.column_config.TextColumn("備註"),
        }
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💾 儲存交易修改 / 刪除", use_container_width=True):
            new_trades = edited_trades.copy()
            if "delete" in new_trades.columns:
                new_trades = new_trades[new_trades["delete"] == False].drop(columns=["delete"])
            new_trades = normalize_trades(new_trades)

            # 重新計算賣出交易的 gross/net
            _, new_trades = rebuild_holdings_from_trades(holdings, new_trades)

            save_csv(new_trades, TRADES_FILE)
            save_daily_snapshot(holdings, new_trades, usd_rate)
            st.success("已儲存交易修改 / 刪除，並更新已實現損益")
            st.rerun()

    with col_b:
        if st.button("🧮 重新計算交易損益", use_container_width=True):
            _, new_trades = rebuild_holdings_from_trades(holdings, trades)
            save_csv(new_trades, TRADES_FILE)
            save_daily_snapshot(holdings, new_trades, usd_rate)
            st.success("已重新計算交易損益")
            st.rerun()

with tabs[3]:
    st.subheader("每日資產紀錄")
    daily = read_csv(DAILY_FILE)
    if not daily.empty:
        daily = daily.sort_values("date", ascending=False)
        daily["較前次變化"] = daily["total_market_value"].diff(-1)
        st.dataframe(daily, use_container_width=True, hide_index=True)
        chart = daily.sort_values("date").set_index("date")
        st.line_chart(chart[["total_market_value","unrealized_profit","realized_profit","total_profit"]])
    else:
        st.info("尚未有每日資產紀錄")

with tabs[4]:
    st.subheader("損益統計")
    if not trades.empty:
        t = trades.copy()
        t["month"] = pd.to_datetime(t["date"], errors="coerce").dt.to_period("M").astype(str)
        t["year"] = pd.to_datetime(t["date"], errors="coerce").dt.year.astype(str)
        st.write("依股票")
        st.dataframe(t.groupby("symbol")[["gross_realized","buy_fee","sell_fee","tax","net_realized"]].sum().reset_index(), use_container_width=True, hide_index=True)
        st.write("依月份")
        st.dataframe(t.groupby("month")[["gross_realized","buy_fee","sell_fee","tax","net_realized"]].sum().reset_index(), use_container_width=True, hide_index=True)
        st.write("依年度")
        st.dataframe(t.groupby("year")[["gross_realized","buy_fee","sell_fee","tax","net_realized"]].sum().reset_index(), use_container_width=True, hide_index=True)
    else:
        st.info("尚未有交易紀錄")

with tabs[5]:
    st.subheader("備份下載")
    backup = {
        "holdings": holdings.to_dict("records"),
        "trades": trades.to_dict("records"),
        "daily": read_csv(DAILY_FILE).to_dict("records")
    }
    st.download_button(
        "⬇️ 下載完整 JSON 備份",
        data=json.dumps(backup, ensure_ascii=False, indent=2),
        file_name="價差交易紀錄備份.json",
        mime="application/json",
        use_container_width=True
    )

    st.download_button("⬇️ 下載庫存 CSV", holdings.to_csv(index=False).encode("utf-8-sig"), "holdings.csv", "text/csv")
    st.download_button("⬇️ 下載交易 CSV", trades.to_csv(index=False).encode("utf-8-sig"), "trades.csv", "text/csv")
    st.download_button("⬇️ 下載每日資產 CSV", read_csv(DAILY_FILE).to_csv(index=False).encode("utf-8-sig"), "daily_assets.csv", "text/csv")
