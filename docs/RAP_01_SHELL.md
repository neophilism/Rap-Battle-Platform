# RAP-01 application shell

This branch implements a separate Python WSGI application. It stores only
downstream league settings in SQLite; Live-Competition-Engine remains the
authority for accounts, sessions, recovery, memberships and roles. No downstream
endpoint creates accounts, issues engine credentials, changes memberships or
publishes a league. Later battle and commerce features remain separate work.

## Engine dependency

Reviewed engine revision: `3a316219da1b97cffd2faed1e99967a1fb8c6362`.
The Node bridge loads that checkout's `AuthenticationService` and
`createPostgresAuthStore`. It checks exact HEAD and rejects tracked modifications
before importing the upstream libraries. Engine workspace dependencies must
already be installed from its own lockfile. Node 24 and Python 3.12+ are required.
The engine's own configured database environment is inherited by the bridge;
never copy a database credential into source, HTTP requests, command arguments
or a checkpoint. The downstream SQLite file is separate from that engine store.

The bridge invokes `authorizeAction` for `content.view_private` or `tenant.manage`
using the organization derived from the operator-provisioned league mapping.
Credentials go through stdin only. Subprocess failure, timeout, unknown revision,
invalid principal, expired/revoked token or wrong organization fails closed.
Error responses never include upstream output or exception text. A current
engine connection is consulted on every operational request, including cookie
requests; a successful sign-in is not a cached membership grant.

The public upstream health response does not establish deployment revision, and
its tenant-domain lookup does not authenticate a user. The direct library
adapter avoids treating either response as identity evidence. Upstream provider
login callbacks remain outside this shell. The public landing page honestly
states that interactive sign-in provisioning is not available in this preview.

## Configuration and storage

Required runtime configuration:

- `RAP_ORIGIN`: exact HTTPS origin, for example `https://rap.example.test`, with
  no path, query, fragment or credential. Host and Origin must match it.
- `RAP_DATABASE`: absolute path in an operator-created private durable directory.
  SQLite contains tenant IDs and private settings; grant access only to the app.
- `RAP_ENGINE_CHECKOUT`: trusted, clean engine checkout at the pinned revision.
  Omitting it keeps readiness false and protected operations unavailable.
- The engine's normal database environment, supplied through the deployment's
  secret store. No additional paid account or service is provisioned here.

Instantiate `rapbattle.runtime.create_from_environment()` from a TLS-capable WSGI
host. Set `wsgi.url_scheme` only through the trusted server/TLS terminator; the
app deliberately ignores browser-supplied forwarded-host/protocol headers.
`python -m rapbattle.runtime` is a loopback-only liveness development server,
not a production host or a TLS proxy. Production deployment remains unverified.

League provisioning is an operator operation, not a public API. Use
`Store.add_league(slug, engine_organization_id, name, timezone)` against the
private settings database after confirming the existing upstream organization.
It grants no upstream membership or role. Slugs and organization mappings are
unique and cannot be changed by the settings API. The file-backed schema is
versioned; newer unsupported versions fail startup instead of being downgraded.

## Routes and session boundary

| Route | Behavior |
| --- | --- |
| `GET /healthz` | Process liveness only; no tenant data or connection details. |
| `GET /readyz` | 200 only when settings storage and pinned engine store respond; otherwise 503. |
| `GET /` | Public product shell; no league names or operational metrics. |
| `GET /leagues/{slug}` | Responsive, escaped private shell; requires upstream scoped read authorization. |
| `GET /api/leagues/{slug}/settings` | Returns the authorized league's name/timezone/version. |
| `PUT /api/leagues/{slug}/settings` | Requires `tenant.manage`, matching Origin and exact positive current version. |
| `POST /api/session` | Requires an existing engine bearer header plus JSON league slug; sets a secure cookie after scoped authorization. |
| `DELETE /api/session` | Matching-Origin local cookie removal; does not claim global upstream token revocation. |

The session cookie is `__Host-rap-session`, Secure, HttpOnly, SameSite=Strict,
Path=/ and limited to 15 minutes. Raw bearer tokens are never persisted in the
downstream database. A header credential takes precedence over cookies. The
bootstrap route requires an explicit header and cannot silently exchange a
cookie. All mutating methods require the exact configured Origin. Browser JSON
requests are bounded to 4096 bytes and cannot update organization or slug.
Settings writes include organization, slug and version in one atomic SQL update;
concurrent stale writes return 409 without losing a successful update.

Private responses use no-store, CSP, anti-framing and no-referrer headers.
The shell performs no provider calls, charging or publication. Synthetic fixture
leagues are labeled; no real promoter relationship or live battle is claimed.

## Verification and remaining acceptance

Run `sh scripts/check_application.sh`. It compiles Python, checks bridge syntax,
and runs credential-free unit, SQLite concurrency and real loopback HTTP tests.
The HTTP fixture uses an explicitly synthetic trusted TLS wrapper and engine
adapter. Tests cover independent NY/Atlanta/LA fixtures, cross-tenant access,
expired/revoked sessions, no role from membership alone, forged scope fields,
CSRF/Host/scheme rejection, persisted settings, concurrent updates, safe rendering,
bounded bodies, secure cookies and redacted upstream errors. The subprocess
negative test really executes the bridge against a nonexistent checkout and
confirms failure without credentials. Synthetic tests do not prove live engine
interoperability, real TLS hosting, production capacity or security certification.

Before RAP-01 operational acceptance, verify the pinned engine checkout with its
installed dependencies and a scoped test database, exercise the actual adapter
with an authorized test session and revoked/cross-organization sessions, and run
the application CI on the exact PR head. Production sign-in, hosting and live
credentials are not invented from a passing fixture. The draft PR must retain
these limits until its integration evidence is observed.
