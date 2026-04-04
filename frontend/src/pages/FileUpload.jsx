import { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

function FileUpload() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a file')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      setLoading(true)
      await axios.post('http://localhost:8000/file_up/file_upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      setSuccess('File uploaded successfully!')
      setTimeout(() => {
        navigate('/file_up/file_list')
      }, 1500)
    } catch (err) {
      setError('Failed to upload file')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Upload File</h1>
      {success && <div className="alert alert-success">{success}</div>}
      {error && <div className="alert alert-danger">{error}</div>}
      <form onSubmit={handleSubmit} className="card">
        <div className="form-group">
          <label htmlFor="file">Select File</label>
          <input
            type="file"
            id="file"
            name="file"
            className="form-control"
            onChange={handleFileChange}
            required
          />
        </div>
        <button type="submit" className="btn" disabled={loading}>
          {loading ? 'Uploading...' : 'Upload'}
        </button>
      </form>
    </div>
  )
}

export default FileUpload