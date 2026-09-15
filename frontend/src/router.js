import { createRouter, createWebHashHistory } from 'vue-router'
import HomePage from './pages/HomePage.vue'
import MatchesPage from './pages/MatchesPage.vue'
import ReportPage from './pages/ReportPage.vue'
import PlanPage from './pages/PlanPage.vue'
import SettingsPage from './pages/SettingsPage.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: HomePage },
    { path: '/matches', component: MatchesPage },
    { path: '/report/:matchId', component: ReportPage },
    { path: '/plan', component: PlanPage },
    { path: '/settings', component: SettingsPage },
  ],
})
