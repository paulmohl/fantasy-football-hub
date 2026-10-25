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

function send(message: unknown, timeoutMs?: number): Promise<{ reply: Reply; failed: boolean }> {
  return new Promise((resolve) => {
    let done = false
    const finish = (value: { reply: Reply; failed: boolean }) => {
      if (done) return
      done = true
      resolve(value)
    }
    if (timeoutMs) setTimeout(() => finish({ reply: undefined, failed: true }), timeoutMs)
    chrome.runtime.sendMessage(
      import.meta.env.VITE_ESPN_EXTENSION_ID as string,
      message,
      (reply: Reply) => finish({ reply, failed: !!chrome.runtime.lastError }),
    )
  })
}

export async function isInstalled(): Promise<boolean> {
  if (!hasRuntime()) return false
  const { reply, failed } = await send({ type: 'ping' }, PING_TIMEOUT_MS)
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
