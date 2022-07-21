# -*- coding: UTF-8 -*-

"""
workflow_handler.py

This view manages the routes
to control user workflow steps, including
the following actions:
- documents presentation;
- statistics on the entities in the project;
- file parsing;
- NER inference;
- Access to annotation view;
- Export enhanced documents.

last updated : 12/05/2022
"""

import json
import requests

from flask import (
    request,
    Response,
    make_response,
    jsonify,
    flash,
    render_template,
    redirect,
    url_for)

import pandas

from app.config import (app, db)
from app.models import (
    Project,
    StandoffView,
    ConfigurationProject,
    MappingNerLabel,
    Document,
    Sentence,
    WordToken)

from app.lib.IO_utils.parsers.XMLParser import XMLStrategiesParser
from app.lib.IO_utils.exporters.XMLExporter import XMLExporterStrategies
from app.lib.Ner.NerSpacy import NerSpacyEngine


@app.route('/project/<int:project_id>', methods=['GET', 'POST'])
def project(project_id):
    """Returns project workflow view"""
    return render_template('main/project.workflow.html',
                           project=Project.query.filter_by(
                               id=project_id
                           ).first(),
                           documents=Document.return_all_documents_from_project_id(
                               project_id=project_id
                           )
                           )


@app.route('/get_ner_statistics_project/<int:project_id>', methods=['GET', 'POST'])
def statistics_ner_project(project_id):
    """Returns proportion of entities per class in the whole project"""
    if request.method == 'GET':
        labels, values = WordToken.compute_stats_entities_for_project(project_id=project_id)
        return jsonify({
            'labels': labels,
            'values': values
        })
    return jsonify({})


@app.route('/save_description/<int:project_id>', methods=['GET', 'POST'])
def new_project_description(project_id):
    """Store markdown project description from workflow view"""
    if request.method == "POST":
        Project.query.filter_by(
            id=project_id
        ).first().description = json.loads(
            request.data
        )['new_description']
        db.session.commit()
        return jsonify(status=True)
    return jsonify(status=True)


@app.route('/progress_parse/PROJECT=<int:project_id>/DOCUMENT=<int:doc_id>',
           methods=['GET', 'POST'])
def parse_document(project_id, doc_id):
    """Parse document and store content in database"""
    document = Document.query.filter_by(id=doc_id).first()
    try:
        result = XMLStrategiesParser(document.data)
        if result.schema == "tei":
            new_standoff_representation = StandoffView(
                plain_text=result.plain_text,
                format="tei",
                document_id=doc_id
            )
            db.session.add(new_standoff_representation)
            db.session.commit()
        if result.schema == "ead":
            sentences = []
            order = 0
            for sentence in result.sentences:
                order += 1
                sentences.append(Sentence(content=sentence, order_id=order, document_id=doc_id))
            db.session.add_all(sentences)
            db.session.commit()
            new_standoff_representation = StandoffView(
                plain_text=result.plain_text,
                format="ead",
                document_id=doc_id
            )
            db.session.add(new_standoff_representation)
            db.session.commit()

        document.is_parse = 1
        db.session.commit()

        flash(f"{document.filename} parse with success", "info")
        return make_response(jsonify({"status": "success"}), 200)
    except ValueError:
        return make_response(jsonify({"status": "error"}), 400)


@app.route('/progress_ner/PROJECT=<int:project_id>/DOCUMENT=<int:doc_id>/<int:rewrite>',
           methods=['GET', 'POST'])
def ner(project_id, doc_id, rewrite=False):
    """Apply named-entity recognition pipeline on document"""
    document = Document.query.filter_by(
        id=doc_id
    ).first()

    if bool(rewrite):
        db.session.query(WordToken).filter_by(document_id=doc_id).delete()
        db.session.commit()

    standoff_view = StandoffView.query.filter_by(
        document_id=doc_id
        ).first()

    # retrieve Ner config for spacy engine
    try:
        ner_config = ConfigurationProject.query.filter_by(
            project_id=document.project_id
        ).first()
        filter_labels = [mapper.label
                         for mapper in MappingNerLabel.query.filter_by(
                          project_id=project_id
                            ).all()]
        ner_engine = NerSpacyEngine(
           language=ner_config.language,
           type_model=ner_config.type_model,
           mapping_filter=filter_labels,
           length_threshold=3)
        # clear all the actual tokens for a document
        db.session.query(WordToken).filter(WordToken.document_id == doc_id).delete()
        db.session.commit()

        sentences = None

        if document.schema == 'text':
            plain = document.data_text
        else:
            plain = standoff_view.plain_text

        if document.schema == 'ead':
            sentences = Sentence.return_texts_tuples(doc_id)

        document.is_ner_applied = True
        db.session.commit()
        flash(f'{document.filename} ner with success', 'info')

        return Response(ner_engine.get_ner(
            project_id=project_id,
            document_id=doc_id,
            schema=document.schema,
            sentences=sentences,
            document=plain
        ), mimetype='text/event-stream')

    except AttributeError:
        return jsonify(status=400)


@app.route('/progress_nel/PROJECT=<int:project_id>/DOCUMENT=<int:doc_id>', methods=['GET', 'POST'])
def nel(project_id, doc_id):
    annotations = WordToken.query.filter_by(document_id=doc_id).order_by(WordToken.start).all()
    text = StandoffView.query.filter_by(document_id=doc_id).first().plain_text
    from app.lib.linking_components.EntityFishingLinking import LinkingEntityFishing
    LinkingEntityFishing(language="fr", text=text, entities=annotations, document_id=doc_id).apply_nel()
    Document.query.filter_by(id=doc_id).first().is_nel_applied = True
    db.session.commit()
    return redirect(url_for('project', project_id=project_id))

@app.route('/correct_nel/<int:project_id>/<int:doc_id>', methods=['GET', 'POST'])
def nel_work_view(project_id, doc_id):
    entities = WordToken.query.filter_by(document_id=doc_id).order_by(WordToken.start).all()
    entities = [{"entity_id": entity.id, "rawName": entity.mention,"type":entity.label,"wikidataId":entity.wikidata_qid} for entity in entities]
    labels = [label.label for label in MappingNerLabel.query.filter_by(project_id=project_id).all()]
    return render_template("main/test_linking_table.html", entities=entities, labels=labels, project_id=project_id, doc_id=doc_id)


@app.route('/data_nel/<int:project_id>/<int:doc_id>', methods=['GET', 'POST'])
def get_nel_data(project_id, doc_id):
    if request.method == "GET":
        entities = WordToken.query.filter_by(project_id=project_id, document_id=doc_id).order_by(WordToken.start).all()
        entities = [{"ID": entity.id, "Mention": entity.mention, "Label": entity.label, "Wikidata ID": entity.wikidata_qid} for entity in entities]
        return make_response(jsonify(entities), 200)

@app.route('/reconcile/<int:project_id>/<int:doc_id>', methods=['GET', 'POST'])
def reconcile_wiki(project_id, doc_id):
    if request.method == "POST":
        import requests
        new_data = json.loads(
            request.data
        )
        property_name = new_data['propertyName']
        property_wiki = new_data['propertyWikidata']
        labels = new_data['labels']
        # retrieve from DB entities ID, wikidata_QID filter project_id and doc_id and filter by labels
        entities = [token for token in WordToken.query.filter_by(project_id=project_id, document_id=doc_id).order_by(WordToken.start).all()]
        # request EF API for each entities to resolve
        entities_resolved = []
        for entity in entities:
            if entity.wikidata_qid != "NIL" and entity.label in labels:
                entity_resolved = {}
                req = requests.request(method="GET",
                                   url="http://nerd.huma-num.fr/nerd/service/kb/concept/"+entity.wikidata_qid,
                                   headers={
                                       "Accept":"application/json"
                                   },
                                 params={"lang":"en"})
                res = req.json()
                new_statements = {k: content[k] for k in ['propertyName',
                                                          'propertyId',
                                                           'value']
                                  for content in res['statements'] if content['propertyId'] == property_wiki}

                if len(new_statements) != 0:
                    entities_resolved.append({"ID": entity.id, "Mention": entity.mention, "Label": entity.label,
                                              "Wikidata ID": entity.wikidata_qid, property_name: new_statements['value']})
                else:
                    entities_resolved.append({"ID": entity.id, "Mention": entity.mention, "Label": entity.label,
                                              "Wikidata ID": entity.wikidata_qid, property_name: ""})
            else:
                entities_resolved.append({"ID": entity.id, "Mention": entity.mention, "Label": entity.label, "Wikidata ID": entity.wikidata_qid, property_name: ""})


        return make_response(jsonify(entities_resolved), 200)
    return redirect(url_for("nel_work_view", project_id=project_id, doc_id=doc_id))


@app.route('/export/PROJECT=<int:project_id>/DOCUMENT=<int:doc_id>', methods=['GET', 'POST'])
def export_enhanced(project_id, doc_id):
    """Export enhanced content into new XML with annotations (inline or not)"""
    output_xml = ""
    # publish = True
    # get document infos
    document = Document.query.filter_by(
        id=doc_id
    ).first()
    annotations = WordToken.query.filter_by(document_id=doc_id).all()
    if request.method == 'POST':
        if len(annotations) > 0:
            # get type export
            type_export = request.form['export_format']
            if type_export == 'w3c_annotations':
                annotations_w3c = WordToken.get_annotations(doc_id)
                return Response(
                    json.dumps(annotations_w3c, ensure_ascii=False),
                    mimetype='application/json',
                    headers={
                             'Content-Disposition': f'attachment; '
                             f'filename={document.filename}_annotations.w3c.json'
                            })
            if type_export == 'csv':
                annotations = WordToken.get_annotations_mention_label(doc_id)
                csv = pandas.DataFrame(annotations).to_csv(index=False, header=False)
                return Response(csv, mimetype='text/csv', headers={
                    'Content-Disposition': f'attachment; '
                                           f'filename={document.filename}_annotations.csv'
                })

            type_xslt = False
            if type_export == 'inline_xslt':
                type_xslt = True

            # pass exporter class
            document_to_export = XMLExporterStrategies(source=document.data,
                                                       document_id=doc_id,
                                                       project_id=project_id,
                                                       type_xslt=type_xslt)
            if type_export == 'ead_controlaccess':
                output_xml = document_to_export.ead_results_to_controlaccess_level()
            elif type_export == 'tei_inline_offsets':
                output_xml = document_to_export.tei_results_to_inline_standoff()
            elif type_export == 'inline_xslt':
                output_xml = document_to_export.results_to_inline_xslt()

            """ experimental TEI Publisher publication
            if publish:
            import requests
            tei_publisher_instance = "http://127.0.1.1:8080/exist/apps/tei-publisher/api/upload/playground"
            headers = {
                'Content-Type': 'multipart/form-data',
            }
            files = {
                f'{document.filename}.xml': str(output_xml)
            }
            response = requests.post(tei_publisher_instance, headers=headers, files=files, auth=('*****', '*****'))
            if  response.status_code == 200:
                print("send OK")
            else:
                print("fail")
            """

            return Response(str(output_xml),
                            mimetype='application/xml',
                            headers={
                            'Content-Disposition': f'attachment; '
                                                   f'filename={document.filename}_enhanced.xml'
                            })

        flash("It seems there are no annotations in your document.", category='warning')
    return redirect(url_for('project', project_id=project_id))
