import { createHandler } from './handler.js'

const handle = createHandler({
  chrome,
  allowedOrigins: ['http://localhost:5173', 'https://predictfantasyfootball.com'],
})

chrome.runtime.onMessageExternal.addListener((message, sender, sendResponse) => {
  handle(message, sender).then(sendResponse)
  return true
})

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message?.relay || sender.id !== chrome.runtime.id || !sender.tab) return false
  handle(message.message, sender).then(sendResponse)
  return true
})
