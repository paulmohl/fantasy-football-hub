import { WebPlugin } from '@capacitor/core'
import type { EspnCookiePlugin, EspnCookieResult } from './definitions'

/**
 * Web fallback — not used directly; the ConnectPage uses the bookmarklet flow on web.
 * This satisfies the Capacitor plugin contract so the app builds on web too.
 */
export class EspnCookieWeb extends WebPlugin implements EspnCookiePlugin {
  async extractCookies(): Promise<EspnCookieResult> {
    throw new Error('Use the bookmarklet flow on web.')
  }
}
