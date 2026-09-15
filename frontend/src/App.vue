<template>
  <div class="layout">
    <header class="topbar">
      <div class="brand">
        <span class="accent">VAL</span> AI 教练
      </div>
      <input
        v-model="playerName"
        class="name-input"
        placeholder="昵称#数字ID"
        @change="saveName"
      />
      <nav class="nav">
        <router-link to="/">首页</router-link>
        <router-link to="/matches">战绩</router-link>
        <router-link to="/plan">训练计划</router-link>
      </nav>
    </header>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { playerName, setPlayerName } from './player'

function saveName() {
  setPlayerName(playerName.value)
}
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  background: var(--panel);
  border-bottom: 2px solid var(--accent);
}
.brand { font-size: 18px; font-weight: 700; white-space: nowrap; }
.name-input { flex: 0 0 200px; }
.nav { display: flex; gap: 20px; margin-left: auto; }
.nav a { color: var(--muted); text-decoration: none; font-size: 14px; }
.nav a.router-link-active { color: var(--accent); font-weight: 600; }
.content { max-width: 960px; margin: 0 auto; padding: 24px 16px; }
</style>
