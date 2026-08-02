import { createRouter, createWebHashHistory } from 'vue-router'

// Layouts
import MainLayout from '../layouts/MainLayout.vue'

// Views
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import RecipientListView from '../views/RecipientListView.vue'
import RecipientCreateView from '../views/RecipientCreateView.vue'
import RecipientDetailView from '../views/RecipientDetailView.vue'
import DonorListView from '../views/DonorListView.vue'
import DonorCreateView from '../views/DonorCreateView.vue'
import DonorDetailView from '../views/DonorDetailView.vue'
import MatchingDashboardView from '../views/MatchingDashboardView.vue'
import VirtualCrossmatchView from '../views/VirtualCrossmatchView.vue'
import WaitingListRecipientsView from '../views/WaitingListRecipientsView.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: LoginView },
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: 'dashboard', name: 'dashboard', component: DashboardView },
      { path: 'recipients', component: RecipientListView },
      { path: 'recipients/new', component: RecipientCreateView },
      { path: 'recipients/:id', component: RecipientDetailView },
      { path: 'donors', component: DonorListView },
      { path: 'donors/new', component: DonorCreateView },
      { path: 'donors/:id', component: DonorDetailView },
      { path: 'matching', component: MatchingDashboardView },
      { path: 'matching/virtual-crossmatch', component: VirtualCrossmatchView },
      { path: 'waiting-list/recipients', component: WaitingListRecipientsView }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
