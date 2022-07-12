# -*- coding: UTF-8 -*-

"""
document_handler.py

This view manages the routes
to control documents in the instance (import, deletion).

last updated : 12/05/2022
"""

from os import path
import uuid

from flask import (request,
                   render_template,
                   flash,
                   redirect,
                   url_for)

from app.config import (app,
                        db,
                        ALLOWED_EXTENSIONS)
from app.models import (Project,
                        Document)
from app.lib.IO_utils.parsers.XMLParser import XML


@app.route('/project/<int:project_id>/manage_documents')
def manage_documents(project_id):
    """Returns view for manage documents in project"""
    return render_template('main/project.manage-documents.html',
                           project_id=project_id,
                           documents=Document.return_all_documents_from_project_id(
                               project_id=project_id
                           )
                           )


def sanity_check_xml_logs(filename, schema):
    """XML sanity check logs (conformity, schemas or unknown errors)"""
    if schema == "conformity_error":
        flash(f'Cannot import {filename}, check XML conformity and try again.',
              category='warning')
        return False
    if schema == "error_schema":
        flash(f'Cannot import {filename}, check XML schema (TEI or EAD are allowed) and try again.',
              category='warning')
        return False
    if schema == "error":
        flash(f'Cannot import {filename}, something bad.',
              category='warning')
        return False

    return True


@app.route('/project/<int:project_id>/manage_documents/import_documents', methods=['GET', 'POST'])
def import_documents(project_id):
    """Check document validity before store it in database"""
    if request.method == 'POST':
        files = request.files.getlist('inputFile[]')
        flash_display = False
        for file in files:
            filename = file.filename
            extension_file = filename.rsplit('.', 1)[1].lower()
            # -- Import tests -- :
            # 1 - Is a ghost import ?
            if filename == "":
                flash('No selected file(s). Please, try again.',
                      category='warning')

            # 2- File with a correct extension ?
            elif not ('.' in filename and extension_file in ALLOWED_EXTENSIONS):
                flash('You can import only file(s) with xml or txt extension. Please, try again.',
                      category='warning')

            # 3- Process file
            else:
                xml = None
                if extension_file == "txt":
                    # 4- Retrieve text content
                    content = str(file.read().decode('utf-8'))
                    to_db = True
                else:
                    # 4a - Retrieve XML content
                    content = file.read()
                    xml = XML(content)
                    # 4b- XML Sanity check
                    to_db = sanity_check_xml_logs(schema=xml.schema, filename=filename)

                if to_db:
                    # 5 - File already loaded ?
                    if Document.query.filter_by(filename=filename,
                                                project_id=project_id).first() is not None:
                        filename = path.splitext(
                            filename
                        )[0] + f'_copy_{str(uuid.uuid4()).split("-", maxsplit=1)[0]}' \
                               f'.{extension_file}'
                        flash(f'{filename} already imported. create a copy.', category='warning')

                    # 6 - All is fine and populate DB with new documents ...
                    new_document = Document(filename=filename,
                                            data=content
                                            if extension_file == "xml"
                                            else b"",
                                            data_text=content
                                            if extension_file == "txt"
                                            else "",
                                            schema=xml.schema
                                            if extension_file == "xml"
                                            else "text",
                                            is_parse=not(extension_file == "xml"),
                                            project_id=project_id)
                    db.session.add(new_document)
                    db.session.commit()

                    # 7 - Import success flash messages for one or multiple files
                    if len(files) > 1 and flash_display is False:
                        flash('All documents imported with success.', category='info')
                        flash_display = True
                    elif len(files) == 1:
                        flash(f'{filename} is imported with success.', category='info')
                    else:
                        continue

    return redirect(url_for('manage_documents',
                            project_id=project_id
                            )
                    )


@app.route('/project/<int:project_id>/manage_documents/remove_document', methods=['GET', 'POST'])
def remove_document(project_id):
    """Remove one document from the database"""
    if request.method == 'POST':
        document_id = request.form['remove_document']
        document = Document.query.filter_by(id=int(document_id)).first()
        # TODO : Remove associate table pos
        db.session.delete(document)
        db.session.commit()
        flash(f'{document.filename} completely removed.', category='warning')

    return redirect(url_for("manage_documents",
                            project_id=project_id
                            )
                    )


@app.route('/project/<int:project_id>/manage_documents/remove_documents', methods=['GET', 'POST'])
def remove_documents(project_id):
    """Remove multiple documents"""
    if request.method == 'POST':
        project = Project.query.filter_by(id=project_id).first()
        if bool(request.form['remove_all_documents']):
            documents = Document.query.filter_by(project_id=project_id).all()
            for document in documents:
                # TODO : Remove associate table pos
                db.session.delete(document)
                db.session.commit()
            flash(
                f'All documents from project "{project.project_name}" are deleted.',
                category='warning'
            )

    return redirect(url_for('manage_documents', project_id=project_id))
