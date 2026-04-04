import { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

function ArticleCreate() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    title: '',
    content: ''
  })
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await axios.post('http://localhost:8000/article/article_create/', formData)
      setSuccess('Article created successfully!')
      setTimeout(() => {
        navigate('/article')
      }, 1500)
    } catch (err) {
      setError('Failed to create article')
      console.error(err)
    }
  }

  return (
    <div className="container">
      <h1>Create New Article</h1>
      {success && <div className="alert alert-success">{success}</div>}
      {error && <div className="alert alert-danger">{error}</div>}
      <form onSubmit={handleSubmit} className="card">
        <div className="form-group">
          <label htmlFor="title">Title</label>
          <input
            type="text"
            id="title"
            name="title"
            className="form-control"
            value={formData.title}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="content">Content</label>
          <textarea
            id="content"
            name="content"
            className="form-control"
            rows={10}
            value={formData.content}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" className="btn">Create Article</button>
      </form>
    </div>
  )
}

export default ArticleCreate