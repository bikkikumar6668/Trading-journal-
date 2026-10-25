import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ----------------------------------------
# 1. Page Configuration & Styling
# ----------------------------------------
st.set_page_config(
    page_title="AlphaLog - Trading Journal & Analytics",
    page_icon="ðŸ“ˆ",
    layout="wide"
)

# Custom CSS for styling metric cards
st.markdown("""
    <style>
    .metric-card {
        background-color: #1e222d;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #2a2e39;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------
# 2. Session State Initialization
# ----------------------------------------
# Initialize an empty DataFrame in session state if it doesn't exist
if "trades_data" not in st.session_state:
    st.session_state.trades_data = pd.DataFrame(columns=[
        "Date", "Symbol", "Trade_Type", "Quantity", "Buy_Price", 
        "Sell_Price", "Net_PnL", "Strategy", "Mistake_Tag"
    ])

# ----------------------------------------
# 3. Helper Functions
# ----------------------------------------
def calculate_metrics(df):
    """Calculates key trading performance metrics from the trade log."""
    if df.empty:
        return 0, 0, 0, 0, 0
    
    total_trades = len(df)
    total_pnl = df["Net_PnL"].sum()
    winning_trades = df[df["Net_PnL"] > 0]
    losing_trades = df[df["Net_PnL"] < 0]
    
    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    total_profit = winning_trades["Net_PnL"].sum()
    total_loss = abs(losing_trades["Net_PnL"].sum())
    profit_factor = round(total_profit / total_loss, 2) if total_loss > 0 else total_profit
    
    return total_trades, total_pnl, win_rate, profit_factor, len(winning_trades)

# ----------------------------------------
# 4. Sidebar Navigation
# ----------------------------------------
st.sidebar.title("âš¡ AlphaLog Controls")
menu = st.sidebar.radio("Navigation", ["Dashboard & Analytics", "Add Manual Trade", "Upload Tradebook (CSV)"])

# ----------------------------------------
# 5. Application Views
# ----------------------------------------

# Section A: Manual Trade Entry
if menu == "Add Manual Trade":
    st.subheader("ðŸ“ Log a New Trade")
    
    with st.form("trade_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            trade_date = st.date_input("Trade Date", datetime.today())
            symbol = st.text_input("Instrument / Symbol (e.g. NIFTY24OCT25500CE, RELIANCE)").upper()
            trade_type = st.selectbox("Type", ["Intraday", "Swing", "F&O Option", "Futures"])
        with col2:
            qty = st.number_input("Quantity", min_value=1, step=1, value=50)
            buy_price = st.number_input("Buy Price (Avg)", min_value=0.05, step=0.05, format="%.2f")
            sell_price = st.number_input("Sell Price (Avg)", min_value=0.05, step=0.05, format="%.2f")
        with col3:
            strategy = st.selectbox("Setup / Strategy", ["Breakout", "Support/Resistance", "CPR Pullback", "Option Scalping", "Trend Following"])
            mistake = st.selectbox("Behavioral Tag", ["Rule Followed (Clean)", "FOMO Entry", "Revenge Trade", "Late Exit", "Over Leveraged"])
            
        submitted = st.form_submit_button("Save Trade")
        
        if submitted:
            if symbol.strip() == "":
                st.error("Kripya Instrument / Symbol enter karein.")
            else:
                net_pnl = round((sell_price - buy_price) * qty, 2)
                new_entry = {
                    "Date": pd.to_datetime(trade_date),
                    "Symbol": symbol,
                    "Trade_Type": trade_type,
                    "Quantity": qty,
                    "Buy_Price": buy_price,
                    "Sell_Price": sell_price,
                    "Net_PnL": net_pnl,
                    "Strategy": strategy,
                    "Mistake_Tag": mistake
                }
                # Append the new trade to the session state dataframe
                st.session_state.trades_data = pd.concat([st.session_state.trades_data, pd.DataFrame([new_entry])], ignore_index=True)
                st.success(f"Trade saved successfully! Net P&L: â‚¹{net_pnl}")

# Section B: CSV Upload (Broker Parser Engine)
elif menu == "Upload Tradebook (CSV)":
    st.subheader("ðŸ“‚ Upload Broker Tradebook")
    st.write("Upload a CSV file containing columns: `Date`, `Symbol`, `Quantity`, `Buy_Price`, `Sell_Price`")
    
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file)
            df_upload["Date"] = pd.to_datetime(df_upload["Date"])
            
            # Fill missing required columns
            if "Net_PnL" not in df_upload.columns:
                df_upload["Net_PnL"] = (df_upload["Sell_Price"] - df_upload["Buy_Price"]) * df_upload["Quantity"]
            if "Strategy" not in df_upload.columns:
                df_upload["Strategy"] = "Uploaded"
            if "Mistake_Tag" not in df_upload.columns:
                df_upload["Mistake_Tag"] = "Rule Followed (Clean)"
            if "Trade_Type" not in df_upload.columns:
                df_upload["Trade_Type"] = "Equity/F&O"
                
            st.session_state.trades_data = pd.concat([st.session_state.trades_data, df_upload], ignore_index=True)
            st.success(f"Successfully imported {len(df_upload)} trades!")
        except Exception as e:
            st.error(f"Error parsing file: {e}")

# Section C: Dashboard & Analytics
elif menu == "Dashboard & Analytics":
    st.title("ðŸ“Š Trading Journal & Performance Dashboard")
    df = st.session_state.trades_data
    
    if df.empty:
        st.info("Abhi koi trades log nahi hue hain. Sidebar se manual trade add karein ya CSV upload karein.")
    else:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(by="Date")
        
        # 1. Performance Metrics Grid
        total_trades, total_pnl, win_rate, profit_factor, wins = calculate_metrics(df)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Trades", total_trades)
        c2.metric("Cumulative Net P&L", f"â‚¹{total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
        c3.metric("Win Rate", f"{win_rate:.1f}%")
        c4.metric("Profit Factor", f"{profit_factor}")
        
        st.markdown("---")
        
        # 2. Cumulative Equity Curve Plot
        df["Cumulative_PnL"] = df["Net_PnL"].cumsum()
        fig_curve = px.line(
            df, 
            x="Date", 
            y="Cumulative_PnL", 
            title="Equity Curve (Cumulative Returns)",
            markers=True
        )
        # Dynamic color based on profitability
        fig_curve.update_traces(line_color="#00C805" if total_pnl >= 0 else "#FF3B30")
        st.plotly_chart(fig_curve, use_container_width=True)
        
        col_chart1, col_chart2 = st.columns(2)
        
        # 3. P&L Breakdown by Strategy
        with col_chart1:
            strat_perf = df.groupby("Strategy")["Net_PnL"].sum().reset_index()
            fig_strat = px.bar(
                strat_perf, 
                x="Strategy", 
                y="Net_PnL", 
                color="Net_PnL",
                color_continuous_scale=["#FF3B30", "#00C805"],
                title="P&L by Strategy"
            )
            st.plotly_chart(fig_strat, use_container_width=True)
            
        # 4. Mistakes & Behavioral Impact Pie Chart
        with col_chart2:
            mistake_counts = df["Mistake_Tag"].value_counts().reset_index()
            mistake_counts.columns = ["Mistake", "Count"]
            fig_mistake = px.pie(
                mistake_counts, 
                names="Mistake", 
                values="Count", 
                hole=0.4,
                title="Trading Psychology & Mistake Breakdown"
            )
            st.plotly_chart(fig_mistake, use_container_width=True)
            
        st.markdown("---")
        
        # 5. Detailed Trade Log Dataframe
        st.subheader("ðŸ“‹ Executed Trades History")
        st.dataframe(
            df[["Date", "Symbol", "Trade_Type", "Quantity", "Buy_Price", "Sell_Price", "Net_PnL", "Strategy", "Mistake_Tag"]],
            use_container_width=True
  )

  import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="AlphaLog - Trading Journal & Analytics",
    page_icon="ðŸ“ˆ",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #1e222d;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #2a2e39;
    }
    </style>
""", unsafe_allow_html=True)

# Session State for Trade Storage
if "trades_data" not in st.session_state:
    st.session_state.trades_data = pd.DataFrame(columns=[
        "Date", "Symbol", "Trade_Type", "Quantity", "Buy_Price", "Sell_Price", "Net_PnL", "Strategy", "Mistake_Tag"
    ])

def calculate_metrics(df):
    if df.empty:
        return 0, 0, 0, 0, 0
    total_trades = len(df)
    total_pnl = df["Net_PnL"].sum()
    winning_trades = df[df["Net_PnL"] > 0]
    losing_trades = df[df["Net_PnL"] < 0]
    
    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    total_profit = winning_trades["Net_PnL"].sum()
    total_loss = abs(losing_trades["Net_PnL"].sum())
    profit_factor = round(total_profit / total_loss, 2) if total_loss > 0 else total_profit
    
    return total_trades, total_pnl, win_rate, profit_factor, len(winning_trades)

# Sidebar Navigation
st.sidebar.title("âš¡ AlphaLog Controls")
menu = st.sidebar.radio("Navigation", ["Dashboard & Analytics", "Add Manual Trade", "Upload Tradebook (CSV / Excel)"])

# Section 1: Manual Trade Entry
if menu == "Add Manual Trade":
    st.subheader("ðŸ“ Log a New Trade")
    
    with st.form("trade_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            trade_date = st.date_input("Trade Date", datetime.today())
            symbol = st.text_input("Instrument / Symbol (e.g. NIFTY, BANKNIFTY, RELIANCE)").upper()
            trade_type = st.selectbox("Type", ["Intraday", "Swing", "F&O Option", "Futures"])
        with col2:
            qty = st.number_input("Quantity", min_value=1, step=1, value=50)
            buy_price = st.number_input("Buy Price (Avg)", min_value=0.05, step=0.05, format="%.2f")
            sell_price = st.number_input("Sell Price (Avg)", min_value=0.05, step=0.05, format="%.2f")
        with col3:
            strategy = st.selectbox("Setup / Strategy", ["Breakout", "Support/Resistance", "CPR Pullback", "Option Scalping", "Trend Following"])
            mistake = st.selectbox("Behavioral Tag", ["Rule Followed (Clean)", "FOMO Entry", "Revenge Trade", "Late Exit", "Over Leveraged"])
            
        submitted = st.form_submit_button("Save Trade")
        
        if submitted:
            if symbol.strip() == "":
                st.error("Kripya Instrument / Symbol enter karein.")
            else:
                net_pnl = round((sell_price - buy_price) * qty, 2)
                new_entry = {
                    "Date": pd.to_datetime(trade_date),
                    "Symbol": symbol,
                    "Trade_Type": trade_type,
                    "Quantity": qty,
                    "Buy_Price": buy_price,
                    "Sell_Price": sell_price,
                    "Net_PnL": net_pnl,
                    "Strategy": strategy,
                    "Mistake_Tag": mistake
                }
                st.session_state.trades_data = pd.concat([st.session_state.trades_data, pd.DataFrame([new_entry])], ignore_index=True)
                st.success(f"Trade successfully save ho gaya! Net P&L: â‚¹{net_pnl}")

# Section 2: CSV / Excel Upload Parser
elif menu == "Upload Tradebook (CSV / Excel)":
    st.subheader("ðŸ“‚ Upload Broker Tradebook (CSV ya Excel)")
    st.write("Aap CSV ya Excel (.xlsx / .xls) file upload kar sakte hain jismein ye columns hon: `Date`, `Symbol`, `Quantity`, `Buy_Price`, `Sell_Price`")
    
    uploaded_file = st.file_uploader("Upload CSV ya Excel File", type=["csv", "xlsx", "xls"])
    if uploaded_file is not None:
        try:
            # File type ke hisaab se reader select karein
            if uploaded_file.name.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            
            # Column headers ko clean karein (strip extra spaces)
            df_upload.columns = df_upload.columns.str.strip()
            
            # Date format parsing
            df_upload["Date"] = pd.to_datetime(df_upload["Date"])
            
            # Agar Net_PnL column pehle se nahi hai toh auto-calculate karein
            if "Net_PnL" not in df_upload.columns:
                df_upload["Net_PnL"] = (df_upload["Sell_Price"] - df_upload["Buy_Price"]) * df_upload["Quantity"]
            
            if "Strategy" not in df_upload.columns:
                df_upload["Strategy"] = "Uploaded"
            if "Mistake_Tag" not in df_upload.columns:
                df_upload["Mistake_Tag"] = "Rule Followed (Clean)"
            if "Trade_Type" not in df_upload.columns:
                df_upload["Trade_Type"] = "Equity/F&O"
                
            st.session_state.trades_data = pd.concat([st.session_state.trades_data, df_upload], ignore_index=True)
            st.success(f"File se {len(df_upload)} trades successfully import ho gaye!")
        except Exception as e:
            st.error(f"File parse karne mein error aaya: {e}")

# Section 3: Dashboard & Visual Analytics
elif menu == "Dashboard & Analytics":
    st.title("ðŸ“Š Trading Journal & Performance Dashboard")
    df = st.session_state.trades_data
    
    if df.empty:
        st.info("Abhi koi trades available nahi hain. Sidebar se manual trade add karein ya Excel/CSV file upload karein.")
    else:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(by="Date")
        
        # Summary Metrics
        total_trades, total_pnl, win_rate, profit_factor, wins = calculate_metrics(df)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Trades", total_trades)
        c2.metric("Cumulative Net P&L", f"â‚¹{total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
        c3.metric("Win Rate", f"{win_rate:.1f}%")
        c4.metric("Profit Factor", f"{profit_factor}")
        
        st.markdown("---")
        
        # Cumulative Equity Curve
        df["Cumulative_PnL"] = df["Net_PnL"].cumsum()
        fig_curve = px.line(
            df, 
            x="Date", 
            y="Cumulative_PnL", 
            title="Equity Curve (Cumulative Returns)",
            markers=True
        )
        fig_curve.update_traces(line_color="#00C805" if total_pnl >= 0 else "#FF3B30")
        st.plotly_chart(fig_curve, use_container_width=True)
        
        col_chart1, col_chart2 = st.columns(2)
        
        # Strategy Wise P&L
        with col_chart1:
            strat_perf = df.groupby("Strategy")["Net_PnL"].sum().reset_index()
            fig_strat = px.bar(
                strat_perf, 
                x="Strategy", 
                y="Net_PnL", 
                color="Net_PnL",
                color_continuous_scale=["#FF3B30", "#00C805"],
                title="P&L by Strategy"
            )
            st.plotly_chart(fig_strat, use_container_width=True)
            
        # Mistake Breakdown
        with col_chart2:
            mistake_counts = df["Mistake_Tag"].value_counts().reset_index()
            mistake_counts.columns = ["Mistake", "Count"]
            fig_mistake = px.pie(
                mistake_counts, 
                names="Mistake", 
                values="Count", 
                hole=0.4,
                title="Trading Psychology & Mistake Breakdown"
            )
            st.plotly_chart(fig_mistake, use_container_width=True)
            
        st.markdown("---")
        
        # Trade Log Table
        st.subheader("ðŸ“‹ Executed Trades History")
        st.dataframe(
            df[["Date", "Symbol", "Trade_Type", "Quantity", "Buy_Price", "Sell_Price", "Net_PnL", "Strategy", "Mistake_Tag"]],
            use_container_width=True
        )
