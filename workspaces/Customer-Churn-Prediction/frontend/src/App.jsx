import { Suspense, lazy, useEffect, useMemo, useState } from 'react'
import { Loader2 } from 'lucide-react'

import Sidebar from './components/Sidebar.jsx'
import Topbar from './components/Topbar.jsx'

const Landing = lazy(() => import('./pages/Landing.jsx'))
const Login = lazy(() => import('./pages/Login.jsx'))
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'))
const UploadPage = lazy(() => import('./pages/UploadPage.jsx'))
const Prediction = lazy(() => import('./pages/Prediction.jsx'))
const RiskAnalysis = lazy(() => import('./pages/RiskAnalysis.jsx'))
const Performance = lazy(() => import('./pages/Performance.jsx'))
const Retention = lazy(() => import('./pages/Retention.jsx'))
const Reports = lazy(() => import('./pages/Reports.jsx'))
const Settings = lazy(() => import('./pages/Settings.jsx'))
const ReviewsPage = lazy(() => import('./pages/ReviewsPage.jsx'))


const PAGE_TITLES = {
  dashboard: 'Dashboard',
  upload: 'Dataset Upload',
  predict: 'Churn Prediction',
  risk: 'Customer Risk Analysis',
  performance: 'Model Performance',
  retention: 'Retention Strategy',
  reports: 'Reports',
  settings: 'Settings',
  reviews: 'Safety Reviews',
}


function PageLoader() {
  return (
    <div className="flex min-h-[55vh] items-center justify-center text-cyan-300">
      <Loader2 size={34} className="animate-spin" />
    </div>
  )
}

function getInitialScreen() {
  return localStorage.getItem('churn_token') ? 'app' : 'landing'
}

function getInitialPage() {
  const savedPage = localStorage.getItem('churn_active_page')
  return savedPage && PAGE_TITLES[savedPage] ? savedPage : 'dashboard'
}

export default function App() {
  const [screen, setScreen] = useState(getInitialScreen)
  const [page, setPage] = useState(getInitialPage)

  const handlePageChange = (nextPage) => {
    setPage(PAGE_TITLES[nextPage] ? nextPage : 'dashboard')
  }

  const pages = useMemo(
    () => ({
      dashboard: <Dashboard />,
      upload: <UploadPage />,
      predict: <Prediction />,
      risk: <RiskAnalysis />,
      performance: <Performance />,
      retention: <Retention />,
      reports: <Reports setPage={handlePageChange} />,
      settings: <Settings />,
      reviews: <ReviewsPage />,
    }),
    [handlePageChange]
  )


  useEffect(() => {
    if (screen === 'app') localStorage.setItem('churn_active_page', page)
  }, [page, screen])

  useEffect(() => {
    if (!localStorage.getItem('churn_token') && screen === 'app') {
      setScreen('landing')
      setPage('dashboard')
    }
  }, [screen])

  const goLogin = () => setScreen('login')
  const goLanding = () => setScreen('landing')

  const onLoginSuccess = () => {
    setScreen('app')
    setPage('dashboard')
    localStorage.setItem('churn_active_page', 'dashboard')
  }

  const logout = () => {
    localStorage.removeItem('churn_token')
    localStorage.removeItem('churn_user')
    localStorage.removeItem('churn_active_page')
    setScreen('landing')
    setPage('dashboard')
  }

  if (screen === 'landing') {
    return <Suspense fallback={<PageLoader />}><Landing onLogin={goLogin} /></Suspense>
  }

  if (screen === 'login') {
    return <Suspense fallback={<PageLoader />}><Login onSuccess={onLoginSuccess} onBack={goLanding} /></Suspense>
  }

  const CurrentPage = pages[page] || pages.dashboard
  const currentTitle = PAGE_TITLES[page] || PAGE_TITLES.dashboard

  return (
    <div className="ai-bg h-screen overflow-hidden flex text-white">
      <Sidebar page={page} setPage={handlePageChange} logout={logout} />
      <main className="flex-1 min-w-0 h-screen overflow-hidden flex flex-col">
        <Topbar title={currentTitle} page={page} setPage={handlePageChange} logout={logout} />
        <section className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-5 lg:p-8 pb-24 lg:pb-32 scroll-smooth">
          <Suspense fallback={<PageLoader />}>{CurrentPage}</Suspense>
        </section>
      </main>
    </div>
  )
}
