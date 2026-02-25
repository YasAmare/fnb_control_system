import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🍔 F&B Control Dashboard (MVP)")

# ===============================
# 1️⃣ Mock Data Setup
# ===============================
items = ["Burger", "Fries", "Drink", "Chicken Wrap", "Pizza"]

# Default purchase / inventory
default_inventory = pd.DataFrame({
    "Ingredient": [
        "Beef", "Bun", "Lettuce", "Tomato", "Oil", "Cheese", "Chicken",
        "Potato", "Syrup", "Water", "Dough"
    ],
    "Qty_in_stock": [100, 200, 50, 60, 30, 40, 80, 100, 50, 50, 50],
    "Unit_cost": [150, 20, 10, 8, 50, 25, 120, 5, 2, 1, 15]
})

# Recipes
recipes = {
    "Burger": {"Beef": 1, "Bun": 1, "Lettuce": 0.1, "Tomato": 0.1, "Cheese": 0.2, "Oil": 0.05},
    "Fries": {"Oil": 0.1, "Potato": 0.5},
    "Drink": {"Syrup": 0.1, "Water": 0.3},
    "Chicken Wrap": {"Chicken": 0.3, "Bun": 1, "Lettuce": 0.1, "Tomato": 0.1, "Oil": 0.05},
    "Pizza": {"Cheese": 0.3, "Tomato": 0.2, "Dough": 0.5, "Oil": 0.05}
}

# Load inventory
try:
    purchase_data = pd.read_csv("data/purchases.csv")
except FileNotFoundError:
    purchase_data = default_inventory.copy()

# Load sales log
try:
    sales_log = pd.read_csv("data/sales.csv", parse_dates=["Date"])
except FileNotFoundError:
    dates = pd.date_range(start="2026-01-01", periods=30)
    sales_log = pd.DataFrame(np.random.randint(10,50,size=(30,len(items))), columns=items)
    sales_log.insert(0, "Date", dates)

# ===============================
# 2️⃣ Sidebar Navigation
# ===============================
tab = st.sidebar.radio("Select Module", ["POS", "Inventory", "Recipes", "Profit", "Forecast"])

# ===============================
# 3️⃣ POS Module - Full Pipeline
# ===============================
if tab == "POS":
    st.subheader("💳 POS Terminal (Full Pipeline)")

    # Session state
    if "purchase_data" not in st.session_state:
        st.session_state.purchase_data = purchase_data.copy()
    if "sales_log" not in st.session_state:
        st.session_state.sales_log = sales_log.copy()

    with st.form("order_form"):
        st.write("### Enter Order Quantities")
        order = {}
        for item in items:
            qty = st.number_input(f"{item}", min_value=0, value=0)
            order[item] = qty
        payment = st.radio("Payment Type", ["Cash", "Card"])
        submit = st.form_submit_button("Submit Order")

    if submit:
        # Check inventory
        insufficient = []
        for item_name, qty in order.items():
            if qty == 0:
                continue
            if item_name in recipes:
                for ing, amt in recipes[item_name].items():
                    required = qty * amt
                    stock = st.session_state.purchase_data.loc[
                        st.session_state.purchase_data["Ingredient"]==ing, "Qty_in_stock"
                    ].values[0]
                    if required > stock:
                        insufficient.append(f"{ing} for {item_name} (need {required}, have {stock})")

        if insufficient:
            st.error("⚠ Cannot process order due to insufficient stock:")
            for msg in insufficient:
                st.write("- " + msg)
        else:
            # Update inventory
            for item_name, qty in order.items():
                if qty == 0:
                    continue
                if item_name in recipes:
                    for ing, amt in recipes[item_name].items():
                        st.session_state.purchase_data.loc[
                            st.session_state.purchase_data["Ingredient"]==ing, "Qty_in_stock"
                        ] -= qty * amt

            # Update sales log
            new_row = {"Date": pd.Timestamp.now().normalize()}
            for i in items:
                new_row[i] = order[i]
            st.session_state.sales_log.loc[len(st.session_state.sales_log)] = new_row

            # Kitchen ticket
            st.write("### 🍳 Kitchen Ticket")
            for item_name, qty in order.items():
                if qty == 0:
                    continue
                st.write(f"**{item_name} x {qty}**")
                if item_name in recipes:
                    ing_list = ", ".join([f"{ing} x {amt*qty}" for ing, amt in recipes[item_name].items()])
                    st.write(f"Ingredients: {ing_list}")

            st.success("✅ Order processed successfully!")

            # Save CSVs
            st.session_state.purchase_data.to_csv("data/purchases.csv", index=False)
            st.session_state.sales_log.to_csv("data/sales.csv", index=False)
            st.success("Inventory and sales log updated in CSV!")

# ===============================
# 4️⃣ Inventory Module - Editable Table
# ===============================
elif tab == "Inventory":
    st.subheader("📦 Inventory Status")
    edited_inventory = st.data_editor(st.session_state.purchase_data, num_rows="dynamic")
    if st.button("Save Inventory Changes"):
        edited_inventory.to_csv("data/purchases.csv", index=False)
        st.session_state.purchase_data = edited_inventory.copy()
        st.success("Inventory updated!")

# ===============================
# 5️⃣ Recipes Module - Costing
# ===============================
elif tab == "Recipes":
    st.subheader("📖 Recipe & Costing")
    recipe_name = st.selectbox("Select Menu Item", items)
    st.write("Ingredients:")
    rec = recipes[recipe_name]
    cost_total = 0
    for ing, amt in rec.items():
        unit_cost = st.session_state.purchase_data.loc[
            st.session_state.purchase_data["Ingredient"]==ing, "Unit_cost"
        ].values[0]
        cost = unit_cost * amt
        st.write(f"{ing}: {amt} unit(s) → Cost: {cost:.2f} ETB")
        cost_total += cost
    st.write(f"**Total Cost per {recipe_name}: {cost_total:.2f} ETB**")

# ===============================
# 6️⃣ Profit & Charts
# ===============================
elif tab == "Profit":
    st.subheader("💰 Profit & Sales Dashboard")
    df = st.session_state.sales_log.copy()
    df["Total_sales"] = df[items].sum(axis=1)

    # Profit calculation
    daily_profit = []
    for idx, row in df.iterrows():
        profit = 0
        for item_name in items:
            qty = row[item_name]
            rec = recipes.get(item_name, {})
            cost = sum([st.session_state.purchase_data.loc[
                st.session_state.purchase_data["Ingredient"]==ing, "Unit_cost"
            ].values[0]*amt for ing, amt in rec.items()])
            profit += (qty*cost*1.5) - (qty*cost)
        daily_profit.append(profit)
    df["Profit"] = daily_profit

    # Individual charts
    st.write("### Individual Item Sales Charts")
    for item_name in items:
        st.line_chart(df.set_index("Date")[[item_name]], height=200)

    # Combined chart
    st.write("### Combined Sales Chart")
    st.line_chart(df.set_index("Date")[items + ["Total_sales"]], height=400)

    # Profit chart
    st.write("### Daily Profit Chart")
    st.line_chart(df.set_index("Date")[["Profit"]], height=300)

    # Export options
    st.write("### Export Data")
    if st.button("Export to CSV"):
        df.to_csv("data/sales_export.csv", index=False)
        st.success("Exported to data/sales_export.csv")
    if st.button("Export to Excel"):
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("Download Excel", data=output.getvalue(), file_name="sales_export.xlsx")

# ===============================
# 7️⃣ Forecast Module
# ===============================
elif tab == "Forecast":
    st.subheader("📈 Sales Prediction (MVP)")
    future_days = 7
    pred_df = pd.DataFrame()
    pred_df["Date"] = pd.date_range(start=st.session_state.sales_log["Date"].max()+pd.Timedelta(days=1), periods=future_days)
    for item in items:
        y = st.session_state.sales_log[item].values
        x = np.arange(len(y))
        coef = np.polyfit(x, y, 1)
        x_future = np.arange(len(y), len(y)+future_days)
        y_pred = coef[0]*x_future + coef[1]
        pred_df[item] = np.round(y_pred)

    st.dataframe(pred_df, use_container_width=True)
    plt.figure(figsize=(10,5))
    for item in items:
        plt.plot(pred_df["Date"], pred_df[item], label=item)
    plt.title("7-Day Sales Forecast")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(plt)
