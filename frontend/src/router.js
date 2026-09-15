import { createRouter, createWebHashHistory } from 'vue-router'
import HomePage from './pages/HomePage.vue'
import MatchesPage from './pages/MatchesPage.vue'
import ReportPage from './pages/ReportPage.vue'
import PlanPage from './pages/PlanPage.vue'
import RangePage from './pages/RangePage.vue'
import SettingsPage from './pages/SettingsPage.vue'
import OnboardingPage from './pages/OnboardingPage.vue'
import { initIdentity, onboarded } from './player'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: HomePage },
    { path: '/matches', component: MatchesPage },
    { path: '/report/:matchId', component: ReportPage },
    { path: '/plan', component: PlanPage },
    { path: '/range', component: RangePage },
    { path: '/settings', component: SettingsPage },
    {
      path: '/onboarding',
      component: OnboardingPage,
      meta: { fullScreen: true },
    },
  ],
})

// 未绑定身份一律进入首次引导；已绑定访问引导页则回到总览
router.beforeEach(async (to) => {
  await initIdentity()
  if (!onboarded.value && to.path !== '/onboarding') return '/onboarding'
  if (onboarded.value && to.path === '/onboarding') return '/'
})

export default router
