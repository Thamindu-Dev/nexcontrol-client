import { defineConfig } from '@capacitor/cli';

export default defineConfig({
  appId: 'com.nexcontrol.app',
  appName: 'NexControl',
  webDir: 'dist/spa',
  bundledWebRuntime: false,

  ios: {
    scheme: 'NexControl'
  },

  android: {
    buildOptions: {
      signingType: 'apk'
    }
  }
});
