import { Button, Result } from 'antd'
import { useNavigate } from 'react-router-dom'
import { HomeOutlined } from '@ant-design/icons'

function NotFound() {
  const navigate = useNavigate()

  return (
    <Result
      status="404"
      title="404"
      subTitle="抱歉，您访问的页面不存在或已被移除。"
      extra={[
        <Button
          key="home"
          type="primary"
          icon={<HomeOutlined />}
          onClick={() => navigate('/')}
          style={{ background: '#6f42c1', borderColor: '#6f42c1' }}
        >
          返回首页
        </Button>,
      ]}
    />
  )
}

export default NotFound
