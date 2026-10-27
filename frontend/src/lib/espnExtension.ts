export type EspnExtensionErrorCode =
  | 'not_installed'
  | 'denied'
  | 'not_signed_in'
  | 'busy'
  | 'unreachable'

export class EspnExtensionError extends Error {
  constructor(public code: EspnExtensionErrorCode) {
    super(code)
    this.name = 'EspnExtensionError'
  }
}

export interface EspnCookies {
  swid: string
  espn_s2: string
}

const PING_TIMEOUT_MS = 2000

type Reply = Record<string, unknown> | undefined

function hasRuntime(): boolean {
  try {
    return typeof chrome !== 'undefined' && !!chrome.runtime?.sendMessage
  } catch {
    // Another extension can wrap `chrome` in a proxy that throws on property reads; let send() try for real.
    return true
  }
}

let lastProbeDetail = ''
let route: 'bridge' | 'direct' = 'direct'

const BRIDGE_TIMEOUT_MS = 1500

export function resetExtensionRoute(): void {
  route = 'direct'
}

// The extension's content script relays these to the background; it runs in an isolated world, so other
// extensions that wrap the page's `chrome` object cannot break it.
function bridgeSend(message: unknown, timeoutMs?: number): Promise<Reply> {
  return new Promise((resolve) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    const onMessage = (event: MessageEvent) => {
      const data = event.data
      if (event.origin !== window.location.origin) return
      if (!data || data.source !== 'fantasy-hub-extension' || data.id !== id) return
      cleanup()
      resolve(data.reply as Reply)
    }
    const timer = timeoutMs
      ? setTimeout(() => {
          cleanup()
          resolve(undefined)
        }, timeoutMs)
      : undefined
    const cleanup = () => {
      window.removeEventListener('message', onMessage)
      if (timer) clearTimeout(timer)
    }
    window.addEventListener('message', onMessage)
    window.postMessage({ source: 'fantasy-hub-page', id, message }, window.location.origin)
  })
}

async function dispatch(message: unknown, timeoutMs?: number): Promise<{ reply: Reply; failed: boolean; error?: string }> {
  if (route === 'bridge') {
    const reply = await bridgeSend(message, timeoutMs)
    return { reply, failed: !reply, error: reply ? undefined : 'no response from relay' }
  }
  return send(message, timeoutMs)
}

export function getProbeDetail(): string {
  return lastProbeDetail
}

function send(message: unknown, timeoutMs?: number): Promise<{ reply: Reply; failed: boolean; error?: string }> {
  return new Promise((resolve) => {
    let done = false
    const finish = (value: { reply: Reply; failed: boolean; error?: string }) => {
      if (done) return
      done = true
      resolve(value)
    }
    if (timeoutMs) setTimeout(() => finish({ reply: undefined, failed: true, error: 'no response within timeout' }), timeoutMs)
    try {
      chrome.runtime.sendMessage(
        import.meta.env.VITE_ESPN_EXTENSION_ID as string,
        message,
        (reply: Reply) => {
          const lastError = chrome.runtime.lastError
          finish({ reply, failed: !!lastError, error: lastError?.message })
        },
      )
    } catch (err) {
      finish({ reply: undefined, failed: true, error: `threw: ${(err as Error)?.message ?? String(err)}` })
    }
  })
}

export async function isInstalled(): Promise<boolean> {
  try {
    return await probe()
  } catch (err) {
    lastProbeDetail = `threw: ${(err as Error)?.message ?? String(err)}`
    return false
  }
}

async function probe(): Promise<boolean> {
  const extensionId = import.meta.env.VITE_ESPN_EXTENSION_ID as string
  const viaBridge = await bridgeSend({ type: 'ping' }, BRIDGE_TIMEOUT_MS)
  if (viaBridge?.installed === true) {
    route = 'bridge'
    lastProbeDetail = `relay reply: ${JSON.stringify(viaBridge)}`
    return true
  }
  route = 'direct'
  const bridgeNote = 'relay: no response'
  if (!hasRuntime()) {
    lastProbeDetail = `${bridgeNote}; chrome.runtime.sendMessage is not available in this browser (id ${extensionId})`
    return false
  }
  const { reply, failed, error } = await send({ type: 'ping' }, PING_TIMEOUT_MS)
  lastProbeDetail = failed
    ? `${bridgeNote}; Chrome error: ${error} (id ${extensionId})`
    : `${bridgeNote}; reply: ${JSON.stringify(reply)} (id ${extensionId})`
  return !failed && reply?.installed === true
}

export async function requestCookies(): Promise<EspnCookies> {
  if (route === 'direct' && !hasRuntime()) throw new EspnExtensionError('not_installed')
  const { reply, failed } = await dispatch({ type: 'espn.connect' })
  if (failed || !reply) throw new EspnExtensionError('unreachable')
  const error = reply.error
  if (error === 'denied' || error === 'not_signed_in' || error === 'busy') {
    throw new EspnExtensionError(error)
  }
  if (typeof reply.swid !== 'string' || typeof reply.espn_s2 !== 'string') {
    throw new EspnExtensionError('unreachable')
  }
  return { swid: reply.swid, espn_s2: reply.espn_s2 }
}
