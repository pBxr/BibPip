import basic_functions as bf
import prepare_Koha_Export as prep

import os

os.environ['HF_HOME'] = 'your_model_path' #If you don´t want to save the models in the default directory

import run_Translation as rt
import run_NER_on_Abstracts as rn

from settings import ttwSettings

if __name__=='__main__':

    """
    CAUTION: 
    The source folder path in Step 1 is mandatory to initialize BibPip correctly. 
    The scripts in Step 2 can be run independently of each other. 
    In this case, the file name must be specified for each script.
    If all three scripts are run, it is sufficient to specify the file name in Step 1.
    """ 

    # Step 1: Initializing BibPip -------------------------------------
    
    sourceFolderPath = '00_TEST_FILES'
    settings = ttwSettings(sourceFolderPath)
    settings.fileName = 'Koha_Test_Data.csv'
    
    # Step 2: Choosen script(s) you want to run----------------------------

    runKohaPreparation = True 
    #settings.fileName = 'Koha_Test_Data.csv' #Result gets extension: "_lang_detected.csv"
        
    runTranslation = True 
    #settings.fileNameForTranslation = 'Koha_Test_Data_lang_detected.csv' #Result gets extension: "_translated.csv"
        
    runNER = True
    #settings.fileNameForNER = 'Koha_Test_Data_lang_detected_translated.csv'
    # If desired, default settings can be overwritten in the following: 
    
    #settings.NER_Parameters['model'] = 'alexbrandsen/ArchaeoBERT-NER'  #default = 'dslim/bert-base-NER' 
    #settings.NER_Parameters['origLangOnly'] = False                    #default = True
    #settings.NER_Parameters['checkLocKwGazetteer'] = False             #default = True
    #settings.NER_Parameters['translateKWforGazetteerCheck'] = False    #default = True
    #settings.NER_Parameters['unidecode'] = True                        #default = False
    #settings.NER_Parameters['aggStrat'] = 'first'                      #default = max 
        
    # Step 3: Run chosen scripts----------------------------
    
    if runKohaPreparation:
        prep.prepare_Koha_Export(settings)

    if runTranslation:
        rt.run_translation(settings) 
    
    if runNER:
        rn.run_NER(settings)
