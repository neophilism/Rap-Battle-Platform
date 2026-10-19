"""WSGI application shell. All operational routes require upstream authorization."""
import html
import json
import re
from http.cookies import SimpleCookie, CookieError
from urllib.parse import urlsplit

from .identity import IdentityError, EngineUnavailable, UnconfiguredEngine
from .store import Conflict, SLUG


COOKIE = "__Host-rap-session"
MAX_BODY = 4096
HEADERS = [
    ("Cache-Control", "private, no-store"),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
    ("Content-Security-Policy", "default-src 'none'; style-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"),
    ("Strict-Transport-Security", "max-age=31536000"),
]
STATUSES = {200:"OK", 204:"No Content", 400:"Bad Request", 401:"Unauthorized",
            403:"Forbidden", 404:"Not Found", 405:"Method Not Allowed", 409:"Conflict",
            413:"Content Too Large", 415:"Unsupported Media Type", 421:"Misdirected Request",
            500:"Internal Server Error", 503:"Service Unavailable"}


class RequestError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def page(title, content):
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><link rel='stylesheet' href='/assets/shell.css'>"
            "</head><body><a class='skip' href='#main'>Skip to content</a>"
            "<header><a href='/'>Rap Battle</a><span>League workspace</span></header>"
            f"<main id='main' tabindex='-1'>{content}</main></body></html>")


CSS = """:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#11131a;color:#f5f2ee}
*{box-sizing:border-box}body{margin:0}header{display:flex;justify-content:space-between;gap:1rem;
padding:1.5rem max(1.5rem,calc((100vw - 68rem)/2));border-bottom:1px solid #353a49}
header a{font-weight:800;color:#efc47d;text-decoration:none}header span{color:#c1c7d4}
main{max-width:68rem;margin:auto;padding:clamp(1.5rem,5vw,4rem)}h1{font-size:clamp(2rem,5vw,3.5rem);
line-height:1.1;margin:0 0 1.5rem}p{line-height:1.6;max-width:65ch}.eyebrow{color:#efc47d;
font-size:.85rem;text-transform:uppercase;letter-spacing:.1em}.card{background:#1c202b;
border:1px solid #3c4354;border-radius:1rem;padding:1.5rem;margin-top:2rem}
dl{display:grid;grid-template-columns:minmax(8rem,1fr) 2fr;gap:1rem}dt{color:#c1c7d4}dd{margin:0;
overflow-wrap:anywhere}a{color:#efc47d}.skip{position:absolute;left:-9999px}.skip:focus{left:1rem;
top:1rem;background:#11131a;padding:1rem}a:focus-visible{outline:3px solid #efc47d;outline-offset:4px}
@media(max-width:36rem){header{flex-direction:column}dl{grid-template-columns:1fr;gap:.6rem}dd{margin-bottom:.8rem}}
"""


class Application:
    def __init__(self, store, origin, engine=None):
        parsed = urlsplit(origin)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or
                parsed.path or parsed.query or parsed.fragment or "\\" in origin or
                any(c.isspace() for c in origin)):
            raise ValueError("App origin must be a credential-free HTTPS origin without a path")
        self.store, self.origin, self.host = store, origin, parsed.netloc
        try:
            parsed.port
        except ValueError:
            raise ValueError("App origin port is invalid") from None
        self.engine = engine or UnconfiguredEngine()

    def __call__(self, environ, start_response):
        try:
            result = self.dispatch(environ)
        except RequestError as error:
            result = error.status, {"error": error.message}, []
        except IdentityError as error:
            result = (403 if error.code=="forbidden" else 401), {"error": "Access denied"}, []
        except EngineUnavailable:
            result = 503, {"error": "Sign-in service unavailable"}, []
        except Conflict:
            result = 409, {"error": "Settings changed; reload before retrying"}, []
        except ValueError:
            result = 400, {"error": "Invalid request"}, []
        except Exception:
            # Do not disclose SQL, paths, engine diagnostics, tokens or tenant data.
            result = 500, {"error": "Request unavailable"}, []
        status, body, extra = result
        if isinstance(body, str):
            content_type = "text/css; charset=utf-8" if environ.get("PATH_INFO")=="/assets/shell.css" else "text/html; charset=utf-8"
            data = body.encode("utf-8")
        else:
            content_type, data = "application/json; charset=utf-8", json.dumps(body).encode("utf-8")
        if status==204:
            data = b""
        headers = HEADERS+[("Content-Type",content_type),("Content-Length",str(len(data)))]+extra
        start_response(f"{status} {STATUSES[status]}", headers)
        return [data]

    def dispatch(self, env):
        method, path = env.get("REQUEST_METHOD",""), env.get("PATH_INFO","")
        if env.get("HTTP_HOST") != self.host:
            raise RequestError(421, "Unexpected application host")
        if path=="/healthz" and method=="GET":
            return 200, {"status":"ok","service":"rap-battle"}, []
        if env.get("wsgi.url_scheme")!="https":
            raise RequestError(421,"HTTPS required")
        if path=="/readyz" and method=="GET":
            ready = self.store.healthy() and self.engine.ready()
            return (200 if ready else 503), {"status":"ready" if ready else "not_ready"}, []
        if method not in ("GET","POST","PUT","DELETE"):
            raise RequestError(405,"Method not allowed")
        if method!="GET" and env.get("HTTP_ORIGIN")!=self.origin:
            raise RequestError(403,"Request origin rejected")
        if path=="/" and method=="GET":
            return 200,page("Rap Battle", "<p class='eyebrow'>Independent leagues. One stage.</p>"
                            "<h1>Your league starts here.</h1><p>A dedicated workspace for local rap battle leagues.</p>"
                            "<section class='card'><h2>League access</h2><p>Use your league's authorized sign-in to enter its workspace."
                            " Sign-in provisioning is not available in this foundation preview.</p></section>"),[]
        if path=="/assets/shell.css" and method=="GET":
            return 200,CSS,[]
        if path=="/api/session" and method=="DELETE":
            return 204,{},[("Set-Cookie",self.cookie("",0))]
        if path=="/api/session" and method=="POST":
            body=self.json_body(env)
            if set(body)!={"league"} or not isinstance(body["league"],str):
                raise RequestError(400,"A league is required")
            self.access(env,body["league"],"content.view_private",header_only=True)
            token=env["HTTP_AUTHORIZATION"][7:]
            return 200,{"signedIn":True},[("Set-Cookie",self.cookie(token,900))]
        match=re.fullmatch(r"/(api/leagues|leagues)/([a-z0-9-]+)(/settings)?",path)
        if not match or len(match[2])>63 or not SLUG.fullmatch(match[2]):
            raise RequestError(404,"Not found")
        api,slug,settings=match.groups()
        if (api=="leagues" and (settings or method!="GET")) or (api=="api/leagues" and not settings):
            raise RequestError(404,"Not found")
        if method not in ("GET","PUT") or (method=="PUT" and not settings):
            raise RequestError(405,"Method not allowed")
        league=self.access(env,slug,"tenant.manage" if method=="PUT" else "content.view_private")
        if method=="PUT":
            body=self.json_body(env)
            if set(body)!={"name","timezone","version"}:
                raise RequestError(400,"Only name, timezone and version can be updated")
            league=self.store.update_settings(slug,league["organization_id"],**body)
        if api=="api/leagues":
            return 200,{k:league[k] for k in ("slug","name","timezone","version","synthetic")},[]
        label="Synthetic league fixture" if league["synthetic"] else "League workspace"
        return 200,page(league["name"],f"<p class='eyebrow'>{label}</p><h1>{html.escape(league['name'])}</h1>"
                        "<section class='card'><h2>Workspace settings</h2><dl>"
                        f"<dt>League</dt><dd>{html.escape(slug)}</dd><dt>Timezone</dt><dd>{html.escape(league['timezone'])}</dd>"
                        f"<dt>Settings version</dt><dd>{league['version']}</dd></dl></section>"),[]

    def access(self,env,slug,action,header_only=False):
        if not SLUG.fullmatch(slug) or len(slug)>63:
            raise RequestError(404,"Workspace unavailable")
        league=self.store.league(slug)
        if not league:
            # Same response as denied membership, without exposing tenant existence.
            raise RequestError(403,"Access denied")
        authorization=env.get("HTTP_AUTHORIZATION")
        if authorization is None and not header_only:
            cookie=SimpleCookie()
            try:
                cookie.load(env.get("HTTP_COOKIE",""))
            except CookieError:
                raise IdentityError("invalid") from None
            if COOKIE in cookie:
                authorization="Bearer "+cookie[COOKIE].value
        if not authorization or not re.fullmatch(r"Bearer [A-Za-z0-9_-]{43}",authorization):
            raise IdentityError("invalid" if authorization else "missing")
        principal=self.engine.authorize(authorization,league["organization_id"],action)
        if principal.organization_id!=league["organization_id"]:
            raise IdentityError("forbidden")
        return league

    @staticmethod
    def cookie(token,age):
        cookie=SimpleCookie()
        cookie[COOKIE]=token
        for key,value in (("path","/"),("secure",True),("httponly",True),("samesite","Strict"),("max-age",age)):
            cookie[COOKIE][key]=value
        return cookie.output(header="").strip()

    @staticmethod
    def json_body(env):
        if env.get("CONTENT_TYPE","").split(";",1)[0]!="application/json":
            raise RequestError(415,"JSON content type required")
        try:
            size=int(env.get("CONTENT_LENGTH",""))
        except (TypeError,ValueError):
            raise RequestError(400,"A valid content length is required") from None
        if not 0<size<=MAX_BODY:
            raise RequestError(413,"Request body is too large")
        data=env["wsgi.input"].read(size)
        if len(data)!=size:
            raise RequestError(400,"Incomplete request body")
        try:
            body=json.loads(data)
        except (ValueError,UnicodeDecodeError):
            raise RequestError(400,"Invalid JSON") from None
        if not isinstance(body,dict):
            raise RequestError(400,"JSON object required")
        return body
