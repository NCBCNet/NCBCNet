import { useEffect, useState } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'

function FileList() {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const response = await axios.get('http://localhost:8000/file_up/file_list/')
        setFiles(response.data)
      } catch (err) {
        setError('Failed to fetch files')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchFiles()
  }, [])

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      try {
        await axios.delete(`http://localhost:8000/file_up/file_delete/${id}/`)
        setFiles(files.filter(file => file.id !== id))
      } catch (err) {
        setError('Failed to delete file')
        console.error(err)
      }
    }
  }

  if (loading) {
    return <div>Loading files...</div>
  }

  if (error) {
    return <div className="alert alert-danger">{error}</div>
  }

  return (
    <div className="container">
      <h1>File List</h1>
      <Link to="/file_up/file_upload" className="btn">Upload File</Link>
      <div className="file-list">
        {files.length === 0 ? (
          <p>No files found.</p>
        ) : (
          files.map((file) => (
            <div key={file.id} className="card">
              <h3>{file.file_name}</h3>
              <p>Size: {file.file_size} bytes</p>
              <p>Uploaded: {file.upload_time}</p>
              <div className="file-actions">
                <a href={`http://localhost:8000/file_up/file_download/${file.id}/`} className="btn">Download</a>
                <button onClick={() => handleDelete(file.id)} className="btn" style={{ backgroundColor: '#dc3545', color: 'white' }}>Delete</button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default FileList