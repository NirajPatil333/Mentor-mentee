import { useState } from 'react'

export const getProfilePictureUrl = (path) => {
  if (!path) return null
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('data:')) {
    return path
  }
  const cleanPath = path.startsWith('/') ? path.slice(1) : path
  return `http://localhost:5000/${cleanPath}`
}

function Avatar({
  src,
  name = '',
  size = 'md',
  className = '',
  alt = ''
}) {
  const [imgError, setImgError] = useState(false)

  const sizeClasses = {
    xs: 'w-6 h-6 text-[10px]',
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
    xl: 'w-16 h-16 text-xl',
    '2xl': 'w-24 h-24 text-2xl font-bold',
  }

  const selectedSize = sizeClasses[size] || sizeClasses.md
  const initial = name ? name.trim().charAt(0).toUpperCase() : 'U'
  const imageUrl = !imgError ? getProfilePictureUrl(src) : null

  if (imageUrl) {
    return (
      <img
        src={imageUrl}
        alt={alt || name || 'User profile picture'}
        onError={() => setImgError(true)}
        className={`rounded-full object-cover shrink-0 border border-slate-200/90 shadow-2xs ${selectedSize} ${className}`}
      />
    )
  }

  // Default Avatar when no picture uploaded or image fails to load
  return (
    <div
      className={`rounded-full bg-linear-to-br from-blue-500 to-indigo-600 text-white font-bold flex items-center justify-center shrink-0 border border-blue-400/40 shadow-2xs select-none ${selectedSize} ${className}`}
      title={name || 'User avatar'}
    >
      <span>{initial}</span>
    </div>
  )
}

export default Avatar
