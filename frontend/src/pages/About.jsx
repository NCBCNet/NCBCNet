import { useEffect, useState } from 'react'
import axios from 'axios'

function About() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('http://localhost:8000/server/about/')
        setData(response.data)
      } catch (err) {
        setError('Failed to fetch about data')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return <div>Loading about page...</div>
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>
  }

  return (
    <div className="container">
      <h1>About NCBCNet</h1>
      <div className="card">
        <h2>Project Introduction</h2>
        <p>NCBCNet is a comprehensive web application built with Django + Daphne as backend and React as frontend.</p>
        <h3>Features</h3>
        <ul>
          <li>Article management system with rich text editor</li>
          <li>User authentication and profile management</li>
          <li>File upload, download and management</li>
          <li>Real-time communication with WebSocket</li>
          <li>Responsive design for different devices</li>
        </ul>
        <h3>Technologies Used</h3>
        <ul>
          <li>Backend: Django, Daphne, Channels</li>
          <li>Frontend: React, React Router, Axios</li>
          <li>Database: MySQL/SQLite</li>
          <li>Styling: CSS, Bootstrap</li>
          <li>Deployment: Nginx, Supervisor</li>
        </ul>
      </div>
    </div>
  )
}

export default About