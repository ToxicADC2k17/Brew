import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Coffee, ArrowLeft, Search, Eye, Download, Calendar } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CURRENCIES = {
  EUR: "€", USD: "$", GBP: "£", BRL: "R$", CHF: "CHF"
};

export default function BillHistory() {
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [selectedBill, setSelectedBill] = useState(null);

  useEffect(() => {
    fetchBills();
  }, []);

  const fetchBills = async () => {
    try {
      let url = `${API}/bills`;
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (searchTerm) params.append('search', searchTerm);
      if (params.toString()) url += `?${params.toString()}`;
      
      const res = await axios.get(url);
      setBills(res.data);
    } catch (err) {
      toast.error("Failed to load bills");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setLoading(true);
    fetchBills();
  };

  const clearFilters = () => {
    setSearchTerm("");
    setStartDate("");
    setEndDate("");
    setLoading(true);
    setTimeout(() => {
      axios.get(`${API}/bills`).then(res => {
        setBills(res.data);
        setLoading(false);
      });
    }, 100);
  };

  const downloadBill = (bill) => {
    const sym = CURRENCIES[bill.currency] || "€";
    const billText = `
========================================
           CAFE BREW HOUSE
========================================
Bill #: ${bill.bill_number}
Date: ${new Date(bill.created_at).toLocaleString()}
${bill.customer_name ? `Customer: ${bill.customer_name}` : ''}
${bill.table_number ? `Table: ${bill.table_number}` : ''}
${bill.nif ? `NIF: ${bill.nif}` : ''}
----------------------------------------
ITEMS:
${bill.items.map(i => `${i.name} x${i.quantity}\n  ${sym}${(i.price * i.quantity).toFixed(2)}`).join('\n')}
----------------------------------------
Subtotal:      ${sym}${bill.subtotal.toFixed(2)}
${bill.discount_percent > 0 ? `Discount(${bill.discount_percent}%): -${sym}${bill.discount_amount.toFixed(2)}` : ''}
IVA/Tax(${bill.tax_percent}%): ${sym}${bill.tax_amount.toFixed(2)}
========================================
TOTAL:         ${sym}${bill.total.toFixed(2)}
========================================
    `;
    const blob = new Blob([billText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bill-${bill.bill_number}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Bill downloaded");
  };

  const getCurrencySymbol = (currency) => CURRENCIES[currency] || "€";

  return (
    <div className="min-h-screen" data-testid="bill-history">
      {/* Header */}
      <header className="bg-[#2C1A1D] text-white px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Coffee className="w-8 h-8 text-[#D97706]" />
            <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'Manrope' }}>
              Bill History
            </h1>
          </div>
          <Link to="/">
            <Button 
              variant="outline" 
              className="border-[#D97706] text-[#D97706] hover:bg-[#D97706] hover:text-white btn-press"
              data-testid="back-to-billing-btn"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Billing
            </Button>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-6">
        <div className="bg-card border border-border rounded-lg p-6">
          {/* Filters */}
          <div className="flex flex-wrap items-end gap-4 mb-6">
            <div className="flex-1 min-w-[200px]">
              <label className="text-sm text-muted-foreground block mb-1">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Customer, NIF, or Table..."
                  className="pl-10"
                  data-testid="search-input"
                />
              </div>
            </div>
            <div>
              <label className="text-sm text-muted-foreground block mb-1">From</label>
              <Input 
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-40"
                data-testid="start-date-input"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground block mb-1">To</label>
              <Input 
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-40"
                data-testid="end-date-input"
              />
            </div>
            <Button 
              onClick={handleSearch}
              className="bg-[#2C1A1D] hover:bg-[#3d2628]"
              data-testid="search-btn"
            >
              <Search className="w-4 h-4 mr-2" /> Search
            </Button>
            <Button 
              onClick={clearFilters}
              variant="outline"
              data-testid="clear-filters-btn"
            >
              Clear
            </Button>
          </div>

          {/* Results count */}
          <p className="text-sm text-muted-foreground mb-4">
            {bills.length} bill{bills.length !== 1 ? 's' : ''} found
          </p>

          {/* Bills Table */}
          {loading ? (
            <div className="space-y-3">
              {[1,2,3,4,5].map(i => (
                <div key={i} className="h-14 bg-muted animate-pulse rounded" />
              ))}
            </div>
          ) : bills.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Calendar className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No bills found</p>
              <p className="text-sm">Try adjusting your filters</p>
            </div>
          ) : (
            <div className="border border-border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50">
                    <TableHead>Bill #</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Table</TableHead>
                    <TableHead>NIF</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {bills.map(bill => (
                    <TableRow key={bill.id} data-testid={`bill-row-${bill.id}`}>
                      <TableCell className="font-mono font-medium">#{bill.bill_number}</TableCell>
                      <TableCell className="text-sm">
                        {new Date(bill.created_at).toLocaleDateString()}
                        <br />
                        <span className="text-muted-foreground text-xs">
                          {new Date(bill.created_at).toLocaleTimeString()}
                        </span>
                      </TableCell>
                      <TableCell>{bill.customer_name || "-"}</TableCell>
                      <TableCell>{bill.table_number || "-"}</TableCell>
                      <TableCell className="font-mono text-sm">{bill.nif || "-"}</TableCell>
                      <TableCell className="text-right font-mono font-semibold text-[#D97706]">
                        {getCurrencySymbol(bill.currency)}{bill.total.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button 
                                size="sm" 
                                variant="ghost" 
                                onClick={() => setSelectedBill(bill)}
                                className="h-8 w-8 p-0"
                                data-testid={`view-${bill.id}`}
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-md">
                              <DialogHeader>
                                <DialogTitle style={{ fontFamily: 'Manrope' }}>
                                  Bill #{bill.bill_number}
                                </DialogTitle>
                              </DialogHeader>
                              <div className="font-mono text-sm space-y-3 mt-4">
                                <p className="text-muted-foreground">
                                  {new Date(bill.created_at).toLocaleString()}
                                </p>
                                {bill.customer_name && <p>Customer: {bill.customer_name}</p>}
                                {bill.table_number && <p>Table: {bill.table_number}</p>}
                                {bill.nif && <p>NIF: {bill.nif}</p>}
                                <hr className="border-dashed" />
                                <div className="space-y-1">
                                  {bill.items.map((item, idx) => (
                                    <div key={idx} className="flex justify-between">
                                      <span>{item.name} x{item.quantity}</span>
                                      <span>{getCurrencySymbol(bill.currency)}{(item.price * item.quantity).toFixed(2)}</span>
                                    </div>
                                  ))}
                                </div>
                                <hr className="border-dashed" />
                                <div className="flex justify-between"><span>Subtotal</span><span>{getCurrencySymbol(bill.currency)}{bill.subtotal.toFixed(2)}</span></div>
                                {bill.discount_percent > 0 && (
                                  <div className="flex justify-between text-green-700">
                                    <span>Discount ({bill.discount_percent}%)</span>
                                    <span>-{getCurrencySymbol(bill.currency)}{bill.discount_amount.toFixed(2)}</span>
                                  </div>
                                )}
                                <div className="flex justify-between"><span>IVA/Tax ({bill.tax_percent}%)</span><span>{getCurrencySymbol(bill.currency)}{bill.tax_amount.toFixed(2)}</span></div>
                                <hr />
                                <div className="flex justify-between font-bold text-lg">
                                  <span>TOTAL</span>
                                  <span className="text-[#D97706]">{getCurrencySymbol(bill.currency)}{bill.total.toFixed(2)}</span>
                                </div>
                              </div>
                            </DialogContent>
                          </Dialog>
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            onClick={() => downloadBill(bill)}
                            className="h-8 w-8 p-0"
                            data-testid={`download-${bill.id}`}
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
