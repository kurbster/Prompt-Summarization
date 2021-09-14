# Prompt-Summarization
Using NLP techniques to summarize prompts for program synthesis.
## Motivation
Recently, researchers and companies have been focusing on probram synthesis.
Which is the task of generating code given a prompt. There has been some success when the prompts
are small and self contained. However, the models struggle with longer prompts. We hope to solve this problem by summarizing long prompts to help achieve the same performance on complex problems as we do on shorter problems.

The given dataset has 5000 problems from different coding challenge websites. These websites make prompts that are meant to help humans understand the problem. This means they often repeat details, make up people/places, and abstract the problem to something humans know. All of this confuses the model and by simply removing these nonessential details we hope to improve the model's understanding of the problem.

This area of NLP is changing rapidly and any contributions could change the course of how researchers solve this problem. Being able to summarize prompts would be a significant contribution to this area and would be widely used amongst researchers and the industry alike.

## How to Contribute
1. Fork the repository and `git clone` your local version.
2. Download the dataset.
    1. You can use the `download.sh` script. This will download then prepare the dataset.
3. Copy a problem from the `APPS` directory into the correct directory.
4. Create your summarization files.
    1. `summary.txt` - A basic summary of the prompt
    2. `expert.txt` - An expert summary of the prompt
    3. `instruction.txt` - A description of the code solution
5. Run the `format.sh` script.
6. Push the changes to your local branch and submit a Pull Request.
    1. The `test.sh` will be run for every pull request to decide if it can merge.
    2. You should check this script before you submit your request. 

## How to Create the Summaries
1. The [How-To-Summarize](How-To-Summarize.pdf) pdf has a detailed description of how to create each summary.
2. To summarize what it says:
    1. `summary.txt` - Copy `question.txt` and remove any superfluous information.
    2. `expert.txt` - Copy `summary.txt` and remove any information an expert would find obvious.
    3. `instruction.txt` - Use the `view_solution.sh` script to view different code solutions. Then describe the steps of that solution.
