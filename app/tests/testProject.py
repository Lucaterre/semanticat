# -*- coding: UTF-8 -*-

from . import client

from app.models import Project

PROJECT_CASES = {
    'normal': {
        "project_name": "TESTPROJECT",
        "description": "project-description"
    },
    'empty_title': {
        "project_name": "",
        "description": "project-description"
    },
    'empty_str': {
        "project_name": "TEST PROJECT",
        "description": "project-description"
    }
}


def test_get_project_view(client):
    response = client.get('/')
    assert response.status_code == 200


def test_create_project(client):
    response = client.post('/', data=PROJECT_CASES['normal'])
    assert response.status_code == 200
    # get from database to check zero projects created
    response = client.post('/', data=PROJECT_CASES['empty_title'])
    assert response.status_code == 200
    response = client.post('/', data=PROJECT_CASES['empty_str'])
    assert response.status_code == 200
    # test a copy of same project
    response = client.post('/', data=PROJECT_CASES['normal'])
    assert response.status_code == 200


def test_remove_project(client):
    # create a new project
    client.post('/', data=PROJECT_CASES['normal'])
    project = Project.query.first()
    # add some data
    # Remove project and test response + test remove all data
    response = client.get('/delete_project/'+str(project.id))
    assert response.status_code == 200
    response = client.get('/delete_project/'+str(1))
    assert response.status_code == 404


def test_remove_with_multiples_project(client):
    pass
