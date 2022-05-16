# -*- coding: UTF-8 -*-

import pkgutil
from os import path
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import spacy
from spacy import lang
from spacy.tokens import Doc

from app.config import db, PATH, app
from app.models import WordToken

from app.lib.linking_components.EntityFishingLinking import fishing_entities

CUSTOM_MODELS_SPACY_LOCATION = Path(path.join(PATH, 'instance_config/my_features/my_models/'))


def get_models():
    """return a list of all models (base and custom)"""
    models = []
    for pipe in spacy.info()["pipelines"]:
        models.append(pipe)

    configs = CUSTOM_MODELS_SPACY_LOCATION.glob("**/meta.json")
    for config in configs:
        models.append(config.parent.relative_to(CUSTOM_MODELS_SPACY_LOCATION))
    return models


def get_spacy_languages():
    """return all available languages from spaCy API"""
    return [str(modname) for imp, modname, ispkg in pkgutil.iter_modules(lang.__path__) if ispkg]


class NerSpacyEngine:
    def __init__(self,
                 language: str,
                 type_model: str,
                 mapping_filter: list = None,
                 patterns: list = None,
                 threshold: float = None,
                 length_threshold: float = None) -> None:

        if mapping_filter is None:
            mapping_filter = []
        self.language = language
        self.type_model = type_model
        self.mapping_filter = mapping_filter if mapping_filter is not None else []

        self.patterns = patterns
        self.threshold = threshold
        self.length_treshold = length_threshold

        self.nlp = None
        self.meta = None
        self.ruler = None

        try:
            # case with preload models
            self.nlp = spacy.load(self.type_model, disable=['parser', 'tagger', 'textcat'])
        except:
            path_model = path.join(CUSTOM_MODELS_SPACY_LOCATION, self.type_model)
            self.nlp = spacy.load(path_model, disable=['parser', 'tagger', 'textcat'])

        self.nlp.add_pipe("entity_fishing")

        self.meta = self.nlp.meta

    def get_ner(self, project_id, document_id, schema, sentences=None, document=None):
        counter = 0
        results = []
        # batch_size=200, n_process=2
        if schema == "tei" or schema == "text":
            doc = self.nlp(document)
            for ent in doc.ents:
                counter += 1
                if ent.label_ in self.mapping_filter:
                    print(ent._.QID)
                    results.append(WordToken(project_id=project_id,
                                             document_id=document_id,
                                             mention=str(ent),
                                             label=ent.label_,
                                             start=ent.start_char,
                                             end=ent.end_char))
                percentage = counter / len(doc.ents) * 100
                yield "data:" + str(int(percentage)) + "\n\n"

        if schema == "ead":

            if not Doc.has_extension("text_id"):
                Doc.set_extension("text_id", default=None)

            docs = self.nlp.pipe(sentences, as_tuples=True)
            start_sentence = 0
            number_sentence = 0
            for doc, context in docs:
                if number_sentence == 50:
                    start_sentence = 0
                    number_sentence = 0
                counter += 1
                number_sentence += 1
                start_sentence = start_sentence
                end_sentence = start_sentence + len(doc.text)
                for ent in doc.ents:
                    ent_start_char = start_sentence + ent.start_char
                    ent_end_char = ent_start_char + len(ent.text)
                    if ent.label_ in self.mapping_filter:
                        results.append(WordToken(project_id=project_id,
                                                 document_id=document_id,
                                                 start=ent_start_char,
                                                 end=ent_end_char,
                                                 mention=str(ent),
                                                 label=ent.label_,
                                                 sentence_id=context["text_id"])
                                   )
                start_sentence = end_sentence
                percentage = counter / len(sentences) * 100
                yield "data:" + str(int(percentage)) + "\n\n"
        with app.app_context():
            db.session.bulk_save_objects(results)
            db.session.commit()
