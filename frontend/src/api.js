import axios from 'axios'

const http = axios.create({ baseURL: '', timeout: 60000 })

export const chat = (question, recentFiles = []) => http.post('/api/chat', { question, recent_files: recentFiles })
export const kbStatus = () => http.get('/api/kb/status')
export const kbIngest = () => http.post('/api/kb/ingest')
export const uploadPdfs = (files) => {
  const fd = new FormData()
  files.forEach((f) => fd.append('files', f))
  return http.post('/api/kb/upload', fd, { timeout: 300000 })
}
