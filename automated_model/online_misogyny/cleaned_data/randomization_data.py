# Code that randomly creates the training and validation sets
import pandas as pd
import os

# incoming misogynistic paths
MIS_FILE = 'automated_model/online_misogyny/cleaned_data/misogynistic_text.csv'
NONMIS_FILE = 'automated_model/online_misogyny/cleaned_data/non_misogynistic_text.csv'

# outputing paths
OUTPUT_TRAIN_MIS_TXT = 'automated_model/prompt_engineering/randomized_data/train_misogynistic.txt'
OUTPUT_TRAIN_NONMIS_TXT = 'automated_model/prompt_engineering/randomized_data/train_nonmisogynistic.txt'
OUTPUT_VAL_MIS_TXT = 'automated_model/prompt_engineering/randomized_data/val_misogynistic.txt'
OUTPUT_VAL_NONMIS_TXT = 'automated_model/prompt_engineering/randomized_data/val_nonmisogynistic.txt'

TRAIN_SIZE = 50
VAL_SIZE = 30

def create_train_val_samples():
    mis_df = pd.read_csv(MIS_FILE)
    nonmis_df = pd.read_csv(NONMIS_FILE)

    mis_train = mis_df.sample(TRAIN_SIZE, random_state=42)
    nonmis_train = nonmis_df.sample(TRAIN_SIZE, random_state=42)

    mis_remaining = mis_df.drop(mis_train.index)
    nonmis_remaining = nonmis_df.drop(nonmis_train.index)

    mis_val = mis_remaining.sample(VAL_SIZE, random_state=43)
    nonmis_val = nonmis_remaining.sample(VAL_SIZE, random_state=43)

    def write_to_file(filename, series):
        with open(filename, 'w', encoding='utf-8') as f:
            for text in series:
                f.write(str(text) + '\n')

    write_to_file(OUTPUT_TRAIN_MIS_TXT, mis_train['body'])
    write_to_file(OUTPUT_TRAIN_NONMIS_TXT, nonmis_train['body'])
    write_to_file(OUTPUT_VAL_MIS_TXT, mis_val['body'])
    write_to_file(OUTPUT_VAL_NONMIS_TXT, nonmis_val['body'])

    print("✅ Training and validation samples written:")
    print(f"   Train - Misogynistic ({TRAIN_SIZE}): {OUTPUT_TRAIN_MIS_TXT}")
    print(f"   Train - Non-misogynistic ({TRAIN_SIZE}): {OUTPUT_TRAIN_NONMIS_TXT}")
    print(f"   Val   - Misogynistic ({VAL_SIZE}): {OUTPUT_VAL_MIS_TXT}")
    print(f"   Val   - Non-misogynistic ({VAL_SIZE}): {OUTPUT_VAL_NONMIS_TXT}")

create_train_val_samples()