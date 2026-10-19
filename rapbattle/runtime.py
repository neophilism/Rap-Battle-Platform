"""Operator configuration and local development entrypoint; never provisions identity."""
import argparse
import os
from pathlib import Path
from wsgiref.simple_server import make_server, WSGIRequestHandler

from .app import Application
from .identity import NodeEngine
from .store import Store


def create_from_environment(environ=None):
    env=os.environ if environ is None else environ
    origin=env.get("RAP_ORIGIN")
    database=env.get("RAP_DATABASE")
    if not origin or not database:
        raise ValueError("RAP_ORIGIN and RAP_DATABASE are required")
    path=Path(database).resolve()
    if not path.parent.is_dir():
        raise ValueError("Create the private RAP_DATABASE directory before starting")
    engine=NodeEngine(env["RAP_ENGINE_CHECKOUT"]) if env.get("RAP_ENGINE_CHECKOUT") else None
    return Application(Store(path),origin,engine)


class PrivateRequestHandler(WSGIRequestHandler):
    def log_message(self,format,*args):
        # Default access logging includes full paths/query strings. The shell
        # intentionally emits no access bodies, credentials or tenant routes.
        pass


def main():
    parser=argparse.ArgumentParser(description="Local RAP shell liveness server; production requires a TLS WSGI host")
    parser.add_argument("--port",type=int,default=8000)
    args=parser.parse_args()
    app=create_from_environment()
    # Plain HTTP is loopback-only; private routes still require genuine TLS scheme.
    with make_server("127.0.0.1",args.port,app,handler_class=PrivateRequestHandler) as server:
        server.serve_forever()


if __name__=="__main__":
    main()
