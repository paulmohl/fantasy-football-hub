import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useLeagueStore } from '@/store/league'
import { LeagueSwitcher } from '@/components/LeagueSwitcher'
import { LineupCard } from '@/components/LineupCard'
import { StandingsCard } from '@/components/StandingsCard'
import { WaiverCard, WaiverPlayer } from '@/components/WaiverCard'
import { AddPlayerDialog } from '@/components/AddPlayerDialog'
import { PlayerDetailDrawer, PlayerSlotData } from '@/components/PlayerDetailDrawer'

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

interface LineupSlot {
  slot: string
  player_id: string | null
  full_name: string | null
  position: string | null
  projected_points: number
  confidence: number
  injury_status: string | null
  is_out: boolean
  replacement_suggestion: string | null
  is_swap_suggested: boolean
  weather: { wind_mph: number; precipitation_mm?: number; weather_code?: number; snowfall_mm?: number; has_chip: boolean } | null
  matchup_grade?: string | null
  opponent_rank_vs_position?: number | null
  recent_usage_trend?: string | null
  team?: string | null
}

interface LineupData {
  optimal_lineup: LineupSlot[]
  season_type: string
}

export default function TeamPage() {
  const { activeLeagueId, setActiveLeague } = useLeagueStore()
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerSlotData | null>(null)
  const [addPlayer, setAddPlayer] = useState<AddPlayerState | null>(null)

  const { data: leagueList, isLoading } = useQuery<{
    leagues: Array<{ league_id: string; team_name: string | null }>
  }>({
    queryKey: ['my-team-leagues'],
    queryFn: () => api.get('/team/my').then((r) => r.data),
  })

  // The switcher hides itself with one league, so nothing else would ever pick it.
  useEffect(() => {
    const ids = leagueList?.leagues.map((l) => l.league_id) ?? []
    if (ids.length > 0 && (!activeLeagueId || !ids.includes(activeLeagueId))) setActiveLeague(ids[0])
  }, [leagueList, activeLeagueId, setActiveLeague])

  const teamName = leagueList?.leagues.find((l) => l.league_id === activeLeagueId)?.team_name

  const { data: lineupData } = useQuery<LineupData>({
    queryKey: ['team-lineup', activeLeagueId],
    queryFn: () => api.get('/team/lineup', { params: { league_id: activeLeagueId } }).then((r) => r.data),
    enabled: !!activeLeagueId,
    staleTime: 5 * 60 * 1000,
  })

  const comparePool: PlayerSlotData[] = (lineupData?.optimal_lineup ?? [])
    .filter((s): s is LineupSlot & { player_id: string } => !!s.player_id)
    .map((s) => ({
      player_id: s.player_id,
      full_name: s.full_name,
      position: s.position,
      injury_status: s.injury_status,
      projected_points: s.projected_points,
      confidence: s.confidence,
      matchup_grade: s.matchup_grade,
      opponent_rank_vs_position: s.opponent_rank_vs_position,
      recent_usage_trend: s.recent_usage_trend,
      weather: s.weather
        ? {
            wind_mph: s.weather.wind_mph,
            precipitation_mm: s.weather.precipitation_mm ?? 0,
            weather_code: s.weather.weather_code ?? 0,
            snowfall_mm: s.weather.snowfall_mm ?? 0,
            has_chip: s.weather.has_chip,
          }
        : null,
      team: s.team,
      is_out: s.is_out,
      replacement_suggestion: s.replacement_suggestion,
    }))

  return (
    <div className="px-4 pt-10 pb-4 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-base font-semibold text-text">
            {teamName ?? 'Team Manager'}
          </h1>
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
          <LineupCard
            onPlayerClick={(slot) => {
              if (!slot.player_id) return
              setSelectedPlayer({
                player_id: slot.player_id,
                full_name: slot.full_name,
                position: slot.position,
                injury_status: slot.injury_status,
                projected_points: slot.projected_points,
                confidence: slot.confidence,
                is_out: slot.is_out,
                replacement_suggestion: slot.replacement_suggestion,
                weather: slot.weather
                  ? {
                      wind_mph: slot.weather.wind_mph,
                      precipitation_mm: (slot.weather as { precipitation_mm?: number }).precipitation_mm ?? 0,
                      weather_code: (slot.weather as { weather_code?: number }).weather_code ?? 0,
                      snowfall_mm: (slot.weather as { snowfall_mm?: number }).snowfall_mm ?? 0,
                      has_chip: slot.weather.has_chip,
                    }
                  : null,
              })
            }}
          />

          <WaiverCard
            onAddPlayer={(player, waiverType, dropCandidates, faabBid) =>
              setAddPlayer({ player, waiverType, dropCandidates, faabBid })
            }
          />

          <StandingsCard />
        </div>
      )}

      <PlayerDetailDrawer
        player={selectedPlayer}
        onClose={() => setSelectedPlayer(null)}
        seasonType={lineupData?.season_type}
        activeLeagueId={activeLeagueId}
        comparePool={comparePool}
      />

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
