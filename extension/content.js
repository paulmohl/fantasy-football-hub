// Runs in the extension's isolated world, so other extensions that wrap the page's `chrome` object cannot break it.
;(() => {
  const PAGE = 'fantasy-hub-page'
  const EXTENSION = 'fantasy-hub-extension'

  window.addEventListener('message', (event) => {
    const data = event.data
    if (event.source !== window || event.origin !== window.location.origin) return
    if (!data || data.source !== PAGE || typeof data.id !== 'string') return

    const reply = (body) =>
      window.postMessage({ source: EXTENSION, id: data.id, reply: body }, window.location.origin)

    try {
      chrome.runtime.sendMessage({ relay: true, message: data.message }, (response) => {
        reply(chrome.runtime.lastError || !response ? { error: 'unreachable' } : response)
      })
    } catch {
      reply({ error: 'unreachable' })
    }
  })
})()
