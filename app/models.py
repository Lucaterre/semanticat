# -*- coding: UTF-8 -*-

"""
models.py

Declaration of all the models used in the database

TODO: rename models and refactor attributes/methods
TODO: reformat docstrings
TODO: include a diagram

last updated : 12/05/2022
"""

from collections import Counter
from sqlalchemy import func

from app.config import db


class Sentence(db.Model):
    """Sentence Model"""
    __tablename__ = "sentence"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer)
    content = db.Column(db.Text)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id', ondelete='CASCADE'))

    """"
    @staticmethod
    def _return_all_sentences():
        sentences = Sentence.query.all()
        return sentences
    """
    @staticmethod
    def return_all_sentences_for_document(doc_id):
        """Get all sentences inherit from a specific document by ID attribute
        in format [(1, content1), (2, content2) ...]
        """
        sentences = Sentence.query.filter_by(document_id=doc_id).all()
        sentences_content = [(sentence.id, sentence.content) for sentence in sentences]
        return sentences_content

    @staticmethod
    def return_texts_tuples(doc_id):
        """Get all sentences inherit from a specific document by ID attribute
        in format [(content1, {"text_id":1}), (content2, {"text_id":2}) ...]
        """
        sentences = Sentence.query.filter_by(document_id=doc_id).all()
        return [(sentence.content, {"text_id": sentence.id}) for sentence in sentences]


class WordToken(db.Model):
    """WordToken Model"""
    __tablename__ = "word_token"
    id = db.Column(db.Integer, primary_key=True)
    mention = db.Column(db.String(64))
    start = db.Column(db.Integer)
    end = db.Column(db.Integer)
    label = db.Column(db.String(12))
    wikidata_qid = db.Column(db.Text, default="NIL")
    attributes_ids = db.Column(db.PickleType, default={"Properties": {}})
    sentence_id = db.Column(db.Integer, default=0)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id', ondelete='CASCADE'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'))

    @staticmethod
    def get_annotations_mention_label(document_id):
        """Get list of annotations in tuples as
        [(mention, label), ...]
        """
        return [
            (annotation.mention, annotation.label)
            for annotation in WordToken.query.filter_by(
                document_id=document_id
            ).order_by(
                WordToken.start
            ).all() if annotation.label != ""
        ]

    @staticmethod
    def get_annotations(document_id):
        """Get list of data models corresponding to annotations
        filter by document and order by offset start
        see data model : https://www.w3.org/TR/annotation-model/
        """
        return [{
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": annotation.id,
            "sentence_id": annotation.sentence_id,
            "type": "Annotation",
            "body": [{
                "type": "TextualBody",
                "value": annotation.label,
                "purpose": "highlighting"
            }],
            "target": {
                "selector": [{
                    "type": "TextQuoteSelector",
                    "exact": annotation.mention,
                }, {
                    "type": "TextPositionSelector",
                    "start": annotation.start,
                    "end": annotation.end
                }]
            }
        } for annotation in WordToken.query.filter_by(
            document_id=document_id
        ).order_by(
            WordToken.start
        ).all()
        ]

    @staticmethod
    def get_annotations_to_delete(document_id, mention, label):
        """Get list of data models corresponding to annotations
        to delete filter by document, order by offset start, and
        corresponding to label and mention to delete
        see data model : https://www.w3.org/TR/annotation-model/
        """
        return [{
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": annotation.id,
            "type": "Annotation",
            "body": [{
                "type": "TextualBody",
                "value": annotation.label,
                "purpose": "highlighting"
            }],
            "target": {
                "selector": [{
                    "type": "TextQuoteSelector",
                    "exact": annotation.mention,
                }, {
                    "type": "TextPositionSelector",
                    "start": annotation.start,
                    "end": annotation.end
                }]
            }
        } for annotation in WordToken.query.filter_by(
            document_id=document_id
        ).order_by(
            WordToken.start
        ).all() if (
                annotation.mention == mention and annotation.label == label
        )
        ]

    @staticmethod
    def get_annotations_ead(document_id, list_ids):
        """Get list of data models corresponding to annotations
        filter by document and order by offset start (specific to EAD)
        see data model : https://www.w3.org/TR/annotation-model/
        """
        return [{
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": annotation.id,
            "type": "Annotation",
            "body": [{
                "type": "TextualBody",
                "value": annotation.label,
                "purpose": "highlighting"
            }],
            "target": {
                "selector": [{
                    "type": "TextQuoteSelector",
                    "exact": annotation.mention,
                }, {
                    "type": "TextPositionSelector",
                    "start": annotation.start,
                    "end": annotation.end
                }]
            }
        } for annotation in WordToken.query.filter_by(
            document_id=document_id
        ).order_by(
            WordToken.start
        ).all()
            if annotation.sentence_id in list_ids
        ]

    """
    @staticmethod
    def _return_all_tokens():
        tokens = WordToken.query.all()
        return tokens
    

    @staticmethod
    def _return_entities_from_document(document_id):
       return [{"rawName":token.mention,
                "type":token.label,
                "offsetStart":token.start,
                "offsetEnd":token.end}
                for token in WordToken.query.filter_by(document_id=document_id).order_by(WordToken.start).all()]
    """

    @staticmethod
    def return_all_labels_for_document(doc_id):
        """Returns all labels from a document"""
        tokens = WordToken.query.filter_by(document_id=doc_id).all()
        labels = [tok.label for tok in tokens]
        return labels

    @staticmethod
    def return_all_mentions_for_document(doc_id):
        """Returns all mentions from a document"""
        tokens = WordToken.query.filter_by(document_id=doc_id).all()
        mentions = [tok.mention for tok in tokens]
        return mentions

    @staticmethod
    def compute_stats_entities_for_project(project_id):
        """Returns classes and number of entities per classes"""
        labels_counts_unique = dict(
            Counter(
                [
                    tok.label for tok in WordToken.query.filter_by(
                        project_id=project_id
                    ).all()
                ]
            )
        )
        # create two list that contains labels and values
        labels = []
        values = []
        for key, value in labels_counts_unique.items():
            labels.append(key)
            values.append(value)
        return labels, values

    @staticmethod
    def get_simple_statistics(document_id):
        """Returns classes and number of entities per classes order by numbers of entities
        per class"""
        return dict(
            db.session.query(
                WordToken.label, func.count(WordToken.label)
            ).filter_by(
                document_id=document_id
            ).group_by(
                WordToken.label
            ).all()
        )

    @staticmethod
    def get_mentions_count(document_id):
        """Returns numbers of tokens corresponding to the same mention"""
        mentions_counter = db.session.query(
            WordToken.label,
            WordToken.mention
        ).filter_by(document_id=document_id).all()

        def convert(list_tup):
            converted_dict = {}
            for label, group_mentions in list_tup:
                converted_dict.setdefault(label, []).append(group_mentions)
            return converted_dict

        return {
            label: Counter(mentions).most_common()
            for label, mentions in convert(
                mentions_counter
            ).items()
        }

    """
    @staticmethod
    def _return_annotations_per_sentences(document_id):
        return db.session.query(
            WordToken.label,
            WordToken.mention,
            WordToken.sentence_id
        ).filter_by(document_id=document_id).group_by(WordToken.sentence_id).all()
    """

    @staticmethod
    def return_annotations_per_sentences_id(sentence_id):
        """Returns annotations for a sentence"""
        return db.session.query(
            WordToken.label,
            WordToken.mention,
            WordToken.sentence_id
        ).filter_by(sentence_id=sentence_id).all()


class StandoffView(db.Model):
    """StandoffView Model"""
    __tablename__ = "standoff_view"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plain_text = db.Column(db.Text)
    format = db.Column(db.Text)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id', ondelete='CASCADE'))


class Document(db.Model):
    """Document Model"""
    __tablename__ = "document"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(300))
    data = db.Column(db.LargeBinary, default=b'')
    data_text = db.Column(db.Text, default='')
    schema = db.Column(db.String(10))
    edited_at = db.Column(db.String(50), default='')
    is_parse = db.Column(db.Boolean, default=False)
    is_config_ner_applied = db.Column(db.Boolean, default=False)
    is_mapping_edit = db.Column(db.Boolean, default=False)
    is_ner_applied = db.Column(db.Boolean, default=False)
    is_nel_applied = db.Column(db.Boolean, default=False)
    is_edit = db.Column(db.Boolean, default=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id',
                                                     ondelete='CASCADE'))

    standoff_view = db.relationship(StandoffView,
                                    cascade='all, delete, delete-orphan',
                                    backref="document",
                                    overlaps="document,standoff_view")
    sentences = db.relationship(Sentence,
                                cascade='all, delete, delete-orphan',
                                backref="document",
                                overlaps="document,sentence")
    word_tokens = db.relationship(WordToken,
                                  cascade='all, delete, delete-orphan',
                                  backref="document",
                                  overlaps="document,word_token")

    @staticmethod
    def return_all_documents_from_project_id(project_id):
        """List of documents for a project"""
        return Document.query.filter_by(project_id=project_id).all()


class ConfigurationProject(db.Model):
    """ConfigurationProject Model"""
    __tablename__ = "configuration_project"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    language = db.Column(db.Text)
    type_model = db.Column(db.Text)
    model_ner_tagset = db.Column(db.Text, default='')
    model_ner_f_score = db.Column(db.Integer, default=0)
    rules_activated = db.Column(db.Boolean, default=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'))


class MappingNerLabel(db.Model):
    """MappingNerLabel Model"""
    __tablename__ = "mapping_ner_label"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.Text)
    pref_label = db.Column(db.Text)
    color = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'))

    """
    @staticmethod
    def _all_labels_color(project_id):
        return {map_item.label: map_item.color
                for map_item in MappingNerLabel.query.filter_by(project_id=project_id).all()}
    """

    @staticmethod
    def get_dict(project_id):
        """Returns a dict mapping
        (key : ner label model ; value : list of color and preferred label)
         for a project : {'PER' : ['#FFF', 'PERSON']}"""
        return {
            ma.label: [
                ma.color, ma.pref_label
            ]
            for ma in MappingNerLabel.query.filter_by(
                project_id=project_id
            ).all()
        }

    """
    @staticmethod
    def _return_all_pairs_mapping_for_document(project_id):
        return MappingNerLabel.query.filter_by(project_id=project_id).all()
    
    """
    @staticmethod
    def mapping_ner_as_dict(project_id):
        """Returns a dict mapping
        (key : ner label model ; value : list of color and preferred label)
        for a project :
        {'PER' : {'color':'#FFF', 'prefLabel':'PERSON'}}"""
        return {pair.label: {"color": pair.color, "prefLabel": pair.pref_label}
                for pair in MappingNerLabel.query.filter_by(project_id=project_id).all()}


class Project(db.Model):
    """Project Model"""
    __tablename__ = "project"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_name = db.Column(db.String(300))
    date_time = db.Column(db.String(300))
    description = db.Column(db.Text, default='')
    is_config_ner_valid = db.Column(db.Boolean, default=False)
    is_config_nel_valid = db.Column(db.Boolean, default=False)
    is_config_ner_mapping_valid = db.Column(db.Boolean, default=False)

    documents = db.relationship(Document,
                                backref="project",
                                cascade='all, delete, delete-orphan',
                                overlaps="project,document")
    configuration = db.relationship(ConfigurationProject,
                                    cascade='all, delete, delete-orphan',
                                    backref="project",
                                    overlaps="project,configuration_project")
    mapping_ner_label = db.relationship(MappingNerLabel,
                                        cascade='all, delete, delete-orphan',
                                        backref="project",
                                        overlaps="project,mapping_ner_label")

    @staticmethod
    def return_all_projects():
        """Returns all projects"""
        return Project.query.all()

    @staticmethod
    def is_project_exists(new_project_name):
        """Check if new project already exists in database by its name"""
        for project in Project.return_all_projects():
            if project.project_name == new_project_name:
                return True
        return False
