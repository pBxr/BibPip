import os
import pandas as pd
import time

class log_NER_Class:

    def __init__(self, settings):
         
        self.logCollector = []
        
        self.logCollector.append(f"Log file: {settings.year:4d}-{settings.month:02d}-{settings.day:02d}, {settings.hour:02d}:{settings.minute:02d}:{settings.second:02d}\n\n")
            
        #Prepare to collect the results
        self.completeResultsJSON = {}
        self.resultCollector = {}
        self.inputTextCollector = ['List of input texts:\n']
        self.notInGazetteerCollector = pd.DataFrame({'biblionumber' : [], 'LOC_not_in_gazetteer' : []})
        
        for task in settings.NER_Entities:
            self.resultCollector['listEntities'] = {}
            self.resultCollector['listEntitiesFiltered'] = {}
            self.resultCollector['counterTranslatedKW'] = {} 
            self.resultCollector['counterNewKw'] = {}
            
        for task in settings.NER_Entities:
            self.resultCollector['listEntities'][task] = []
            self.resultCollector['listEntitiesFiltered'][task] = []
            self.resultCollector['counterTranslatedKW'][task] = {} 
            self.resultCollector['counterNewKw'][task] = {}
            for language in settings.NER_Languages:
                self.resultCollector['counterNewKw'][task][language] = 0
                self.resultCollector['counterTranslatedKW'][task][language] = 0 
             
    def add_to_log(self, logInput):
        
        self.logCollector.append(logInput)
        
    def clear_results(self, settings):

        #Only entries will be reset, not the counter
        for task in settings.NER_Entities:
            self.resultCollector['listEntities'][task] = []
            self.resultCollector['listEntitiesFiltered'][task] = []

    def save_log(self, settings):

        with open(os.path.join(settings.resultFolderPath, "01_log.txt"), 'w', encoding="utf8") as fp:
            for logEntry in self.logCollector:
                fp.write(logEntry)
            fp.close()


def read_dataSet(settings, fileName):
    
    dataSet = pd.read_csv(os.path.join(settings.sourceFolderPath, fileName), sep = '|', encoding ='utf-8', dtype = 'string')
    dataSet = dataSet.replace('<NA>', pd.NA)

    return dataSet


def save_dataSet(dataSet, targetPath, fileName):

    #Make not available values readable
    dataSet = dataSet = dataSet.replace('', pd.NA)#
    dataSet = dataSet.replace(pd.NA, '<NA>')
              
    dataSet.to_csv(os.path.join(targetPath, fileName), sep = '|', encoding ='utf-8')   

def save_backups(dataSet, settings, toSave):
    
    #toSaveTemp = tempFolderPath+toSave
    dataSet.to_csv(os.path.join(settings.tempFolderPath, toSave), sep = '|', encoding ='utf-8')
