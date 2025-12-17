import pandas as pd
import os

import basic_functions as bf

from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
    

def translate_abstracts(dataSet, settings):

    print(f"\nStarting translation: {settings.fileNameForTranslation}")
    
    counter = 0
    
    for sourceLanguage in settings.sourceLanguages:
        print("source language: ", sourceLanguage)    
        for row in dataSet.loc[dataSet.lang_detected == sourceLanguage].index.values:
            for source, target in settings.sourceTarget.items():
                textOrig = dataSet.loc[row, source]
                
                if pd.isna(textOrig):
                    res = '<NA>'

                else:
                    try:
                        res = translate_string(textOrig, sourceLanguage, settings.targetLanguage)
                    except:
                        print(f"ERROR in biblionumber {dataSet.loc[row, 'biblionumber']}. (Check if the field is empty)")
                        res = '<NA> (Translation failed)'
                    
                dataSet.loc[row, target] = res
                
                #Break points for backups
                if  counter != 0 ^ counter%100 == 0: #Sets a marker every 100 lines and pushes backup
                    toSave = "bib"+ str(dataSet.loc[row, 'biblionumber']) + ".csv"
                    bf.save_backups(dataSet, settings, toSave)
                    print(f"Row {row} (language = {sourceLanguage}) finished")
                
                counter += 1    
            
    return(dataSet)


def translate_string (textOrig, sourceLanguage, targetLanguage):

    tokenizer.src_lang = sourceLanguage
    encoded_orig = tokenizer(textOrig, return_tensors="pt")
    generated_tokens = model.generate(**encoded_orig, forced_bos_token_id=tokenizer.get_lang_id(targetLanguage))
    resList = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
    res = ''.join(str(element) for element in resList)

    return res

       
def run_translation(settings):
       
    dataSet = bf.read_dataSet(settings, settings.fileNameForTranslation)

    #Run translation
    dataSet = translate_abstracts(dataSet, settings)
    
    #Save
    settings.fileNameForNER = settings.fileNameForTranslation.replace(".csv", "_translated.csv")
    bf.save_dataSet(dataSet, settings.sourceFolderPath, settings.fileNameForNER)
    
    print("Translation: finished")
  