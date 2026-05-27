import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

# Page config
st.set_page_config(page_title="Predictive Maintenance - RUL Predictor", 
                   layout="wide")

# Title
st.title("🔧 Predictive Maintenance Dashboard")
st.subheader("Remaining Useful Life (RUL) Prediction for Aircraft Engines")
st.markdown("Built using NASA CMAPSS Turbofan Engine Dataset")

# Load and prepare data
@st.cache_data
def load_and_train():
    columns = ['unit', 'cycle', 'op1', 'op2', 'op3'] + [f's{i}' for i in range(1, 22)]
    train = pd.read_csv('data/train_FD001.txt', sep=' ', header=None,
                        names=columns, index_col=False)
    train = train.dropna(axis=1)
    
    max_cycles = train.groupby('unit')['cycle'].max().reset_index()
    max_cycles.columns = ['unit', 'max_cycle']
    train = train.merge(max_cycles, on='unit')
    train['RUL'] = train['max_cycle'] - train['cycle']
    
    drop_cols = ['op3', 's1', 's5', 's6', 's10', 's16', 's18', 's19', 'max_cycle']
    train_clean = train.drop(columns=drop_cols)
    
    X = train_clean.drop(columns=['unit', 'RUL'])
    y = train_clean['RUL']
    
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42)
    
    model = XGBRegressor(n_estimators=100, max_depth=6,
                         learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train)
    
    return train, model, scaler, X_test, y_test, train_clean

train, model, scaler, X_test, y_test, train_clean = load_and_train()

# Sidebar
st.sidebar.header("Select Engine")
engine_id = st.sidebar.selectbox("Engine Unit", sorted(train['unit'].unique()))

# Main layout
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Engine {engine_id} - Sensor Readings Over Time")
    engine_data = train[train['unit'] == engine_id]
    
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(engine_data['cycle'], engine_data['s11'], color='blue', label='Sensor 11')
    ax.plot(engine_data['cycle'], engine_data['s12'], color='red', label='Sensor 12')
    ax.set_xlabel('Cycle')
    ax.set_ylabel('Sensor Reading')
    ax.legend()
    ax.set_title('Sensor Degradation Pattern')
    st.pyplot(fig)

with col2:
    st.subheader(f"Engine {engine_id} - RUL Countdown")
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.plot(engine_data['cycle'], engine_data['RUL'], color='green')
    ax2.set_xlabel('Cycle')
    ax2.set_ylabel('Remaining Useful Life')
    ax2.set_title('Actual RUL Over Time')
    st.pyplot(fig2)

# Prediction section
st.subheader("Model Performance - Predicted vs Actual RUL")
y_pred = model.predict(X_test)

fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.scatter(y_test, y_pred, alpha=0.3, color='blue')
ax3.plot([0, 300], [0, 300], 'r--', label='Perfect Prediction')
ax3.set_xlabel('Actual RUL')
ax3.set_ylabel('Predicted RUL')
ax3.legend()
ax3.set_title('Predicted vs Actual RUL')
st.pyplot(fig3)

# Metrics
col3, col4, col5 = st.columns(3)
mae = np.mean(np.abs(y_test - y_pred))
rmse = np.sqrt(np.mean((y_test - y_pred)**2))

col3.metric("MAE", f"{mae:.1f} cycles")
col4.metric("RMSE", f"{rmse:.1f} cycles")
col5.metric("Engines Analyzed", "100")

st.markdown("---")
st.markdown("Built by Smrity | AI & Data Science Masters | Mechanical Engineering Background")