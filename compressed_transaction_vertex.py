import pandas as pd

# Load datasets
paysim = pd.read_csv("PS_20174392719_1491204439457_log.csv")
cc = pd.read_csv("creditcard.csv")

# SAMPLE FIRST 
paysim_sample = paysim.sample(n=10000, random_state=42).reset_index(drop=True)

# CC features
v_cols = [col for col in cc.columns if col.startswith("V")]

v_mean = cc[v_cols].mean(axis=1)
v_std = cc[v_cols].std(axis=1)

cc_features = pd.DataFrame({
    "v_mean": v_mean,
    "v_std": v_std,
    "amount_avg": cc["Amount"],
    "amount_std": cc["Amount"].rolling(10).std().fillna(0),
    "fraud_probability": cc["Class"]
})

# Match size
cc_sample = cc_features.sample(n=len(paysim_sample), replace=True).reset_index(drop=True)

# Merge
transactions = pd.DataFrame({
    "txn_id": range(len(paysim_sample)),
    "amount": paysim_sample["amount"],
    "txn_type": paysim_sample["type"],
    "is_fraud": paysim_sample["isFraud"],

    "v_mean": cc_sample["v_mean"],
    "v_std": cc_sample["v_std"],
    "amount_avg": cc_sample["amount_avg"],
    "amount_std": cc_sample["amount_std"],
    "fraud_probability": cc_sample["fraud_probability"]
})

# Split
fraud = transactions[transactions["is_fraud"] == 1]
non_fraud = transactions[transactions["is_fraud"] == 0]

# Balanced sampling
fraud_sample = fraud.sample(n=min(2000, len(fraud)), random_state=42)
non_fraud_sample = non_fraud.sample(n=5000, random_state=42)

final_small = pd.concat([fraud_sample, non_fraud_sample]).sample(frac=1).reset_index(drop=True)

# Compression
final_small["amount"] = final_small["amount"].round(2)
final_small["v_mean"] = final_small["v_mean"].round(3)
final_small["v_std"] = final_small["v_std"].round(3)

final_small["txn_type"] = final_small["txn_type"].astype("category")

# Save
final_small.to_csv("transactions_small.csv", index=False)

print("Optimized dataset ready!")
