import { useEffect, useState } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'

function ArticleList() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const response = await axios.get('http://localhost:8000/article/')
        setArticles(response.data)
      } catch (err) {
        setError('Failed to fetch articles')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchArticles()
  }, [])

  if (loading) {
    return <div>Loading articles...</div>
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>
  }

  return (
    <div className="container">
      <h1>Article List</h1>
      <Link to="/article/article_create" className="btn">Create New Article</Link>
      <div className="article-list">
        {articles.length === 0 ? (
          <p>No articles found.</p>
        ) : (
          articles.map((article) => (
            <div key={article.id} className="card">
              <h2>{article.title}</h2>
              <p>{article.created_at}</p>
              <p>{article.content.substring(0, 100)}...</p>
              <Link to={`/article/article_detail/${article.id}`} className="btn">Read More</Link>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default ArticleList