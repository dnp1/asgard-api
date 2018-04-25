
import unittest
import json
from http import HTTPStatus

from responses import RequestsMock

from hollowman.conf import DEFAULT_MESOS_ADDRESS
from hollowman.app import application
from hollowman import cache
from hollowman import api

from tests.base import BaseApiTests
from tests.utils import with_json_fixture, get_raw_fixture

class TasksEndpointTest(BaseApiTests, unittest.TestCase):

    @unittest.skip("")
    def test_tasks_return_404_for_not_found_task(self):
        self.fail()

    @unittest.skip("")
    def test_tasks_return_404_for_task_in_another_namespace(self):
        self.fail()

    @with_json_fixture("../fixtures/api/tasks/task_file_browse_namespace_dev.json")
    @with_json_fixture("../fixtures/api/tasks/one_task_json_namespace_dev.json")
    @with_json_fixture("../fixtures/api/tasks/one_slave_json_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    @with_json_fixture("../fixtures/api/tasks/slave_state_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    def test_tasks_browse_files(self, task_browse_file_fixture, one_task_json_fixture, one_slave_json_fixture, slave_state_fixture):
        task_id = "infra_mysql.b331f6c9-fb9e-11e7-ab4b-faf0633ea91f"
        sandbox_directory = "/tmp/mesos/slaves/2084863b-12d1-4319-b515-992eab91a53d-S1/frameworks/27b52920-3899-4b90-a1d6-bf83a87f3612-0000/executors/dev_infra_mysql.b331f6c9-fb9e-11e7-ab4b-faf0633ea91f/runs/e14d7537-c1d0-4846-a076-25d623d6a70f"
        with application.test_client() as client:
            with RequestsMock() as rsps:
                rsps.add(method="GET",
                         url=f"{DEFAULT_MESOS_ADDRESS}/tasks?task_id={self.user.current_account.namespace}_{task_id}",
                         body=json.dumps(one_task_json_fixture),
                         status=200,
                         match_querystring=True)
                rsps.add(method="GET",
                         url=f"{DEFAULT_MESOS_ADDRESS}/slaves?slave_id=2084863b-12d1-4319-b515-992eab91a53d-S1",
                         body=json.dumps(one_slave_json_fixture),
                         status=200,
                         match_querystring=True)
                rsps.add(method="GET",
                         url="http://127.0.0.1:5051/state",
                         body=json.dumps(slave_state_fixture),
                         status=200)
                rsps.add(method="GET",
                         url=f"http://127.0.0.1:5051/files/browse?path={sandbox_directory}",
                         body=json.dumps(task_browse_file_fixture),
                         status=200,
                         match_querystring=True)
                resp = client.get(f"/tasks/{task_id}/files", headers=self.auth_header)
                resp_data = json.loads(resp.data)
                self.assertEquals(200, resp.status_code)
                self.assertEqual(4, len(resp_data))
                self.assertEqual(sorted(["/stdout",
                                         "/stdout.logrotate.conf",
                                         "/stderr",
                                         "/stderr.logrotate.conf"]),
                                 sorted([u['path'] for u in resp_data]))

    @with_json_fixture("../fixtures/api/tasks/task_file_browse_namespace_dev.json")
    @with_json_fixture("../fixtures/api/tasks/task_info_namespace_dev_task_id_infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e.json")
    @with_json_fixture("../fixtures/api/tasks/one_slave_json_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    @with_json_fixture("../fixtures/api/tasks/slave_state_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    def test_tasks__browse_files_task_is_completed(self, task_browse_file_fixture, one_task_json_fixture, one_slave_json_fixture, slave_state_fixture):
        """
            Se tentamos pegar os arquivos de uma task que não está mais rodando, temos que procurá-la
            no array `completed_tasks`.
        """
        slave_id = "31fcae61-51a9-4ad1-8054-538503eb53a9-S5"
        task_id = "infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e"
        sandbox_directory = "/tmp/mesos/slaves/31fcae61-51a9-4ad1-8054-538503eb53a9-S5/frameworks/27b52920-3899-4b90-a1d6-bf83a87f3612-0000/executors/dev_infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e/runs/1ec0d0bf-0f11-49ba-8a03-2cf954ad1cfe"
        with application.test_client() as client:
            with RequestsMock() as rsps:
                rsps.add(method="GET",
                         url=f"{DEFAULT_MESOS_ADDRESS}/tasks?task_id={self.user.current_account.namespace}_{task_id}",
                         body=json.dumps(one_task_json_fixture),
                         status=200,
                         match_querystring=True)
                rsps.add(method="GET",
                         url=f"{DEFAULT_MESOS_ADDRESS}/slaves?slave_id={slave_id}",
                         body=json.dumps(one_slave_json_fixture),
                         status=200,
                         match_querystring=True)
                rsps.add(method="GET",
                         url="http://127.0.0.1:5051/state",
                         body=json.dumps(slave_state_fixture),
                         status=200)
                rsps.add(method="GET",
                         url=f"http://127.0.0.1:5051/files/browse?path={sandbox_directory}",
                         body=json.dumps(task_browse_file_fixture),
                         status=200,
                         match_querystring=True)
                resp = client.get(f"/tasks/{task_id}/files", headers=self.auth_header)
                resp_data = json.loads(resp.data)
                self.assertEquals(200, resp.status_code)
                self.assertEqual(4, len(resp_data))

    def test_tasks_returnn_404_if_task_does_not_exist(self):
        """
        Se o mesos retornar que a task não existe, já retornamos 404 direto.
        """
        task_id = "task_do_not_exist.2580925d-0129-11e8-9a03-6e85ded2ca1e"
        with application.test_client() as client:
            with RequestsMock() as rsps:
                rsps.add(method="GET",
                         url=f"{DEFAULT_MESOS_ADDRESS}/tasks?task_id={self.user.current_account.namespace}_{task_id}",
                         body=json.dumps({"tasks": []}),
                         status=200,
                         match_querystring=True)
                resp = client.get(f"/tasks/{task_id}/files", headers=self.auth_header)
                resp_data = json.loads(resp.data)
                self.assertEquals(404, resp.status_code)

    @with_json_fixture("../fixtures/api/tasks/task_file_read_response.json")
    @with_json_fixture("../fixtures/api/tasks/task_info_namespace_dev_task_id_infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e.json")
    @with_json_fixture("../fixtures/api/tasks/one_slave_json_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    @with_json_fixture("../fixtures/api/tasks/slave_state_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    def test_tasks_read_file_offset(self, task_file_read_fixture, one_task_json_fixture, one_slave_json_fixture, slave_state_fixture):
        slave_id = "31fcae61-51a9-4ad1-8054-538503eb53a9-S5"
        task_id = "infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e"
        sandbox_directory = "/tmp/mesos/slaves/31fcae61-51a9-4ad1-8054-538503eb53a9-S5/frameworks/27b52920-3899-4b90-a1d6-bf83a87f3612-0000/executors/dev_infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e/runs/1ec0d0bf-0f11-49ba-8a03-2cf954ad1cfe"
        with application.test_client() as client:
            with RequestsMock() as rsps:
                rsps.add(method="GET",
                         url=f"{DEFAULT_MESOS_ADDRESS}/tasks?task_id={self.user.current_account.namespace}_{task_id}",
                         body=json.dumps(one_task_json_fixture),
                         status=200,
                         match_querystring=True)
                rsps.add(method="GET",
                         url=f"{DEFAULT_MESOS_ADDRESS}/slaves?slave_id={slave_id}",
                         body=json.dumps(one_slave_json_fixture),
                         status=200,
                         match_querystring=True)
                rsps.add(method="GET",
                         url="http://127.0.0.1:5051/state",
                         body=json.dumps(slave_state_fixture),
                         status=200)
                rsps.add(method="GET",
                         url=f"http://127.0.0.1:5051/files/read?path={sandbox_directory}/stderr&offset=0&length=42",
                         body=json.dumps(task_file_read_fixture),
                         status=200,
                         match_querystring=True)
                resp = client.get(f"/tasks/{task_id}/files/read?path=/stderr&offset=0&length=42", headers=self.auth_header)
                resp_data = json.loads(resp.data)
                self.assertEquals(200, resp.status_code)
                self.assertEquals(0, resp_data['offset'])
                self.assertEqual("*** Starting uWSGI 2.0.14 (64bit) on [Wed Jan 31 19:58:13 2018] ***", resp_data['data'])

    @with_json_fixture("../fixtures/api/tasks/task_info_namespace_dev_task_id_infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e.json")
    @with_json_fixture("../fixtures/api/tasks/one_slave_json_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    @with_json_fixture("../fixtures/api/tasks/slave_state_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    def test_tasks_download_file(self, one_task_json_fixture, one_slave_json_fixture, slave_state_fixture):
        """
        Certifica que a chamada ao endpoint de download popula o cache com os dados
        Teremos nos cache dados como: url, task_id, path do arquivo a ser baixado, etc.
        """
        slave_id = "31fcae61-51a9-4ad1-8054-538503eb53a9-S5"
        slave_ip = one_slave_json_fixture['slaves'][0]['hostname']
        task_id = "infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e"
        sandbox_directory = "/tmp/mesos/slaves/31fcae61-51a9-4ad1-8054-538503eb53a9-S5/frameworks/27b52920-3899-4b90-a1d6-bf83a87f3612-0000/executors/dev_infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e/runs/1ec0d0bf-0f11-49ba-8a03-2cf954ad1cfe"
        with application.test_client() as client:
            with RequestsMock() as rsps:
                rsps.add(method="GET",
                         url=f"{DEFAULT_MESOS_ADDRESS}/tasks?task_id={self.user.current_account.namespace}_{task_id}",
                         body=json.dumps(one_task_json_fixture),
                         status=200,
                         match_querystring=True)
                rsps.add(method="GET",
                         url=f"{DEFAULT_MESOS_ADDRESS}/slaves?slave_id={slave_id}",
                         body=json.dumps(one_slave_json_fixture),
                         status=200,
                         match_querystring=True)
                rsps.add(method="GET",
                         url="http://127.0.0.1:5051/state",
                         body=json.dumps(slave_state_fixture),
                         status=200)
                download_id = "7094c8e5b131416a87ccdc3e7d3131a6" 
                with unittest.mock.patch.object(cache, "set") as cache_set_mock, \
                        unittest.mock.patch.object(api.tasks, 'uuid4', return_value=unittest.mock.Mock(hex=download_id)) as uuid4_mock:
                    resp = client.get(f"/tasks/{task_id}/files/download?path=/stdout&offset=0&length=42", headers=self.auth_header)
                    self.assertEquals(HTTPStatus.OK, resp.status_code)
                    resp_data = json.loads(resp.data)
                    self.assertEqual("tasks/downloads/7094c8e5b131416a87ccdc3e7d3131a6", resp_data["download_url"])
                    cache_set_mock.assert_called_with(f"downloads/{download_id}", {
                        'file_url': f"http://{slave_ip}:5051/files/download?path={sandbox_directory}/stdout",
                        'task_id': task_id,
                        'file_path': "/stdout"
                    }, timeout=30)

    @with_json_fixture("../fixtures/api/tasks/task_info_namespace_dev_task_id_infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e.json")
    @with_json_fixture("../fixtures/api/tasks/one_slave_json_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    @with_json_fixture("../fixtures/api/tasks/slave_state_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    def test_tasks_return_404_on_file_not_found(self, one_task_json_fixture, one_slave_json_fixture, slave_state_fixture):
        slave_id = "31fcae61-51a9-4ad1-8054-538503eb53a9-S5"
        task_id = "infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e"
        sandbox_directory = "/tmp/mesos/slaves/31fcae61-51a9-4ad1-8054-538503eb53a9-S5/frameworks/27b52920-3899-4b90-a1d6-bf83a87f3612-0000/executors/dev_infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e/runs/1ec0d0bf-0f11-49ba-8a03-2cf954ad1cfe"
        with application.test_client() as client:
            with RequestsMock() as rsps:
                rsps.add(method="GET",
                         url=f"{DEFAULT_MESOS_ADDRESS}/tasks?task_id={self.user.current_account.namespace}_{task_id}",
                         body=json.dumps(one_task_json_fixture),
                         status=200,
                         match_querystring=True)
                rsps.add(method="GET",
                         url=f"{DEFAULT_MESOS_ADDRESS}/slaves?slave_id={slave_id}",
                         body=json.dumps(one_slave_json_fixture),
                         status=200,
                         match_querystring=True)
                rsps.add(method="GET",
                         url="http://127.0.0.1:5051/state",
                         body=json.dumps(slave_state_fixture),
                         status=200)
                rsps.add(method="GET",
                         url=f"http://127.0.0.1:5051/files/read?path={sandbox_directory}/not_found_file&offset=0&length=42",
                         body="",
                         status=404,
                         match_querystring=True)
                resp = client.get(f"/tasks/{task_id}/files/read?path=/not_found_file&offset=0&length=42", headers=self.auth_header)
                resp_data = json.loads(resp.data)
                self.assertEquals(404, resp.status_code)

    def test_download_by_id_expired(self):
        """
        Se o ID não existir mais no cache, retornamos 404
        """
        download_id = "7094c8e5b131416a87ccdc3e7d3131a6"
        with application.test_client() as client:
            resp = client.get(f"/tasks/downloads/{download_id}")
            self.assertEquals(404, resp.status_code)

    @with_json_fixture("../fixtures/api/tasks/task_info_namespace_dev_task_id_infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e.json")
    @with_json_fixture("../fixtures/api/tasks/one_slave_json_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    @with_json_fixture("../fixtures/api/tasks/slave_state_id_2084863b-12d1-4319-b515-992eab91a53d-S1.json")
    def test_download_by_id_task_running(self, one_task_json_fixture, one_slave_json_fixture, slave_state_fixture):
        """
        Retornamos o arquivo desejado
        """
        task_file_download_fixture = get_raw_fixture("../fixtures/api/tasks/task_file_download_response.txt")
        slave_ip = one_slave_json_fixture['slaves'][0]['hostname']
        slave_id = "31fcae61-51a9-4ad1-8054-538503eb53a9-S5"
        task_id = "infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e"
        sandbox_directory = "/tmp/mesos/slaves/31fcae61-51a9-4ad1-8054-538503eb53a9-S5/frameworks/27b52920-3899-4b90-a1d6-bf83a87f3612-0000/executors/dev_infra_mongodb_mongodb1.2580925d-0129-11e8-9a03-6e85ded2ca1e/runs/1ec0d0bf-0f11-49ba-8a03-2cf954ad1cfe"
        with application.test_client() as client:
            with RequestsMock() as rsps:
                rsps.add(method="GET",
                         url=f"http://127.0.0.1:5051/files/download?path={sandbox_directory}/stdout",
                         body=task_file_download_fixture,
                         status=200,
                         match_querystring=True)
                download_id = "7094c8e5b131416a87ccdc3e7d3131a6"
                cache_data = {
                        'file_url': f"http://{slave_ip}:5051/files/download?path={sandbox_directory}/stdout",
                        'task_id': task_id,
                        'file_path': "/stdout"
                }
                with unittest.mock.patch.object(cache, "get", return_value=cache_data), \
                        unittest.mock.patch.object(api.tasks, 'uuid4', return_value=unittest.mock.Mock(hex=download_id)) as uuid4_mock:
                    resp = client.get(f"/tasks/downloads/{download_id}", headers=self.auth_header)
                    self.assertEquals(200, resp.status_code)
                    self.assertEqual(bytes(task_file_download_fixture, "utf-8"), resp.data)
                    self.assertEqual(resp.headers.get("Content-Disposition"), f"attachment; filename={task_id}_stdout.log")


