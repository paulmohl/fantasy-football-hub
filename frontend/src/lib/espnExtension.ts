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
  return typeof chrome !== 'undefined' && !!chrome.runtime?.sendMessage
}

let lastProbeDetail = ''

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
  const extensionId = import.meta.env.VITE_ESPN_EXTENSION_ID as string
  if (!hasRuntime()) {
    lastProbeDetail = `chrome.runtime.sendMessage is not available in this browser (id ${extensionId})`
    return false
  }
  const { reply, failed, error } = await send({ type: 'ping' }, PING_TIMEOUT_MS)
  lastProbeDetail = failed
    ? `Chrome error: ${error} (id ${extensionId})`
    : `reply: ${JSON.stringify(reply)} (id ${extensionId})`
  return !failed && reply?.installed === true
}

export async function requestCookies(): Promise<EspnCookies> {
  if (!hasRuntime()) throw new EspnExtensionError('not_installed')
  const { reply, failed } = await send({ type: 'espn.connect' })
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
