import { useState } from 'react'
import { api } from '@/lib/api'
import { useToast } from './Toast'
import { HealthDot } from './HealthDot'
import { ProgressBar } from './ProgressBar'
import { DisconnectModal } from './DisconnectModal'

interface League {
  id: string
  name: string
  season: string
  host_platform: string
  draft_type: string | null
  keeper_flag: boolean
  dynasty_flag: boolean
  last_synced_at: string | null
  connected_at: string
}

interface ConnectionCardProps {
  league: League
  onDisconnected: (id: string) => void
}

function timeAgo(iso: string | null): string {
  if (!iso) return 'never'
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`
  return `${Math.floor(diff / 86400)} days ago`
}

export function ConnectionCard({ league, onDisconnected }: ConnectionCardProps) {
  const { toast } = useToast()
  const [refreshing, setRefreshing] = useState(false)
  const [showRefreshBar, setShowRefreshBar] = useState(false)
  const [refreshDone, setRefreshDone] = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)
  const [showModal, setShowModal] = useState(false)

  async function handleRefresh() {
    setRefreshing(true)
    const timer = setTimeout(() => setShowRefreshBar(true), 3000)
    try {
      await api.post(`/leagues/${league.id}/refresh`)
      clearTimeout(timer)
      setShowRefreshBar(false)
      setRefreshDone(true)
      setTimeout(() => setRefreshDone(false), 2000)
      toast('League data refreshed.')
    } catch {
      clearTimeout(timer)
      setShowRefreshBar(false)
      toast('Sync timed out. Sleeper may be slow — try again in a moment.', 'error', true)
    } finally {
      setRefreshing(false)
    }
  }

  async function handleDisconnect() {
    setDisconnecting(true)
    try {
      await api.delete(`/leagues/${league.id}/connection`)
      setShowModal(false)
      toast(`${league.name} disconnected.`)
      onDisconnected(league.id)
    } catch {
      toast('Failed to disconnect. Please try again.', 'error')
    } finally {
      setDisconnecting(false)
    }
  }

  const formatLabel = league.dynasty_flag ? 'Dynasty' : league.keeper_flag ? 'Keeper' : 'Redraft'

  return (
    <>
      <div className="bg-surface border border-border rounded-xl p-4 flex flex-col gap-3">
        {showRefreshBar && <ProgressBar pulsing className="mb-1" />}

        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-text flex-1">{league.name}</span>
          <span className="text-xs font-semibold bg-raised px-2 py-0.5 rounded text-muted capitalize">
            {league.host_platform}
          </span>
        </div>

        <p className="text-xs text-muted">
          {league.draft_type ?? 'snake'} · {formatLabel} · {league.season} · Synced{' '}
          <span className="font-mono">{timeAgo(league.last_synced_at)}</span>
        </p>

        <HealthDot status="healthy" />

        <div className="flex gap-4 justify-end">
          {refreshing ? (
            <span className="text-sm text-muted">Refreshing…</span>
          ) : refreshDone ? (
            <span className="text-sm text-success">Updated</span>
          ) : (
            <button onClick={handleRefresh} className="text-sm text-accent hover:underline">
              Refresh now
            </button>
          )}
          <button
            onClick={() => setShowModal(true)}
            className="text-sm text-danger hover:underline"
          >
            Disconnect
          </button>
        </div>
      </div>

      <DisconnectModal
        leagueName={league.name}
        open={showModal}
        onOpenChange={setShowModal}
        onConfirm={handleDisconnect}
        loading={disconnecting}
      />
    </>
  )
}
