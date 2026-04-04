import { useEffect, useState } from 'react'
import axios from 'axios'

function Home() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('http://localhost:8000/')
        setData(response.data)
      } catch (err) {
        setError('Failed to fetch data')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>
  }

  return (
    <div className="container">
      <h1>Welcome to NCBCNet</h1>
      <p>This is the home page of NCBCNet project.</p>
      <p>Backend: Django + Daphne</p>
      <p>Frontend: React</p>
      <div className="card">
        <h2>Project Overview</h2>
        <p>NCBCNet is a comprehensive web application with the following features:</p>
        <ul>
          <li>Article management system</li>
          <li>User authentication and management</li>
          <li>File upload and management</li>
          <li>Real-time communication with WebSocket</li>
        </ul>
      </div>
    </div>
  )
}

export default Home