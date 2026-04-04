import { useEffect, useState } from 'react'
import { Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Button, Space, Avatar, Dropdown, Typography } from 'antd'
import {
  HomeOutlined,
  FileTextOutlined,
  FolderOutlined,
  InfoCircleOutlined,
  UserOutlined,
  LoginOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import Home from './pages/Home'
import ArticleList from './pages/ArticleList'
import ArticleDetail from './pages/ArticleDetail'
import ArticleCreate from './pages/ArticleCreate'
import Login from './pages/Login'
import Register from './pages/Register'
import FileList from './pages/FileList'
import FileUpload from './pages/FileUpload'
import About from './pages/About'
import request from './utils/request'

const { Header, Content, Footer } = Layout
const { Text } = Typography

function App() {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState(null)

  useEffect(() => {
    request.get('/usermanage/api/user/')
      .then(res => {
        if (res.data.authenticated) {
          setUser(res.data)
        } else {
          setUser(null)
        }
      })
      .catch(() => setUser(null))
  }, [location.pathname])

  const handleLogout = () => {
    request.post('/usermanage/api/logout/')
      .then(() => {
        setUser(null)
        navigate('/')
      })
      .catch(() => {
        setUser(null)
        navigate('/')
      })
  }

  const navItems = [
    { key: '/', icon: <HomeOutlined />, label: <Link to="/">首页</Link> },
    { key: '/article', icon: <FileTextOutlined />, label: <Link to="/article">文章</Link> },
    { key: '/file_up/file_list', icon: <FolderOutlined />, label: <Link to="/file_up/file_list">文件</Link> },
    { key: '/server/about', icon: <InfoCircleOutlined />, label: <Link to="/server/about">关于</Link> },
  ]

  const selectedKey = navItems.find(item => location.pathname.startsWith(item.key) && item.key !== '/')
    ? navItems.find(item => location.pathname.startsWith(item.key) && item.key !== '/')?.key
    : location.pathname === '/' ? '/' : undefined

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px', gap: 16 }}>
        <Text strong style={{ color: '#fff', fontSize: 18, marginRight: 24, whiteSpace: 'nowrap' }}>
          NCBCNet
        </Text>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[selectedKey]}
          items={navItems}
          style={{ flex: 1, minWidth: 0 }}
        />
        <Space>
          {user ? (
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'logout',
                    icon: <LogoutOutlined />,
                    label: '退出登录',
                    onClick: handleLogout,
                  },
                ],
              }}
            >
              <Space style={{ cursor: 'pointer', color: '#fff' }}>
                <Avatar icon={<UserOutlined />} size="small" />
                <Text style={{ color: '#fff' }}>{user.username}</Text>
              </Space>
            </Dropdown>
          ) : (
            <>
              <Button type="link" icon={<LoginOutlined />} style={{ color: '#fff' }} onClick={() => navigate('/usermanage/login')}>
                登录
              </Button>
              <Button type="primary" ghost onClick={() => navigate('/usermanage/register')}>
                注册
              </Button>
            </>
          )}
        </Space>
      </Header>

      <Content style={{ padding: '24px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/article" element={<ArticleList />} />
          <Route path="/article/article_detail/:id" element={<ArticleDetail />} />
          <Route path="/article/article_create" element={<ArticleCreate />} />
          <Route path="/usermanage/login" element={<Login setUser={setUser} />} />
          <Route path="/usermanage/register" element={<Register />} />
          <Route path="/file_up/file_list" element={<FileList />} />
          <Route path="/file_up/file_upload" element={<FileUpload />} />
          <Route path="/server/about" element={<About />} />
        </Routes>
      </Content>

      <Footer style={{ textAlign: 'center', background: '#f0f2f5' }}>
        NCBCNet © {new Date().getFullYear()} — 南城广播网
      </Footer>
    </Layout>
  )
}

export default App
