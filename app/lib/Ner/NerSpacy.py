# -*- coding: UTF-8 -*-

import pkgutil
from os import path
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import spacy
from spacy import lang
from spacy.tokens import Doc
from rapidfuzz import process, fuzz, string_metric
from spacy.language import Language
from phruzz_matcher.phrase_matcher import PhruzzMatcher

from app.config import db, PATH, app
from app.models import WordToken


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
        self.mapping_filter = mapping_filter if mapping_filter is not None else []
        self.language = language
        self.type_model = type_model

        self.patterns = patterns
        self.threshold = threshold
        self.length_treshold = length_threshold

        self.nlp = None
        self.meta = None
        self.ruler = None
        self.spaczz_ruler = None
        config = {
            "overwrite_ents": True
        }

        try:
            # case with preload models
            self.nlp = spacy.load(self.type_model, disable=['tok2vec', 'tagger', 'parser', 'attribute_ruler', 'lemmatizer', 'senter'])
        except:
            path_model = path.join(CUSTOM_MODELS_SPACY_LOCATION, self.type_model)
            self.nlp = spacy.load(path_model, disable=['tok2vec', 'tagger', 'parser', 'attribute_ruler', 'lemmatizer', 'senter'])

        if self.patterns != None and "entity_ruler" not in self.nlp.pipe_names:
            print("ajout entity ruler")
            #self.spaczz_ruler = self.nlp.add_pipe("spaczz_ruler", config=config, before="ner")
            #self.spaczz_ruler.add_patterns(patterns)
            #self.nlp.add_pipe("sentencizer")
            #self.ruler = self.nlp.add_pipe('entity_ruler', config=config, before="ner")
            #self.ruler.add_patterns(self.patterns)
            self.candidates = []
            self.ids = []
            self.canditates_ids = {}
            for pattern in self.patterns:
                for key, value in pattern.items():
                    if key == "pattern":
                        p = value
                        self.candidates.append(p)
                    if key == "id":
                        identifier = value
                        self.ids.append(identifier)
            for p, i in zip(self.candidates, self.ids):
                self.canditates_ids[p] = i

            @Language.factory("phrase_matcher")
            def phrase_matcher(nlp: Language, name: str):
                return PhruzzMatcher(nlp, self.candidates, "INDEX", 85)

            self.nlp.add_pipe('phrase_matcher', before="ner")

            # self.candidates = [pattern for pattern in self.patterns for _, pattern, _, _, _ in pattern.items()]
            # self.candidates_ids = {pattern: identifier for pattern in self.patterns for _, pattern, identifier, _, _ in pattern.items()}
        self.meta = self.nlp.meta




    def get_ner(self, project_id, document_id, schema, sentences=None, document=None):
        counter = 0
        results = []
        # batch_size=200, n_process=2
        if schema == "tei":
            print("first pass")
            doc = self.nlp(document)
            print("secondpass")
            for ent in doc.ents:
                counter += 1
                if ent.label_ in self.mapping_filter:
                    results.append(WordToken(project_id=project_id,
                                             document_id=document_id,
                                             mention=str(ent),
                                             label=ent.label_,
                                             start=ent.start_char,
                                             end=ent.end_char))

                    print(str(ent), ent.label_, ent.ent_id_)
                    #else:
                    #    r = process.extractOne(str(ent), self.candidates, scorer=fuzz.ratio, score_cutoff=80)
                    #    if r is not None:
                    #        print(str(ent), " : ", r[0], " : ", r[1], " : ", self.canditates_ids[r[0]])


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
