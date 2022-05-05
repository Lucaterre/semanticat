<!--<img src="" width=300 align=right>-->

![Python Version](https://img.shields.io/badge/python-3.8-blue) [![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/tterb/atomic-design-ui/blob/master/LICENSEs) [![Semantic@ CI build](https://github.com/Lucaterre/semanticat/actions/workflows/CI.yml/badge.svg)](https://github.com/Lucaterre/semanticat/actions/workflows/CI.yml)


# Semanti🐱 

**WORK-IN-PROGRESS**

Semantic@ is a semantic annotation platform for enriching XML documents in [TEI](https://tei-c.org/) or [EAD](https://www.loc.gov/ead/) schemas with semantic annotations.

Follow a simple workflow: After importing the document(s), apply the NER model and correct prediction or annotate manually from-zero and finally export and/or publish your XML with annotations directly inside.

This platform is also designed to adapt generically to the diversity of publishing projects and a base for adding custom components.


## :movie_camera: Demo

![semanticat_demo](./documentation/semanticat_demo.gif)

## :battery: Installation

1. Clone the Github repository

```bash
git clone https://github.com/Lucaterre/semanticat.git
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

:fire: This application is intended to be simple and local for the moment. **Please note that the application is currently optimized for the Firefox browser.**

Use the semantic@ CLI; inside the `semanticat/` directory, launch the command :

```bash
python run.py
```

Others arguments :

| **Type**              | **Details**                              |
|-----------------------|------------------------------------------|
| `--dev_mode`          | Launch application in development mode   |
| `--erase_recreate_db` | Clean and Restore all database :warning: |


## :arrow_forward: Getting started


- Start by creating a project with the button `Create a new project` and open your project;
- Go to `Menu` > `Manage documents` and import your XML, now you can see your documents in
`Project workflow` view (You can mix EAD and TEI);
- In `Project workflow` view: Apply `parse` feature on document one by one or apply `Parse All` on all documents;

- Go to `Menu` > `configuration`, two use cases :

1. You don't want to apply a NER model, and you want to manually annotate your data :
- First, define Annotation mapping (see the "Mapping details" section);
- Add labels with `Add new pair to mapping scope`;
- Then, go to `Project workflow` > `correct named entities` and start annotation.

2. You want to use an NER (recommend) model to predict named entities and correct afterwards (see the "NER configuration details" section):
- First, select checkbox `NER Recommenders`;
- Then, Choose the correct language that corresponding to your model;
- Then, Select the model and save;
- Wait, the pre-mapping appears, you can then adapt it (see the "Mapping details" section);
- Go to `Project workflow` > `Launch Ner` (or `Launch Ner on all`);
- When the process is complete,s, go to `correct named entities` and correct the predictions or add annotations.

- Whatever the chosen scenario, once the correction is finished, you can export your document (see the "Export details" section) !

## :dart: Detail sections

### Mapping

The mapping is a table that references the labels you use for annotation with:

- *Ner Label*: The default label use to annotate or use by your model;
- *Prefered Index label*: The label that will appear in the output;
- *Color*: label color in annotation view.

You can add new labels to your existing schema via `Add new pair to mapping scope`.

Be careful if you remove a label from table, if your model has already made predictions or if you have started to correct document, all annotations will be destroyed.

### NER configuration

Currently, Semantic@ uses the NER SpaCy framework, in the future other frameworks may be integrated.

When installing the Semantic@, two pre-trained models for French (fr_core_news_sm) and English (en_core_web_sm) are already available

For add a new available [SpaCy pre-trained model](https://spacy.io/usage/models), before starting Semantic@, launch in terminal : 

```bash
python -m spacy download <name-pretrained-model>
```

The new pre-trained model will be directly available in model list from `configuration`.

Sometimes, SpaCy’s default in-built pre-trained NER model are too slow and too generic for your data (the model is far from perfect so it doesn't necessarily detect your labels).
If you have training a better statistical NER model with SpaCy, you can place your NER model folder under `/instance_config/my_features/my_models/` 

Your model will be directly available in model list from `configuration`.

### Export

There are different XML export solutions : 

- `annotations inline (based on characters offsets)` (TEI specific): This export uses standoff converter and uses the positions of annotations in the text to produce output. It is precise but sometimes it takes time.
- `annotations to controlaccess level` (EAD specific): This export tags annotations in a level of type <controlaccess>.
- `annotations inline (based on surface form matching)` (TEI & EAD): This export uses the surface shape of annotated mentions to tag the output. It is fast but sometimes less precise.


- `annotations in JSON`: This export allows you to keep track of your annotations in a JSON format and import it directly into the annotation view.

## :crying_cat_face: Bug reports

Feel free to create a [new issue](https://github.com/Lucaterre/semanticat/issues/new/choose) (new features, bug reports, documentation etc.).

## :computer: Stack 

### Interface

[![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/en/2.1.x/)
[![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/index.html)
[![Bootstrap](https://img.shields.io/badge/bootstrap-%23563D7C.svg?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)

### Main Components

- [![Spacy](https://img.shields.io/badge/NLP%20with-SpaCy-blue)](https://spacy.io/)

- [![RecogitoJS](https://img.shields.io/badge/Text%20annotation%20with-RecogitoJS-9cf)](https://github.com/recogito/recogito-js)

- [![Standoffconverter](https://img.shields.io/badge/Annotations%20in%20TEI%20with-StandoffConverter-red)](https://github.com/standoff-nlp/standoffconverter)

## :bust_in_silhouette: Mainteners

- [@Lucaterre](https://github.com/Lucaterre)


## :black_nib: How to cite

Please use the following citation:

    @misc{terriel-2022-semanticat,
        title = "Semantic@ : a semantic annotation platform for enriching XML documents in TEI or EAD schemas with semantic annotations.",
        author = "Terriel, Lucas",
        year = "2022",
        url = "https://github.com/Lucaterre/semanticat",
    }

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
