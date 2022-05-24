# Prompt-Summarization
You can find our paper on [ArXiv](https://arxiv.org/abs/2203.08597). We presented this work as part of the [SPA workshop](https://www.semiparametric.ml/) at ACL 2022!


Using NLP techniques to summarize prompts for program synthesis. After cloning make sure to download our [dataset from here](https://drive.google.com/file/d/1yakjokSlHxkTveYumcVTmCnNbJBU-yBU/view?usp=sharing). The data directory contains all of the human generated summaries, Studio21 generated summaries, and GPT generated summaries. Along with an experiments directory that contains all of the experiments run.

## Motivation
Recently, researchers and companies have been focusing on probram synthesis.
Which is the task of generating code given a prompt. There has been some success when the prompts
are small and self contained. However, the models struggle with longer prompts. We hope to solve this problem by summarizing long prompts to help achieve the same performance on complex problems as we do on shorter problems.

The given dataset has 5000 problems from different coding challenge websites. These websites make prompts that are meant to help humans understand the problem. This means they often repeat details, make up people/places, and abstract the problem to something humans know. All of this confuses the model and by simply removing these nonessential details we hope to improve the model's understanding of the problem.

This area of NLP is changing rapidly and any contributions could change the course of how researchers solve this problem. Being able to summarize prompts would be a significant contribution to this area and would be widely used amongst researchers and the industry alike.

## How to Get Started
1. Fork the repository and `git clone` your local version.
2. Download the original APPS dataset.
    1. You can do this by running the `download.sh` script in the `src` directory. This will download then prepare the original dataset automatically.
3. Download and extract our contributed dataset.
    1. The link to download is [here](https://drive.google.com/file/d/1yakjokSlHxkTveYumcVTmCnNbJBU-yBU/view?usp=sharing). You will need to extract the tar file inside of the `Prompt-Summarization` directory.
4. Set up your api keys.
    1. Set up a directory called `.env` or `environ`. These directories are in the `.gitignore` file so your api keys won't be pushed to github.
    2. After obtaining api keys from [OpenAI](https://beta.openai.com/) or [StudioAI21](https://studio.ai21.com/) you should save them in a file like this 
    ```
    export OPENAI_API_KEY=...
    export STUDIO21_API_KEY=...
    ```
    3. Before running a script you need to source that file to export those environment variables.
    ```
    . .env/my_api_keys
    ```
6. Install the requirements, `pip install -r requirements.txt`.
7. Now you're all set up! Read the sections below to see how to run the specific examples.

## Generating samples with GPT3
1. To generate samples with the GPT3 API, simply run `./gpt_api.py`

## Generating samples with StudioAI21
1. To generate samples with the StudioAI21 API, simply run: `./studio21_api.py --single`.

## Generating samples with Codex
1. To generate samples with the Codex API, simply run `./codex_api.py`

## How to Contribute Human Generated Samples
3. Copy a problem from the `APPS` directory into the data directory in the corresponding difficulty directory.
4. Create your summarization files.
    1. `summary.txt` - A basic summary of the prompt
    2. `expert.txt` - An expert summary of the prompt
5. Run the `format.sh` script.
6. Push the changes to your local branch and submit a Pull Request.
    1. The `test.sh` will be run for every pull request to decide if it can be merged.
    2. You should check this script before you submit your request. 

## How to Create the Summaries
1. The [How-To-Summarize](How-To-Summarize.pdf) pdf has a detailed description of how to create each summary.
2. To summarize what it says:
    1. `summary.txt` - Copy `question.txt` and remove any superfluous information.
    2. `expert.txt` - Copy `summary.txt` and remove any information an expert would find obvious.

## Other Scripts and utilities
`check_split.py` - Check how many files we are currently splitting. When generating a prompt we split the prompt according to the `split.txt` file.

`model_results.sh` - Report the summarization results for every model generated problem. The output is a file called `report.txt` in the following format `summary type,word reduction, char reduction`.

`get_results.sh` - Concat the output from `model_results.sh` into 1 file named `aggregate_results.csv`

`results.sh` - Report the summarization results for every human generated problem. This script also outputs to `stdout` and has a more verbose output. 

`remove_bad.sh` - Remove any model generated examples that did not output anything (sometimes caused by an API error).

`view_solution.sh` - A bash script that takes a problem number as an argument and outputs a human made solution for that problem.

`prompt_generation.py` - This is the python script that will format a prompt to be summarized. The only function you should use is `generate_prompt(config_fname)`. The input is the name of a `.yaml` config file.
That config file will determine how the prompt is formed. The output of the function is `full_prompt, remaining_prompt, output_dir`, see the docstring for more details.

`config.yaml` - Our config file for generating summaries with StudioAI21's API.

`studio21_api.py` - Our python script for calling StudioAI21's API.
