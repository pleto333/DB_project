import { createRouter, createWebHistory } from 'vue-router'
import AuthView from '../views/AuthView.vue'
import MainView from '../views/MainView.vue'
import StockDetailView from '../views/StockDetailView.vue'

const routes = [
  { path: '/', component: AuthView },
  { path: '/main', component: MainView },
  { path: '/stock/:code', component: StockDetailView },
]

export default createRouter({
  history: createWebHistory(),
  routes
})
