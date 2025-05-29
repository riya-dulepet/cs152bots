# File chooses 50 random lines from the misogynistic text and nonmisogynistic text

import pandas as pd
import os

MIS_FILE = 'automated_model/online_misogyny/cleaned_data/misogynistic_text.csv'
NONMIS_FILE = 'automated_model/online_misogyny/cleaned_data/non_misogynistic_text.csv'

OUTPUT_MIS_TXT = 'automated_model/online_misogyny/cleaned_data/sample_misogynistic.txt'
OUTPUT_NONMIS_TXT = 'automated_model/online_misogyny/cleaned_data/sample_nonmisogynistic.txt'

MIS_AMT = 699
NONMIS_AMT = 5868
SAMPLE_SIZE = 50

def create_random_sample():
    mis_df = pd.read_csv(MIS_FILE)
    nonmis_df = pd.read_csv(NONMIS_FILE)

    mis_sample = mis_df.sample(SAMPLE_SIZE).copy()
    nonmis_sample = nonmis_df.sample(SAMPLE_SIZE).copy()

    with open(OUTPUT_MIS_TXT, 'w', encoding='utf-8') as f:
        for text in mis_sample['body']:
            f.write(str(text) + '\n')

    with open(OUTPUT_NONMIS_TXT, 'w', encoding='utf-8') as f:
        for text in nonmis_sample['body']:
            f.write(str(text) + '\n')

    print("✅ Samples written to separate .txt files:")
    print(f"   Misogynistic ({SAMPLE_SIZE} lines): {OUTPUT_MIS_TXT}")
    print(f"   Non-misogynistic ({SAMPLE_SIZE} lines): {OUTPUT_NONMIS_TXT}")

create_random_sample()