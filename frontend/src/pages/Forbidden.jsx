import { Button, Result } from 'antd'
import { useNavigate } from 'react-router-dom'
import { HomeOutlined, LoginOutlined } from '@ant-design/icons'

function Forbidden() {
  const navigate = useNavigate()

  return (
    <Result
      status="403"
      title="403"
      subTitle="抱歉，您没有权限访问该页面，请登录后重试。"
      extra={[
        <Button
          key="login"
          type="primary"
          icon={<LoginOutlined />}
          onClick={() => navigate('/usermanage/login')}
          style={{ background: '#6f42c1', borderColor: '#6f42c1' }}
        >
          去登录
        </Button>,
        <Button key="home" icon={<HomeOutlined />} onClick={() => navigate('/')}>
          返回首页
        </Button>,
      ]}
    />
  )
}

export default Forbidden
