import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createHandler } from '../handler.js'

const ORIGIN = 'https://predictfantasyfootball.com'
const SENDER = { origin: ORIGIN }

function fakeChrome({ cookies = {}, decision = 'allow' } = {}) {
  const created = []
  const listeners = { removed: [], message: [] }
  const chrome = {
    runtime: {
      getManifest: () => ({ version: '1.2.3' }),
      onMessage: { addListener: (fn) => listeners.message.push(fn) },
      getURL: (p) => `chrome-extension://id/${p}`,
    },
    cookies: {
      get: async ({ name }) => (cookies[name] ? { name, value: cookies[name] } : null),
    },
    tabs: { create: async (o) => created.push(o) },
    windows: {
      onRemoved: { addListener: (fn) => listeners.removed.push(fn) },
      create: async () => {
        setTimeout(() => {
          if (decision === 'allow' || decision === 'deny') {
            listeners.message.forEach((fn) => fn({ type: 'approval', allow: decision === 'allow' }, {}))
          } else if (decision === 'close') {
            listeners.removed.forEach((fn) => fn(42))
          }
        }, 0)
        return { id: 42 }
      },
    },
  }
  return { chrome, created }
}

const handler = (opts) => {
  const f = fakeChrome(opts)
  return { ...f, handle: createHandler({ chrome: f.chrome, allowedOrigins: [ORIGIN] }) }
}

test('ping reports installed and version', async () => {
  const { handle } = handler()
  assert.deepEqual(await handle({ type: 'ping' }, SENDER), { installed: true, version: '1.2.3' })
})

test('allow with both cookies returns them unmodified', async () => {
  const { handle } = handler({ cookies: { SWID: '{ABC}', espn_s2: 'AE%2Bxyz%2Fq' } })
  assert.deepEqual(await handle({ type: 'espn.connect' }, SENDER), { swid: '{ABC}', espn_s2: 'AE%2Bxyz%2Fq' })
})

test('deny returns denied', async () => {
  const { handle } = handler({ cookies: { SWID: 'a', espn_s2: 'b' }, decision: 'deny' })
  assert.deepEqual(await handle({ type: 'espn.connect' }, SENDER), { error: 'denied' })
})

test('closing the popup without choosing returns denied', async () => {
  const { handle } = handler({ cookies: { SWID: 'a', espn_s2: 'b' }, decision: 'close' })
  assert.deepEqual(await handle({ type: 'espn.connect' }, SENDER), { error: 'denied' })
})

test('missing espn_s2 returns not_signed_in and opens ESPN login', async () => {
  const { handle, created } = handler({ cookies: { SWID: 'a' } })
  assert.deepEqual(await handle({ type: 'espn.connect' }, SENDER), { error: 'not_signed_in' })
  assert.equal(created.length, 1)
  assert.match(created[0].url, /espn\.com/)
})

test('second concurrent connect returns busy', async () => {
  const { handle } = handler({ cookies: { SWID: 'a', espn_s2: 'b' } })
  const first = handle({ type: 'espn.connect' }, SENDER)
  assert.deepEqual(await handle({ type: 'espn.connect' }, SENDER), { error: 'busy' })
  assert.equal((await first).swid, 'a')
})

test('origin not allowlisted is forbidden', async () => {
  const { handle } = handler()
  assert.deepEqual(await handle({ type: 'ping' }, { origin: 'https://evil.example' }), { error: 'forbidden' })
})
