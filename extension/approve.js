const origin = new URLSearchParams(location.search).get('origin') ?? ''
document.getElementById('origin').textContent = origin

function decide(allow) {
  chrome.runtime.sendMessage({ type: 'approval', allow }, () => window.close())
}

document.getElementById('allow').addEventListener('click', () => decide(true))
document.getElementById('deny').addEventListener('click', () => decide(false))
