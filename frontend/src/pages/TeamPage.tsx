import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useLeagueStore } from '@/store/league'
import { LeagueSwitcher } from '@/components/LeagueSwitcher'
import { LineupCard } from '@/components/LineupCard'
import { StandingsCard } from '@/components/StandingsCard'
import { WaiverCard, WaiverPlayer } from '@/components/WaiverCard'
import { AddPlayerDialog } from '@/components/AddPlayerDialog'

interface Player {
  player_id: string
  full_name: string
  position: string
  team: string
  projected_points: number
  status?: string
}

interface RosterSlot {
  slot_type: string
  display: string
  player: Player | null
}

interface TeamData {
  team_name: string
  owner_name: string
  record: string
  points_for: number
  waiver_position: number
  roster: RosterSlot[]
  leagues?: Array<{ league_id: string; name: string; season: string; platform: string }>
}

function StatusDot({ status }: { status?: string }) {
  if (!status || status === 'Active') return null
  const color = status === 'Out' ? 'bg-danger' : status === 'Questionable' ? 'bg-warning' : 'bg-muted'
  return (
    <span className={`inline-block w-2 h-2 rounded-full ${color} ml-1.5`} title={status} />
  )
}

export function PlayerCard({ slot }: { slot: RosterSlot }) {
  return (
    <div className="bg-surface border border-border rounded-xl p-3 flex items-center gap-3">
      <div className="shrink-0 w-8 h-8 rounded-lg bg-raised flex items-center justify-center">
        <span className="text-[10px] font-bold text-muted">{slot.slot_type}</span>
      </div>
      {slot.player ? (
        <>
          <div className="flex-1 min-w-0">
            <div className="flex items-center">
              <span className="font-semibold text-text text-sm truncate">{slot.player.full_name}</span>
              <StatusDot status={slot.player.status} />
            </div>
            <p className="text-xs text-muted">{slot.player.position} · {slot.player.team}</p>
          </div>
          <div className="shrink-0 text-right">
            <p className="text-sm font-semibold text-accent">{slot.player.projected_points.toFixed(1)}</p>
            <p className="text-[10px] text-muted">proj</p>
          </div>
        </>
      ) : (
        <div className="flex-1">
          <p className="text-sm text-muted italic">{slot.display} — Empty</p>
        </div>
      )}
    </div>
  )
}

interface DropCandidate {
  player_id: string
  full_name: string
  position: string
  ros_value: number
  injury_status: string | null
}

interface FaabBid {
  mid_bid: number
  confidence_range: number
  min_bid: number
  max_bid: number
}

interface AddPlayerState {
  player: WaiverPlayer
  waiverType: 'faab' | 'rolling'
  dropCandidates: DropCandidate[]
  faabBid: FaabBid | null
}

export default function TeamPage() {
  const { activeLeagueId } = useLeagueStore()
  const [selectedPlayer, setSelectedPlayer] = useState<unknown>(null)
  const [addPlayer, setAddPlayer] = useState<AddPlayerState | null>(null)

  const { data, isLoading } = useQuery<TeamData>({
    queryKey: ['my-team', activeLeagueId],
    queryFn: () => api.get('/team/my').then((r) => r.data),
    enabled: !!activeLeagueId,
  })

  return (
    <div className="px-4 pt-10 pb-4 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-base font-semibold text-text">
            {data?.team_name ?? 'Team Manager'}
          </h1>
          {data?.record && (
            <p className="text-xs text-muted mt-0.5">
              {data.record} · <span className="font-mono">{data.points_for ?? 0}</span> pts
            </p>
          )}
        </div>
        <LeagueSwitcher />
      </div>

      {!activeLeagueId && (
        <div className="bg-surface border border-border rounded-xl p-6 text-center">
          <p className="text-sm font-semibold text-text">Select a league</p>
          <p className="text-xs text-muted mt-1">Choose a league from the dropdown to see your team.</p>
        </div>
      )}

      {activeLeagueId && isLoading && (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-32 animate-pulse bg-raised rounded-xl" />
          ))}
        </div>
      )}

      {activeLeagueId && !isLoading && (
        <div className="space-y-3">
          <LineupCard onPlayerClick={setSelectedPlayer} />

          <WaiverCard
            onAddPlayer={(player, waiverType, dropCandidates, faabBid) =>
              setAddPlayer({ player, waiverType, dropCandidates, faabBid })
            }
          />

          <StandingsCard />
        </div>
      )}

      {/* PlayerDetailDrawer — wired in Plan 11 */}
      {selectedPlayer && (
        <div />
      )}

      <AddPlayerDialog
        open={!!addPlayer}
        onClose={() => setAddPlayer(null)}
        playerName={addPlayer?.player.full_name ?? ''}
        waiverType={addPlayer?.waiverType ?? 'rolling'}
        dropCandidates={addPlayer?.dropCandidates ?? []}
        faabBid={addPlayer?.faabBid ?? null}
      />
    </div>
  )
}
