
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🍔 F&B Control Dashboard (MVP)")

# ===============================
# 1️⃣ Mock Data Setup (Updated)
# ===============================
# Items
items = ["Burger", "Fries", "Drink", "Chicken Wrap", "Pizza"]

# Purchase / Inventory - all ingredients included
purchase_data = pd.DataFrame({
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

# Sales Log (POS)
sales_columns = ["Date"] + items
dates = pd.date_range(start="2026-01-01", periods=30)
sales_log = pd.DataFrame(np.random.randint(10, 50, size=(30, len(items))), columns=items)
sales_log.insert(0, "Date", dates)

# ===============================
# 2️⃣ Sidebar Navigation
# ===============================
tab = st.sidebar.radio("Select Module", ["POS", "Inventory", "Recipes", "Profit", "Forecast"])

# ===============================
# 3️⃣ POS Module
# ===============================
if tab == "POS":
    st.subheader("💳 POS Terminal (MVP)")
    order = {}
    for item in items:
        qty = st.number_input(f"Quantity {item}", min_value=0, value=0)
        order[item] = qty

    payment = st.radio("Payment Type", ["Cash", "Card"])

    if st.button("Submit Sale"):
        new_row = {"Date": pd.Timestamp.now().normalize()}
        for i in items:
            new_row[i] = order[i]
        sales_log.loc[len(sales_log)] = new_row
        st.success("Sale recorded!")
        # Update inventory
        for item_name, qty in order.items():
            if item_name in recipes:
                for ing, amt in recipes[item_name].items():
                    purchase_data.loc[purchase_data["Ingredient"]==ing, "Qty_in_stock"] -= qty*amt

# ===============================
# 4️⃣ Inventory Module
# ===============================
elif tab == "Inventory":
    st.subheader("📦 Inventory Status")
    st.dataframe(purchase_data, use_container_width=True)
    low_stock = purchase_data[purchase_data["Qty_in_stock"] < 5]
    if not low_stock.empty:
        st.warning("⚠ Low Stock Alert!")
        st.dataframe(low_stock)

# ===============================
# 5️⃣ Recipes Module
# ===============================
elif tab == "Recipes":
    st.subheader("📖 Recipe & Costing")
    recipe_name = st.selectbox("Select Menu Item", items)
    st.write("Ingredients:")
    rec = recipes[recipe_name]
    cost_total = 0
    for ing, amt in rec.items():
        unit_cost = purchase_data.loc[purchase_data["Ingredient"]==ing, "Unit_cost"].values[0]
        cost = unit_cost * amt
        st.write(f"{ing}: {amt} unit(s) → Cost: {cost:.2f} ETB")
        cost_total += cost
    st.write(f"**Total Cost per {recipe_name}: {cost_total:.2f} ETB**")

# ===============================
# 6️⃣ Profit Module
# ===============================
elif tab == "Profit":
    st.subheader("💰 Profit Dashboard")
    sales_log["Total_sales"] = sales_log[items].sum(axis=1)
    daily_profit = []
    for idx, row in sales_log.iterrows():
        profit = 0
        for item_name in items:
            qty = row[item_name]
            rec = recipes.get(item_name, {})
            cost = sum([purchase_data.loc[purchase_data["Ingredient"]==ing, "Unit_cost"].values[0]*amt for ing, amt in rec.items()])
            profit += (qty * cost * 1.5) - (qty * cost)  # Simple 50% markup
        daily_profit.append(profit)
    sales_log["Profit"] = daily_profit
    st.line_chart(sales_log.set_index("Date")[["Total_sales", "Profit"]])

# ===============================
# 7️⃣ Forecast Module
# ===============================
elif tab == "Forecast":
    st.subheader("📈 Sales Prediction (MVP)")
    X = np.arange(len(sales_log)).reshape(-1,1)
    preds = {}
    for item in items:
        y = sales_log[item].values
        model = LinearRegression()
        model.fit(X, y)
        future_days = 7
        X_future = np.arange(len(X), len(X)+future_days).reshape(-1,1)
        y_pred = model.predict(X_future)
        preds[item] = np.round(y_pred)
    pred_df = pd.DataFrame(preds)
    pred_df["Date"] = pd.date_range(start=sales_log["Date"].max()+pd.Timedelta(days=1), periods=future_days)
    st.dataframe(pred_df, use_container_width=True)
    for item in items:
        plt.plot(pred_df["Date"], pred_df[item], label=item)
    plt.legend()
    plt.title("7-Day Sales Forecast")
    st.pyplot(plt)
