export interface EspnCookieResult {
  swid: string
  espnS2: string
  leagueId: string
}

export interface EspnCookiePlugin {
  /** Opens an in-app WebView, lets the user log in to ESPN, then extracts SWID + espn_s2 cookies. */
  extractCookies(): Promise<EspnCookieResult>
}
