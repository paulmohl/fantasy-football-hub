import { createHandler } from './handler.js'

const handle = createHandler({
  chrome,
  allowedOrigins: ['http://localhost:5173', 'https://predictfantasyfootball.com'],
})

chrome.runtime.onMessageExternal.addListener((message, sender, sendResponse) => {
  handle(message, sender).then(sendResponse)
  return true
})
