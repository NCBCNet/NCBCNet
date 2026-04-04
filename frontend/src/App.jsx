import { Routes, Route, Link } from 'react-router-dom'
import './App.css'
import Home from './pages/Home'
import ArticleList from './pages/ArticleList'
import ArticleDetail from './pages/ArticleDetail'
import ArticleCreate from './pages/ArticleCreate'
import Login from './pages/Login'
import Register from './pages/Register'
import FileList from './pages/FileList'
import FileUpload from './pages/FileUpload'
import About from './pages/About'

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <nav>
          <ul>
            <li><Link to="/">首页</Link></li>
            <li><Link to="/article">文章</Link></li>
            <li><Link to="/file_up/file_list">文件</Link></li>
            <li><Link to="/server/about">关于</Link></li>
            <li><Link to="/usermanage/login">登录</Link></li>
            <li><Link to="/usermanage/register">注册</Link></li>
          </ul>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/article" element={<ArticleList />} />
          <Route path="/article/article_detail/:id" element={<ArticleDetail />} />
          <Route path="/article/article_create" element={<ArticleCreate />} />
          <Route path="/usermanage/login" element={<Login />} />
          <Route path="/usermanage/register" element={<Register />} />
          <Route path="/file_up/file_list" element={<FileList />} />
          <Route path="/file_up/file_upload" element={<FileUpload />} />
          <Route path="/server/about" element={<About />} />
        </Routes>
      </main>
      <footer>
        <p>© 2026 NCBCNet</p>
      </footer>
    </div>
  )
}

export default App
