import { lazy, Suspense } from 'react'
import { Routes, Route, useNavigate } from 'react-router-dom'
import { Layout, Menu, Dropdown, Avatar, Spin, Button, Modal, message } from 'antd'
import {
  HomeOutlined,
  ReadOutlined,
  CloudOutlined,
  InfoCircleOutlined,
  UserOutlined,
  LoginOutlined,
  UserAddOutlined,
  LogoutOutlined,
  EditOutlined,
  SettingOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import './App.css'
import { useAuth } from './store/authStore'
import ErrorBoundary from './components/ErrorBoundary'

// 路由级代码分割（React.lazy + Suspense），降低首屏包体积
const Home = lazy(() => import('./pages/Home'))
const ArticleList = lazy(() => import('./pages/ArticleList'))
const ArticleDetail = lazy(() => import('./pages/ArticleDetail'))
const ArticleCreate = lazy(() => import('./pages/ArticleCreate'))
const ArticleEdit = lazy(() => import('./pages/ArticleEdit'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const FileList = lazy(() => import('./pages/FileList'))
const FileUpload = lazy(() => import('./pages/FileUpload'))
const Profile = lazy(() => import('./pages/Profile'))
const About = lazy(() => import('./pages/About'))
const NotFound = lazy(() => import('./pages/NotFound'))
const Forbidden = lazy(() => import('./pages/Forbidden'))
const ServerError = lazy(() => import('./pages/ServerError'))

const { Header, Content, Footer } = Layout

function App() {
  const { user, loading, isAuthenticated, logout, deleteAccount } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    message.success('已退出登录')
    navigate('/')
  }

  const handleDeleteAccount = () => {
    Modal.confirm({
      title: '确认删除用户',
      content: '确认删除用户资料吗？此操作不可撤销！',
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deleteAccount()
          message.success('用户已删除')
          navigate('/')
        } catch {
          message.error('删除失败')
        }
      },
    })
  }

  const menuItems = [
    { key: '/', label: '首页', icon: <HomeOutlined /> },
    { key: '/article', label: '论坛', icon: <ReadOutlined /> },
    { key: '#', label: '学习', icon: <ReadOutlined /> },
    { key: '/file_up/file_list', label: '云盘', icon: <CloudOutlined /> },
    { key: '/server/about', label: '关于', icon: <InfoCircleOutlined /> },
  ]

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    )
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
      onClick: () => user?.id && navigate(`/usermanage/profile/${user.id}`),
    },
    {
      key: 'admin',
      icon: <SettingOutlined />,
      label: '后台管理',
      onClick: () => window.open('/admin', '_blank'),
    },
    {
      key: 'write',
      icon: <EditOutlined />,
      label: '写文章',
      onClick: () => navigate('/article/article_create'),
    },
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除用户',
      danger: true,
      onClick: handleDeleteAccount,
    },
  ]

  return (
    <Layout className="app-layout">
      <Header
        style={{
          background: '#6f42c1',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <div
            style={{ color: '#fff', fontSize: 20, fontWeight: 700, cursor: 'pointer' }}
            onClick={() => navigate('/')}
          >
            NCNet
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            style={{ background: 'transparent', borderBottom: 'none', flex: 1, minWidth: 400 }}
            items={menuItems}
            onClick={({ key }) => key !== '#' && navigate(key)}
          />
        </div>
        <div>
          {isAuthenticated ? (
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button
                type="text"
                style={{ color: '#fff', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <Avatar
                  size="small"
                  icon={<UserOutlined />}
                  style={{ backgroundColor: 'rgba(255,255,255,0.3)' }}
                />
                {user?.username || '用户'}
              </Button>
            </Dropdown>
          ) : (
            <div style={{ display: 'flex', gap: 8 }}>
              <Button type="text" style={{ color: '#fff' }} icon={<LoginOutlined />} onClick={() => navigate('/usermanage/login')}>
                登录
              </Button>
              <Button ghost style={{ color: '#fff', borderColor: 'rgba(255,255,255,0.5)' }} icon={<UserAddOutlined />} onClick={() => navigate('/usermanage/register')}>
                注册
              </Button>
            </div>
          )}
        </div>
      </Header>
      <Content className="app-content">
        <ErrorBoundary>
          <Suspense
            fallback={
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
                <Spin size="large" />
              </div>
            }
          >
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/article" element={<ArticleList />} />
              <Route path="/article/article_detail/:id" element={<ArticleDetail />} />
              <Route path="/article/article_create" element={<ArticleCreate />} />
              <Route path="/article/article_edit/:id" element={<ArticleEdit />} />
              <Route path="/usermanage/login" element={<Login />} />
              <Route path="/usermanage/register" element={<Register />} />
              <Route path="/file_up/file_list" element={<FileList />} />
              <Route path="/file_up/file_upload" element={<FileUpload />} />
              <Route path="/usermanage/profile/:id" element={<Profile />} />
              <Route path="/server/about" element={<About />} />
              <Route path="/403" element={<Forbidden />} />
              <Route path="/500" element={<ServerError />} />
              <Route path="/404" element={<NotFound />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </ErrorBoundary>
      </Content>
      <Footer className="app-footer">
        Copyright &copy; www.ncbcstudent.top 2024-2026 v0.5.8.0
      </Footer>
    </Layout>
  )
}

export default App
