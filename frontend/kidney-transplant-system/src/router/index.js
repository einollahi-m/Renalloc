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
import WaitingListDonorsView from '../views/WaitingListDonorsView.vue'
import DeceasedDonorMatchingView from '../views/DeceasedDonorMatchingView.vue'
import PatientMatchesView from '../views/PatientMatchesView.vue'
import UserProfileView from '../views/UserProfileView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import { useAuth } from '../composables/useAuth'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: LoginView, meta: { guestOnly: true } },
  { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView },
  { path: '/reset-password', name: 'reset-password', component: ResetPasswordView },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
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
      { path: 'waiting-list/recipients', component: WaitingListRecipientsView },
      { path: 'waiting-list/donors', component: WaitingListDonorsView },
      { path: 'matching/deceased-donor', component: DeceasedDonorMatchingView },
      { path: 'patient-portal/matches', component: PatientMatchesView },
      { path: 'profile', name: 'user-profile', component: UserProfileView }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach(async (to) => {
  const { ensureAuthenticated } = useAuth()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  // Revalidate the token with Django before every protected navigation.
  if (requiresAuth && !(await ensureAuthenticated(true))) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && (await ensureAuthenticated())) {
    return { name: 'dashboard' }
  }
  return true
})

export default router
