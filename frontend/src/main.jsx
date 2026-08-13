import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { SceneProvider } from './context/SceneContext.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <SceneProvider>
      <App />
    </SceneProvider>
  </React.StrictMode>,
)
