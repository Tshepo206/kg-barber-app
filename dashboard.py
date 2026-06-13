import os
import streamlit as st
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# 1. Platform Infrastructure Config
st.set_page_config(page_title="KG Barber Workstation", page_icon="💈", layout="wide")
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

@st.cache_data(ttl=5) # Caches data for 5 seconds to protect database connections
def load_financial_metrics(selected_date):
    """Queries live data points from the Postgres cloud engine for a specific date."""
    conn = psycopg2.connect(DB_URL)
    
    # Fetch core aggregates target metrics
    rev_query = "SELECT COALESCE(SUM(amount), 0) FROM financial_ledger WHERE category IN ('Service', 'Retail') AND date = %s;"
    exp_query = "SELECT COALESCE(SUM(amount), 0) FROM financial_ledger WHERE category = 'Expense' AND date = %s;"
    book_query = "SELECT b.booking_time, c.full_name, b.service_type, b.status FROM bookings b JOIN clients c USING (phone_number) WHERE b.booking_date = %s ORDER BY b.booking_time ASC;"
    
    df_books = pd.read_sql(book_query, conn, params=(selected_date,))
    
    cursor = conn.cursor()
    cursor.execute(rev_query, (selected_date,))
    gross_rev = float(cursor.fetchone()[0])
    
    cursor.execute(exp_query, (selected_date,))
    total_exp = float(cursor.fetchone()[0])
    
    cursor.close()
    conn.close()
    return gross_rev, total_exp, df_books

# =====================================================================
# 2. STREAMLIT SIDEBAR WORKSTATION CONTROL PARAMETERS
# =====================================================================
with st.sidebar:
    st.markdown("### 📅 Dashboard Controls")
    # Injects an interactive date lookup calendar node inside the panel
    target_lookup_date = st.date_input("Filter Matrices By Date", value=pd.Timestamp.now().date())
    st.write("---")
    st.caption("Fade Administrative Terminal Engine v1.0")

# Extract Dynamic Data Values matching chosen calendar definitions
try:
    gross_rev, total_exp, df_books = load_financial_metrics(target_lookup_date)
    net_profit = gross_rev - total_exp
except Exception as e:
    st.error(f"Database Connection Offline: {e}")
    st.stop()

# 3. Custom UI Styling Elements
st.markdown("""
    <style>
        .metric-container { background-color: #f0fcfc; padding: 20px; border-radius: 12px; border: 1px solid #e0f2f1; margin-bottom: 15px; }
        h3 { color: #004d40; }
    </style>
""", unsafe_allow_html=True)

# 4. Main Executive Layout Grid Display Viewport
st.title("💈 KG Barber Control Panel")
st.caption(f"Displaying Metrics for: {target_lookup_date.strftime('%A, %d %B %Y')}")
st.write("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💰 Profitability Engine")
    
    st.markdown(f"""
    <div class='metric-container'>
        <p style='margin:0; font-size:14px; color:gray;'>Gross Revenue (Selected Day)</p>
        <h2 style='margin:0; color:#004d40;'>R {gross_rev:,.2f}</h2>
    </div>
    <div class='metric-container'>
        <p style='margin:0; font-size:14px; color:gray;'>Net Cash Profit</p>
        <h2 style='margin:0; color:#00bfa5;'>R {net_profit:,.2f}</h2>
        <p style='margin:0; font-size:12px; color:red;'>Expenses: -R {total_exp:.2f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    break_even_target = 1000.00
    progress_percentage = min(gross_rev / break_even_target, 1.0)
    st.progress(progress_percentage, text=f"Daily Break-Even Floor Tracker: {progress_percentage*100:.1f}%")
    st.caption("FNB Speedpoint Settlement Note: Gross deposits clear tomorrow.")

with col2:
    st.markdown("### 📅 Fade Scheduling Matrix")
    
    if df_books.empty:
        st.info(f"No active appointments booked on the calendar for {target_lookup_date} yet.")
    else:
        st.dataframe(
            df_books.rename(columns={
                "booking_time": "Time Slot",
                "full_name": "Customer Name",
                "service_type": "Service Requested",
                "status": "Booking Status"
            }),
            use_container_width=True,
            hide_index=True
        )

st.write("---")
st.markdown("<p style='text-align: center; color: #a0a0a0; font-size: 12px;'>Fade Automated Accounting Interface Engine v1.0</p>", unsafe_allow_html=True)
