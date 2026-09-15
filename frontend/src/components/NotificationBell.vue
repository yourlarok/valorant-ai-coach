<template>
  <div ref="rootEl" class="bell">
    <button
      class="bell__btn"
      type="button"
      aria-label="通知中心"
      @click="toggle"
    >
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.7 21a2 2 0 0 1-3.4 0" />
      </svg>
      <span v-if="unread > 0" class="bell__dot" :aria-label="`${unread} 条未读通知`" />
    </button>

    <div v-if="open" class="bell__panel">
      <div class="bell__head">
        <span class="bell__head-title">通知中心</span>
        <UiButton
          v-if="items.length"
          variant="subtle"
          size="sm"
          :disabled="!unread || markingAll"
          @click="markAll"
        >
          {{ markingAll ? '处理中…' : '全部已读' }}
        </UiButton>
      </div>

      <UiEmpty
        v-if="!items.length"
        title="暂无通知"
        description="新的分析完成、复测提醒会出现在这里"
      />

      <ul v-else class="bell__list">
        <li v-for="n in items" :key="n.id">
          <button
            class="bell__item"
            :class="{ 'bell__item--unread': !n.read }"
            type="button"
            @click="openNotification(n)"
          >
            <span class="bell__item-top">
              <span class="bell__item-title">{{ n.title }}</span>
              <span class="bell__item-time muted">{{ relativeTime(n.created_at) }}</span>
            </span>
            <span v-if="n.body" class="bell__item-body muted">{{ n.body }}</span>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../api'
import { UiButton, UiEmpty, useToast } from './ui'

const POLL_MS = 30000

const router = useRouter()
const toast = useToast()

const rootEl = ref(null)
const open = ref(false)
const items = ref([])
const unread = ref(0)
const markingAll = ref(false)
let timer = null

async function refresh() {
  try {
    const data = await getNotifications(false)
    items.value = data?.items || []
    unread.value = data?.unread || 0
  } catch {
    // 轮询失败静默跳过，下轮重试，避免后台请求打扰用户
  }
}

async function toggle() {
  open.value = !open.value
  if (open.value) await refresh()
}

async function openNotification(n) {
  open.value = false
  if (!n.read) {
    try {
      await markNotificationRead(n.id)
      n.read = true
      unread.value = Math.max(0, unread.value - 1)
    } catch (e) {
      toast.error(e.message || '标记已读失败')
    }
  }
  if (n.link) router.push(n.link)
}

async function markAll() {
  markingAll.value = true
  try {
    await markAllNotificationsRead()
    items.value.forEach((n) => { n.read = true })
    unread.value = 0
  } catch (e) {
    toast.error(e.message || '操作失败，请重试')
  } finally {
    markingAll.value = false
  }
}

function relativeTime(iso) {
  const t = new Date(iso)
  if (Number.isNaN(t.getTime())) return ''
  const diff = Date.now() - t.getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min} 分钟前`
  const hour = Math.floor(min / 60)
  if (hour < 24) return `${hour} 小时前`
  const day = Math.floor(hour / 24)
  if (day < 30) return `${day} 天前`
  return t.toLocaleDateString('zh-CN')
}

function onClickOutside(e) {
  if (open.value && rootEl.value && !rootEl.value.contains(e.target)) {
    open.value = false
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, POLL_MS)
  document.addEventListener('click', onClickOutside)
})

onBeforeUnmount(() => {
  clearInterval(timer)
  document.removeEventListener('click', onClickOutside)
})
</script>

<style scoped>
.bell { position: relative; }

.bell__btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  background: transparent;
  border: 1px solid var(--c-border);
  border-radius: var(--r-sm);
  color: var(--c-text-muted);
  cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease-out),
    color var(--dur-fast) var(--ease-out);
}
.bell__btn:hover { border-color: var(--c-accent); color: var(--c-accent); background: transparent; }

.bell__dot {
  position: absolute;
  top: -3px;
  right: -3px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--c-accent);
  border: 2px solid var(--c-surface-1);
}

.bell__panel {
  position: absolute;
  top: calc(100% + var(--sp-2));
  right: 0;
  width: 340px;
  max-height: 420px;
  display: flex;
  flex-direction: column;
  background: var(--c-surface-2);
  border: 1px solid var(--c-border-strong);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-3);
  overflow: hidden;
  z-index: 200;
}

.bell__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--c-border);
}
.bell__head-title {
  font-size: var(--fs-caption);
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--c-text-muted);
  text-transform: uppercase;
}

.bell__list {
  margin: 0;
  padding: 0;
  list-style: none;
  overflow-y: auto;
}
.bell__item {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  width: 100%;
  padding: var(--sp-2) var(--sp-3);
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--c-border);
  border-radius: 0;
  text-align: left;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out);
}
.bell__item:hover { background: var(--c-surface-3); }
.bell__item--unread { background: var(--c-accent-dim); }
.bell__item--unread:hover { background: var(--c-surface-3); }

.bell__item-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-2);
}
.bell__item-title { font-size: var(--fs-body); font-weight: 600; color: var(--c-text); }
.bell__item-time { font-size: var(--fs-micro); white-space: nowrap; }
.bell__item-body { font-size: var(--fs-caption); }
</style>
