# prompt generation.
# other api files are scaffolding around this
# ramya can work on this

from automated_model.online_misogyny.cleaned_data.randomization_data import create_random_sample
import os

SAMPLE_MIS_TXT = 'automated_model/online_misogyny/cleaned_data/sample_misogynistic.txt'
SAMPLE_NONMIS_TXT = 'automated_model/online_misogyny/cleaned_data/sample_nonmisogynistic.txt'

SHORT_FILE_TXT = 'automated_model/prompt_engineering/short_llm.txt'
MED_FILE_TXT = 'automated_model/prompt_engineering/med_llm.txt'
LONG_FILE_TXT = 'automated_model/prompt_engineering/long_llm.txt'

PROMPT_DIR = 'automated_model/model_apis/prompts_created/'

# increment up as we get more prompts
PROMPT_NUM = 'automated_model/model_apis/prompts_created/prompt_number.txt'

# size = "short", "long" --> this is to be used in openai_api / gemini_api
def prompt_generation(size):
    prompt_instructions = None
    if size == "short":
        # access short llm prompting
        with open(SHORT_FILE_TXT, 'r') as f:
            prompt_instructions = f.read()
    elif size == "long":
        # access long llm prompting
        with open(LONG_FILE_TXT, 'r') as f:
            prompt_instructions = f.read()
    else:
        # throw error
        raise ValueError("Size must be 'short' or 'long'")

    # creates random sampling of test prompts
    create_random_sample()

    with open(SAMPLE_MIS_TXT, 'r') as f:
        mis_samples = f.read()
    with open(SAMPLE_NONMIS_TXT, 'r') as f:
        nonmis_samples = f.read()

    full_prompt = (
        f"{prompt_instructions.strip()}\n\n"
        "Below are 50 misogynistic examples:\n"
        f"{mis_samples.strip()}\n\n"
        "Below are 50 non-misogynistic examples:\n"
        f"{nonmis_samples.strip()}\n"
    )

    with open(PROMPT_NUM, 'r+') as f:
        prompt_number = int(f.read().strip())
        new_prompt_filename = f"prompt_{prompt_number}.txt"
        new_prompt_path = os.path.join(PROMPT_DIR, new_prompt_filename)

        # Write the combined prompt to a new file
        with open(new_prompt_path, 'w') as out_f:
            out_f.write(full_prompt)

        # Increment and save the new prompt number
        f.seek(0)
        f.write(str(prompt_number + 1))
        f.truncate()
