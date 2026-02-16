import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Coffee, Settings, Plus, Minus, Trash2, Printer, Download, Receipt, History, BarChart3, Cog, X, Check } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CURRENCIES = [
  { code: "EUR", symbol: "€", name: "Euro" },
  { code: "USD", symbol: "$", name: "US Dollar" },
  { code: "GBP", symbol: "£", name: "British Pound" },
  { code: "BRL", symbol: "R$", name: "Brazilian Real" },
  { code: "CHF", symbol: "CHF", name: "Swiss Franc" },
];

export default function Dashboard() {
  const [menuItems, setMenuItems] = useState([]);
  const [categories, setCategories] = useState(["All"]);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [orderItems, setOrderItems] = useState([]);
  const [discountPercent, setDiscountPercent] = useState(0);
  const [taxPercent, setTaxPercent] = useState(23); // Portugal IVA
  const [currency, setCurrency] = useState("EUR");
  const [customerName, setCustomerName] = useState("");
  const [tableNumber, setTableNumber] = useState("");
  const [nif, setNif] = useState("");
  const [loading, setLoading] = useState(true);
  const [generatedBill, setGeneratedBill] = useState(null);
  const [modifiers, setModifiers] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedModifiers, setSelectedModifiers] = useState({});
  const [isModifierDialogOpen, setIsModifierDialogOpen] = useState(false);
  const billRef = useRef(null);

  const currencySymbol = CURRENCIES.find(c => c.code === currency)?.symbol || "€";

  useEffect(() => {
    fetchMenu();
    fetchCategories();
  }, []);

  const fetchMenu = async () => {
    try {
      const res = await axios.get(`${API}/menu`);
      setMenuItems(res.data.filter(item => item.available));
    } catch (err) {
      toast.error("Failed to load menu");
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/menu/categories`);
      setCategories(["All", ...res.data]);
    } catch (err) {
      console.error("Failed to load categories");
    }
  };

  const filteredItems = selectedCategory === "All" 
    ? menuItems 
    : menuItems.filter(item => item.category === selectedCategory);

  const addToOrder = (item) => {
    setGeneratedBill(null);
    const existing = orderItems.find(o => o.menu_item_id === item.id);
    if (existing) {
      setOrderItems(orderItems.map(o => 
        o.menu_item_id === item.id ? { ...o, quantity: o.quantity + 1 } : o
      ));
    } else {
      setOrderItems([...orderItems, {
        menu_item_id: item.id,
        name: item.name,
        price: item.price,
        quantity: 1
      }]);
    }
    toast.success(`Added ${item.name}`);
  };

  const updateQuantity = (itemId, delta) => {
    setGeneratedBill(null);
    setOrderItems(orderItems.map(o => {
      if (o.menu_item_id === itemId) {
        const newQty = o.quantity + delta;
        return newQty > 0 ? { ...o, quantity: newQty } : o;
      }
      return o;
    }).filter(o => o.quantity > 0));
  };

  const removeFromOrder = (itemId) => {
    setGeneratedBill(null);
    setOrderItems(orderItems.filter(o => o.menu_item_id !== itemId));
    toast.info("Item removed");
  };

  const clearOrder = () => {
    setOrderItems([]);
    setDiscountPercent(0);
    setCustomerName("");
    setTableNumber("");
    setNif("");
    setGeneratedBill(null);
    toast.info("Order cleared");
  };

  const subtotal = orderItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const discountAmount = subtotal * (discountPercent / 100);
  const taxableAmount = subtotal - discountAmount;
  const taxAmount = taxableAmount * (taxPercent / 100);
  const total = taxableAmount + taxAmount;

  const generateBill = async () => {
    if (orderItems.length === 0) {
      toast.error("Add items to generate bill");
      return;
    }
    try {
      const res = await axios.post(`${API}/bills`, {
        items: orderItems,
        discount_percent: discountPercent,
        tax_percent: taxPercent,
        customer_name: customerName,
        table_number: tableNumber,
        nif: nif,
        currency: currency
      });
      setGeneratedBill(res.data);
      toast.success(`Bill #${res.data.bill_number} generated!`);
    } catch (err) {
      toast.error("Failed to generate bill");
    }
  };

  const printBill = () => {
    if (billRef.current) {
      const printContent = billRef.current.innerHTML;
      const printWindow = window.open('', '', 'width=400,height=700');
      printWindow.document.write(`
        <html>
          <head>
            <title>Bill #${generatedBill?.bill_number || 'Receipt'}</title>
            <style>
              body { font-family: 'Courier New', monospace; padding: 20px; max-width: 300px; margin: 0 auto; font-size: 12px; }
              .header { text-align: center; margin-bottom: 15px; }
              .header h2 { margin: 0; font-size: 18px; }
              .info { margin: 10px 0; }
              .line { border-top: 1px dashed #000; margin: 10px 0; }
              .item { display: flex; justify-content: space-between; margin: 5px 0; }
              .total { font-weight: bold; font-size: 14px; }
              .footer { text-align: center; margin-top: 15px; font-size: 11px; }
            </style>
          </head>
          <body>${printContent}</body>
        </html>
      `);
      printWindow.document.close();
      printWindow.print();
    }
  };

  const downloadBill = () => {
    if (!generatedBill) return;
    const sym = CURRENCIES.find(c => c.code === generatedBill.currency)?.symbol || "€";
    const billText = `
========================================
           CAFE BREW HOUSE
========================================
Bill #: ${generatedBill.bill_number}
Date: ${new Date(generatedBill.created_at).toLocaleString()}
${generatedBill.customer_name ? `Customer: ${generatedBill.customer_name}` : ''}
${generatedBill.table_number ? `Table: ${generatedBill.table_number}` : ''}
${generatedBill.nif ? `NIF: ${generatedBill.nif}` : ''}
----------------------------------------
ITEMS:
${generatedBill.items.map(i => `${i.name} x${i.quantity}\n  ${sym}${(i.price * i.quantity).toFixed(2)}`).join('\n')}
----------------------------------------
Subtotal:      ${sym}${generatedBill.subtotal.toFixed(2)}
${generatedBill.discount_percent > 0 ? `Discount(${generatedBill.discount_percent}%): -${sym}${generatedBill.discount_amount.toFixed(2)}` : ''}
IVA/Tax(${generatedBill.tax_percent}%): ${sym}${generatedBill.tax_amount.toFixed(2)}
========================================
TOTAL:         ${sym}${generatedBill.total.toFixed(2)}
========================================
        Thank you for visiting!
         Cafe Brew House
    `;
    const blob = new Blob([billText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bill-${generatedBill.bill_number}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Bill downloaded");
  };

  return (
    <div className="min-h-screen" data-testid="dashboard">
      {/* Header */}
      <header className="bg-[#2C1A1D] text-white px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Coffee className="w-8 h-8 text-[#D97706]" />
            <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'Manrope' }}>
              Cafe Brew House
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Link to="/history">
              <Button 
                variant="ghost" 
                className="text-white hover:bg-white/10 btn-press"
                data-testid="bill-history-btn"
              >
                <History className="w-4 h-4 mr-2" />
                History
              </Button>
            </Link>
            <Link to="/reports">
              <Button 
                variant="ghost" 
                className="text-white hover:bg-white/10 btn-press"
                data-testid="sales-report-btn"
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                Reports
              </Button>
            </Link>
            <Link to="/manage">
              <Button 
                variant="outline" 
                className="border-[#D97706] text-[#D97706] hover:bg-[#D97706] hover:text-white btn-press"
                data-testid="manage-menu-btn"
              >
                <Settings className="w-4 h-4 mr-2" />
                Manage Menu
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Menu Section */}
          <div className="lg:col-span-8">
            {/* Category Filter */}
            <div className="flex flex-wrap gap-2 mb-6" data-testid="category-filter">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`category-pill btn-press ${selectedCategory === cat ? 'active' : 'inactive'}`}
                  data-testid={`category-${cat.toLowerCase()}`}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Menu Grid */}
            {loading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1,2,3,4,5,6].map(i => (
                  <div key={i} className="h-48 bg-muted animate-pulse rounded-lg" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="menu-grid">
                {filteredItems.map(item => (
                  <div 
                    key={item.id} 
                    className="menu-item-card menu-card-hover p-4 flex flex-col"
                    data-testid={`menu-item-${item.id}`}
                  >
                    <div className="flex-1">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-bold text-lg text-foreground" style={{ fontFamily: 'Manrope' }}>
                          {item.name}
                        </h3>
                        <span className="price-tag text-[#D97706] font-semibold">
                          {currencySymbol}{item.price.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-muted-foreground text-sm mb-3">{item.description}</p>
                      <span className="inline-block px-2 py-1 bg-secondary text-secondary-foreground text-xs rounded">
                        {item.category}
                      </span>
                    </div>
                    <Button 
                      onClick={() => addToOrder(item)}
                      className="mt-4 w-full bg-[#2C1A1D] hover:bg-[#3d2628] btn-press"
                      data-testid={`add-${item.name.toLowerCase().replace(/\s+/g, '-')}-btn`}
                    >
                      <Plus className="w-4 h-4 mr-2" /> Add to Order
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Bill Panel */}
          <div className="lg:col-span-4">
            <div className="bill-panel sticky top-4 p-6" data-testid="bill-panel">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Receipt className="w-5 h-5 text-[#D97706]" />
                  <h2 className="text-xl font-bold" style={{ fontFamily: 'Manrope' }}>Current Order</h2>
                </div>
                <Select value={currency} onValueChange={setCurrency}>
                  <SelectTrigger className="w-24 h-8" data-testid="currency-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CURRENCIES.map(c => (
                      <SelectItem key={c.code} value={c.code}>{c.symbol} {c.code}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {orderItems.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Coffee className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>No items yet</p>
                  <p className="text-sm">Add items from the menu</p>
                </div>
              ) : (
                <>
                  <ScrollArea className="h-[200px] pr-4">
                    {orderItems.map(item => (
                      <div key={item.menu_item_id} className="flex items-center justify-between py-3 border-b border-border" data-testid={`order-item-${item.menu_item_id}`}>
                        <div className="flex-1">
                          <p className="font-medium text-sm">{item.name}</p>
                          <p className="price-tag text-xs text-muted-foreground">
                            {currencySymbol}{item.price.toFixed(2)} each
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <button 
                            onClick={() => updateQuantity(item.menu_item_id, -1)}
                            className="qty-btn"
                            data-testid={`decrease-${item.menu_item_id}`}
                          >
                            <Minus className="w-3 h-3" />
                          </button>
                          <span className="price-tag w-8 text-center font-medium">{item.quantity}</span>
                          <button 
                            onClick={() => updateQuantity(item.menu_item_id, 1)}
                            className="qty-btn"
                            data-testid={`increase-${item.menu_item_id}`}
                          >
                            <Plus className="w-3 h-3" />
                          </button>
                          <button 
                            onClick={() => removeFromOrder(item.menu_item_id)}
                            className="ml-2 text-destructive hover:text-destructive/80"
                            data-testid={`remove-${item.menu_item_id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </ScrollArea>

                  <Separator className="my-4" />

                  {/* Customer Info */}
                  <div className="space-y-3 mb-4">
                    <div className="flex items-center gap-3">
                      <label className="text-sm text-muted-foreground w-20">Customer</label>
                      <Input 
                        value={customerName}
                        onChange={(e) => setCustomerName(e.target.value)}
                        placeholder="Name (optional)"
                        className="h-8 text-sm"
                        data-testid="customer-name-input"
                      />
                    </div>
                    <div className="flex items-center gap-3">
                      <label className="text-sm text-muted-foreground w-20">Table #</label>
                      <Input 
                        value={tableNumber}
                        onChange={(e) => setTableNumber(e.target.value)}
                        placeholder="Table (optional)"
                        className="h-8 text-sm"
                        data-testid="table-number-input"
                      />
                    </div>
                    <div className="flex items-center gap-3">
                      <label className="text-sm text-muted-foreground w-20">NIF</label>
                      <Input 
                        value={nif}
                        onChange={(e) => setNif(e.target.value)}
                        placeholder="NIF (optional)"
                        className="h-8 text-sm price-tag"
                        data-testid="nif-input"
                      />
                    </div>
                  </div>

                  <Separator className="my-4" />

                  {/* Discount & Tax */}
                  <div className="flex items-center gap-3 mb-3">
                    <label className="text-sm text-muted-foreground w-20">Discount %</label>
                    <Input 
                      type="number"
                      min="0"
                      max="100"
                      value={discountPercent}
                      onChange={(e) => {
                        setGeneratedBill(null);
                        setDiscountPercent(Math.min(100, Math.max(0, Number(e.target.value))));
                      }}
                      className="price-tag h-8"
                      data-testid="discount-input"
                    />
                  </div>

                  <div className="flex items-center gap-3 mb-4">
                    <label className="text-sm text-muted-foreground w-20">Tax/IVA %</label>
                    <Input 
                      type="number"
                      min="0"
                      max="100"
                      value={taxPercent}
                      onChange={(e) => {
                        setGeneratedBill(null);
                        setTaxPercent(Math.min(100, Math.max(0, Number(e.target.value))));
                      }}
                      className="price-tag h-8"
                      data-testid="tax-input"
                    />
                  </div>

                  <Separator className="my-4" />

                  {/* Calculations */}
                  <div className="space-y-2 price-tag text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Subtotal</span>
                      <span>{currencySymbol}{subtotal.toFixed(2)}</span>
                    </div>
                    {discountPercent > 0 && (
                      <div className="flex justify-between text-green-700">
                        <span>Discount ({discountPercent}%)</span>
                        <span>-{currencySymbol}{discountAmount.toFixed(2)}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">IVA/Tax ({taxPercent}%)</span>
                      <span>{currencySymbol}{taxAmount.toFixed(2)}</span>
                    </div>
                    <Separator className="my-2" />
                    <div className="flex justify-between text-lg font-bold">
                      <span>Total</span>
                      <span className="text-[#D97706]">{currencySymbol}{total.toFixed(2)}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="mt-6 space-y-2">
                    <Button 
                      onClick={generateBill}
                      className="w-full bg-[#D97706] hover:bg-[#b86505] btn-press"
                      data-testid="generate-bill-btn"
                    >
                      <Receipt className="w-4 h-4 mr-2" /> Generate Bill
                    </Button>
                    
                    {generatedBill && (
                      <div className="flex gap-2">
                        <Button 
                          onClick={printBill}
                          variant="outline"
                          className="flex-1 btn-press"
                          data-testid="print-bill-btn"
                        >
                          <Printer className="w-4 h-4 mr-2" /> Print
                        </Button>
                        <Button 
                          onClick={downloadBill}
                          variant="outline"
                          className="flex-1 btn-press"
                          data-testid="download-bill-btn"
                        >
                          <Download className="w-4 h-4 mr-2" /> Download
                        </Button>
                      </div>
                    )}
                    
                    <Button 
                      onClick={clearOrder}
                      variant="ghost"
                      className="w-full text-destructive hover:text-destructive hover:bg-destructive/10 btn-press"
                      data-testid="clear-order-btn"
                    >
                      <Trash2 className="w-4 h-4 mr-2" /> Clear Order
                    </Button>
                  </div>
                </>
              )}

              {/* Hidden print template */}
              {generatedBill && (
                <div ref={billRef} className="hidden print-area">
                  <div className="header">
                    <h2>CAFE BREW HOUSE</h2>
                    <p>Bill #{generatedBill.bill_number}</p>
                    <p>{new Date(generatedBill.created_at).toLocaleString()}</p>
                  </div>
                  {(generatedBill.customer_name || generatedBill.table_number || generatedBill.nif) && (
                    <div className="info">
                      {generatedBill.customer_name && <p>Customer: {generatedBill.customer_name}</p>}
                      {generatedBill.table_number && <p>Table: {generatedBill.table_number}</p>}
                      {generatedBill.nif && <p>NIF: {generatedBill.nif}</p>}
                    </div>
                  )}
                  <div className="line"></div>
                  {generatedBill.items.map((item, idx) => (
                    <div key={idx} className="item">
                      <span>{item.name} x{item.quantity}</span>
                      <span>{CURRENCIES.find(c => c.code === generatedBill.currency)?.symbol || "€"}{(item.price * item.quantity).toFixed(2)}</span>
                    </div>
                  ))}
                  <div className="line"></div>
                  <div className="item"><span>Subtotal</span><span>{CURRENCIES.find(c => c.code === generatedBill.currency)?.symbol || "€"}{generatedBill.subtotal.toFixed(2)}</span></div>
                  {generatedBill.discount_percent > 0 && (
                    <div className="item"><span>Discount ({generatedBill.discount_percent}%)</span><span>-{CURRENCIES.find(c => c.code === generatedBill.currency)?.symbol || "€"}{generatedBill.discount_amount.toFixed(2)}</span></div>
                  )}
                  <div className="item"><span>IVA/Tax ({generatedBill.tax_percent}%)</span><span>{CURRENCIES.find(c => c.code === generatedBill.currency)?.symbol || "€"}{generatedBill.tax_amount.toFixed(2)}</span></div>
                  <div className="line"></div>
                  <div className="item total"><span>TOTAL</span><span>{CURRENCIES.find(c => c.code === generatedBill.currency)?.symbol || "€"}{generatedBill.total.toFixed(2)}</span></div>
                  <div className="footer">
                    <p>Thank you for visiting!</p>
                    <p>Cafe Brew House</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
