import { BrowserRouter } from 'react-router-dom'
import { Provider } from 'react-redux'
import { store } from '@/store'
import { AppProvider } from '@/context/AppContext'
import { ThemeProvider } from '@/context/ThemeProvider'
import { ToastProvider } from '@/context/ToastContext'
import { DashboardActionProvider } from '@/context/DashboardActionContext'
import { AppRoutes } from '@/routes'
import { AuthProvider } from '@/auth/AuthContext'

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <ToastProvider>
          <AuthProvider>
            <AppProvider>
              <BrowserRouter>
                <DashboardActionProvider>
                  <AppRoutes />
                </DashboardActionProvider>
              </BrowserRouter>
            </AppProvider>
          </AuthProvider>
        </ToastProvider>
      </ThemeProvider>
    </Provider>
  )
}

export default App


