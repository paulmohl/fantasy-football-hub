// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { EspnExtensionError, isInstalled, requestCookies, resetExtensionRoute } from './espnExtension'

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
  resetExtensionRoute()
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

describe('getProbeDetail', () => {
  it('reports the Chrome error after a failed ping', async () => {
    const { getProbeDetail } = await import('./espnExtension')
    ;(globalThis as any).chrome = {
      runtime: {
        lastError: { message: 'Could not establish connection. Receiving end does not exist.' },
        sendMessage: (_id: string, _m: unknown, cb: (r?: unknown) => void) => cb(undefined),
      },
    }
    expect(await isInstalled()).toBe(false)
    expect(getProbeDetail()).toContain('Receiving end does not exist')
  })
})

describe('isInstalled when sendMessage throws', () => {
  it('resolves false and records the thrown message', async () => {
    const { getProbeDetail } = await import('./espnExtension')
    ;(globalThis as any).chrome = {
      runtime: {
        sendMessage: () => {
          throw new Error('Invalid extension id')
        },
      },
    }
    expect(await isInstalled()).toBe(false)
    expect(getProbeDetail()).toContain('threw: Invalid extension id')
  })
})

describe('isInstalled when chrome.runtime reads throw', () => {
  it('still resolves and records the throw', async () => {
    const { getProbeDetail } = await import('./espnExtension')
    ;(globalThis as any).chrome = {
      get runtime() {
        throw new TypeError('Cannot convert a Symbol value to a string')
      },
    }
    expect(await isInstalled()).toBe(false)
    expect(getProbeDetail()).toContain('Symbol value')
  })
})

describe('relay through the extension content script', () => {
  function installRelay(reply: unknown) {
    const handler = (event: MessageEvent) => {
      if (event.data?.source !== 'fantasy-hub-page') return
      // jsdom reports an empty origin for postMessage, unlike browsers, so build the event explicitly.
      window.dispatchEvent(
        new MessageEvent('message', {
          data: { source: 'fantasy-hub-extension', id: event.data.id, reply },
          origin: window.location.origin,
        }),
      )
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }

  it('detects the extension and gets cookies even when chrome.runtime.sendMessage throws', async () => {
    ;(globalThis as any).chrome = {
      runtime: {
        sendMessage: () => {
          throw new Error('Cannot convert a Symbol value to a string')
        },
      },
    }
    const stop = installRelay({ installed: true, version: '1.1.0' })
    expect(await isInstalled()).toBe(true)
    stop()
    const stop2 = installRelay({ swid: '{A}', espn_s2: 'B%2Bc' })
    expect(await requestCookies()).toEqual({ swid: '{A}', espn_s2: 'B%2Bc' })
    stop2()
  })

  it('maps relay errors to EspnExtensionError', async () => {
    const stop = installRelay({ installed: true })
    await isInstalled()
    stop()
    const stop2 = installRelay({ error: 'denied' })
    await expect(requestCookies()).rejects.toMatchObject({ code: 'denied' })
    stop2()
  })
})
