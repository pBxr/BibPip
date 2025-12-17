import os
import sys
import pandas as pd
import numpy as np
import re
import json
import requests
import urllib.parse

from unidecode import unidecode

import basic_functions as bf

import run_Translation as rt
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import logging #To suppress transformers warnings


def analyze_result(inputData, settings, logGenerator):

    #Create new DataFrame to collect statistics
    dataSetResult = pd.DataFrame()

    inputDataAnalysis = inputData
    inputDataAnalysis = inputDataAnalysis.replace('', pd.NA)
    
    if settings.NER_Parameters['language'] == 'none':
        selectedLanguages = pd.Series(settings.NER_Languages)
    else:
        selectedLanguages = pd.Series([settings.NER_Parameters['language']])
    
    for column in settings.columnsStatistics:
        if column == 'Language':
            dataSetResult['Language'] = selectedLanguages
        else:
            dataSetResult[column] = pd.Series([pd.NA for x in range(len(dataSetResult.index))])

    #Analyze result
    for row in dataSetResult.index.values:
        nrLang = len(inputDataAnalysis.loc[inputDataAnalysis.lang_detected == dataSetResult.loc[row, 'Language']])
        dataSetResult.loc[row, 'Entries'] = nrLang

        subSet = inputDataAnalysis.loc[inputDataAnalysis.lang_detected == dataSetResult.loc[row, 'Language']]
        nrWithLOC = len(subSet.loc[pd.notna(subSet.Geographic_Name)])
        dataSetResult.loc[row, '... with entries in kwLOC'] = nrWithLOC

        nrWithMISC = len(subSet.loc[pd.notna(subSet.Topical_Term)])
        dataSetResult.loc[row, '... with entries in kwMISC',] = nrWithMISC

        #Get counters
        dataSetResult.loc[row, '... newly added_kwLOC'] = logGenerator.resultCollector['counterNewKw']['LOC'][dataSetResult.loc[row, 'Language']]
        dataSetResult.loc[row, '(found after translation, if selected)'] = logGenerator.resultCollector['counterTranslatedKW']['LOC'][dataSetResult.loc[row, 'Language']]
        dataSetResult.loc[row, '... newly added_kwMISC'] = logGenerator.resultCollector['counterNewKw']['MISC'][dataSetResult.loc[row, 'Language']]\
                                                                         + logGenerator.resultCollector['counterNewKw']['ORG'][dataSetResult.loc[row, 'Language']]\
                                                                         + logGenerator.resultCollector['counterNewKw']['PER'][dataSetResult.loc[row, 'Language']]
                           
    return dataSetResult.loc[dataSetResult.Entries >0]


def apply_input_filters(inputData, settings):

    #Language filter (only index values for the selected language will be passed)
    if settings.NER_Parameters['language'] != 'none':
        indexFiltered = inputData.loc[inputData.lang_detected == settings.NER_Parameters['language']].index.values
    else:
        indexFiltered = inputData.index.values

    return inputData, indexFiltered


def call_gazetteer(result):

    gazetteerResult = []
    check = False
    
    #Prepare call
    result = urllib.parse.quote_plus(result, safe='/:?=&')
  
    try:
        toSearch = "https://gazetteer.dainst.org/search.json?q=" + result
        response = requests.get(toSearch)
        
        resultListComplete = response.json()
        resultList = resultListComplete['result']
        
        gazetterHits = len(resultList)

        gazetteerResult.append(f"Searching {result} in gazetteer: {gazetterHits} hit(s)\n")
 
        for item in resultList:
            if item['prefName']['title']:
                check = result in item['prefName']['title']
                gazetteerResult.append(f"{result} in {item['prefName']['title']}: " + str(check) + "\n")
                
            if 'names' in item:
                for name in item['names']:
                    if name['title']:
                        check = result in name['title']
                        gazetteerResult.append(f"{result} in {name['title']}: " + str(check) + "\n")
    except:
        gazeteerResult = ''

    if len(gazetteerResult) > 1:
        res = True
    else:
        res = False

    #GazetteerResult will not be recorded in this version
       
    return res


def translate_placename(settings, inputData, row, name):
    nameTranslated = ''
    if settings.NER_Parameters['origLangOnly'] is True:
        sourceLanguage = inputData.loc[row, 'lang_detected']
    else:
        sourceLanguage = 'en'
    try:
        nameTranslated = rt.translate_string(name, sourceLanguage, 'de') 
    except:
        return '<NA>'

    return nameTranslated

def check_source(settings, dataSet):

    textInfo = "\nFile checked..."
    
    for item in settings.mandatoryColumns:
        if item not in dataSet:
            check = False
            textInfo = "ERROR: Missing columns, source file is not prepared correctly.\nRetry with correct .csv file.\n"
            return check, textInfo
        
    return True, textInfo


def collect_entities(nerResults, settings, logGenerator):
   
    logGenerator.clear_results(settings)
    toInsert = ""
    
    for nerResult in reversed(nerResults):

        #First check threshold...
        if float(nerResult['score']) > float(settings.NER_Parameters['threshold']):

            #... now get entries
            for entityGroup, y in logGenerator.resultCollector['listEntities'].items():
                if nerResult['entity_group'] == entityGroup:
                    toInsert = nerResult['word'] + toInsert
                    logGenerator.resultCollector['listEntities'][entityGroup].append(toInsert)
                    toInsert = ""

    #Delete duplicates
    for entityGroup, y in logGenerator.resultCollector['listEntities'].items():
        logGenerator.resultCollector['listEntities'][entityGroup] = list(set(logGenerator.resultCollector['listEntities'][entityGroup]))
        logGenerator.resultCollector['listEntities'][entityGroup].sort()


def collect_subTitle(inputDataTest, row, varSubTitle, varTitle):

    subTitle = ""
    
    if pd.isna(inputDataTest.loc[row, varSubTitle]):
        return subTitle
    else:
        if inputDataTest.loc[row, varTitle][-1:] == ".":
            subTitle = " "
        else:
            subTitle = ". "
        subTitle = subTitle + inputDataTest.loc[row, varSubTitle]
        
    return subTitle


def collect_inputText(settings, inputDataTest, row):

    #Clear empty cells
    for entries in settings.sourceTarget.items():
        for entry in entries:
            if pd.isna(inputDataTest.loc[row, entry]):
                inputDataTest.loc[row, entry] = ''
    
    #Get entries
    if settings.NER_Parameters['origLangOnly'] == True:

        subTitle = collect_subTitle(inputDataTest, row, 'Subtitle', 'Title')
        
        inputText = inputDataTest.loc[row, 'Title'] + subTitle + ", " + inputDataTest.loc[row, 'Abstract']
            
        targetColumn = 'kw###_NEW_orig_lang'

    else:
        #In case translation is missing fall back to original language
        if inputDataTest.loc[row, 'abstract_translated_en'] == '': 

            subTitle = collect_subTitle(inputDataTest, row, 'Subtitle', 'Title')

            inputText = inputDataTest.loc[row, 'Title'] + subTitle + ", " + inputDataTest.loc[row, 'Abstract']

            targetColumn = 'kw###_NEW_orig_lang'

        else:
            abstractText = inputDataTest.loc[row, 'Abstract']

            subTitle = ''
            
            if inputDataTest.loc[row, 'title_translated_en'] == '' and inputDataTest.loc[row, 'subtitle_translated_en'] == '':
                TitleText = inputDataTest.loc[row, 'Title']
                subTitle = collect_subTitle(inputDataTest, row, 'Subtitle', 'Title')

            if inputDataTest.loc[row, 'title_translated_en'] == '' and inputDataTest.loc[row, 'subtitle_translated_en'] != '':
                TitleText = inputDataTest.loc[row, 'subtitle_translated_en']

            if inputDataTest.loc[row, 'title_translated_en'] != '' and inputDataTest.loc[row, 'subtitle_translated_en'] != '':
                TitleText = inputDataTest.loc[row, 'title_translated_en']
                subTitle = collect_subTitle(inputDataTest, row, 'subtitle_translated_en', 'title_translated_en')
                
            if inputDataTest.loc[row, 'title_translated_en'] != '' and inputDataTest.loc[row, 'subtitle_translated_en'] == '':
                TitleText = inputDataTest.loc[row, 'title_translated_en']
             
            inputText = TitleText + subTitle + ", " + abstractText

            targetColumn = 'kw###_NEW_translated_en'

        
    #Prepare input text and remonve some of the inconsistencies
    if settings.NER_Parameters['unidecode'] == True:
        inputText = unidecode(inputText)

    #Cleaning inputText with a search and replace list, see comment in settings
    for key, value in settings.toReplace.items():
        inputText = inputText.replace(key, value)
    
    return inputText, targetColumn


def filter_LOC_results(settings, logGenerator, row, inputData):

    logGenerator.add_to_log(f"\nEntity type ['LOC']:"  + "\n")    
    
    inputTest = inputData.replace(pd.NA, '<NA>')
    
    for name in logGenerator.resultCollector['listEntities']['LOC']:
        
        #Check for existing Koha entry
        if name in inputTest.loc[row, 'Geographic_Name']\
            or name in inputTest.loc[row, 'kwLOC_orig_translated_en']:
                logGenerator.add_to_log("(" + name + " already in Koha)\n")
        
        #Check length after deleting all non-alphanumeric characters, words < 3 characters are unlikely
        else:
            logString = '(no result)'
            nameStripped = re.sub("[\\W\\d\\s]", "", name) 
            
        #If selected: Call gazetteer (return value is only True or False)
            if len(nameStripped) > 2:
                resOriginal = False
                resTranslation = False
                nameTranslated = ''
                if settings.NER_Parameters['checkLocKwGazetteer'] == True:
                    resOriginal = call_gazetteer(name)
                    
                    #If selected, try to translate name in German and run it again
                    if resOriginal is False and settings.NER_Parameters['translateKWforGazetteerCheck'] is True:
                        nameTranslated = translate_placename(settings, inputData, row, name)
                        
                        if nameTranslated == '<NA>':
                            resTranslation = False
                        else:
                            resTranslation = call_gazetteer(nameTranslated)
                save_LOC_results_in_collector(settings, logGenerator, row, inputTest, name, nameTranslated, resTranslation, resOriginal)
 

def filter_other_results(settings, logGenerator, row, inputData):

    inputTest = inputData.replace(pd.NA, '<NA>')

    #... now the other entities including authority ressources calls need to be implemented...
    for entityType, y in logGenerator.resultCollector['listEntities'].items():
        if entityType != 'LOC':

            logGenerator.add_to_log(f"\nEntity type ['{entityType}']:" + "\n")    

            if len(logGenerator.resultCollector['listEntities'][entityType]) == 0:
                logGenerator.add_to_log("(no result) \n")
            else:
                for name in logGenerator.resultCollector['listEntities'][entityType]:
                    nameStripped = re.sub("[\\W\\d\\s]", "", name)

                    if len(nameStripped) > 2:
                        if name in inputTest.loc[row, 'Topical_Term'] or name in inputTest.loc[row, 'kwMISC_orig_translated_en']:
                            logGenerator.add_to_log("(" + name + " already in Koha)\n")
                        else:
                            logGenerator.resultCollector['listEntitiesFiltered'][entityType].append(name)
                            logGenerator.add_to_log(name  + "\n")
                            logGenerator.resultCollector['counterNewKw'][entityType][inputTest.loc[row, 'lang_detected']] += 1
                            
                            #here should be implemented something like
                            #res = call_repositoryXY(name)


def run_NER(settings):
    print("\nStarting NER: ", settings.fileNameForNER)
    
    logGenerator = bf.log_NER_Class(settings)
    logGenerator.add_to_log(f"File: {settings.fileNameForNER}\n\n")
    
    #Start with log
    logGenerator.add_to_log("Selected parameters:\n")
    for x, y in settings.NER_Parameters.items():
        logGenerator.add_to_log(x + ": " + str(y) + "\n")
    logGenerator.add_to_log("\n")
    settings.build_result_fileName_extension()

    #Read and check input .csv
    inputData = bf.read_dataSet(settings, settings.fileNameForNER)
    checkResult, textInfo = check_source(settings, inputData)
    print(textInfo)
    logGenerator.add_to_log(textInfo)

    if checkResult == False:
        logGenerator.save_log(settings)
        sys.exit()

    #Apply filters to prepare input.
    #Note: In case of language filters the function
    #returns only the index numbers of the selected languages
    inputData, indexFiltered = apply_input_filters(inputData, settings)
    
    #Run NER   
    textInfo = ''

    success, inputData, textInfo = run_NER_process(settings, inputData, logGenerator, indexFiltered)

    logGenerator.add_to_log(textInfo)
    print(textInfo)
       
    #Run statistics
    statistics = analyze_result(inputData, settings, logGenerator)
    print("\nStatistics:")    
    print(statistics)
    
    #Save results
    save_results(settings, statistics, inputData, logGenerator)


def run_NER_process(settings, inputData, logGenerator, indexFiltered):

    for x, y in settings.NER_Parameters.items():
        print(f"{x}: {y}")
    
    #Suppressing transformers warnings. Comment out the line if you want to receive warnings
    logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

    tokenizer = AutoTokenizer.from_pretrained(settings.NER_Parameters['model'])
    model = AutoModelForTokenClassification.from_pretrained(settings.NER_Parameters['model'])
    
    nlp = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy=settings.NER_Parameters['aggStrat'])
    inputDataTest = inputData
    try:
        for row in indexFiltered:
            
            logGenerator.add_to_log(f"\nBiblionumber {inputData.loc[row, 'biblionumber']}:\n1. Filtered entities \n")

            #Collect input text from columns and specify target column
            inputText, targetColumn = collect_inputText(settings, inputDataTest, row)
            
            logGenerator.inputTextCollector.append(f"\nBiblionumber {inputData.loc[row, 'biblionumber']}: {inputText}\n")
                
            #Run NER
            nerResults = nlp(inputText)
            
            #Revise the results
            collect_entities(nerResults, settings, logGenerator)
            
            logGenerator.completeResultsJSON[inputData.loc[row, 'biblionumber']] = nerResults #Will not used at the moment
            
            filter_LOC_results(settings, logGenerator, row, inputData)

            filter_other_results(settings, logGenerator, row, inputData)

            write_NER_results(row, logGenerator, settings, nerResults, targetColumn, inputData)
            
            #Break points for backups and console status messages
            if  row != 0 ^ row%100 == 0: #Sets a marker every 100 lines and pushes backup
                toSave = "bib" + str(inputData.loc[row, 'biblionumber']) + ".csv"
                bf.save_backups(inputData, settings, toSave)
                print("Row ", row, " finished")
              
    except:
        textInfo = ("\n\nSome unexpected problem occured while starting the NER pipeline.\n\n"
                    "Check your environment.\n\n")
    
        logGenerator.add_to_log(textInfo)
        logGenerator.save_log(files)
  
        return False, inputData, textInfo
    
    else:
        textInfo = "\nProcess finished. Check log files for detailed result."
        return True, inputData, textInfo


def save_LOC_results_in_collector(settings, logGenerator, row, inputTest, name, nameTranslated, resTranslation, resOriginal):

    if settings.NER_Parameters['checkLocKwGazetteer'] == False:
        logGenerator.resultCollector['listEntitiesFiltered']['LOC'].append(name)
        logString = name
        logGenerator.resultCollector['counterNewKw']['LOC'][inputTest.loc[row, 'lang_detected']] += 1
    
    if settings.NER_Parameters['checkLocKwGazetteer'] == True:
        if resOriginal == False:
            if resTranslation == False:
                notInGazetteer = name
                logString = f"({name} not in gazetteer, no German translation found)"
            if resTranslation == True:
                notInGazetteer = f"{name} German translation \'{nameTranslated}\' found and recorded"
                logString = f"({name} not in gazetteer, but German translation \'{nameTranslated}\' found and recorded)"
                logGenerator.resultCollector['counterTranslatedKW']['LOC'][inputTest.loc[row, 'lang_detected']] += 1
                logGenerator.resultCollector['listEntitiesFiltered']['LOC'].append(nameTranslated + " (TRANSLATED)")
            logGenerator.notInGazetteerCollector.loc[len(logGenerator.notInGazetteerCollector)] = [inputTest.loc[row, 'biblionumber'], notInGazetteer]
        if resOriginal == True:
            logString = name
            logGenerator.resultCollector['listEntitiesFiltered']['LOC'].append(name)
            logGenerator.resultCollector['counterNewKw']['LOC'][inputTest.loc[row, 'lang_detected']] += 1
    logGenerator.add_to_log(logString + "\n")


def save_results(settings, statistics, inputData, logGenerator):
    
    #Save statistics.html...
    statisticHTML = statistics.to_html()
    fileNameExport = "Statistics" + settings.resultExtension + '.html'
    
    with open(os.path.join(settings.resultFolderPath, fileNameExport), 'w', encoding="utf8") as fp:
        for entry in statisticHTML:
            fp.write(entry)
        
        fp.write("<p>" + settings.fileNameForNER + "</p>" + "<p>Date and Time: " + settings.timeStamp + "</p>" )
        for x, y in settings.NER_Parameters.items():
            fp.write("<p>" + x + ": " + str(y) + "</p>")
        
    fp.close()

    #... the results ...
    settings.fileName = 'RESULT' + settings.resultExtension + '.csv'
    bf.save_dataSet(inputData, settings.resultFolderPath, settings.fileName)

    settings.fileName = "Statistics" + settings.resultExtension + '.csv'
    bf.save_dataSet(statistics, settings.resultFolderPath, settings.fileName)

    #... the input texts ...
    with open(os.path.join(settings.resultFolderPath, '02_input-texts.txt'), 'w', encoding="utf8") as fp:
        for entry in logGenerator.inputTextCollector:
            fp.write(entry)
    fp.close()

    #... the negative gazetteer hits ...
    if settings.NER_Parameters['checkLocKwGazetteer'] == True:
        settings.fileName = '03_not_in_gazetteer.csv'
        bf.save_dataSet(logGenerator.notInGazetteerCollector, settings.resultFolderPath, settings.fileName)
    
    #... and the log
    logGenerator.save_log(settings)
    

def write_NER_results(row, logGenerator, settings, nerResults, targetColumn, inputData):

    #Write detailed result to log ...
    logGenerator.add_to_log("\n2. Detailed NER result:\n")
    for result in nerResults:
        logGenerator.add_to_log(str(result)+"\n")

    #Write entities in .csv list
    #... first LOC ...
    toWrite = ''
    if len(logGenerator.resultCollector['listEntitiesFiltered']['LOC']) == 0:
        toWrite = pd.NA
    else:
        for result in logGenerator.resultCollector['listEntitiesFiltered']['LOC']:
            toWrite = toWrite + result + ", "

    targetColumn = targetColumn.replace('###', 'LOC')
    inputData.loc[row, targetColumn] = toWrite
    toWrite = ''

    #... now the rest (merging all non LOC hits to MISC)
    collector = []
    for entity in settings.NER_Entities:
        if entity != 'LOC':
            collector = collector + logGenerator.resultCollector['listEntitiesFiltered'][entity]
    logGenerator.resultCollector['listEntitiesFiltered']['MISC'] = collector
    
    if len(logGenerator.resultCollector['listEntitiesFiltered']['MISC']) == 0:
        toWrite = pd.NA
    else:
        for result in logGenerator.resultCollector['listEntitiesFiltered']['MISC']:
                toWrite = toWrite + result + ", "

    targetColumn = targetColumn.replace('LOC', 'MISC')
    inputData.loc[row, targetColumn] = toWrite       
