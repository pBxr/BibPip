# BibPip

Test pipeline for Named Entity Recognition in bibliographical entries.

## Introductory remarks

`BibPip` is based on a `Named Entity Recognition (NER)` pipeline that was originally implemented for the `TagTool_WiZArD application (ttw)` (https://github.com/pBxr/TagTool_WiZArd) using the `Hugging Face` `Transformers` pipeline (see https://huggingface.co). 
For testing purposes the `ttw` pipeline was modified so that it can be run on bibliographical entries in iDAI.bibliography, the catalogue of the German Archaeological Institute´s (DAI) libraries and one of the largest databases with bibliographic entries on ancient studies (https://zenon.dainst.org). The idea is to find out if freely available and even domain unspecific models have already reached a sufficient level of quality so that they can provide added value by enriching bibliographical entries with extracted keywords. 

Due to its modular setup, it is possible to combine different models for different tasks and several options can be chosen to test their effect on the output quality and to adjust different settings to the dataset, i. e. that the dataset can be processed iteratively to achieve the best result.

Since this is an "on premises" solution, it is also compliant to copyright protection regulations.

For the above mentioned purpose `BibPip` provides three scripts (`prepare_Koha_Export.py`, `run_Translation.py` and `run_NER_on_Abstracts.py`). The main file (`BibPip.py`) serves as a starting point from which the scripts can be run independently of each other (see "The main scripts" below for more information). 

## How to setup

It is recommended to create a Python virtual environment first (see e. g. `ttw_help.html`in https://github.com/pBxr/TagTool_WiZArd). For informations on how to install the `Hugging Face` `Transformers` pipeline see https://huggingface.co/docs/transformers/installation.
Following Python libraries need to be installed as well: `pandas`, `langdetect`, `unidecode`.

Depending on the models additional packages or libraries might need to be installed, see the `Hugging Face` model cards including the installation guides (e. g. the here used `m2m100_418M` model for translation requires to install `sentencepiece` first). Furthermore the `BibPip` code might need to be modified as well (see e. g. 'NER_Entities' below). 

This repo is tested with Python 3.12.0. 

### Models

The code was tested with the following models:
- Named Entity Recognition: `dslim/bert-base-NER` 
- Translation: `facebook/m2m100_418M` model for Many-to-many translation.

## Approach

Starting point is a `.csv` file with entries exported from Koha, an open source library system. Following categories/column names are mandatory (separator = '|'. Explaining numbers in brackets below refer to MARC21 format used in this case):

- 'biblionumber'
- 'Abstract' (export from 520a)
- 'Title' (export from 245a)
- 'Subtitle' (export from 245b)
- 'Topical_Term' (export from 650a)
- 'Geographic_Name' (export from 651a)

The file `Koha_Test_Data.csv` contains a few entries and can be used for testing purposes.

### The main scripts 

First, set up your environment and install all dependiences: 

```python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

See the comments in the main file (`BibPip.py`) on how to initialize BibPip and how to run the scripts below.

1.) Prepare the source `.csv` file (`prepare_Koha_Export.py`):

- After being loaded into a `Pandas` DataFrame, Koha export artefacts and unspecific characters are being removed from the entries (search/replace list needs more elaboration), also unicode normalization is being carried out (to 'NFC').
- The language is being assigned by using the Python `langdetect` library (codes according to ISO 639-1).
- Finally the mandatory columns for the further steps are being created and the file is saved again as `.csv` file.

2.) Translation (OPTIONAL) (`run_Translation.py`)

- 'Title', 'Subtitle', 'Topical_Term', 'Geographic_Name' as well as the 'Abstract' are being translated and saved in separate columns. By default entries in 'de', 'fr', 'es', 'it' will be translated into 'en'. This step is optional. The idea is to test whether a translation of non-English-language abstracts can have a positive effect on the `NER` in the next step.
- The translation was tested with `facebook/m2m100_418M` (see above)

3.) Named Entity Recognition (`run_NER_on_Abstracts.py`):

- The entries in 'Title', 'Subtitle' and 'Abstract' are merged to a single string from which the model extracts the specific entity classes.
- If selected, the LOC-results are run through the iDAI.gazetteer webservice to identify the locations. If the query does not return a hit the LOC-result is discarded. If the LOC-result is not in German it will be translated and run again. In case of a hit a remark is added to the log.
- As mentioned above, the pipeline is tested with `dslim/bert-base-NER`. Despite the fact that other models may need additional packages, they might as well return different entity classes as result (see the remarks in `settings.py`), therefore the code needs to be modified accordingly.
- When writing the results, all results that are not 'LOC' will be saved as 'MISC', i. e. `BibPip` distinguishes only between 'LOC' and 'MISC' in this version.  
- Theoretically, the tool can be run several times in succession with different models depending on the language to achieve the best result for each language.

## Settings

- Because `BibPip` does not have a GUI in this version, some details - like the file path - must to be entered manually in the script (see the comments in the code). 
- The default options are set in the 'NER_parameters' variable in `settings.py`. They also can be overwritten in the main file (`BibPip.py`).
- If 'origLangOnly' is set to 'False', `BibPip` takes the English translation for the `NER`. In case there is no Englisch translation available it falls back to the original language.
- 'NER_Entities': Depending on the model the classes need to be modified. By default (i. e. for the `dslim/bert-base-NER` model) they are set to ['LOC', 'MISC', 'ORG', 'PER'], others may differ (e. g. 'alexbrandsen/ArchaeoBERT-NER', see the comment in `settings.py`).
- 'aggStrat': 'none' and 'simple' are not integrated.

## Logs, temps and backup files

`run_NER_on_Abstracts.py` creates a 'NER_results' folder for every session. Together with the result, log files make the outcome comprehensible:

- '01_log.txt': According to the model´s specific `NER` classes the results are listed here. In case Koha already contained a keyword that was extracted by `BibPip` it is noticed in brackets and the result will be discarted. Additionally the detailed`NER` result is listed an the end of the entry.
- '02_input-texts.txt': To check if the texts were merged correctly ('Title', 'Subtitle' and 'Abstract'), the input texts are saved here as well.
- '03_not_in_gazetteer.csv': If the option 'checkLocKwGazetteer' is selected, all LOC hits that could not be found in iDAI.gazetteer are saved here to identify possible false negative hits. 
- As well as for the translation as for the `NER` process a temp folder will be created every session to save intermediate backup files. The frequency in which the backup files are beeing written can be selected manually according to the size of the dataset (see 'Break points for backups' in `run_Translation.py` and `run_NER_on_Abstracts.py`). By default every 100 iterations a backup is being pushed.

## Results and statistics

The main result is saved as a `.csv` file. For a better understanding the extension of the file name represents the settings. For example 'RESULT_max_0_5_none_0_1_0.csv" means: aggStrat = 'max', threshold = 0.5, Language = 'none', origLangOnly = False, checkLocKwGazetteer = True, unidecode = False. The statistics are saved as `.html` and `.csv` file with the same file name extension.

## Further remarks:

- Because `BibPip` is a derivate of `ttw` where settings and options can be chosen with a selection menue in the GUI, some parts of the code in this version are without function (see `settings.py`) but kept in the repo in case a GUI will be implemented in one of the next versions.
- Transformers warnings are suppressed (see note in 'run_NER_process' function in `run_NER_on_Abstracts.py`)

## To be done

- The scripts for the translation and Named Entity Recognition maybe need to be combined provide a flexible option for translations within in NER script logic (e. g. translating LOC hits before running them through reference ressources like iDAI.gazetteer).
- Due to the many possible combinations (especially in `run_NER_on_Abstracts.py`) the structure of the code needs to be improved, because it is not easy to understand.

## Sources and citations

- `Hugging Face` `Transformers`:

see https://huggingface.co/docs/transformers/index

@misc{wolf2020huggingfacestransformersstateoftheartnatural,
      title={HuggingFace's Transformers: State-of-the-art Natural Language Processing}, 
      author={Thomas Wolf and Lysandre Debut and Victor Sanh and Julien Chaumond and Clement Delangue and Anthony Moi and Pierric Cistac and Tim Rault and Rémi Louf and Morgan Funtowicz and Joe Davison and Sam Shleifer and Patrick von Platen and Clara Ma and Yacine Jernite and Julien Plu and Canwen Xu and Teven Le Scao and Sylvain Gugger and Mariama Drame and Quentin Lhoest and Alexander M. Rush},
      year={2020},
      eprint={1910.03771},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/1910.03771}, 
}

- `dslim/bert-base-NER`:

see https://huggingface.co/dslim/bert-base-NER

@misc{devlin2019bertpretrainingdeepbidirectional,
      title={BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding}, 
      author={Jacob Devlin and Ming-Wei Chang and Kenton Lee and Kristina Toutanova},
      year={2019},
      eprint={1810.04805},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/1810.04805}, 
}

@inproceedings{tjong-kim-sang-de-meulder-2003-introduction,
    title = "Introduction to the {C}o{NLL}-2003 Shared Task: Language-Independent Named Entity Recognition",
    author = "Tjong Kim Sang, Erik F.  and
      De Meulder, Fien",
    booktitle = "Proceedings of the Seventh Conference on Natural Language Learning at {HLT}-{NAACL} 2003",
    year = "2003",
    url = "https://aclanthology.org/W03-0419/",
    pages = "142--147"
}

- `facebook/m2m100_418M`:

see https://huggingface.co/facebook/m2m100_418M

@misc{fan2020englishcentricmultilingualmachinetranslation,
      title={Beyond English-Centric Multilingual Machine Translation}, 
      author={Angela Fan and Shruti Bhosale and Holger Schwenk and Zhiyi Ma and Ahmed El-Kishky and Siddharth Goyal and Mandeep Baines and Onur Celebi and Guillaume Wenzek and Vishrav Chaudhary and Naman Goyal and Tom Birch and Vitaliy Liptchinsky and Sergey Edunov and Edouard Grave and Michael Auli and Armand Joulin},
      year={2020},
      eprint={2010.11125},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2010.11125}, 
}