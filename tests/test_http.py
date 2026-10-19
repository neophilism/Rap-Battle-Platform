"""Real loopback HTTP against WSGI; synthetic TLS terminator and engine fixture."""
import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from wsgiref.simple_server import make_server

from rapbattle.app import Application
from rapbattle.runtime import PrivateRequestHandler, create_from_environment
from rapbattle.store import Store
from test_app import FixtureEngine, TOKEN, ORIGIN


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        store=Store(Path(self.temp.name)/"http.sqlite")
        store.add_league("ny","org-ny","NY HTTP fixture",synthetic=True)
        store.add_league("la","org-la","LA HTTP fixture",synthetic=True)
        self.engine=FixtureEngine()
        app=Application(store,ORIGIN,self.engine)
        def fixture_tls(env,start):
            # A fixture-only trusted server wrapper, not a forwarded-header parser.
            env["wsgi.url_scheme"]="https"
            return app(env,start)
        self.server=make_server("127.0.0.1",0,fixture_tls,handler_class=PrivateRequestHandler)
        self.worker=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.worker.start()

    def tearDown(self):
        self.server.shutdown()
        self.worker.join(timeout=2)
        self.server.server_close()
        self.temp.cleanup()

    def call(self,method,path,body=None,cookie=None,authorization=True):
        headers={"Host":"rap.example.test","Origin":ORIGIN}
        if authorization:
            headers["Authorization"]="Bearer "+TOKEN
        if cookie:
            headers["Cookie"]=cookie
        if body is not None:
            body=json.dumps(body)
            headers["Content-Type"]="application/json"
        connection=HTTPConnection("127.0.0.1",self.server.server_port,timeout=3)
        try:
            connection.request(method,path,body,headers)
            response=connection.getresponse()
            return response.status,dict(response.getheaders()),response.read().decode()
        finally:
            connection.close()

    def test_cookie_session_settings_and_tenant_isolation_over_http(self):
        status,headers,_=self.call("POST","/api/session",{"league":"ny"})
        self.assertEqual(status,200)
        cookie=headers["Set-Cookie"].split(";",1)[0]
        self.assertEqual(self.call("GET","/leagues/ny",cookie=cookie,authorization=False)[0],200)
        self.assertEqual(self.call("GET","/leagues/la",cookie=cookie,authorization=False)[0],403)
        status,_,body=self.call("PUT","/api/leagues/ny/settings",
                               {"name":"Updated over HTTP","timezone":"UTC","version":1},cookie,False)
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)["version"],2)
        status,_,body=self.call("GET","/api/leagues/ny/settings",cookie=cookie,authorization=False)
        self.assertEqual(json.loads(body)["name"],"Updated over HTTP")
        self.assertEqual(self.call("DELETE","/api/session",cookie=cookie,authorization=False)[0],204)

    def test_health_and_stylesheet_have_no_operational_league_data(self):
        self.assertEqual(self.call("GET","/healthz",authorization=False)[0],200)
        status,headers,body=self.call("GET","/assets/shell.css",authorization=False)
        self.assertEqual(status,200)
        self.assertTrue(headers["Content-Type"].startswith("text/css"))
        self.assertIn("@media",body)
        self.assertNotIn("NY HTTP fixture",body)


class RuntimeTests(unittest.TestCase):
    def test_configuration_requires_private_storage_and_https_origin(self):
        for env in ({},{"RAP_ORIGIN":ORIGIN},{"RAP_DATABASE":"/tmp/unused-rap-database"}):
            with self.assertRaises(ValueError):
                create_from_environment(env)
        with tempfile.TemporaryDirectory() as root:
            app=create_from_environment({"RAP_ORIGIN":ORIGIN,"RAP_DATABASE":str(Path(root)/"db.sqlite")})
            self.assertFalse(app.engine.ready())
            self.assertTrue(app.store.healthy())
            with self.assertRaises(ValueError):
                create_from_environment({"RAP_ORIGIN":"http://rap.example.test","RAP_DATABASE":str(Path(root)/"db.sqlite")})
