import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import clickOutside from './directives/clickOutside'

// Styles
import './styles/main.css'

const app = createApp(App)

app.use(router)

// Register directives
app.directive('click-outside', clickOutside)

app.mount('#app')
