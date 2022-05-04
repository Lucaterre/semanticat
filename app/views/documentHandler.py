# -*- coding: UTF-8 -*-

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


def allowed_file(filename: str) -> bool:
    """A simple file extension checker.

    Notes :
         `ALLOWED_FILE` : check general config
    of Flask app that contains file extensions accepted.

    Args:
        filename (str): name of file uploaded

    Returns:
        bool : True if file extension is ok, otherwise False
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/project/<int:project_id>/manage_documents')
def manage_documents(project_id):
    """Returns view for manage documents in project"""
    return render_template('main/project.manage-documents.html',
                           project_id=project_id,
                           documents=Document.return_all_documents_from_project_id(project_id=project_id))


@app.route('/project/<int:project_id>/manage_documents/import_documents', methods=['GET', 'POST'])
def import_documents(project_id):
    """Check document validity before store it in database"""
    if request.method == 'POST':
        files = request.files.getlist('inputFile[]')
        flash_display = False
        for file in files:
            filename = file.filename
            # -- Import tests -- :
            # 1 - Is a ghost import ?
            if filename == "":
                flash(f'No selected file(s). Please, try again.',
                      category='warning')

            # 2- File with a correct extension ?
            elif allowed_file(filename) is not True:
                flash(f'You can import only file(s) with XML extension. Please, try again.',
                      category='warning')

            # 3- Sanity XML conformity and schema check (TEI or EAD)
            else:
                content = file.read()
                xml = XML(content)

                if xml.schema == "conformity_error":
                    flash(f'Cannot import {filename}, check XML conformity and try again.',
                          category='warning')
                elif xml.schema == "unknown_error":
                    flash(f'Cannot import {filename}, something bad.',
                          category='warning')
                else:
                    # 4 - File already loaded ?
                    if Document.query.filter_by(filename=filename, project_id=project_id).first() is not None:
                        newFile = Document(
                            filename=path.splitext(filename)[0] + f'_copy_{str(uuid.uuid4()).split("-")[0]}.xml',
                            data=content,
                            schema=xml.schema,
                            project_id=project_id)
                        db.session.add(newFile)
                        db.session.commit()
                        flash(f'{filename} already imported. create a copy.', category='warning')

                    # 5- All is fine and populate DB with new documents ...
                    else:
                        newFile = Document(filename=filename,
                                           data=content,
                                           schema=xml.schema,
                                           project_id=project_id)
                        db.session.add(newFile)
                        db.session.commit()

                    if len(files) > 1 and flash_display is False:
                        flash(f'All documents imported with success.', category='info')
                        flash_display = True
                    elif len(files) == 1:
                        flash(f'{filename} is imported with success.', category='info')
                    else:
                        continue

        return redirect(url_for("manage_documents", project_id=project_id))


@app.route('/project/<int:project_id>/manage_documents/remove_document', methods=['GET', 'POST'])
def remove_document(project_id):
    """Remove one document from the database"""
    if request.method == 'POST':
        document_id = request.form['remove_document']
        document = Document.query.filter_by(id=int(document_id)).first()
        db.session.delete(document)
        db.session.commit()
        flash(f'{document.filename} completely removed.', category='warning')

    return redirect(url_for("manage_documents", project_id=project_id))


@app.route('/project/<int:project_id>/manage_documents/remove_documents', methods=['GET', 'POST'])
def remove_documents(project_id):
    """Remove multiple documents"""
    if request.method == 'POST':
        project = Project.query.filter_by(id=project_id).first()
        if bool(request.form['remove_all_documents']):
            documents = Document.query.filter_by(project_id=project_id).all()
            for document in documents:
                db.session.delete(document)
                db.session.commit()
            flash(f'All documents from project "{project.project_name}" are deleted.', category='warning')

    return redirect(url_for('manage_documents', project_id=project_id))
