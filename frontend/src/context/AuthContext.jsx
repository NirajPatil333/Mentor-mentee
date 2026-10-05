import { createContext, useContext, useState } from 'react'

const AuthContext = createContext()

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(
    localStorage.getItem('token')
  )

  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user')

    return savedUser ? JSON.parse(savedUser) : null
  })

 const login = (newToken, userData) => {

  localStorage.setItem('token', newToken)
  localStorage.setItem('user', JSON.stringify(userData))

  setToken(newToken)
  setUser(userData)
}

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')

    setToken(null)
    setUser(null)
  }

  const isAuthenticated = !!token

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        login,
        logout,
        isAuthenticated,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  return useContext(AuthContext)
}