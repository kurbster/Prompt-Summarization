
import pandas as pd


def create_summary_data(data, file):
    data_dict = {"prompt" : [], "completion" : []}
    for i in range(len(data)):
        data_dict["prompt"].append(data[i][0])
        data_dict["completion"].append(data[i][1])
    data = pd.DataFrame(data_dict)
    data.to_csv(file)
    print("file sucessfully created at {}".format(file))
