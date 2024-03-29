# -*- coding: UTF-8 -*-

"""
project_handler.py

This view manages the routes
to control documents in the instance (import, deletion).

last updated : 12/05/2022
"""

import datetime

from flask import (request,
                   redirect,
                   render_template,
                   flash,
                   abort,
                   url_for)

from app.config import (app,
                        db)
from app.models import Project


@app.route('/', methods=['GET', 'POST'])
def index():
    """Initialize a new project"""
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        project_description = request.form.get('project-description')
        if not Project.is_project_exists(project_name):
            if project_name == '':
                flash('The project name cannot be empty ! Please try again.',
                      category='warning')
            if ' ' in project_name:
                flash('The project name cannot contains empty string '
                      '! Please check typo and try again.',
                      category='warning')
            else:
                new_project = Project(
                    project_name=project_name,
                    description=project_description,
                    date_time=datetime.datetime.now().strftime('%d/%m/%Y - %H:%M:%S')
                )
                db.session.add(new_project)
                db.session.commit()
                flash(f'New project {project_name} created now.',
                      category='success')
        else:
            flash('Project always exist ! Please change the name.',
                  category='warning')
    return render_template('main/project.edition.html',
                           projects=Project.return_all_projects(),
                           mode=app.config['FLASK_ENV']), 200


@app.route('/delete_project/<int:project_id>', methods=['GET', 'POST'])
def remove_project(project_id):
    """Delete a project and dependencies that
    inherit from it (documents, entities, configuration etc.)"""
    project = Project.query.filter_by(id=project_id).first()
    if project is not None:
        db.session.delete(project)
        db.session.commit()
        flash(f'Project : {project.project_name} completely removed.',
              category='warning')
        return redirect(url_for('index'))
    return abort(404, description="Project not found")
