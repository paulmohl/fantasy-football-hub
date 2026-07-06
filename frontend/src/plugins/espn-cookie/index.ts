import { registerPlugin, Capacitor } from '@capacitor/core'
import type { EspnCookiePlugin, EspnCookieResult } from './definitions'

const EspnCookieNative = registerPlugin<EspnCookiePlugin>('EspnCookie', {
  web: () => import('./web').then((m) => new m.EspnCookieWeb()),
})

export { EspnCookieNative }
export type { EspnCookiePlugin, EspnCookieResult }

/** True when running inside a Capacitor native shell (iOS or Android). */
export const isNative = () => Capacitor.isNativePlatform()
