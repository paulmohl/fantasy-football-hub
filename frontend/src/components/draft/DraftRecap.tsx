/**
 * DraftRecap — post-draft grades, value picks, reaches, full pick log (DR-14, D-13).
 *
 * Fetches GET /api/v1/drafts/{id}/recap when status=complete.
 * Supports image export via html2canvas (export button saves PNG).
 */
import { useEffect, useRef, useState } from 'react'
import html2canvas from 'html2canvas'
import { useDraftStore } from '@/store/draft'
import { api } from '@/lib/api'

interface GradeEntry {
  grade: string
  adp_avg_diff?: number
}

interface RecapPick {
  pick_num: number
  round: number
  player_id: string
  team_id: string
  is_auto_pick: boolean
}

interface RecapData {
  draft_id: string
  grades: Record<string, GradeEntry>
  picks: RecapPick[]
  value_picks: RecapPick[]
  reaches: RecapPick[]
}

function gradeColor(grade: string): string {
  if (grade.startsWith('A')) return 'text-emerald-400'
  if (grade.startsWith('B')) return 'text-accent'
  if (grade.startsWith('C')) return 'text-amber-400'
  return 'text-red-400'
}

export function DraftRecap() {
  const config = useDraftStore((s) => s.config)
  const availablePlayers = useDraftStore((s) => s.availablePlayers)
  const [recap, setRecap] = useState<RecapData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const captureRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!config?.draft_id) return
    api
      .get(`/drafts/${config.draft_id}/recap`)
      .then((res) => {
        setRecap(res.data)
        setLoading(false)
      })
      .catch(() => {
        setError('Failed to load recap')
        setLoading(false)
      })
  }, [config?.draft_id])

  const playerName = (playerId: string): string => {
    const p = availablePlayers.find((pl) => pl.player_id === playerId)
    return p?.name ?? playerId
  }

  const handleExport = async () => {
    if (!captureRef.current || exporting) return
    setExporting(true)
    try {
      const canvas = await html2canvas(captureRef.current, {
        backgroundColor: '#0d0d0d',
        scale: 2,
      })
      const link = document.createElement('a')
      link.download = 'draft-recap.png'
      link.href = canvas.toDataURL('image/png')
      link.click()
    } catch {
      // Export failed silently — not critical
    } finally {
      setExporting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-bg text-text-muted font-mono text-sm">
        LOADING RECAP...
      </div>
    )
  }

  if (error || !recap) {
    return (
      <div className="flex h-screen items-center justify-center bg-bg text-red-400 font-mono text-sm">
        {error ?? 'Recap unavailable'}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg text-text font-mono p-6" data-testid="draft-recap">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold tracking-wide">DRAFT RECAP</h1>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="bg-accent text-bg text-sm px-4 py-2 rounded hover:bg-accent-hover disabled:opacity-50 transition-colors"
          data-testid="export-recap-button"
        >
          {exporting ? 'Exporting...' : 'Export PNG'}
        </button>
      </div>

      <div ref={captureRef} className="bg-bg p-4 rounded-lg">

        <section className="mb-6">
          <h2 className="text-[10px] tracking-widest uppercase text-text-muted mb-3">Team Grades</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {Object.entries(recap.grades).map(([teamId, gradeData]) => (
              <div key={teamId} className="bg-surface border border-border rounded p-3 flex flex-col gap-1">
                <span className="text-[10px] text-text-muted truncate">{teamId.slice(0, 12)}</span>
                <span className={`text-2xl font-bold ${gradeColor(gradeData.grade)}`}>
                  {gradeData.grade}
                </span>
                {gradeData.adp_avg_diff !== undefined && (
                  <span className="text-[10px] text-text-muted">
                    ADP diff: {gradeData.adp_avg_diff > 0 ? '+' : ''}{gradeData.adp_avg_diff.toFixed(1)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>

        {recap.value_picks.length > 0 && (
          <section className="mb-6">
            <h2 className="text-[10px] tracking-widest uppercase text-text-muted mb-3">
              Value Picks ({recap.value_picks.length})
            </h2>
            <div className="flex flex-wrap gap-2">
              {recap.value_picks.map((p) => (
                <span key={p.pick_num} className="bg-surface border border-emerald-400/40 text-emerald-400 rounded px-2 py-1 text-xs">
                  #{p.pick_num} {playerName(p.player_id)}
                </span>
              ))}
            </div>
          </section>
        )}

        {recap.reaches.length > 0 && (
          <section className="mb-6">
            <h2 className="text-[10px] tracking-widest uppercase text-text-muted mb-3">
              Reaches ({recap.reaches.length})
            </h2>
            <div className="flex flex-wrap gap-2">
              {recap.reaches.map((p) => (
                <span key={p.pick_num} className="bg-surface border border-red-400/40 text-red-400 rounded px-2 py-1 text-xs">
                  #{p.pick_num} {playerName(p.player_id)}
                </span>
              ))}
            </div>
          </section>
        )}

        <section>
          <h2 className="text-[10px] tracking-widest uppercase text-text-muted mb-3">
            Pick Log ({recap.picks.length} picks)
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-1 pr-3 text-text-muted font-normal">#</th>
                  <th className="text-left py-1 pr-3 text-text-muted font-normal">Rd</th>
                  <th className="text-left py-1 pr-3 text-text-muted font-normal">Player</th>
                  <th className="text-left py-1 pr-3 text-text-muted font-normal">Team</th>
                </tr>
              </thead>
              <tbody>
                {recap.picks.map((p) => (
                  <tr key={p.pick_num} className="border-b border-border/40">
                    <td className="py-1 pr-3 text-text-muted">{p.pick_num}</td>
                    <td className="py-1 pr-3 text-text-muted">{p.round}</td>
                    <td className="py-1 pr-3 text-text">
                      {playerName(p.player_id)}
                      {p.is_auto_pick && <span className="ml-1 text-text-muted text-[9px]">AUTO</span>}
                    </td>
                    <td className="py-1 pr-3 text-text-muted text-[10px]">{p.team_id.slice(0, 8)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

      </div>
    </div>
  )
}
