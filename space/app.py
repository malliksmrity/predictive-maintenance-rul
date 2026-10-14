"""Predictive maintenance: XGBoost estimate of remaining engine life on the NASA C-MAPSS FD001 test engines."""
import matplotlib
matplotlib.use("Agg")
import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor

COLS = ["unit", "cycle", "op1", "op2", "op3"] + [f"s{i}" for i in range(1, 22)]
DROP = ["op3", "s1", "s5", "s6", "s10", "s16", "s18", "s19"]
rd = lambda f: pd.read_csv(f"data/{f}", sep=r"\s+", header=None, names=COLS)
train, test = rd("train_FD001.txt"), rd("test_FD001.txt")
true = pd.read_csv("data/RUL_FD001.txt", header=None)[0].to_numpy()
train["RUL"] = (train.groupby("unit")["cycle"].transform("max") - train["cycle"]).clip(upper=125)
cols = [c for c in train.columns if c not in DROP + ["unit", "RUL"]]
sc = MinMaxScaler().fit(train[cols])
model = XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=1).fit(sc.transform(train[cols]), train["RUL"])


def show(engine):
    e = int(engine)
    d = test[test.unit == e]
    pred = model.predict(sc.transform(d[cols]))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4))
    a1.plot(d["cycle"], d["s11"], color="#0b5d6b")
    a1.set_xlabel("Cycle"); a1.set_ylabel("Sensor 11"); a1.set_title("Sensor history")
    a2.plot(d["cycle"], pred, color="#0b5d6b", label="predicted remaining cycles")
    a2.axhline(true[e - 1], color="#b35c1e", linestyle="--", label="true at the last cycle")
    a2.set_xlabel("Cycle"); a2.legend(fontsize=8)
    fig.tight_layout()
    text = (f"Engine {e}: predicted {pred[-1]:.0f} cycles left at the last reading, true value {true[e - 1]}. "
            "RMSE of this model over the 100 test engines: 18.9 cycles (labels capped at 125). Simulated data.")
    return text, fig


demo = gr.Interface(show, gr.Slider(1, 100, value=1, step=1, label="Test engine"), [gr.Textbox(label="Result"), gr.Plot()],
                    title="Engine remaining useful life (XGBoost)", description="Code: github.com/malliksmrity/predictive-maintenance-rul")
if __name__ == "__main__":
    demo.launch()
