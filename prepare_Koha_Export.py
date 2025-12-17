import pandas as pd

from langdetect import detect

import basic_functions as bf

def clean_string(dataSet, settings):

    for column in settings.columnsToClean:

        #Cleaning the columns with a search and replace list, see comment in settings
        for key, value in settings.toReplace.items():
            dataSet[column] = dataSet[column].str.replace(key, value)

        dataSet[column] = dataSet[column].str.strip()
        dataSet[column] = dataSet[column].str.normalize('NFC')

    return dataSet


def detect_languages(dataSet):
    print("\nStarting language detection") 
    for row in range(0,len(dataSet)):
        
        toAnalyze = dataSet.loc[row, 'Abstract']
        try:
            res = detect(toAnalyze)
        except:
            res = '<NA>'
        dataSet.loc[row, 'lang_detected'] = res
    
        if row != 0 ^ row%100 == 0: #A message is displayed on the terminal every 100 lines
            print("Row ", row, " finished")
   
    print("detect_languages: finished")
    return dataSet


def add_columns(dataSet, settings):
               
    for columnName in settings.mandatoryColumns:
        if columnName not in dataSet:
            dataSet[columnName] = pd.Series(pd.NA for x in range(len(dataSet.index)))

    return dataSet

      
def prepare_Koha_Export(settings):

    print("Preparing Koha export: ", settings.fileName)
    
    dataSet = bf.read_dataSet(settings, settings.fileName)
    
    dataSet = clean_string(dataSet, settings)
    
    dataSet = add_columns(dataSet, settings)

    dataSet = detect_languages(dataSet)

    #Save result
    settings.fileNameForNER = settings.fileName
    settings.fileNameForTranslation = settings.fileName.replace(".csv", "_lang_detected.csv")
    bf.save_dataSet(dataSet, settings.sourceFolderPath, settings.fileNameForTranslation)
    