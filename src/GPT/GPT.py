import os
import openai
import yaml
import pickle



def get_summary(prompt, settings_file):

    openai.api_key = os.getenv("OPENAI_API_KEY")

    with open(settings_file) as file:
        GPT_settings = yaml.load(file, Loader=yaml.FullLoader)

    response = openai.Completion.create(
        prompt=prompt,
        **GPT_settings
    )
    return [val["text"] for val in response["choices"]]


if __name__ == "__main__":
    if "summary_obj.pkl" not in os.listdir():
        prompt = "Summarize the following : Davis et al. (2015) set out to empirically test the popular saying “an apple a day keeps the doctor away.” Apples are often used to represent a healthy lifestyle, and research has shown their nutritional properties could be beneficial for various aspects of health. The authors’ unique approach is to take the saying literally and ask: do people who eat apples use healthcare services less frequently? If there is indeed such a relationship, they suggest, promoting apple consumption could help reduce healthcare costs.The study used publicly available cross-sectional data from the National Health and Nutrition Examination Survey. Participants were categorized as either apple eaters or non-apple eaters based on their self-reported apple consumption in an average 24-hour period. They were also categorized as either avoiding or not avoiding the use of healthcare services in the past year. The data was statistically analyzed to test whether there was an association between apple consumption and several dependent variables: physician visits, hospital stays, use of mental health services, and use of prescription medication."
        summary = get_summary(prompt,"./settings.yaml")
        with open('summary.pkl', "wb") as f:
            pickle.dump(summary, f)
    else:
        file = open('summary.pkl', 'rb')
        summary = pickle.load(file)
        file.close()

    print(summary)