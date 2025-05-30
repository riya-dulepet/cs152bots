# prompt generation.
# other api files are scaffolding around this
# ramya can work on this

from online_misogyny.cleaned_data.randomization_data import create_random_sample

SAMPLE_MIS_TXT = 'automated_model/online_misogyny/cleaned_data/sample_misogynistic.txt'
SAMPLE_NONMIS_TXT = 'automated_model/online_misogyny/cleaned_data/sample_nonmisogynistic.txt'

SHORT_FILE_TXT = 'automated_model/prompt_engineering/short_llm.txt'
MED_FILE_TXT = 'automated_model/prompt_engineering/med_llm.txt'
LONG_FILE_TXT = 'automated_model/prompt_engineering/long_llm.txt'

# size = "short", "long" --> this is to be used in openai_api / gemini_api
def prompt_generation(size, output_path):
    prompt_instructions = None
    if size == "short":
        # access short llm prompting
        pass
    elif size == "long":
        # access long llm prompting
        pass
    else:
        # throw error
        pass

    # creates random sampling of test prompts
    create_random_sample()

    # gather random sample prompts to pass through API
        