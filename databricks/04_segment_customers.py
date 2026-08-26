import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PLOTS_DIR = DATA_DIR / "plots"
customers_path = DATA_DIR / "customers.csv"
transactions_path = DATA_DIR / "transactions.csv"

N_CLUSTERS = int(os.getenv("N_CLUSTERS", "4"))


def name_segments(profile: pd.DataFrame) -> dict[int, str]:
    risk_cut = profile["default_risk"].median()
    value_cut = profile["customer_value"].median()
    labels = {}
    for segment_id, row in profile.iterrows():
        high_risk = row["default_risk"] >= risk_cut
        high_value = row["customer_value"] >= value_cut
        if high_value and not high_risk:
            labels[segment_id] = "Alto valor / bajo riesgo"
        elif high_value and high_risk:
            labels[segment_id] = "Alto valor / alto riesgo"
        elif not high_value and not high_risk:
            labels[segment_id] = "Bajo valor / bajo riesgo"
        else:
            labels[segment_id] = "Bajo valor / alto riesgo"
    return labels


def build_features(customers: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    mix = (
        transactions.pivot_table(
            index="customer_id",
            columns="transaction_type",
            values="amount",
            aggfunc="size",
            fill_value=0,
        )
        .pipe(lambda frame: frame.div(frame.sum(axis=1).replace(0, 1), axis=0))
        .add_prefix("share_")
        .reset_index()
    )
    tx = (
        transactions.groupby("customer_id")
        .agg(
            tx_count=("amount", "size"),
            tx_sum=("amount", "sum"),
            tx_mean=("amount", "mean"),
        )
        .reset_index()
    )
    df = customers.merge(tx, on="customer_id", how="left").merge(mix, on="customer_id", how="left")
    numeric_cols = ["tx_count", "tx_sum", "tx_mean"] + [col for col in df.columns if col.startswith("share_")]
    df[numeric_cols] = df[numeric_cols].fillna(0)
    df["customer_value"] = df["tx_sum"] * (1 - df["default_risk"])
    return df


def plot_charts(df: pd.DataFrame) -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    order = sorted(df["segment"].unique())

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(
        data=df,
        x="default_risk",
        y="tx_sum",
        hue="segment",
        hue_order=order,
        size="customer_value",
        sizes=(30, 280),
        ax=ax,
        alpha=0.8,
    )
    ax.set_title("Valor transaccional vs riesgo de default")
    ax.set_xlabel("Probabilidad de default")
    ax.set_ylabel("Suma de transacciones")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "01_risk_vs_spend.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    means = df.groupby("segment")["customer_value"].mean().reindex(order)
    means.plot(kind="bar", ax=ax, color="#6ee0b0")
    ax.set_title("Valor medio del cliente por segmento")
    ax.set_ylabel("tx_sum × (1 - default_risk)")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "02_value_by_segment.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=df, x="segment", y="customer_value", order=order, ax=ax)
    ax.set_title("Distribución del valor por segmento")
    ax.set_xlabel("")
    ax.set_ylabel("Valor del cliente")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "03_value_boxplot.png", dpi=140)
    plt.close(fig)

    feature_cols = ["default_risk", "tx_count", "tx_sum", "tx_mean", "customer_value"]
    heatmap = df.groupby("segment")[feature_cols].mean()
    heatmap = (heatmap - heatmap.mean()) / heatmap.std(ddof=0)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.heatmap(heatmap, annot=True, fmt=".2f", cmap="RdYlGn", center=0, ax=ax)
    ax.set_title("Perfil estandarizado de cada segmento")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "04_segment_profile.png", dpi=140)
    plt.close(fig)


def main() -> None:
    for path in (customers_path, transactions_path):
        if not path.exists():
            raise FileNotFoundError(f"Falta {path}. Ejecuta 01 y 02 antes de segmentar.")

    customers = pd.read_csv(customers_path)
    transactions = pd.read_csv(transactions_path)
    df = build_features(customers, transactions)

    feature_cols = ["default_risk", "tx_count", "tx_sum", "tx_mean"]
    scaled = StandardScaler().fit_transform(df[feature_cols])
    model = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    df["segment_id"] = model.fit_predict(scaled)

    profile = df.groupby("segment_id")[["default_risk", "customer_value"]].mean()
    labels = name_segments(profile)
    df["segment"] = df["segment_id"].map(labels)

    out_cols = [
        "customer_id",
        "name",
        "default_risk",
        "tx_count",
        "tx_sum",
        "tx_mean",
        "customer_value",
        "segment_id",
        "segment",
    ]
    segments_path = DATA_DIR / "customer_segments.csv"
    df[out_cols].to_csv(segments_path, index=False)
    plot_charts(df)

    print(df.groupby("segment")[["default_risk", "tx_sum", "customer_value"]].mean().round(2).to_string())
    print(f"\nSegmentos: {len(df)} -> {segments_path}")
    print(f"Gráficos: {PLOTS_DIR}")


if __name__ == "__main__":
    main()
