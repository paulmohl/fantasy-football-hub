import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'

const source = readFileSync(new URL('../content.js', import.meta.url), 'utf8')
const ORIGIN = 'https://predictfantasyfootball.com'

function setup({ response, lastError } = {}) {
  const posted = []
  const sent = []
  const plain = (v) => JSON.parse(JSON.stringify(v))
  let listener
  const window = {
    location: { origin: ORIGIN },
    addEventListener: (_type, fn) => (listener = fn),
    postMessage: (data, target) => posted.push(plain({ data, target })),
  }
  const chrome = {
    runtime: {
      get lastError() {
        return lastError
      },
      sendMessage: (msg, cb) => {
        sent.push(plain(msg))
        cb(response)
      },
    },
  }
  vm.runInNewContext(source, { window, chrome })
  const dispatch = (data, overrides = {}) =>
    listener({ source: window, origin: ORIGIN, data, ...overrides })
  return { window, posted, sent, dispatch }
}

test('relays a page message to the background and posts the reply back with the same id', () => {
  const { posted, sent, dispatch } = setup({ response: { installed: true, version: '1.1.0' } })
  dispatch({ source: 'fantasy-hub-page', id: 'abc', message: { type: 'ping' } })
  assert.deepEqual(sent, [{ relay: true, message: { type: 'ping' } }])
  assert.deepEqual(posted, [
    { data: { source: 'fantasy-hub-extension', id: 'abc', reply: { installed: true, version: '1.1.0' } }, target: ORIGIN },
  ])
})

test('ignores messages from other origins, other sources, or without the page marker', () => {
  const { sent, dispatch, window } = setup({ response: {} })
  dispatch({ source: 'fantasy-hub-page', id: 'a', message: {} }, { origin: 'https://evil.example' })
  dispatch({ source: 'fantasy-hub-page', id: 'a', message: {} }, { source: {} })
  dispatch({ source: 'other', id: 'a', message: {} })
  dispatch({ source: 'fantasy-hub-page', message: {} })
  assert.equal(sent.length, 0)
  assert.ok(window)
})

test('reports unreachable when the background errors', () => {
  const { posted, dispatch } = setup({ response: undefined, lastError: { message: 'x' } })
  dispatch({ source: 'fantasy-hub-page', id: 'z', message: { type: 'ping' } })
  assert.deepEqual(posted[0].data.reply, { error: 'unreachable' })
})
