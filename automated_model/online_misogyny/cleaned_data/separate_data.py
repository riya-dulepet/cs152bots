import pandas as pd
import os

# Define paths
input_path = 'automated_model/online_misogyny/original_data/final_labels.csv'
output_dir = 'automated_model/online_misogyny/cleaned_data/'

# Load the data
df = pd.read_csv(input_path)

# Clean whitespace and fix casing (if needed)
df['level_1'] = df['level_1'].astype(str).str.strip()

# Replace newlines/tabs in body with a space, strip surrounding whitespace
df['body'] = df['body'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()

# Filter based on exact equality
misogynistic_df = df[df['level_1'] == 'Misogynistic'][['body']]
non_misogynistic_df = df[df['level_1'] == 'Nonmisogynistic'][['body']]

# Output file paths
misogynistic_file = os.path.join(output_dir, 'misogynistic_text.csv')
non_misogynistic_file = os.path.join(output_dir, 'non_misogynistic_text.csv')

# Save to CSV
misogynistic_df.to_csv(misogynistic_file, index=False)
non_misogynistic_df.to_csv(non_misogynistic_file, index=False)

print("✅ Files created with exact label matching and cleaned body:")
print(f"   Misogynistic -> {misogynistic_file}")
print(f"   Non-misogynistic -> {non_misogynistic_file}")
