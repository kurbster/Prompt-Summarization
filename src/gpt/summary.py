#!/usr/bin/env python3
import os
import sys
sys.path.append('..')
import yaml
import openai

#from prompt_generation import generate_prompt

def get_summary(prompt, settings_file, fine_tuned_model=None):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    with open(settings_file) as file:
        GPT_settings = yaml.safe_load(file)

    # Use our model instead of the pretrained ones
    if fine_tuned_model:
        GPT_settings.pop('engine')
        GPT_settings['model'] = fine_tuned_model

    #response = openai.Completion.create(
    #    prompt=prompt,
    #    **GPT_settings
    #)
    #return [val["text"] for val in response["choices"]]
    return "I am summary"

def save_code(responses, destinations):
    for res, dst in zip(responses, destinations):
        with open(destinations, 'w') as f:
            f.write(res)

if __name__ == "__main__":
    print(f'api key: {os.getenv("OPENAI_API_KEY")}')
    prompt = ["Summarize the following"]
    if len(sys.argv) > 1:
        model = sys.argv[1]
        print(f'Using fine tuned model: {model}')
        summaries = get_summary(prompt, "./settings.yaml", fine_tuned_model=model)
    else:
        print(f'Using pretrained model defined in settings.yaml')
        summaries = get_summary(prompt, "./settings.yaml")
    print(summaries)