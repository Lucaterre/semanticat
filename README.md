<!--<img src="" width=300 align=right>-->

![Python Version](https://img.shields.io/badge/python-3.8-blue) [![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/tterb/atomic-design-ui/blob/master/LICENSEs)
<!-- CI badge -->
# Semanti🐱 

**WORK-IN-PROGRESS**

Semantic@ is a platform for enriching XML documents in TEI or EAD format with named entities. 

After importing the document(s), apply the NER model and correct prediction or annotate manually from-zero and finally export and/or publish your XML with annotations inside.


## :battery: Installation



1. Clone the Github repository

```bash
git clone 
```

2. Move inside the directory

```bash
cd ./semanticat
```

4. Create a virtual environment with virtualenv

```bash
virtualenv --python=/usr/bin/python3.8 venv
```

5. Activate the virtual environment

```bash
source venv/bin/activate
```

6. Install dependencies

```bash
pip install -r requirements.txt
```


## :rocket: Run Locally

Use the semantic@ CLI; inside the `semanticat/` directory, launch the command :

```bash
python run.py
```

Others arguments :

| **Type**              | **Details**                                  |
|-----------------------|----------------------------------------------|
| `--dev_mode`          | Launch app in development mode               |
| `--erase_recreate_db` | Clean and Restore all database :warning: |

## :arrow_forward: Quick Start

(TODO : créer un wiki ? avec détails sur les exports, sur la manière d'annoter, sur comment enregistrer sur modèle NER etc.)

- Start by "create a new project"
- Go to "Menu" > "Manage documents" and import your XML, You can see your documents in
"Project workflow" view
- Apply "parse" on document one by one or apply "parse" on all documents
- Go to "Menu" > "configuration", two use cases :

1. You don't apply NER model, and use semantic@ to create manually annotated data :
- First, define Annotation mapping ("NER Label" is display on annotation view, "Prefered index label" is display in export, define color) and save everytime
- Then, go to "Project workflow" > "correct named entities" and start annotate

2. You want to use NER recommenders to predict named entities (see the "NER configuration details section"):
- First, select checkbox 'NER Recommenders'
- then, Choose the language that corresponding to your model
- then, Select the model and save
- Adjust the mapping
- Go to "Project workflow" > "Launch Ner"
- After the process, go to "correct named entities" to correct the predictions

- Now you can export your document !

## NER configuration details section

The NER framework that semantic@ use is SpaCy.

By default, the platform provides two small pre-trained model for French and English.

For add new [SpaCy pre-trained model](https://spacy.io/usage/models) : 

```bash
python -m spacy download <name-pretrained-model>
```

The SpaCy pre-trained language are sometimes slow and too generic for your data, you 
can use your own trained model, place your NER model folder under `/instance_config/my_features/my_models/` 

## :crying_cat_face: Bug reports

## :computer: Stack 

### Interface

[![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/en/2.1.x/)
[![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/index.html)
[![Bootstrap](https://img.shields.io/badge/bootstrap-%23563D7C.svg?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)

### Main Components

## :bust_in_silhouette: Authors

- [@Lucaterre](https://github.com/Lucaterre)

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
