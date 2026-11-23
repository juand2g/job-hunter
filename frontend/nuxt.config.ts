export default defineNuxtConfig({
  compatibilityDate: '2026-11-12',
  devServer: { port: 3001 },
  css: ['~/assets/main.css'],
  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000',
    },
  },
})
