import { useState } from 'react'
import AdminInterface from './AdminInterface'
import './App.css'
import UserInterface from './UserInterface'

function App() {
  const [view, setView] = useState('user') // 'user' or 'admin'

  return (
    <>
      {/* Simple Toggle Header */}
      <nav style={{ 
        padding: '10px', 
        background: '#f4f4f4', 
        display: 'flex', 
        gap: '10px',
        justifyContent: 'center',
        borderBottom: '1px solid #ccc' 
      }}>
        <button 
          onClick={() => setView('user')}
          style={{ fontWeight: view === 'user' ? 'bold' : 'normal' }}
        >
          View User App
        </button>
        <button 
          onClick={() => setView('admin')}
          style={{ fontWeight: view === 'admin' ? 'bold' : 'normal' }}
        >
          View Admin Panel
        </button>
      </nav>

      {/* Conditional Rendering */}
      <main>
        {view === 'user' ? <UserInterface /> : <AdminInterface />}
      </main>
    </>
  )
}

export default App