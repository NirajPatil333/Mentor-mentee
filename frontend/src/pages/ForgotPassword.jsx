import { useState } from 'react'
import { Link } from 'react-router-dom'

function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      setError('Please enter your email address.')
      return
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(trimmedEmail)) {
      setError('Please enter a valid email address.')
      return
    }

    setLoading(true)

    // Demo mode: No backend reset endpoint exists currently.
    // Display clear, demo-safe notification.
    setTimeout(() => {
      setLoading(false)
      setSubmitted(true)
    }, 400)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4 py-8">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-md border border-gray-100">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Reset Password</h1>
          <p className="text-gray-500 text-sm">
            Enter your email to receive password reset instructions
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-200 p-3.5 text-sm text-red-700">
            {error}
          </div>
        )}

        {submitted ? (
          <div className="space-y-4">
            <div className="rounded-lg bg-blue-50 border border-blue-200 p-4 text-sm text-blue-800">
              <p className="font-semibold mb-1">Demo Mode Notice</p>
              <p>
                In a production environment, if an account associated with{' '}
                <span className="font-medium text-blue-900">{email}</span> exists, password reset instructions would be sent to that address.
              </p>
              <p className="mt-2 text-xs text-blue-700">
                (Note: Backend password reset service is not currently configured for this demo.)
              </p>
            </div>

            <Link
              to="/login"
              className="block w-full text-center rounded-lg bg-blue-600 py-3 px-4 font-semibold text-white hover:bg-blue-700 transition-colors"
            >
              Back to Login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 rounded-lg bg-blue-600 py-3 px-4 font-semibold text-white hover:bg-blue-700 active:bg-blue-800 disabled:opacity-50 transition-colors flex items-center justify-center space-x-2 cursor-pointer disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Processing...</span>
                </>
              ) : (
                <span>Send Reset Link</span>
              )}
            </button>

            <div className="mt-6 text-center text-sm">
              <Link to="/login" className="font-semibold text-blue-600 hover:text-blue-700 transition-colors">
                &larr; Back to Login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

export default ForgotPassword
