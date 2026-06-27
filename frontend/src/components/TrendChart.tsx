import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface WeeklyPoint {
  week: number
  pts: number
}

interface TrendChartProps {
  data: WeeklyPoint[]
  compareData?: WeeklyPoint[]
  showCompare?: boolean
  isLoading?: boolean
}

export function TrendChart({ data, compareData, showCompare = false, isLoading = false }: TrendChartProps) {
  if (isLoading) {
    return (
      <div className="h-[120px] animate-pulse bg-raised rounded-xl" />
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-[120px] flex items-center justify-center">
        <p className="text-xs text-muted italic">Stats available in-season</p>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={120}>
      <LineChart
        data={showCompare && compareData ? compareData : data}
        margin={{ top: 4, right: 4, bottom: 4, left: -20 }}
      >
        <XAxis
          dataKey="week"
          tick={{ fontSize: 10, fill: '#9AA3B2' }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: '#9AA3B2' }}
          tickLine={false}
          axisLine={false}
          domain={['auto', 'auto']}
        />
        <Tooltip
          formatter={(v, _name, item) => [
            typeof v === 'number' ? `${v.toFixed(1)} pts wk ${(item as { payload: WeeklyPoint }).payload.week}` : String(v),
            'Points',
          ]}
          contentStyle={{
            background: '#141822',
            border: '1px solid #262C3A',
            borderRadius: '8px',
            fontSize: '11px',
            fontFamily: 'JetBrains Mono, monospace',
            color: '#E8ECF1',
          }}
        />
        <Line
          type="monotone"
          dataKey="pts"
          stroke="#3DA9FC"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
