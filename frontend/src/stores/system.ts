import { defineStore } from "pinia"

import { fetchHealth } from "@/services/system"

interface SystemState {
  isLoading: boolean
  healthStatus: string | null
  appName: string | null
  appEnv: string | null
  errorMessage: string | null
}

export const useSystemStore = defineStore("system", {
  state: (): SystemState => ({
    isLoading: false,
    healthStatus: null,
    appName: null,
    appEnv: null,
    errorMessage: null,
  }),
  getters: {
    healthSummary(state): string | null {
      if (state.errorMessage) {
        return "连接失败"
      }

      if (!state.healthStatus) {
        return null
      }

      return `${state.appName ?? "backend"} / ${state.healthStatus}`
    },
  },
  actions: {
    async loadHealth() {
      this.isLoading = true
      this.errorMessage = null

      try {
        const payload = await fetchHealth()
        this.healthStatus = payload.status
        this.appName = payload.app_name
        this.appEnv = payload.app_env
      } catch (error) {
        this.healthStatus = null
        this.appName = null
        this.appEnv = null
        this.errorMessage =
          error instanceof Error ? error.message : "无法连接后端服务。"
      } finally {
        this.isLoading = false
      }
    },
  },
})
