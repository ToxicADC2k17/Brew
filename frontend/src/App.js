import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import Dashboard from "@/pages/Dashboard";
import MenuManagement from "@/pages/MenuManagement";
import BillHistory from "@/pages/BillHistory";
import SalesReport from "@/pages/SalesReport";

function App() {
  return (
    <div className="app-container noise-bg">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/manage" element={<MenuManagement />} />
          <Route path="/history" element={<BillHistory />} />
          <Route path="/reports" element={<SalesReport />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
