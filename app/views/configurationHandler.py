# -*- coding: UTF-8 -*-

import json
import random
from unicodedata import normalize
from io import StringIO
import csv
import pandas

from flask import (
    request,
    render_template,
    make_response,
    jsonify,
    url_for,
    redirect)

from app.config import (app, db)
from app.models import (
    Project,
    ConfigurationProject,
    Document,
    MappingNerLabel,
    WordToken)
from app.lib.Ner.NerSpacy import (
    NerSpacyEngine,
    get_models,
    get_spacy_languages)


def get_random_hex() -> str:
    """hexadecimal code generator.
    Returns:
        str : hexadecimal code
    """
    random_number = random.randint(0, 16777215)
    # convert to hexadecimal
    hex_number = str(hex(random_number))
    # remove 0x and prepend '#'
    return '#' + hex_number[2:]


@app.route('/project/<int:project_id>/configuration', methods=['GET', 'POST'])
def configuration(project_id):
    """Returns the configuration view"""
    project = Project.query.filter_by(id=project_id).first()
    mapping = MappingNerLabel.query.filter_by(project_id=project_id).all()
    return render_template('main/project.configuration.html',
                           project=project,
                           mappings=mapping)


@app.route('/models', methods=['GET', 'POST'])
def list_models():
    """Returns a list of all models available (pretrained and custom)"""
    if request.method == 'GET':
        return jsonify({'available_models': [str(model) for model in get_models()]})


@app.route('/spaCy_languages', methods=['GET', 'POST'])
def list_languages():
    """Returns all available languages pipelines from SpaCy API"""
    if request.method == 'GET':
        return jsonify({'available_langs': get_spacy_languages()})


@app.route('/actual_mapping/<int:project_id>', methods=['GET', 'POST'])
def list_tagset(project_id):
    """Returns list of actual tag set"""
    if request.method == 'GET':
        mapping = MappingNerLabel.query.filter_by(project_id=project_id).all()
        return jsonify({'available_tags': [tag.label for tag in mapping]})


@app.route('/actual_configuration_recommender/<int:project_id>')
def actual_configuration_ner_recommender_project(project_id):
    """Returns actual configuration"""
    actual_configuration = ConfigurationProject.query.filter_by(project_id=project_id).first()
    return jsonify({
            'model_type': actual_configuration.type_model,
            'language': actual_configuration.language,
            'model_tag_set': actual_configuration.model_ner_tagset,
            'ner_performance': actual_configuration.model_ner_f_score
        })


@app.route('/new_ner_recommender_configuration/<int:project_id>', methods=['GET', 'POST'])
def save_ner_recommender_configuration(project_id):
    """Save or update ner recommender for project"""
    if request.method == 'POST':
        response = json.loads(request.data)
        project = Project.query.filter_by(id=project_id).first()
        actual_configuration = ConfigurationProject.query.filter_by(project_id=project_id).first()
        if actual_configuration is not None:
            # create a new ner engine
            ner_engine = NerSpacyEngine(
                language=response['language'],
                type_model=response['model_type']
            )
            # rewrite actual config
            actual_configuration.language = response['language']
            actual_configuration.type_model = response['model_type']
            actual_configuration.model_ner_f_score = int(float(ner_engine.meta['performance']['ents_f'])*100)
            actual_configuration.model_ner_tagset = ','.join(ner_engine.meta['labels']['ner'])
            db.session.commit()
            # remove actual mapping
            db.session.query(MappingNerLabel).filter(MappingNerLabel.project_id == project_id).delete()
            db.session.commit()
            # write a new mapping
            for label in ner_engine.meta['labels']['ner']:
                color = get_random_hex()
                pre_mapping = MappingNerLabel(label=label,
                                              pref_label=label,
                                              color=color,
                                              project_id=project_id)
                db.session.add(pre_mapping)
            db.session.commit()
            # delete all entities from documents
            db.session.query(WordToken).filter(WordToken.project_id == project_id).delete()
            db.session.commit()
            # remove property ner apply on document
            documents = Document.query.filter_by(project_id=project_id).all()
            for document in documents:
                document.is_ner_applied = False
                db.session.commit()
        else:
            # remove actual mapping
            db.session.query(MappingNerLabel).filter(MappingNerLabel.project_id == project_id).delete()
            db.session.commit()
            # delete all entities from documents
            db.session.query(WordToken).filter(WordToken.project_id == project_id).delete()
            db.session.commit()
            # write a new config
            # create a new ner engine
            ner_engine = NerSpacyEngine(
                language=response['language'],
                type_model=response['model_type']
            )
            # save in DB
            new_recommender_ner = ConfigurationProject(
                language=response['language'],
                type_model=response['model_type'],
                model_ner_f_score=int(float(ner_engine.meta['performance']['ents_f'])*100),
                model_ner_tagset=','.join(ner_engine.meta['labels']['ner']),
                project_id=project_id
            )
            db.session.add(new_recommender_ner)
            project.is_config_ner_valid = True
            db.session.commit()
            # write a new mapping from model
            for label in ner_engine.meta['labels']['ner']:
                color = get_random_hex()
                pre_mapping = MappingNerLabel(label=label, pref_label=label, color=color, project_id=project_id)
                # TODO : create a list of object to add in one time
                db.session.add(pre_mapping)
            db.session.commit()
            # create a cache (load) for model
        return jsonify({
            'ner_configuration': 'success'
        })

##########################################


@app.route('/save_index/<int:project_id>', methods=['GET', 'POST'])
def save_vocabulary(project_id):
    """save control vocabulary in database"""
    """
    TODO : 
        1. check if is CSV
        2. create JS requests
        3. not possible if a NER recommender is not activate 
        4. remove index 
        5. one index only ! 
    
    """
    if request.method == "POST":
        name_index = request.form['index-name']

        file = request.files.getlist('inputFile[]')[0]

        # create a ner engine with actual configuration
        ner_config = ConfigurationProject.query.filter_by(project_id=project_id).first()

        ner_engine = NerSpacyEngine(
            language=ner_config.language,
            type_model=ner_config.type_model,
            length_threshold=3)

        # add all in method ner_engine :
        # create a ruler
        ruler = ner_engine.nlp.add_pipe("entity_ruler")

        # transform into patterns
        data = pandas.read_csv(file)
        terms = data.term.to_list()
        labels = data.label.to_list()
        ids = data.id.to_list()
        patterns = [{"label": label, "pattern": term, "id": id} for term, label, id in zip(terms, labels, ids)]

        # add and convert patterns to bytes
        ruler.add_patterns(patterns)
        ruler_bytes = ruler.to_bytes()

        # save patterns bytes to DB and create a flag in config for is_index : True|False
        print(ruler_bytes)

        # remove ruler from nlp pipe
        # ner_engine.nlp.select_pipes(disable="entity_ruler")

    return redirect(url_for('configuration', project_id=project_id))




########################################

@app.route('/remove_pair_ner_label/<int:project_id>', methods=['GET', 'POST'])
def remove_pair(project_id):
    """Remove mapping pair"""
    pair_id = request.form.get('mapping_id')
    pair = MappingNerLabel.query.filter_by(id=pair_id).first()
    pair_label = pair.label
    # remove all entities with this label
    db.session.query(WordToken).filter(
        (WordToken.project_id == project_id) & (WordToken.label == pair_label)
    ).delete()
    db.session.commit()
    # remove pair mapping
    db.session.delete(pair)
    db.session.commit()

    return make_response(jsonify({
        'status': 'success',
        'label': f'{str(pair_label)}',
        'type': 'warning',
        'message': f'Mapping group {pair_id} label removed.'}), 200)


@app.route('/save_pair_ner_label', methods=['GET', 'POST'])
def save_pair():
    """Update and save mapping pair"""
    pair_id = request.form.get('mapping_id')
    ner_label = request.form.get('nerLabel')
    pref_ner_label = request.form.get('prefNerLabel')
    color = request.form.get('color')

    pair = MappingNerLabel.query.filter_by(id=pair_id).first()

    pair.label = ner_label
    pair.pref_label = pref_ner_label
    pair.color = color

    db.session.commit()
    return make_response(jsonify({
        'status': 'success',
        'type': 'success',
        'message': f'Mapping group : {ner_label} | {pref_ner_label} | {color} in table is updated.'}), 200)


@app.route('/new_pair_ner_label', methods=['GET', 'POST'])
def new_pair():
    """Create a new mapping pair"""
    project_id = request.form.get('project_id')
    ner_label = request.form.get('nerLabel')
    pref_ner_label = request.form.get('prefNerLabel')
    color = request.form.get('color')
    try:
        actual_mapping = MappingNerLabel.query.filter_by(project_id=project_id).all()
        labels_list = [map_item.label for map_item in actual_mapping]
        if ner_label in labels_list:
            return make_response(jsonify({'status': 'error',
                                          'message': 'duplicate'}), 400)
        else:
            new_entry_mapping = MappingNerLabel(label=ner_label,
                                                pref_label=pref_ner_label,
                                                color=color,
                                                project_id=project_id)
            db.session.add(new_entry_mapping)
            db.session.commit()
            return make_response(jsonify({'status': 'success'}), 200)
    except AttributeError:
        new_entry_mapping = MappingNerLabel(label=ner_label,
                                            pref_label=pref_ner_label,
                                            color=color,
                                            project_id=project_id)
        db.session.add(new_entry_mapping)
        db.session.commit()
        return make_response(jsonify({'status': 'success'}), 200)
