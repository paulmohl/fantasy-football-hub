/**
 * Socket.IO client for /draft namespace.
 *
 * CRITICAL (04-RESEARCH Pitfall 5): socket.io-client connects to /draft NAMESPACE
 * at /ws PATH. These are separate concepts:
 *   path: '/ws'       — the HTTP upgrade endpoint configured in server's ASGIApp
 *   namespace: /draft — the namespace registered via sio.register_namespace
 *
 * Usage:
 *   const socket = connectDraftSocket({ token, draft_id })
 *   socket.on('pick_confirmed', (data) => ...)
 */
import { io, Socket } from 'socket.io-client'

let _socket: Socket | null = null

export interface DraftSocketAuth {
  token: string
  draft_id: string
}

export function connectDraftSocket(auth: DraftSocketAuth): Socket {
  if (_socket?.connected) {
    _socket.disconnect()
  }

  const baseUrl = import.meta.env.VITE_API_URL ?? ''

  _socket = io(`${baseUrl}/draft`, {
    path: '/ws',
    auth,
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    transports: ['websocket', 'polling'],
  })

  return _socket
}

export function getDraftSocket(): Socket | null {
  return _socket
}

export function disconnectDraftSocket(): void {
  if (_socket) {
    _socket.disconnect()
    _socket = null
  }
}
