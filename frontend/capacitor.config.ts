import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.ffhub.app',
  appName: 'Fantasy Football Hub',
  webDir: 'dist',
  server: {
    // Dev only — remove before App Store build
    url: 'http://localhost:5173',
    cleartext: true,
  },
  plugins: {
    SplashScreen: { launchShowDuration: 0 },
  },
}

export default config
