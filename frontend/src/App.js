import "@/App.css";
import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import axios from "axios";
import Dashboard from "@/pages/Dashboard";
import MenuManagement from "@/pages/MenuManagement";
import BillHistory from "@/pages/BillHistory";
import SalesReport from "@/pages/SalesReport";
import Settings from "@/pages/Settings";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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
          <Route path="/" element={<Dashboard />} />
          <Route path="/manage" element={<MenuManagement />} />
          <Route path="/history" element={<BillHistory />} />
          <Route path="/reports" element={<SalesReport />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
