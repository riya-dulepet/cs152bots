# prompt generation.
# other api files are scaffolding around this
# ramya can work on this

from online_misogyny.cleaned_data.randomization_data import create_random_sample

# size = "short", "long"
def prompt_generation(size):
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

        