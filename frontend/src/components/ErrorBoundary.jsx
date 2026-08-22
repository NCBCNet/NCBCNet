import { Component } from 'react'
import { Button, Result } from 'antd'
import { ReloadOutlined, HomeOutlined } from '@ant-design/icons'

/**
 * 错误边界：捕获子树中的渲染错误，展示友好回退界面，避免整站白屏。
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReload = () => {
    window.location.reload()
  }

  handleHome = () => {
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="500"
          title="页面出错了"
          subTitle="抱歉，页面发生了未知错误，请刷新重试或返回首页。"
          extra={[
            <Button
              key="reload"
              type="primary"
              icon={<ReloadOutlined />}
              onClick={this.handleReload}
              style={{ background: '#6f42c1', borderColor: '#6f42c1' }}
            >
              刷新页面
            </Button>,
            <Button key="home" icon={<HomeOutlined />} onClick={this.handleHome}>
              返回首页
            </Button>,
          ]}
        />
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary
