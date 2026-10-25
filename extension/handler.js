const ESPN_LOGIN_URL = 'https://www.espn.com/login'
const COOKIE_URL = 'https://www.espn.com'

export function createHandler({ chrome, allowedOrigins }) {
  let pending = false

  async function requestApproval(origin) {
    let windowId = null
    let settle
    const decided = new Promise((resolve) => {
      settle = resolve
    })
    const onMessage = (msg) => {
      if (msg?.type === 'approval') settle(Boolean(msg.allow))
    }
    const onRemoved = (id) => {
      if (id === windowId) settle(false)
    }
    chrome.runtime.onMessage.addListener(onMessage)
    chrome.windows.onRemoved.addListener(onRemoved)
    try {
      const url = chrome.runtime.getURL(`approve.html?origin=${encodeURIComponent(origin)}`)
      const win = await chrome.windows.create({ url, type: 'popup', width: 420, height: 320 })
      windowId = win.id
      return await decided
    } finally {
      chrome.runtime.onMessage.removeListener?.(onMessage)
      chrome.windows.onRemoved.removeListener?.(onRemoved)
    }
  }

  async function connect(origin) {
    if (pending) return { error: 'busy' }
    pending = true
    try {
      if (!(await requestApproval(origin))) return { error: 'denied' }
      const [swid, s2] = await Promise.all(
        ['SWID', 'espn_s2'].map((name) => chrome.cookies.get({ url: COOKIE_URL, name })),
      )
      if (!swid?.value || !s2?.value) {
        await chrome.tabs.create({ url: ESPN_LOGIN_URL })
        return { error: 'not_signed_in' }
      }
      return { swid: swid.value, espn_s2: s2.value }
    } finally {
      pending = false
    }
  }

  return async function handle(message, sender) {
    if (!allowedOrigins.includes(sender?.origin)) return { error: 'forbidden' }
    if (message?.type === 'ping') {
      return { installed: true, version: chrome.runtime.getManifest().version }
    }
    if (message?.type === 'espn.connect') return connect(sender.origin)
    return { error: 'unknown_message' }
  }
}
