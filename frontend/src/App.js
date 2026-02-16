import "@/App.css";
import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import axios from "axios";
import Dashboard from "@/pages/Dashboard";
import MenuManagement from "@/pages/MenuManagement";
import BillHistory from "@/pages/BillHistory";
import SalesReport from "@/pages/SalesReport";
import Settings from "@/pages/Settings";
import Login from "@/pages/Login";
import Inventory from "@/pages/Inventory";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Protected route wrapper
function ProtectedRoute({ children }) {
  const token = localStorage.getItem("token");
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  const [themeLoaded, setThemeLoaded] = useState(false);

  useEffect(() => {
    const loadTheme = async () => {
      try {
        const res = await axios.get(`${API}/config/theme`);
        const t = res.data;
        document.documentElement.style.setProperty('--theme-primary', t.primary_color);
        document.documentElement.style.setProperty('--theme-accent', t.accent_color);
        document.documentElement.style.setProperty('--theme-background', t.background_color);
        document.documentElement.style.setProperty('--theme-card', t.card_color);
        document.documentElement.style.setProperty('--theme-text', t.text_color);
        document.documentElement.style.setProperty('--theme-muted', t.muted_color);
        document.documentElement.style.setProperty('--theme-border', t.border_color);
      } catch (err) {
        console.error("Failed to load theme, using defaults");
      } finally {
        setThemeLoaded(true);
      }
    };
    loadTheme();
  }, []);

  if (!themeLoaded) {
    return <div className="min-h-screen bg-[#F8FAFC]" />;
  }

  return (
    <div className="app-container noise-bg">
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/manage" element={<ProtectedRoute><MenuManagement /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><BillHistory /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><SalesReport /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          <Route path="/inventory" element={<ProtectedRoute><Inventory /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
