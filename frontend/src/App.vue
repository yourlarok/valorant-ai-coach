<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="sidebar__brand">
        <span class="sidebar__logo cut-corner">VAL</span>
        <div class="sidebar__brand-text">
          <span class="sidebar__title">AI 教练</span>
          <span class="sidebar__subtitle">VALORANT COACH</span>
        </div>
      </div>
      <nav class="sidebar__nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar__link"
        >
          <span class="sidebar__link-bar" />
          <span class="sidebar__link-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar__foot muted">P1.5 · 本地数据</div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="topbar__search">
          <input
            v-model="playerName"
            class="topbar__input"
            placeholder="搜索玩家：昵称#数字ID"
            @change="saveName"
            @keyup.enter="saveName"
          />
        </div>
        <div class="topbar__status">
          <UiTag :tone="llmConfigured ? 'win' : 'firstblood'" dot>
            {{ llmConfigured ? 'LLM 已连接' : 'Mock 演示通道' }}
          </UiTag>
        </div>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>

    <UiToast />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { playerName, setPlayerName } from './player'
import { configured as llmConfigured, loadSettings } from './settings'
import { UiTag, UiToast } from './components/ui'

const navItems = [
  { to: '/', label: '总览' },
  { to: '/matches', label: '战绩' },
  { to: '/plan', label: '训练中心' },
  { to: '/settings', label: '设置' },
]

onMounted(async () => {
  try {
    await loadSettings()
  } catch {
    // 读取失败时状态未知，徽标保持默认（Mock 演示通道）
  }
})

function saveName() {
  setPlayerName(playerName.value)
}
</script>

<style scoped>
.shell {
  display: flex;
  min-height: 100vh;
}

/* ---- 左侧导航 ---- */
.sidebar {
  flex: 0 0 var(--sidebar-w);
  display: flex;
  flex-direction: column;
  background: var(--c-surface-1);
  border-right: 1px solid var(--c-border);
  position: sticky;
  top: 0;
  height: 100vh;
}
.sidebar__brand {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--c-border);
}
.sidebar__logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--c-accent);
  color: var(--c-on-accent);
  font-family: var(--font-num);
  font-weight: 800;
  font-size: var(--fs-h3);
  letter-spacing: 0.04em;
}
.sidebar__brand-text { display: flex; flex-direction: column; line-height: 1.2; }
.sidebar__title { font-size: var(--fs-h3); font-weight: 700; }
.sidebar__subtitle {
  font-size: var(--fs-micro);
  letter-spacing: 0.18em;
  color: var(--c-text-faint);
}
.sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-3) var(--sp-2);
  flex: 1;
}
.sidebar__link {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--r-sm);
  color: var(--c-text-muted);
  text-decoration: none;
  font-size: var(--fs-body);
  font-weight: 600;
  letter-spacing: 0.06em;
  transition: background var(--dur-fast) var(--ease-out),
    color var(--dur-fast) var(--ease-out);
}
.sidebar__link-bar {
  width: 3px;
  height: 16px;
  background: transparent;
  transition: background var(--dur-fast) var(--ease-out);
}
.sidebar__link:hover { background: var(--c-surface-2); color: var(--c-text); }
.sidebar__link.router-link-active {
  background: var(--c-accent-dim);
  color: var(--c-accent);
}
.sidebar__link.router-link-active .sidebar__link-bar { background: var(--c-accent); }
.sidebar__foot {
  padding: var(--sp-3) var(--sp-4);
  font-size: var(--fs-caption);
  border-top: 1px solid var(--c-border);
}

/* ---- 右侧主区 ---- */
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.topbar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  height: var(--topbar-h);
  padding: 0 var(--sp-4);
  background: var(--c-surface-1);
  border-bottom: 1px solid var(--c-border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.topbar__search { flex: 1; max-width: 420px; }
.topbar__input { width: 100%; }
.topbar__status { margin-left: auto; display: flex; align-items: center; gap: var(--sp-2); }

.content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-w);
  margin: 0 auto;
  padding: var(--sp-4) var(--sp-4) var(--sp-7);
}
</style>
