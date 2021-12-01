import os
import json

def get_relative_dir_path(dir_path, relative_data_path = "../../", absolute_path = True):
    if absolute_path :
        dir_path = os.path.join(relative_data_path, "data/experiments")+dir_path.split("data/experiments")[-1]
    return dir_path

def get_result_dict(dir_list, relative_data_path = "../"):
    test_file = "test.json"
    results_file = "all_results.json"
    result_dict = {}
    for dir_path in dir_list:
        dir_path = get_relative_dir_path(dir_path, relative_data_path)
        
        # read files
        test_f = open(os.path.join(dir_path,test_file))
        test_paths = json.load(test_f)
        result_f = open(os.path.join(dir_path,results_file))
        result_obj = json.load(result_f)

        #generate result dict
        for ind in range(0, len(test_paths), 2):
            print("*** : ", test_paths[ind].split("data")[-1])
            result_dict[test_paths[ind].split("data")[-1]] = {
                "human" : result_obj[str(ind)][0],
                "original" : result_obj[str(ind+1)][0]
            }
    return result_dict   

dir_list = ["/Users/Kirby_Stuff/Documents/APPS-Summary/Prompt-Summarization/data/experiments/11-29-2021/15_23", \
    "/Users/Kirby_Stuff/Documents/APPS-Summary/Prompt-Summarization/data/experiments/11-30-2021/13_11"]

print(get_result_dict(dir_list))