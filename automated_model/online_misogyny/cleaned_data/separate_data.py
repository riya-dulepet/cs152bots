# Static script (needs to only be run one) that splits data into misogynistic data vs nonmisogynistic data

import pandas as pd
import os

final_labels_path = 'automated_model/online_misogyny/original_data/final_labels.csv'
clean_data_path = 'automated_model/online_misogyny/cleaned_data/'

df = pd.read_csv(final_labels_path)
df['level_1'] = df['level_1'].astype(str).str.strip()
df['body'] = df['body'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()

misogynistic_df = df[df['level_1'] == 'Misogynistic'][['body']]
misogynistic_file = os.path.join(clean_data_path, 'misogynistic_text.csv')
misogynistic_df.to_csv(misogynistic_file, index=False)

non_misogynistic_df = df[df['level_1'] == 'Nonmisogynistic'][['body']]
non_misogynistic_file = os.path.join(clean_data_path, 'non_misogynistic_text.csv')
non_misogynistic_df.to_csv(non_misogynistic_file, index=False)

print("✅ Files created with exact label matching and cleaned body:")
print(f"   Misogynistic -> {misogynistic_file} ({misogynistic_df.shape[0]} rows)")
print(f"   Non-misogynistic -> {non_misogynistic_file} ({non_misogynistic_df.shape[0]} rows)")