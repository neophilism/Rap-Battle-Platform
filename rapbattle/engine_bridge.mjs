// Reuse the exact reviewed upstream auth implementation. Credentials arrive via
// stdin, never command arguments, files or diagnostics. No session is issued.
import {execFileSync} from 'node:child_process';
import {readFileSync, realpathSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const revision = '3a316219da1b97cffd2faed1e99967a1fb8c6362';
let output;
try {
  const root = realpathSync(process.argv[2]);
  const git = (...args) => execFileSync('git', ['-C', root, ...args], {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 2000
  }).trim();
  if (git('rev-parse', 'HEAD') !== revision || git('status', '--porcelain', '--untracked-files=no')) {
    throw new Error('Unverified engine checkout');
  }
  const input = readFileSync(0, 'utf8');
  if (input.length > 4096) throw new Error('Input too large');
  const request = JSON.parse(input);
  const {AuthenticationService} = await import(pathToFileURL(resolve(root, 'packages/auth/src/index.ts')));
  const {createPostgresAuthStore} = await import(pathToFileURL(resolve(root, 'packages/db/src/auth-store.ts')));
  const store = createPostgresAuthStore();
  const service = new AuthenticationService(store);
  if (request.operation === 'ready') {
    // Exercise the configured store with a noncredential hash, without issuing a session.
    await store.findSession('0'.repeat(64));
    output = {revision, ready: true};
  } else if (request.operation === 'authorize' &&
      ['content.view_private', 'tenant.manage'].includes(request.action) &&
      typeof request.organizationId === 'string' && request.organizationId.length > 0 &&
      request.organizationId.length <= 128 &&
      typeof request.authorization === 'string' && /^Bearer [A-Za-z0-9_-]{43}$/.test(request.authorization)) {
    try {
      const principal = await service.authorizeAction(request.authorization, request.action, {
        organizationId: request.organizationId
      });
      output = {revision, principal: {accountId: principal.accountId,
        sessionId: principal.sessionId, organizationId: principal.organizationId}};
    } catch (error) {
      if (!['missing', 'invalid', 'expired', 'revoked', 'forbidden'].includes(error.code)) throw error;
      output = {revision, error: error.code};
    }
  } else throw new Error('Unsupported request');
} catch {
  // The parent only receives a fixed diagnostic. Never serialize an exception,
  // database connection string, token, SQL or upstream package output.
  process.stderr.write('Engine verification unavailable\n');
  process.exit(1);
}
process.stdout.write(JSON.stringify(output));
// The upstream SQL pool may hold event-loop handles after this one-shot request.
process.exit(0);
