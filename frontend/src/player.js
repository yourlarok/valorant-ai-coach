import { ref } from 'vue'

const STORAGE_KEY = 'val_player_name'

export const playerName = ref(localStorage.getItem(STORAGE_KEY) || '')

export function setPlayerName(name) {
  playerName.value = name.trim()
  localStorage.setItem(STORAGE_KEY, playerName.value)
}
