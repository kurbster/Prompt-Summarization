#!/usr/bin/env python3
import inquirer
import os
import sys
import json

def getExperimentFiles():
  cwd = os.getcwd()
  if "src" not in cwd:
    print("run the script in src directory")
    sys.exit(1)

  experimentDir = os.listdir('../data/experiments')
  os.chdir('../data/experiments')

  fileList= []
  for dir in experimentDir:
    dirList = os.listdir(dir)
    for file in dirList:
      fileList.append(os.path.abspath(os.path.join(dir, file)))

  return fileList

def getFileInputPath(files):
  questions = [
    inquirer.List('results',
                  message="Select which folder do you need to view results?",
                  choices=files,
              ),
  ]
  answers = inquirer.prompt(questions)

  return answers['results']

def loadAndReturnData(filePath):
  os.chdir(filePath)

  with open('test.json') as f:
    testData = json.load(f)
  
  with open('all_results.json') as f:
    resultsData = json.load(f)

  if(not os.path.exists("integrated_results.txt")):
    f = open("integrated_results.txt", "x")
    f.write('{:20s} {:5s} {:4s} {:4s} {:4s} {:4s} \n'.format("File Name", "-1", "True", "False", "-2", "Accuracy"))
    f.close()
  else:
    f = open("integrated_results.txt", "w")
    f.write('{:20s} {:5s} {:4s} {:4s} {:4s} {:4s} \n'.format("File Name", "-1", "True", "False", "-2", "Accuracy"))
    f.close()
  
  return testData, resultsData

def getCountOfValues(results):
  numberOfMinus1 = 0
  numberOfMinus2 = 0
  numberOfTrue = 0
  numberOfFalse = 0
  for res1 in results:
    if(res1 == -1):
      numberOfMinus1 = numberOfMinus1 + 1
    elif(res1 == True):
      numberOfTrue = numberOfTrue + 1
    elif(res1 == -2):
      numberOfMinus2 = numberOfMinus2 + 1
    else:
      numberOfFalse = numberOfFalse + 1
    
  return numberOfMinus1, numberOfMinus2, numberOfTrue, numberOfFalse

def generateResultsDictionary(filePath):
  testData, resultsData = loadAndReturnData(filePath)
  dictionary = {"test":{"competition": {}, "introductory": {}, "interview": {}},"train":{"competition": {}, "introductory": {}, "interview": {}}}

  strictAccuracy = []
  for i in range(0,len(testData)-1,2):
    filePath1 = testData[i].split("/")[-4:]
    filePath2 = testData[i+1].split("/")[-4:]
    results1 = resultsData[str(i)][0]
    results2 = resultsData[str(i+1)][0]

    numberOfMinus1, numberOfMinus2, numberOfTrue, numberOfFalse = getCountOfValues(results1)
    
    dictVal1 = { 
        "-1": numberOfMinus1,
        "-2": numberOfMinus2,
        "True": numberOfTrue,
        "False": numberOfFalse
      }

    numberOfMinus1, numberOfMinus2, numberOfTrue, numberOfFalse = getCountOfValues(results2)

    dictVal2 = { 
        "-1": numberOfMinus1,
        "-2": numberOfMinus2,
        "True": numberOfTrue,
        "False": numberOfFalse
      }

    if(dictVal1["True"] == len(results1)):
      strictAccuracy.append(f"Passed all of it for {filePath1[2]}/{filePath1[3]}")
    if(dictVal2["True"] == len(results2)):
      strictAccuracy.append(f"Passed all of it for {filePath1[2]}/{filePath1[3]}")

    string1 = '{:20s} {:4d} {:4d} {:4d} {:4d}   {:8f} \n'.format(f"{filePath1[2]}/{filePath1[3]}", dictVal1["-1"], dictVal1["True"], dictVal1["False"], dictVal1["-2"], dictVal1["True"]*100/len(results1))
    string2 = '{:20s} {:4d} {:4d} {:4d} {:4d}   {:8f} \n'.format(f"{filePath2[2]}/{filePath2[3]}", dictVal2["-1"], dictVal2["True"], dictVal2["False"], dictVal2["-2"], dictVal2["True"]*100/len(results2))
    f = open("integrated_results.txt", "a+")
    f.write(string1)
    f.write(string2)
    f.close()


    if(filePath1[0] == "test"):
      problemLevel = {**dictionary["test"][filePath1[1]],
          filePath1[2]: {
            filePath1[3]: dictVal1,
            filePath2[3]: dictVal2
          }
        }
      dictionary["test"].update({
        filePath1[1] : problemLevel
      })
    else:
      problemLevel = {**dictionary["train"][filePath1[1]],
          filePath1[2]: {
            filePath1[3]: dictVal1,
            filePath2[3]: dictVal2
          }
        }
      dictionary["train"].update({
        filePath1[1] : problemLevel
      })

  f = open("integrated_results.txt", "a+")
  f.write(f"\nTotal Questions are {len(testData)/2}")
  if(len(strictAccuracy) == 0):
    f.write("\nStrict Accuracy is 0\n")
  else:
    f.write(f"\nStrict Accuracy is {len(strictAccuracy)*100/len(testData)}\n")
  f.close()

  print(f"Results generated in integrated_results.txt in the {filePath}")
  return dictionary

def returnBetterResults(values,level,problem,trainortest):
  better = {"-2=>-1":"0", "-2=>False":"0", "-2=>True": "0", "-1=>False": "0", "-1=>True": "0", "False=>True": "0"}
  checkIfBetter = False

  if(values["question.txt"]["-2"] and values["expert.txt"]["-1"]):
    checkIfBetter = True
    better["-2=>-1"] = f"{values['question.txt']['-2']} => {values['expert.txt']['-1']}"
  if(values["question.txt"]["-2"] and values["expert.txt"]["False"]):
    checkIfBetter = True
    better["-2=>False"] = f"{values['question.txt']['-2']} => {values['expert.txt']['False']}"
  if(values["question.txt"]["-2"] and values["expert.txt"]["True"]):
    checkIfBetter = True
    better["-2=>True"] = f"{values['question.txt']['-2']} => {values['expert.txt']['True']}"
  if(values["question.txt"]["-1"] and values["expert.txt"]["False"]):
    checkIfBetter = True
    better["-1=>False"] = f"{values['question.txt']['-1']} => {values['expert.txt']['False']}"
  if(values["question.txt"]["-1"] and values["expert.txt"]["True"]):
    checkIfBetter = True
    better["-1=>True"] = f"{values['question.txt']['-1']} => {values['expert.txt']['True']}"
  if(values["question.txt"]["False"] and values["expert.txt"]["True"]):
    checkIfBetter = True
    better["False=>True"] = f"{values['question.txt']['False']} => {values['expert.txt']['True']}"
  
  a=[]
  if(checkIfBetter):
    a.append('{:30s} {:15s} {:15s} {:15s} {:15s} {:15s} {:15s} \n'.format(f"{trainortest}/{level}/{problem}", better["-2=>-1"], better["-2=>False"], better["-2=>True"], better["-1=>False"], better["-1=>True"], better["False=>True"]))
  
  return a

def returnWorseResults(val2,level,problem, trainortest):
  worse = {"True=>False":"0", "True=>-1":"0", "True=>-2":"0", "False=>-1":"0", "False=>-2":"0", "-1=>-2":"0"}
  checkIfworse = False

  if(val2["question.txt"]["True"] and val2["expert.txt"]["-1"]):
    checkIfworse = True
    worse["True=>-1"] = f"{val2['question.txt']['True']} => {val2['expert.txt']['-1']}"
  if(val2["question.txt"]["True"] and val2["expert.txt"]["False"]):
    checkIfworse = True
    worse["True=>False"] = f"{val2['question.txt']['True']} => {val2['expert.txt']['False']}"
  if(val2["question.txt"]["True"] and val2["expert.txt"]["-2"]):
    checkIfworse = True
    worse["True=>-2"] = f"{val2['question.txt']['True']} => {val2['expert.txt']['-2']}"
  if(val2["question.txt"]["False"] and val2["expert.txt"]["-2"]):
    checkIfworse = True
    worse["False=>-2"] = f"{val2['question.txt']['False']} => {val2['expert.txt']['-2']}"
  if(val2["question.txt"]["False"] and val2["expert.txt"]["-1"]):
    checkIfworse = True
    worse["False=>-1"] = f"{val2['question.txt']['False']} => {val2['expert.txt']['-1']}"
  if(val2["question.txt"]["False"] and val2["expert.txt"]["True"]):
    checkIfworse = True
    worse["False=>True"] = f"{val2['question.txt']['False']} => {val2['expert.txt']['True']}"
  
  a=[]
  if(checkIfworse):
    a.append('{:30s} {:15s} {:15s} {:15s} {:15s} {:15s} {:15s} \n'.format(f"{trainortest}/{level}/{problem}", worse["True=>False"], worse["True=>-1"], worse["True=>-2"], worse["False=>-1"], worse["False=>-2"], worse["-1=>-2"]))

  return a

def returnSameResults(val2,level,problem, trainortest):
  same = {"True=>True":"0", "False=>False":"0", "-1=>-1":"0", "-2=>-2":"0"}
  checkIfsame = False

  if(val2["question.txt"]["True"] and val2["expert.txt"]["True"]):
    checkIfsame = True
    same["True=>True"] = f"{val2['question.txt']['True']} => {val2['expert.txt']['True']}"
  if(val2["question.txt"]["False"] and val2["expert.txt"]["False"]):
    checkIfsame = True
    same["False=>False"] = f"{val2['question.txt']['False']} => {val2['expert.txt']['False']}"
  if(val2["question.txt"]["-1"] and val2["expert.txt"]["-1"]):
    checkIfsame = True
    same["-1=>-1"] = f"{val2['question.txt']['-1']} => {val2['expert.txt']['-1']}"
  if(val2["question.txt"]["-2"] and val2["expert.txt"]["-2"]):
    checkIfsame = True
    same["-2=>-2"] = f"{val2['question.txt']['-2']} => {val2['expert.txt']['-2']}"
  
  a=[]
  if(checkIfsame):
    a.append('{:30s} {:15s} {:15s} {:15s} {:15s} \n'.format(f"{trainortest}/{level}/{problem}", same["True=>True"], same["False=>False"], same["-1=>-1"], same["-2=>-2"]))
  
  return a

def printResults(array, level, header):
  if(len(array) > 0):
    f = open("integrated_results.txt", "a+")
    f.write(f"\n{level} performance \n")
    f.write(header)
    for i in array:
      f.write(i)
    f.close()

def printSummaries(competition,introductory,interview,train,test):
  f = open("integrated_results.txt", "a+")
  f.write(f"\nCompetition level have {competition['same']} same, {competition['better']} better and {competition['worse']} worse results")
  f.write(f"\nIntroductory level have {introductory['same']} same, {introductory['better']} better and {introductory['worse']} worse results")
  f.write(f"\nInterview level have {interview['same']} same, {interview['better']} better and {interview['worse']} worse results")
  f.write(f"\nTraining data have {train['same']} same, {train['better']} better and {train['worse']} worse results")
  f.write(f"\nTest data have {test['same']} same, {test['better']} better and {test['worse']} worse results \n")
  f.close()


def getAccuracy(dictionary):
  same = []
  better = []
  worse = []
  competition={"same":0,"worse":0,"better":0}
  introductory={"same":0,"worse":0,"better":0}
  interview={"same":0,"worse":0,"better":0}
  train={"same":0,"worse":0,"better":0}
  test={"same":0,"worse":0,"better":0}
  for key1,value in dictionary.items():
    for k,val in value.items():
      for i,val2 in val.items():
        if(len(returnBetterResults(val2,k,i,key1)) != 0):
          eval(k)["better"] = eval(k)["better"] +1
          eval(key1)["better"] = eval(key1)["better"] + 1
          better.append(returnBetterResults(val2,k,i,key1)[0])
        if(len(returnWorseResults(val2,k,i,key1)) != 0):
          eval(k)["worse"] = eval(k)["worse"] +1
          eval(key1)["worse"] = eval(key1)["worse"] + 1
          worse.append(returnWorseResults(val2,k,i,key1)[0])
          eval(k)["same"] = eval(k)["same"] +1
          eval(key1)["same"] = eval(key1)["same"] + 1
        if(len(returnSameResults(val2,k,i,key1)) != 0):
          same.append(returnSameResults(val2,k,i,key1)[0])
  
  printSummaries(competition,introductory,interview,train,test)
  printResults(better,'better','{:30s} {:15s} {:15s} {:15s} {:15s} {:15s} {:15s} \n'.format("Problem Name", "-2=>-1", "-2=>False", "-2=>True", "-1=>False", "-1=>True", "False=>True"))
  printResults(same,'same','{:30s} {:15s} {:15s} {:15s} {:15s} \n'.format("Problem Name", "True=>True", "False=>False", "-1=>-1", "-2=>-2"))
  printResults(worse,'worse','{:30s} {:15s} {:15s} {:15s} {:15s} {:15s} {:15s} \n'.format("Problem Name", "True=>False", "True=>-1", "True=>-2", "False=>-1", "False=>-2", "-1=>-2"))
  

files = getExperimentFiles()

getAccuracy(generateResultsDictionary(getFileInputPath(files)))
