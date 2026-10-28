import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api from '../services/api'

function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [loading, setLoading] = useState(true)
  const [success, setSuccess] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  // Resend state
  const [resendEmail, setResendEmail] = useState('')
  const [resendLoading, setResendLoading] = useState(false)
  const [resendMessage, setResendMessage] = useState('')
  const [resendError, setResendError] = useState('')

  useEffect(() => {
    if (!token) {
      setLoading(false)
      setErrorMessage('Missing verification token in URL.')
      return
    }

    const verifyToken = async () => {
      try {
        const response = await api.post('/auth/verify-email', { token })
        setSuccess(true)
      } catch (err) {
        setErrorMessage(
          err.response?.data?.message || 'Verification link is invalid or has expired.'
        )
      } finally {
        setLoading(false)
      }
    }

    verifyToken()
  }, [token])

  const handleResend = async (e) => {
    e.preventDefault()
    setResendError('')
    setResendMessage('')

    const trimmed = resendEmail.trim()
    if (!trimmed) {
      setResendError('Please enter your email.')
      return
    }

    setResendLoading(true)
    try {
      const res = await api.post('/auth/resend-verification', { email: trimmed })
      setResendMessage(res.data?.message || 'Verification link sent!')
      setResendEmail('')
    } catch (err) {
      setResendError(err.response?.data?.message || 'Failed to resend verification.')
    } finally {
      setResendLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-8">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-sm border border-slate-200/80 hover:shadow-md transition-all duration-200 text-center">
        
        {/* Brand Header */}
        <div className="mx-auto w-12 h-12 rounded-2xl bg-blue-600 text-white flex items-center justify-center shadow-sm mb-4">
          <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>

        <h1 className="text-2xl font-bold text-slate-900 tracking-tight mb-2">
          Email Verification
        </h1>

        {loading ? (
          <div className="py-8 space-y-3">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
            <p className="text-sm text-slate-600">Verifying your email token, please wait...</p>
          </div>
        ) : success ? (
          <div className="space-y-6 py-4">
            <div className="rounded-xl bg-emerald-50 border border-emerald-200/80 p-4 text-emerald-800 text-sm">
              <svg className="w-8 h-8 text-emerald-600 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="font-semibold text-base mb-1">Account Verified Successfully!</p>
              <p className="text-emerald-700 text-xs">
                Your email has been confirmed. You can now log in to access the platform.
              </p>
            </div>

            <Link
              to="/login"
              className="block w-full text-center rounded-lg bg-blue-600 py-2.5 px-4 font-semibold text-white hover:bg-blue-700 transition-all shadow-xs text-sm"
            >
              Proceed to Login
            </Link>
          </div>
        ) : (
          <div className="space-y-6 py-2 text-left">
            <div className="rounded-xl bg-rose-50 border border-rose-200/80 p-4 text-rose-800 text-sm">
              <div className="flex items-center gap-2 font-semibold mb-1">
                <svg className="w-5 h-5 text-rose-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Verification Failed</span>
              </div>
              <p className="text-xs text-rose-700">{errorMessage}</p>
            </div>

            {/* Resend Option */}
            <div className="border-t border-slate-200 pt-4">
              <h2 className="text-sm font-semibold text-slate-800 mb-2">Need a new verification link?</h2>
              
              {resendMessage && (
                <div className="mb-3 text-xs bg-emerald-50 text-emerald-700 p-2.5 rounded-lg border border-emerald-200">
                  {resendMessage}
                </div>
              )}
              {resendError && (
                <div className="mb-3 text-xs bg-rose-50 text-rose-700 p-2.5 rounded-lg border border-rose-200">
                  {resendError}
                </div>
              )}

              <form onSubmit={handleResend} className="space-y-3">
                <input
                  type="email"
                  placeholder="Enter your registered email"
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3.5 py-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-xs"
                />
                <button
                  type="submit"
                  disabled={resendLoading}
                  className="w-full rounded-lg bg-slate-800 py-2 px-3 text-xs font-semibold text-white hover:bg-slate-900 disabled:opacity-50 cursor-pointer"
                >
                  {resendLoading ? 'Sending...' : 'Resend Verification Email'}
                </button>
              </form>
            </div>

            <div className="pt-2 text-center text-xs">
              <Link to="/login" className="font-semibold text-blue-600 hover:text-blue-700">
                &larr; Back to Login
              </Link>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}

export default VerifyEmail
