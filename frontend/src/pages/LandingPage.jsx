
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const features = [
  {
    icon: '👨‍🏫',
    title: 'Mentor Matching',
    description: 'Find suitable mentors based on skills, experience and availability.',
  },
  {
    icon: '📅',
    title: 'Online Sessions',
    description: 'Schedule mentorship sessions and connect through online meetings.',
  },
  {
    icon: '📚',
    title: 'Learning Resources',
    description: 'Access shared study materials and resources for your learning journey.',
  },
  {
    icon: '📈',
    title: 'Track Progress',
    description: 'Set learning goals, monitor progress and celebrate achievements.',
  },
]

function LandingPage() {
  const { isAuthenticated, user } = useAuth()

  if (isAuthenticated && user?.role === 'mentor') {
    return <Navigate to="/dashboard/mentor" replace />
  }

  if (isAuthenticated && user?.role === 'mentee') {
    return <Navigate to="/dashboard/mentee" replace />
  }

  return (
    <div className="min-h-screen bg-white text-slate-800">
      {/* Navbar */}
      <nav className="border-b border-slate-100 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-xl text-white">
              🎓
            </div>
            <span className="text-xl font-bold text-slate-900">
              MentorConnect
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="rounded-lg px-4 py-2 font-medium text-slate-700 hover:bg-slate-100"
            >
              Login
            </Link>
            <Link
              to="/register"
              className="rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white hover:bg-blue-700"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="overflow-hidden bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-6 py-20 md:grid-cols-2 md:py-28">
          <div>
            <span className="inline-block rounded-full bg-blue-100 px-4 py-2 text-sm font-semibold text-blue-700">
              Collaborative Learning Platform
            </span>

            <h1 className="mt-6 text-4xl font-extrabold leading-tight tracking-tight text-slate-900 md:text-6xl">
              Learn Together.
              <span className="block text-blue-600">
                Grow Together.
              </span>
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
              Connect with experienced mentors, develop practical skills,
              achieve your learning goals and build your future through
              collaborative learning.
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                to="/register"
                className="rounded-xl bg-blue-600 px-7 py-3.5 font-semibold text-white shadow-lg shadow-blue-600/20 transition hover:-translate-y-0.5 hover:bg-blue-700"
              >
                Start Learning →
              </Link>

              <a
                href="#features"
                className="rounded-xl border border-slate-300 bg-white px-7 py-3.5 font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Explore Features
              </a>
            </div>

            <p className="mt-5 text-sm text-slate-500">
              A collaborative space for mentors and aspiring learners.
            </p>
          </div>

          {/* Hero visual */}
          <div className="relative mx-auto w-full max-w-lg">
            <div className="absolute -left-8 -top-8 h-40 w-40 rounded-full bg-blue-200/50 blur-3xl" />
            <div className="absolute -bottom-8 -right-8 h-40 w-40 rounded-full bg-indigo-200/60 blur-3xl" />

            <div className="relative rounded-3xl border border-white bg-white p-6 shadow-2xl shadow-blue-900/10 sm:p-8">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Your learning journey</p>
                  <h2 className="mt-1 text-xl font-bold text-slate-900">
                    Learn with guidance
                  </h2>
                </div>
                <span className="rounded-xl bg-blue-100 p-3 text-2xl">
                  🎯
                </span>
              </div>

              <div className="mt-7 rounded-2xl bg-blue-50 p-5">
                <div className="flex items-center gap-4">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 text-2xl text-white">
                    👨‍💻
                  </div>
                  <div>
                    <p className="font-bold text-slate-900">
                      Find your mentor
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      Learn from experienced developers
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4 space-y-4">
                {[
                  ['01', 'Discover mentors', 'Find guidance for your goals'],
                  ['02', 'Attend sessions', 'Learn through collaboration'],
                  ['03', 'Track progress', 'Build skills step by step'],
                ].map(([number, title, description]) => (
                  <div key={number} className="flex items-center gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 font-bold text-blue-600">
                      {number}
                    </div>
                    <div>
                      <p className="font-semibold text-slate-800">{title}</p>
                      <p className="text-sm text-slate-500">{description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="bg-slate-50 px-6 py-20 md:py-24">
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-semibold text-blue-600">WHAT WE OFFER</p>
            <h2 className="mt-3 text-3xl font-bold text-slate-900 md:text-4xl">
              Everything you need to grow
            </h2>
            <p className="mt-4 leading-7 text-slate-600">
              A single platform to connect, collaborate and make meaningful
              progress toward your learning goals.
            </p>
          </div>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg"
              >
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-3xl">
                  {feature.icon}
                </div>
                <h3 className="mt-5 text-lg font-bold text-slate-900">
                  {feature.title}
                </h3>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="px-6 py-20 md:py-24">
        <div className="mx-auto max-w-7xl">
          <div className="text-center">
            <p className="font-semibold text-blue-600">SIMPLE PROCESS</p>
            <h2 className="mt-3 text-3xl font-bold text-slate-900 md:text-4xl">
              How it works
            </h2>
          </div>

          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {[
              {
                step: '01',
                title: 'Discover a mentor',
                text: 'Explore mentor profiles and find expertise that matches your interests.',
              },
              {
                step: '02',
                title: 'Connect and learn',
                text: 'Send mentorship requests and arrange online learning sessions.',
              },
              {
                step: '03',
                title: 'Achieve your goals',
                text: 'Track your progress, access resources and showcase achievements.',
              },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600 text-xl font-bold text-white shadow-lg shadow-blue-600/20">
                  {item.step}
                </div>
                <h3 className="mt-5 text-xl font-bold text-slate-900">
                  {item.title}
                </h3>
                <p className="mx-auto mt-3 max-w-sm leading-7 text-slate-600">
                  {item.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-20">
        <div className="mx-auto max-w-7xl rounded-3xl bg-blue-700 px-6 py-14 text-center text-white md:px-12 md:py-16">
          <h2 className="text-3xl font-bold md:text-4xl">
            Ready to begin your learning journey?
          </h2>
          <p className="mx-auto mt-4 max-w-2xl leading-7 text-blue-100">
            Join a collaborative learning community where guidance,
            practical skills and continuous improvement come together.
          </p>
          <Link
            to="/register"
            className="mt-8 inline-block rounded-xl bg-white px-7 py-3.5 font-semibold text-blue-700 transition hover:bg-blue-50"
          >
            Create Your Account →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white px-6 py-6">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 text-center sm:flex-row sm:text-left">
          <p className="font-bold text-slate-800">MentorConnect</p>
          <p className="text-sm text-slate-500">
            Empowering learning through mentorship and collaboration.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
