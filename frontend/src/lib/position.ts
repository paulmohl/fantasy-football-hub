const TONES: Record<string, string> = {
  QB: 'bg-[#F26D6D]/12 text-[#F59A9A]',
  RB: 'bg-[#5CC8A9]/12 text-[#7FD9BF]',
  WR: 'bg-[#3DA9FC]/12 text-[#7CC4FD]',
  TE: 'bg-[#F2B66D]/12 text-[#F5CB92]',
  K: 'bg-[#B58CF2]/12 text-[#CBB0F6]',
  DEF: 'bg-[#9AA3B2]/12 text-[#BCC3CF]',
}

export function positionTone(slot: string | null | undefined): string {
  const key = (slot ?? '').replace(/\d+$/, '').toUpperCase()
  return TONES[key] ?? 'bg-raised text-muted'
}
