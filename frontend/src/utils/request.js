import axios from 'axios'

function getCsrfToken() {
  const cookie = document.cookie
    .split(';')
    .find(c => c.trim().startsWith('csrftoken='))
  return cookie ? cookie.split('=')[1] : ''
}

const request = axios.create({
  withCredentials: true,
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
  },
})

request.interceptors.request.use(config => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    config.headers['X-CSRFToken'] = getCsrfToken()
  }
  return config
})

request.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      window.location.href = '/usermanage/login'
    }
    return Promise.reject(error)
  }
)

export default request
