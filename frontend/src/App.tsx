import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import { AppLayout } from './layouts/AppLayout';
import { Login } from './pages/Login';
import { RawMaterials } from './pages/RawMaterials';
import { RawMaterialsStatus } from './pages/RawMaterialsStatus';
import { TrendAnalysis } from './pages/TrendAnalysis';
import { ThemeProvider } from './theme/ThemeProvider';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router basename={import.meta.env.BASE_URL}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/raw-materials" element={<RawMaterials />} />
              <Route path="/raw-materials/trend" element={<TrendAnalysis />} />
              <Route path="/raw-materials/status" element={<RawMaterialsStatus />} />
              <Route path="/" element={<Navigate to="/raw-materials" replace />} />
            </Route>
            <Route path="*" element={<Navigate to="/raw-materials" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
