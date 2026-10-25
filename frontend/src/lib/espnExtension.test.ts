import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { EspnExtensionError, isInstalled, requestCookies } from './espnExtension'

type Reply = Record<string, unknown> | undefined

function stubChrome(reply: Reply, lastError?: string) {
  const sendMessage = vi.fn((_id: string, _msg: unknown, cb: (r: Reply) => void) => {
    (globalThis as any).chrome.runtime.lastError = lastError ? { message: lastError } : undefined
    cb(reply)
  })
  ;(globalThis as any).chrome = { runtime: { sendMessage, lastError: undefined } }
  return sendMessage
}

beforeEach(() => {
  vi.stubEnv('VITE_ESPN_EXTENSION_ID', 'abcdefghijklmnopabcdefghijklmnop')
})

afterEach(() => {
  delete (globalThis as any).chrome
  vi.unstubAllEnvs()
})

describe('isInstalled', () => {
  it('is true when the extension answers ping', async () => {
    const send = stubChrome({ installed: true, version: '1.0.0' })
    expect(await isInstalled()).toBe(true)
    expect(send.mock.calls[0][1]).toEqual({ type: 'ping' })
  })

  it('is false when chrome is undefined', async () => {
    expect(await isInstalled()).toBe(false)
  })

  it('is false when runtime.lastError is set', async () => {
    stubChrome(undefined, 'Could not establish connection')
    expect(await isInstalled()).toBe(false)
  })
})

describe('requestCookies', () => {
  it('resolves with cookies, passing espn_s2 through unmodified', async () => {
    stubChrome({ swid: '{ABC}', espn_s2: 'AE%2Bxyz%2Fq' })
    expect(await requestCookies()).toEqual({ swid: '{ABC}', espn_s2: 'AE%2Bxyz%2Fq' })
  })

  it.each(['denied', 'not_signed_in', 'busy'] as const)('maps %s from the reply', async (code) => {
    stubChrome({ error: code })
    await expect(requestCookies()).rejects.toMatchObject({ code })
  })

  it('rejects not_installed when chrome is undefined', async () => {
    await expect(requestCookies()).rejects.toMatchObject({ code: 'not_installed' })
  })

  it('rejects unreachable when lastError is set', async () => {
    stubChrome(undefined, 'The message port closed')
    const err = await requestCookies().catch((e) => e)
    expect(err).toBeInstanceOf(EspnExtensionError)
    expect(err.code).toBe('unreachable')
  })
})
