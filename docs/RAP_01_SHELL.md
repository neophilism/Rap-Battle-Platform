# RAP-01 implementation status

The separate application remains incomplete. This branch currently contains a
dependency-binding module and tests; it has no authenticated league routes,
persistent sessions, deployed health endpoint or product CI evidence.

The reviewed upstream source is Live-Competition-Engine commit
`3a316219da1b97cffd2faed1e99967a1fb8c6362`. `EngineBinding` requires this exact
revision and a server-configured HTTPS origin without credentials or URL paths.
It does not fetch URLs or validate identity. Its readiness result is only an
internal calculation over trusted adapter observations, never an attestation.

At this upstream revision, `apps/web/src/app/api/health/route.ts` returns service
health and a timestamp, without the deployed revision. The
`apps/web/src/app/api/tenant-context/handler.ts` route resolves a domain over HTTPS;
it does not establish an authenticated user session. Neither response can
independently prove readiness. Missing revision/session evidence stays pending.

Run `python -m unittest discover -s tests -v` for the isolated binding tests.
These cover origin rejection, exact revision binding and missing prerequisites.
They do not prove live upstream interoperability or tenant authorization.

Next implementation must connect a verified upstream session adapter, enforce
tenant membership on every scoped route, provide health/readiness endpoints and
exercise three independent fictional league fixtures. Do not accept a browser
supplied tenant, revision or session-verification flag as trusted evidence.
