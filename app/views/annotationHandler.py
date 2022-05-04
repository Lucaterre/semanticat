# -*- coding: UTF-8 -*-

import datetime
import json

from flask import (
    request,
    render_template,
    jsonify)

from app.config import (app, db)
from app.models import (
    Project,
    StandoffView,
    Document,
    Sentence,
    MappingNerLabel,
    WordToken)


@app.route('/project/<int:project_id>/document/<int:doc_id>/features_ner', methods=['GET', 'POST'])
def workbase_ner(project_id, doc_id):
    """Returns annotation view"""
    s = None
    text = ''
    document = Document.query.filter_by(
        id=doc_id
    ).first()
    document.edited_at = str(datetime.datetime.now().strftime('%d/%m/%Y - %H:%M:%S'))
    db.session.commit()
    project = Project.query.filter_by(
        id=document.project_id
    ).first()
    mapping = MappingNerLabel.get_dict(project_id)
    stats_mentions_count = WordToken.get_mentions_count(doc_id)
    if document.schema == 'tei':
        text = StandoffView.query.filter_by(
            document_id=doc_id
        ).first().plain_text
    if document.schema == 'ead':
        page = request.args.get('page', 1)
        if isinstance(page, str) and page.isdigit():
            page = int(page)
        else:
            page = 1
        s = Sentence.query.filter_by(document_id=doc_id).filter(Sentence.order_id).paginate(
            page=page,
            per_page=50
        )
        sentences_to_return = [se.order_id for se in s.items]
        start = min(sentences_to_return) - 1
        end = max(sentences_to_return)
        sentences = Sentence.return_texts_tuples(doc_id=doc_id)
        text = "".join([f"<p id='{sentence[1]['text_id']}'>{sentence[0]}</p>" for sentence in sentences[start:end]])
    return render_template('main/project.document.annotation.html',
                           project_id=project_id,
                           mapping=mapping,
                           stats_mention=stats_mentions_count,
                           document_id=doc_id,
                           sentences=s,
                           project=project,
                           document=document,
                           text=text,
                           format=document.schema
                           )


@app.route('/mapping/<int:project_id>', methods=['GET', 'POST'])
def get_mapping(project_id):
    """Returns actual mapping"""
    if request.method == 'GET':
        mapping = MappingNerLabel.get_dict(project_id)
        return jsonify(mapping)
    else:
        return jsonify(status='error')


@app.route('/annotations/<int:document_id>/<int:page>', methods=['GET', 'POST'])
def get_annotations(document_id, page):
    """Returns actual annotations"""
    document = Document.query.filter_by(
        id=document_id
    ).first()
    if document.schema == 'ead':
        s = Sentence.query.filter_by(document_id=document_id).filter(Sentence.order_id).paginate(
            page=page,
            per_page=50
        )
        sentences_to_return = [se.id for se in s.items]

        annotations = WordToken.get_annotations_ead(document_id, sentences_to_return)
    else:
        annotations = WordToken.get_annotations(document_id)
    if request.method == 'GET':
        return jsonify(annotations)
    else:
        return jsonify(status=False)


def get_correct_data(data, from_w3c):
    if from_w3c:
        mention = data['destroyOne']['target']['selector'][0]['exact']
        label = data['destroyOne']['body'][0]['value']
        start = data['destroyOne']['target']['selector'][1]['start']
        end = data['destroyOne']['target']['selector'][1]['end']
        document_id = data['destroyOne']['documentID']
        project_id = data['destroyOne']['projectID']
    else:
        mention = data['mention']
        label = data['label']
        start = data['start']
        end = data['end']
        document_id = data['documentID']
        project_id = data['projectID']
    return mention, label, start, end, document_id, project_id


def get_correct_token(data, token_id, from_w3c):
    mention, label, start, end, document_id, project_id = get_correct_data(data, from_w3c=from_w3c)
    if str(token_id).startswith('#'):
        # New annotation provides from Recogito with UUID
        token = WordToken.query.filter_by(mention=mention,
                                          label=label,
                                          start=start,
                                          end=end,
                                          document_id=document_id,
                                          project_id=project_id).first()
    else:
        # Old annotation comes with autoincrement primary key ID
        token = WordToken.query.filter_by(id=int(token_id)).first()
    return token


@app.route('/return_annotations_to_delete', methods=['GET', 'POST'])
def annotations_to_delete():
    """Returns annotations to delete"""
    if request.method == 'POST':
        response = json.loads(request.data)
        mention_to_delete = response['mention']
        label_to_delete = response['label']
        annotations = WordToken.get_annotations_to_delete(response['document_id'],
                                                          mention=mention_to_delete,
                                                          label=label_to_delete)
        return jsonify(annotations)


@app.route('/get_statitics/<int:document_id>', methods=['GET', 'POST'])
def labels_count(document_id):
    """Count number of entities per labels"""
    if request.method == 'GET':
        return WordToken.get_simple_statistics(document_id=document_id)


@app.route('/new_annotation', methods=['GET', 'POST'])
def add_annotation():
    """Add and save new annotation"""
    if request.method == 'POST':
        response = json.loads(request.data)
        token = WordToken(mention=response['mention'],
                          label=response['label'],
                          start=response['start'],
                          end=response['end'],
                          sentence_id=response['sentenceID'],
                          document_id=response['documentID'],
                          project_id=response['projectID'])
        db.session.add(token)
        db.session.commit()
    return jsonify(status=True)


@app.route('/load_annotations_from_json/<int:project_id>/<int:document_id>', methods=['GET', 'POST'])
def add_annotations_from_json(project_id, document_id):
    """Add multiples annotations from JSON"""
    if request.method == 'POST':
        response = json.loads(request.data)
        annotations = [WordToken(mention=annotation['target']['selector'][0]['exact'],
                                 start=annotation['target']['selector'][1]['start'],
                                 end=annotation['target']['selector'][1]['end'],
                                 label=annotation['body'][0]['value'],
                                 sentence_id=annotation['sentence_id'],
                                 document_id=document_id,
                                 project_id=project_id) for annotation in response]
        db.session.add_all(annotations)
        db.session.commit()
    return jsonify(status=True)


@app.route("/delete_annotation", methods=['GET', 'POST'])
def remove_annotation():
    """Remove an annotation"""
    if request.method == 'POST':
        response = json.loads(request.data)
        token_id = response['id']
        token = get_correct_token(response, token_id, from_w3c=False)
        db.session.delete(token)
        db.session.commit()
    return jsonify(status=True)


@app.route('/update_annotation', methods=['GET', 'POST'])
def modify_annotation():
    """Update an annotation"""
    if request.method == 'POST':
        response = json.loads(request.data)
        token_id = response['id']
        token = get_correct_token(response, token_id, from_w3c=False)
        token.label = response['updatedLabel']
        db.session.commit()
    return jsonify(status=True)


@app.route('/destroy_annotations', methods=['GET', 'POST'])
def remove_all_annotations():
    """Remove multiple annotations in batch"""
    if request.method == 'POST':
        data = json.loads(request.data)
        if data['destroyAll'] and bool(data['destroyAll']) is not False:
            try:
                db.session.query(WordToken).filter_by(document_id=data['id']).delete()
                db.session.commit()
            except Exception:
                db.session.rollback()
        elif data['destroyOne']:
            token_id = str(data['destroyOne']['id'])
            token = get_correct_token(data, token_id, from_w3c=True)
            db.session.delete(token)
            db.session.commit()

    return jsonify(status=True)
