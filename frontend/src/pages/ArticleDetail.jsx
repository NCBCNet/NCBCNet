import { useEffect, useState } from 'react'
import axios from 'axios'
import { useParams } from 'react-router-dom'

function ArticleDetail() {
  const { id } = useParams()
  const [article, setArticle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/article/article_detail/${id}/`)
        setArticle(response.data)
      } catch (err) {
        setError('Failed to fetch article')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchArticle()
  }, [id])

  if (loading) {
    return <div>Loading article...</div>
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>
  }

  return (
    <div className="container">
      {article && (
        <div className="card">
          <h1>{article.title}</h1>
          <p>{article.created_at}</p>
          <div dangerouslySetInnerHTML={{ __html: article.content }} />
          <div className="article-meta">
            <p>Views: {article.total_views}</p>
            <p>Likes: {article.likes}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default ArticleDetail