# generates the full prompt script.
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from automated_model.online_misogyny.cleaned_data.randomization_data import create_train_val_samples

SAMPLE_MIS_TXT = 'automated_model/prompt_engineering/randomized_data/train_misogynistic.txt'
SAMPLE_NONMIS_TXT = 'automated_model/prompt_engineering/randomized_data/train_nonmisogynistic.txt'

SHORT_FILE_TXT = 'automated_model/prompt_engineering/short_llm.txt'
LONG_FILE_TXT = 'automated_model/prompt_engineering/long_llm.txt'

PROMPT_DIR = 'automated_model/model_apis/prompts_created/'
PROMPT_NUM_SHORT = 'automated_model/prompt_engineering/prompt_metrics/prompt_short_number.txt'
PROMPT_NUM_LONG = 'automated_model/prompt_engineering/prompt_metrics/prompt_long_number.txt'
PROMPT_NUM_BOTH = 'automated_model/prompt_engineering/prompt_metrics/prompt_both_number.txt'

# generating prompt with a specific size
def prompt_generation(size):
    if size not in ("short", "long"):
        raise ValueError("Size must be 'short' or 'long'")

    if size == "short":
        prompt_file = SHORT_FILE_TXT
        output_subdir = os.path.join(PROMPT_DIR, "short")
        prompt_number_file = PROMPT_NUM_SHORT
    else:
        prompt_file = LONG_FILE_TXT
        output_subdir = os.path.join(PROMPT_DIR, "long")
        prompt_number_file = PROMPT_NUM_LONG

    os.makedirs(output_subdir, exist_ok=True)

    with open(prompt_file, 'r') as f:
        prompt_instructions = f.read().strip()

    create_train_val_samples()

    if size == "short":
        full_prompt = prompt_instructions
    else:
        with open(SAMPLE_MIS_TXT, 'r') as f:
            mis_samples = f.read().strip()
        with open(SAMPLE_NONMIS_TXT, 'r') as f:
            nonmis_samples = f.read().strip()

        full_prompt = (
            f"{prompt_instructions}\n\n"
            "Below are 50 misogynistic examples:\n"
            f"{mis_samples}\n\n"
            "Below are 50 non-misogynistic examples:\n"
            f"{nonmis_samples}"
        )

    if not os.path.exists(prompt_number_file):
        with open(prompt_number_file, 'w') as f:
            f.write('0')

    with open(prompt_number_file, 'r+') as f:
        prompt_number = int(f.read().strip())
        new_prompt_filename = f"prompt_{prompt_number}.txt"
        new_prompt_path = os.path.join(output_subdir, new_prompt_filename)

        with open(new_prompt_path, 'w') as out_f:
            out_f.write(full_prompt)

        f.seek(0)
        f.write(str(prompt_number + 1))
        f.truncate()

    print(f"✅ {size.capitalize()} prompt saved to: {new_prompt_path}")

# generating prompt for both sizes
def prompt_generation_both():
    output_subdir = os.path.join(PROMPT_DIR, "both")
    os.makedirs(output_subdir, exist_ok=True)

    # creating one common sample -- only used on long prompts
    create_train_val_samples()

    if not os.path.exists(PROMPT_NUM_BOTH):
        with open(PROMPT_NUM_BOTH, 'w') as f:
            f.write('0')

    with open(PROMPT_NUM_BOTH, 'r+') as f:
        prompt_number = int(f.read().strip())

        # creating the short prompting
        with open(SHORT_FILE_TXT, 'r') as short_f:
            short_instructions = short_f.read().strip()

        short_path = os.path.join(output_subdir, f"prompt_short_{prompt_number}.txt")
        with open(short_path, 'w') as out_short:
            out_short.write(short_instructions)

        # creating the long prompting
        with open(LONG_FILE_TXT, 'r') as long_f:
            long_instructions = long_f.read().strip()
        with open(SAMPLE_MIS_TXT, 'r') as f_mis:
            mis_samples = f_mis.read().strip()
        with open(SAMPLE_NONMIS_TXT, 'r') as f_nonmis:
            nonmis_samples = f_nonmis.read().strip()

        long_prompt = (
            f"{long_instructions}\n\n"
            "Below are 50 misogynistic examples:\n"
            f"{mis_samples}\n\n"
            "Below are 50 non-misogynistic examples:\n"
            f"{nonmis_samples}"
        )

        long_path = os.path.join(output_subdir, f"prompt_long_{prompt_number}.txt")
        with open(long_path, 'w') as out_long:
            out_long.write(long_prompt)

        f.seek(0)
        f.write(str(prompt_number + 1))
        f.truncate()

    print(f"✅ Both prompts saved to: {short_path} and {long_path}")

prompt_generation_both()