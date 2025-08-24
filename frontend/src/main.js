import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import axios from 'axios'
import * as echarts from 'echarts'

// 配置axios
axios.defaults.baseURL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000'
axios.defaults.timeout = 10000

// 请求拦截器
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
axios.interceptors.response.use(
  response => {
    return response
  },
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token')
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)

// 全局属性
app.config.globalProperties.$http = axios
app.config.globalProperties.$echarts = echarts

app.use(ElementPlus)
app.mount('#app')
