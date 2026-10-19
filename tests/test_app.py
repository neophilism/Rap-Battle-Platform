"""Synthetic engine fixture: verifies downstream behavior, never live auth acceptance."""
import io
import json
import tempfile
import unittest
from pathlib import Path

from rapbattle.app import Application, COOKIE
from rapbattle.identity import Principal, IdentityError, EngineUnavailable
from rapbattle.store import Store


TOKEN="a"*43
ORIGIN="https://rap.example.test"


class FixtureEngine:
    def __init__(self):
        self.allowed={"org-ny"}
        self.manager=True
        self.error=None
        self.calls=[]

    def ready(self):
        return self.error is None

    def authorize(self,authorization,organization_id,action):
        self.calls.append((authorization,organization_id,action))
        if self.error:
            raise self.error
        if authorization!="Bearer "+TOKEN:
            raise IdentityError("invalid")
        if organization_id not in self.allowed or (action=="tenant.manage" and not self.manager):
            raise IdentityError("forbidden")
        return Principal("fixture-account","fixture-session",organization_id)


def request(app,path="/",method="GET",body=None,token=TOKEN,extra=None):
    encoded=json.dumps(body).encode() if body is not None else b""
    env={"REQUEST_METHOD":method,"PATH_INFO":path,"QUERY_STRING":"",
         "wsgi.url_scheme":"https","HTTP_HOST":"rap.example.test",
         "wsgi.input":io.BytesIO(encoded),"CONTENT_LENGTH":str(len(encoded)),
         "CONTENT_TYPE":"application/json","HTTP_ORIGIN":ORIGIN}
    if token is not None:
        env["HTTP_AUTHORIZATION"]="Bearer "+token
    env.update(extra or {})
    response={}
    def start(status,headers):
        response.update(status=int(status.split()[0]),headers=dict(headers))
    response["body"]=b"".join(app(env,start)).decode()
    return response


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"shell.sqlite"
        self.store=Store(self.path)
        for slug,org,name,tz in [("ny","org-ny","New York fixture","America/New_York"),
                                 ("atlanta","org-atl","Atlanta fixture","America/New_York"),
                                 ("la","org-la","Los Angeles fixture","America/Los_Angeles")]:
            self.store.add_league(slug,org,name,tz,synthetic=True)
        self.engine=FixtureEngine()
        self.app=Application(self.store,ORIGIN,self.engine)

    def tearDown(self):
        self.temp.cleanup()

    def test_health_liveness_and_dependency_readiness_are_distinct(self):
        closed=Application(self.store,ORIGIN)
        self.assertEqual(request(closed,"/healthz",extra={"wsgi.url_scheme":"http"})["status"],200)
        self.assertEqual(request(closed,"/readyz")["status"],503)
        self.assertEqual(request(self.app,"/readyz")["status"],200)
        self.assertEqual(request(self.app,"/",extra={"wsgi.url_scheme":"http"})["status"],421)
        self.assertEqual(request(self.app,"/",extra={"HTTP_HOST":"evil.example.test"})["status"],421)

    def test_independent_league_access_and_private_rendering(self):
        ny=request(self.app,"/leagues/ny")
        self.assertEqual(ny["status"],200)
        self.assertIn("Synthetic league fixture",ny["body"])
        self.assertNotIn("Atlanta",ny["body"])
        for slug in ("atlanta","la"):
            self.assertEqual(request(self.app,"/leagues/"+slug)["status"],403)
        self.engine.allowed={"org-atl"}
        self.assertEqual(request(self.app,"/leagues/atlanta")["status"],200)
        self.assertEqual(request(self.app,"/leagues/ny")["status"],403)
        self.engine.allowed={"org-la"}
        self.assertEqual(request(self.app,"/leagues/la")["status"],200)

    def test_missing_invalid_expired_revoked_or_recovered_session_denied(self):
        for token in (None,"short","a"*42,"a"*44,"a"*42+"\n"):
            self.assertEqual(request(self.app,"/leagues/ny",token=token)["status"],401)
        for code in ("expired","revoked","invalid"):
            self.engine.error=IdentityError(code)
            self.assertEqual(request(self.app,"/leagues/ny")["status"],401)
        self.engine.error=EngineUnavailable("postgres://SECRET@example.test")
        response=request(self.app,"/leagues/ny")
        self.assertEqual(response["status"],503)
        self.assertNotIn("SECRET",response["body"])

    def test_session_cookie_rechecks_upstream_each_request(self):
        login=request(self.app,"/api/session","POST",{"league":"ny"})
        self.assertEqual(login["status"],200)
        cookie=login["headers"]["Set-Cookie"]
        for flag in ("HttpOnly","Secure","SameSite=Strict","Path=/","Max-Age=900"):
            self.assertIn(flag,cookie)
        self.assertNotIn("Domain=",cookie)
        headers={"HTTP_COOKIE":cookie.split(";",1)[0]}
        self.assertEqual(request(self.app,"/leagues/ny",token=None,extra=headers)["status"],200)
        self.engine.error=IdentityError("revoked")
        self.assertEqual(request(self.app,"/leagues/ny",token=None,extra=headers)["status"],401)
        logout=request(self.app,"/api/session","DELETE",token=None,extra=headers)
        self.assertEqual(logout["status"],204)
        self.assertIn("Max-Age=0",logout["headers"]["Set-Cookie"])
        # No raw bearer token is persisted in the downstream database.
        self.assertNotIn(TOKEN.encode(),self.path.read_bytes())

    def test_cookie_cannot_bootstrap_another_cookie_session(self):
        result=request(self.app,"/api/session","POST",{"league":"ny"},token=None,
                       extra={"HTTP_COOKIE":COOKIE+"="+TOKEN})
        self.assertEqual(result["status"],401)

    def test_settings_round_trip_restart_and_optimistic_concurrency(self):
        changed=request(self.app,"/api/leagues/ny/settings","PUT",
                        {"name":"New York revised","timezone":"UTC","version":1})
        self.assertEqual(changed["status"],200)
        self.assertEqual(json.loads(changed["body"])["version"],2)
        restarted=Application(Store(self.path),ORIGIN,self.engine)
        persisted=json.loads(request(restarted,"/api/leagues/ny/settings")["body"])
        self.assertEqual((persisted["name"],persisted["timezone"],persisted["version"]),
                         ("New York revised","UTC",2))
        stale=request(restarted,"/api/leagues/ny/settings","PUT",
                      {"name":"Lost update","timezone":"UTC","version":1})
        self.assertEqual(stale["status"],409)
        self.assertEqual(self.store.league("ny")["name"],"New York revised")
        self.assertEqual(self.store.league("atlanta")["version"],1)

    def test_membership_does_not_grant_settings_management(self):
        self.engine.manager=False
        self.assertEqual(request(self.app,"/api/leagues/ny/settings")["status"],200)
        denied=request(self.app,"/api/leagues/ny/settings","PUT",
                       {"name":"Unauthorized","timezone":"UTC","version":1})
        self.assertEqual(denied["status"],403)
        self.assertEqual(self.store.league("ny")["version"],1)

    def test_tenant_identity_cannot_be_overridden_by_body_headers_or_query(self):
        forged=request(self.app,"/api/leagues/ny/settings","PUT",
                       {"name":"Attempt","timezone":"UTC","version":1,"organization_id":"org-la"},
                       extra={"HTTP_X_TENANT_ID":"org-la","QUERY_STRING":"organization_id=org-la"})
        self.assertEqual(forged["status"],400)
        self.assertEqual(self.engine.calls[-1][1],"org-ny")
        self.assertEqual(self.store.league("ny")["version"],1)
        self.engine.authorize=lambda *args: Principal("a","s","org-la")
        self.assertEqual(request(self.app,"/leagues/ny")["status"],403)

    def test_csrf_host_scheme_and_forwarded_header_spoofs_fail_closed(self):
        for extra in ({"HTTP_ORIGIN":"https://evil.example.test"},{"HTTP_ORIGIN":""},
                      {"HTTP_HOST":"evil.example.test","HTTP_X_FORWARDED_HOST":"rap.example.test"},
                      {"wsgi.url_scheme":"http","HTTP_X_FORWARDED_PROTO":"https"}):
            self.assertIn(request(self.app,"/api/session","POST",{"league":"ny"},extra=extra)["status"],(403,421))

    def test_markup_is_escaped_and_responses_never_cache_private_data(self):
        self.store.update_settings("ny","org-ny","<script>alert(1)</script>","UTC",1)
        response=request(self.app,"/leagues/ny")
        self.assertNotIn("<script>",response["body"])
        self.assertIn("&lt;script&gt;",response["body"])
        self.assertIn("no-store",response["headers"]["Cache-Control"])
        self.assertIn("frame-ancestors 'none'",response["headers"]["Content-Security-Policy"])
        self.assertIn("Skip to content",response["body"])
        self.assertNotIn("New York",request(self.app,"/",token=None)["body"])

    def test_invalid_payloads_methods_routes_and_content_are_rejected(self):
        for body in ({"name":"","timezone":"UTC","version":1},
                     {"name":"OK","timezone":"Mars/Unknown","version":1},
                     {"name":"OK","timezone":"UTC","version":True},[]):
            self.assertEqual(request(self.app,"/api/leagues/ny/settings","PUT",body)["status"],400)
        self.assertEqual(request(self.app,"/api/session","POST",{"league":"ny"},extra={"CONTENT_LENGTH":"5000"})["status"],413)
        self.assertEqual(request(self.app,"/api/session","POST",{"league":"ny"},extra={"CONTENT_TYPE":"text/plain"})["status"],415)
        self.assertEqual(request(self.app,"/leagues/ny","TRACE")["status"],405)
        for path in ("/leagues/../ny","/leagues/ny%2Fsecret","/api/leagues/ny"):
            self.assertEqual(request(self.app,path)["status"],404)


if __name__=="__main__":
    unittest.main()
