import os
import time

"""
Because BibPip is a derivate of ttw where settings and options
can be chosen with selection menues, some parts of the code
in this version are without function but kept in the repo 
in case a GUI will be implemented in one of the next versions.
"""

class ttwSettings:
    def __init__(self, sourceFolderPath):
        
        self.fileName = ''
        self.sourceFolderPath = sourceFolderPath
        
        self.fileNameForTranslation = ''
        self.fileNameForNER = ''
        
        self.resultExtension = '_'
         
        #Create time stamp
        self.actualTime = time.localtime()
        self.year, self.month, self.day = self.actualTime[0:3]
        self.hour, self.minute, self.second = self.actualTime[3:6]
        self.timeStamp = (f"{self.year:4d}{self.month:02d}{self.day:02d}_{self.hour:02d}{self.minute:02d}{self.second:02d}_")
        
        #Create result folder for NER results
        self.resultFolderPath = os.path.join(self.sourceFolderPath , (self.timeStamp  + "NER_results"))
        
        if not os.path.exists(self.resultFolderPath):
            os.makedirs(self.resultFolderPath)

        #Create temp folder
        folderName = "_temp_" + str(self.timeStamp)
        self.tempFolderPath = os.path.join(self.sourceFolderPath, folderName)
    
        if not os.path.exists(self.tempFolderPath):
                os.makedirs(self.tempFolderPath)    
     
        #Set default NER parameters, see also lists below
        self.NER_Parameters = dict(model = 'dslim/bert-base-NER',
                            aggStrat = 'max',
                            threshold = 0.5,
                            language = 'none', #If not 'none' NER only takes
                                               #into account the entries
                                               #in the selected original language
                            origLangOnly = True, #False = prefering englisch translations
                            checkLocKwGazetteer = True,
                            translateKWforGazetteerCheck = True,
                            unidecode = False)

        #Possible NER parameter lists (not all will be used)
        self.NER_Models = ['dslim/bert-base-NER', \
                            #'alexbrandsen/ArchaeoBERT-NER',
                            #'dslim/bert-large-NER',
                           ]
                
        self.NER_Thresholds = [0.5, 0.75, 0.90]

        #Abbreviations refer to ISO 639-1 codes
        self.NER_Languages = ['af', 'ar', 'bg', 'bn', 'ca', 'cs', 
                              'cy', 'da', 'de', 'el', 'en', 'es',
                              'et', 'fa', 'fi', 'fr', 'gu', 'he',
                              'hi', 'hr', 'hu', 'id', 'it', 'ja',
                              'kn', 'ko', 'lt', 'lv', 'mk', 'ml',
                              'mr', 'ne', 'nl', 'no', 'pa', 'pl',
                              'pt', 'ro', 'ru', 'sk', 'sl', 'so',
                              'sq', 'sv', 'sw', 'ta', 'te', 'th',
                              'tl', 'tr', 'uk', 'ur', 'vi', 'zh-cn', 
                              'zh-tw', '<NA>']

        #Caution: The abbreviations may vary depending on the chosen model.  
        self.NER_Entities = ['LOC', 'MISC', 'ORG', 'PER'] #Categories refering to dslim/bert-base-NER

        #ArchaeoBERT-NER uses 'PER' for 'Time Periods', i. e.:
        #self.NER_Entities = ['LOC', 'MISC', 'ORG', 'PER', 'ART', 'CON', 'MAT', 'SPE']
        
        self.aggStrats = ['first', 'average', 'max']
        #'none' and 'simple' are not integrated
        
        #Translation
        self.columnsToClean = ['Abstract',
                               'Title',
                               'Subtitle',
                               'Topical_Term',
                               'Geographic_Name']
        
        self.mandatoryColumns = ['lang_detected',
                                'title_translated_en',
                                'subtitle_translated_en',
                                'abstract_translated_en',
                                'kwLOC_orig_translated_en',
                                'kwMISC_orig_translated_en',
                                'kwLOC_NEW_orig_lang',
                                'kwMISC_NEW_orig_lang',
                                'kwLOC_NEW_translated_en',
                                'kwMISC_NEW_translated_en']

        self.sourceTarget = {'Title' : 'title_translated_en',
                    'Subtitle' : 'subtitle_translated_en',
                    'Abstract' : 'abstract_translated_en',
                    'Topical_Term' : 'kwLOC_orig_translated_en',
                    'Geographic_Name' : 'kwMISC_orig_translated_en'}
        
        self.columnsStatistics = ['Language',
                                  'Entries',
                                  '... with entries in kwLOC',
                                  '... with entries in kwMISC',
                                  '... newly added_kwLOC',
                                  '... newly added_kwMISC',
                                  '(found after translation, if selected)',#NEW
                                  ]
        #Set default translation parameters
        self.sourceLanguages = ['de', 'fr', 'es', 'it']
        self.targetLanguage = 'en'

        #Search and replace list
        """
        Following expressions were randomly noticed in previous runs,
        so they are listed here. The list is not complete and must be extended.
        """

        self.toReplace = { 
                "  " : " ",
                " - Engl." : "Engl.",
                " , " : " ",
                " ; ": "; ",
                " : " : " ",
                " :" : ". ",
                " /" : ". ",
                " = " : ". ",
                "--" : "",
                "?." : "?",
                ".," : ".",
                ".." : ".",
                "/" : ". ",
                "\"" : "",
                "\n" : "",
                "\t" : "",
                "&amp;" : "&",
                "&amp" : "&",
                "Dt. Zusammenfassung" : "",
                "Engl. summary" : "",
                "engl. summary" : "",
                "English summary" : "",
                "Summary engl. u. franz." : "",
                "Summary in Arabic. language" : "",
                "summary in dt. language" : "",
                "Summary in dt. language" : "",
                "Summary in English" : "",
                "Summary in French and English" : "",
                "Summary in Pers. language" : "",
                "Summary in Portuguese. language" : "",
                "Summary in Span. language" : "",
                "Zsfassung" : "Zusammenfassung",
                "Zsfassungen" : "Zusammenfassungen",
                "Zusammenfassung in arab. Sprache" : "",
                "Zusammenfassung in dt. Sprache" : "",
                "Zusammenfassung in engl. Sprache" : "",
                "Zusammenfassung in pers. Sprache" : "",
                "Zusammenfassung in portug. Sprache" : "",
                "Zusammenfassung in russ. Sprache" : "",
                "Zusammenfassung in span. Sprache" : "",
                "Zusammenfassungen in engl. Sprache" : "",
                "Zusammenfassungen in engl. u. dt. Sprache" : "",
                "Zusammenfassungen in franz. engl. u. dt. Sprache" : "",
                "Zusammenfassungen in franz. u. engl. Sprache" : "",
                "Zusammenfassungen in portug. Sprache" : "",
                }
        
    def build_result_fileName_extension(self):
        
        for x, y in self.NER_Parameters.items():
            if x != 'model':
                if type(y) == bool:
                    y = str(int(y))
                self.resultExtension = self.resultExtension + str(y) + '_'
        self.resultExtension = self.resultExtension[:-1]
        self.resultExtension = self.resultExtension.replace('.', '_')
    