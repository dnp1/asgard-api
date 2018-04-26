
import json
import requests
from http import HTTPStatus
from uuid import uuid4

from flask import Blueprint, Response, redirect, request, url_for
from hollowman.decorators import auth_required
from hollowman.conf import MESOS_ADDRESSES
from hollowman import cache

tasks_blueprint = Blueprint(__name__, __name__)


def get_task_data(task_id):

    task_id_with_namespace = task_id
    task_info = requests.get(f"{MESOS_ADDRESSES[0]}/tasks?task_id={task_id_with_namespace}").json()['tasks']

    if not task_info:
        return None, None
    task_info = task_info[0]

    framework_id = task_info['framework_id']
    slave_id = task_info['slave_id']

    slave_info = requests.get(f"{MESOS_ADDRESSES[0]}/slaves?slave_id={slave_id}").json()['slaves'][0]
    slave_ip = slave_info['hostname']

    slave_state = requests.get(f"http://{slave_ip}:5051/state").json()
    framework_info = [fwk for fwk in slave_state['frameworks'] if fwk['id'] == framework_id][0]
    execuor_info = [executor for executor in framework_info['executors'] if executor['id'] == task_id_with_namespace]
    if not execuor_info:
        execuor_info = [executor for executor in framework_info['completed_executors'] if executor['id'] == task_id_with_namespace]

    if execuor_info:
        execuor_info = execuor_info[0]
    sandbox_directory = execuor_info['directory']
    return (slave_ip, sandbox_directory)


@tasks_blueprint.route("/<string:task_id>/files")
@auth_required(pass_user=True)
def task_files_list(task_id, user):
    namespace = user.current_account.namespace
    slave_ip, sandbox_directory = get_task_data(f"{namespace}_{task_id}")
    if not slave_ip:
        return Response(response=json.dumps({}), status=404)
    files_info = requests.get(f"http://{slave_ip}:5051/files/browse?path={sandbox_directory}").json()
    for file_data in files_info:
        file_data['path'] = file_data['path'].replace(sandbox_directory, "", 1)

    return Response(response=json.dumps(files_info), status=200, mimetype="application/json")

@tasks_blueprint.route("/<string:task_id>/files/read")
@auth_required(pass_user=True)
def task_files_read(task_id, user):
    namespace = user.current_account.namespace
    slave_ip, sandbox_directory = get_task_data(f"{namespace}_{task_id}")
    if not slave_ip:
        return Response(response=json.dumps({}), status=404)

    offset = request.args.get("offset", 0)
    length = request.args.get("length", 1024)
    path = request.args.get("path", "")
    files_info = requests.get(f"http://{slave_ip}:5051/files/read?path={sandbox_directory}{path}&offset={offset}&length={length}")

    if files_info.status_code == HTTPStatus.NOT_FOUND:
        return Response(response=json.dumps({}), status=404)
    file_info_data = files_info.json()

    return Response(response=json.dumps(file_info_data), status=200, mimetype="application/json")

@tasks_blueprint.route("/<string:task_id>/files/download")
@auth_required(pass_user=True)
def task_files_download(task_id, user):
    namespace = user.current_account.namespace
    slave_ip, sandbox_directory = get_task_data(f"{namespace}_{task_id}")
    if not slave_ip:
        return Response(response=json.dumps({}), status=404)

    offset = request.args.get("offset", 0)
    length = request.args.get("length", 1024)
    path = request.args.get("path", "")
    file_final_url = f"http://{slave_ip}:5051/files/download?path={sandbox_directory}{path}"
    download_id = uuid4().hex
    cache.set(f"downloads/{download_id}", {
        'file_url': file_final_url,
        'task_id': task_id,
        'file_path': path
    }, timeout=30) 
    download_id_url = url_for('hollowman.api.tasks.download_by_id', download_id=download_id) 
    return Response(response=json.dumps({'download_url': download_id_url.strip("/")}), status=HTTPStatus.OK)

@tasks_blueprint.route("/downloads/<string:download_id>")
def download_by_id(download_id):
    file_data = cache.get(f"downloads/{download_id}")
    if not file_data:
        return Response(status=HTTPStatus.NOT_FOUND)

    file_url = file_data['file_url']
    task_id = file_data['task_id']
    file_path = file_data['file_path']

    response = requests.get(file_url, stream=True)

    if response.status_code == HTTPStatus.NOT_FOUND:
        return Response(response=json.dumps({}), status=HTTPStatus.NOT_FOUND)

    filename = f"{task_id}_{file_path.strip('/')}.log"

    return Response(response=response.iter_content(chunk_size=4096), status=200, headers={"Content-Disposition":  f"attachment; filename={filename}",
                                                                                            "Content-Type": "application/octet-stream"})
