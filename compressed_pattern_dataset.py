import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv("creditcard.csv")

# CREATE PATTERN GROUP
# Group similar transactions into patterns

df["pattern_group"] = (
    (df["Amount"] // 50).astype(str) + "_" + 
    df["Class"].astype(str)
)

# FEATURE EXTRACTION
pattern_data = []

for pattern_id, group in df.groupby("pattern_group"):

    features = group[[f"V{i}" for i in range(1, 29)]].values

    v_mean = np.mean(features)
    v_std = np.std(features)

    amount_avg = group["Amount"].mean()
    fraud_rate = group["Class"].mean()
    frequency = len(group)

    # Pattern classification 
    if fraud_rate > 0.7:
        pattern_type = "high_fraud"
    elif fraud_rate > 0.3:
        pattern_type = "medium_fraud"
    else:
        pattern_type = "low_fraud"

    pattern_data.append({
        "pattern_id": pattern_id,
        "v_mean": round(v_mean, 4),
        "v_std": round(v_std, 4),
        "amount_avg": round(amount_avg, 2),
        "fraud_rate": round(fraud_rate, 4),
        "frequency": frequency,
        "pattern_type": pattern_type,
        "source": "creditcard_dataset"
    })

# CREATE FINAL DATASET
pattern_df = pd.DataFrame(pattern_data)

pattern_df["last_seen"] = pd.Timestamp.now()

pattern_df.to_csv("pattern_vertex.csv", index=False)

print("✅ Pattern dataset ready!")
print(pattern_df.head())