import { Button, Result } from 'antd'
import { useNavigate } from 'react-router-dom'
import { ReloadOutlined, HomeOutlined } from '@ant-design/icons'

function ServerError() {
  const navigate = useNavigate()

  return (
    <Result
      status="500"
      title="500"
      subTitle="抱歉，服务器开小差了，请稍后重试。"
      extra={[
        <Button
          key="reload"
          type="primary"
          icon={<ReloadOutlined />}
          onClick={() => window.location.reload()}
          style={{ background: '#6f42c1', borderColor: '#6f42c1' }}
        >
          刷新重试
        </Button>,
        <Button key="home" icon={<HomeOutlined />} onClick={() => navigate('/')}>
          返回首页
        </Button>,
      ]}
    />
  )
}

export default ServerError
