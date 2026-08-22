import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter as Router } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from './store/authStore'
import { UploadProvider } from './store/uploadStore'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Router>
      <ConfigProvider
        locale={zhCN}
        theme={{
          token: {
            colorPrimary: '#6f42c1',
            colorLink: '#6f42c1',
            borderRadius: 6,
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif",
          },
          components: {
            Menu: {
              colorItemBgActive: 'rgba(111, 66, 193, 0.1)',
              colorItemTextActive: '#6f42c1',
            },
            Button: {
              colorPrimary: '#6f42c1',
              colorPrimaryHover: '#8a5bd6',
              primaryShadow: '0 2px 0 rgba(111, 66, 193, 0.1)',
            },
          },
        }}
      >
        <AuthProvider>
          <UploadProvider>
            <App />
          </UploadProvider>
        </AuthProvider>
      </ConfigProvider>
    </Router>
  </StrictMode>,
)
