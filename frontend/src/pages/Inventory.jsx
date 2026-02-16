import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Coffee, ArrowLeft, Plus, Package, AlertTriangle, TrendingUp, History, Truck, Edit, Trash2 } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Inventory() {
  const navigate = useNavigate();
  const [inventory, setInventory] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [menuItems, setMenuItems] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Dialogs
  const [isInventoryDialogOpen, setIsInventoryDialogOpen] = useState(false);
  const [isSupplierDialogOpen, setIsSupplierDialogOpen] = useState(false);
  const [isAdjustDialogOpen, setIsAdjustDialogOpen] = useState(false);
  const [isHistoryDialogOpen, setIsHistoryDialogOpen] = useState(false);
  
  // Form data
  const [inventoryForm, setInventoryForm] = useState({
    menu_item_id: "",
    current_stock: 0,
    min_stock_level: 10,
    max_stock_level: 100,
    cost_price: 0,
    supplier_id: "",
    unit: "units"
  });
  const [supplierForm, setSupplierForm] = useState({
    name: "",
    contact_name: "",
    email: "",
    phone: "",
    address: "",
    notes: ""
  });
  const [adjustForm, setAdjustForm] = useState({
    inventory_id: "",
    quantity: 0,
    transaction_type: "restock",
    notes: ""
  });
  const [selectedHistory, setSelectedHistory] = useState([]);
  const [editingSupplier, setEditingSupplier] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }
    fetchData();
  }, [navigate]);

  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
  });

  const fetchData = async () => {
    try {
      const [invRes, lowRes, supRes, menuRes, transRes] = await Promise.all([
        axios.get(`${API}/inventory`),
        axios.get(`${API}/inventory/low-stock`),
        axios.get(`${API}/suppliers`),
        axios.get(`${API}/menu`),
        axios.get(`${API}/stock-transactions?limit=50`)
      ]);
      setInventory(invRes.data);
      setLowStock(lowRes.data);
      setSuppliers(supRes.data);
      setMenuItems(menuRes.data);
      setTransactions(transRes.data);
    } catch (err) {
      if (err.response?.status === 401) {
        navigate("/login");
      } else {
        toast.error("Failed to load data");
      }
    } finally {
      setLoading(false);
    }
  };

  // Get menu items not yet in inventory
  const availableMenuItems = menuItems.filter(
    m => !inventory.some(i => i.menu_item_id === m.id)
  );

  const handleCreateInventory = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/inventory`, inventoryForm, getAuthHeaders());
      toast.success("Inventory item created");
      setIsInventoryDialogOpen(false);
      setInventoryForm({
        menu_item_id: "",
        current_stock: 0,
        min_stock_level: 10,
        max_stock_level: 100,
        cost_price: 0,
        supplier_id: "",
        unit: "units"
      });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create inventory");
    }
  };

  const handleCreateSupplier = async (e) => {
    e.preventDefault();
    try {
      if (editingSupplier) {
        await axios.put(`${API}/suppliers/${editingSupplier}`, supplierForm, getAuthHeaders());
        toast.success("Supplier updated");
      } else {
        await axios.post(`${API}/suppliers`, supplierForm, getAuthHeaders());
        toast.success("Supplier created");
      }
      setIsSupplierDialogOpen(false);
      setEditingSupplier(null);
      setSupplierForm({ name: "", contact_name: "", email: "", phone: "", address: "", notes: "" });
      fetchData();
    } catch (err) {
      toast.error("Failed to save supplier");
    }
  };

  const handleDeleteSupplier = async (id) => {
    if (!window.confirm("Delete this supplier?")) return;
    try {
      await axios.delete(`${API}/suppliers/${id}`, getAuthHeaders());
      toast.success("Supplier deleted");
      fetchData();
    } catch (err) {
      toast.error("Failed to delete supplier");
    }
  };

  const handleAdjustStock = async (e) => {
    e.preventDefault();
    try {
      await axios.post(
        `${API}/inventory/${adjustForm.inventory_id}/adjust`,
        {
          quantity: adjustForm.quantity,
          transaction_type: adjustForm.transaction_type,
          notes: adjustForm.notes
        },
        getAuthHeaders()
      );
      toast.success("Stock adjusted");
      setIsAdjustDialogOpen(false);
      setAdjustForm({ inventory_id: "", quantity: 0, transaction_type: "restock", notes: "" });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to adjust stock");
    }
  };

  const openAdjustDialog = (inv) => {
    setAdjustForm({ ...adjustForm, inventory_id: inv.id });
    setIsAdjustDialogOpen(true);
  };

  const openHistoryDialog = async (inv) => {
    try {
      const res = await axios.get(`${API}/inventory/${inv.id}/history`);
      setSelectedHistory(res.data);
      setIsHistoryDialogOpen(true);
    } catch (err) {
      toast.error("Failed to load history");
    }
  };

  const editSupplier = (supplier) => {
    setSupplierForm(supplier);
    setEditingSupplier(supplier.id);
    setIsSupplierDialogOpen(true);
  };

  const getStockStatus = (item) => {
    if (item.current_stock <= item.min_stock_level) return "critical";
    if (item.current_stock <= item.min_stock_level * 1.5) return "low";
    return "ok";
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--theme-background)' }} data-testid="inventory-page">
      {/* Header */}
      <header className="themed-header text-white px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Package className="w-8 h-8 themed-accent" />
            <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'Manrope' }}>
              Inventory Management
            </h1>
          </div>
          <Link to="/">
            <Button 
              variant="outline" 
              className="border-[var(--theme-accent)] text-[var(--theme-accent)] hover:bg-[var(--theme-accent)] hover:text-white"
              data-testid="back-to-billing-btn"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Billing
            </Button>
          </Link>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Items</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{inventory.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-500" /> Low Stock
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-500">{lowStock.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Suppliers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{suppliers.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Recent Transactions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{transactions.length}</div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="inventory" className="space-y-4">
          <TabsList>
            <TabsTrigger value="inventory" data-testid="inventory-tab">
              <Package className="w-4 h-4 mr-2" /> Inventory
            </TabsTrigger>
            <TabsTrigger value="suppliers" data-testid="suppliers-tab">
              <Truck className="w-4 h-4 mr-2" /> Suppliers
            </TabsTrigger>
            <TabsTrigger value="transactions" data-testid="transactions-tab">
              <History className="w-4 h-4 mr-2" /> Transactions
            </TabsTrigger>
          </TabsList>

          {/* Inventory Tab */}
          <TabsContent value="inventory">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Stock Levels</CardTitle>
                <Dialog open={isInventoryDialogOpen} onOpenChange={setIsInventoryDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="themed-accent-btn text-white" data-testid="add-inventory-btn">
                      <Plus className="w-4 h-4 mr-2" /> Add Item
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add Inventory Item</DialogTitle>
                      <DialogDescription>Track stock for a menu item</DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleCreateInventory} className="space-y-4">
                      <div>
                        <Label>Menu Item</Label>
                        <Select
                          value={inventoryForm.menu_item_id}
                          onValueChange={(v) => setInventoryForm({ ...inventoryForm, menu_item_id: v })}
                        >
                          <SelectTrigger data-testid="menu-item-select">
                            <SelectValue placeholder="Select item" />
                          </SelectTrigger>
                          <SelectContent>
                            {availableMenuItems.map(item => (
                              <SelectItem key={item.id} value={item.id}>{item.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>Current Stock</Label>
                          <Input
                            type="number"
                            value={inventoryForm.current_stock}
                            onChange={(e) => setInventoryForm({ ...inventoryForm, current_stock: parseInt(e.target.value) })}
                            data-testid="current-stock-input"
                          />
                        </div>
                        <div>
                          <Label>Unit</Label>
                          <Select
                            value={inventoryForm.unit}
                            onValueChange={(v) => setInventoryForm({ ...inventoryForm, unit: v })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="units">Units</SelectItem>
                              <SelectItem value="kg">Kilograms</SelectItem>
                              <SelectItem value="liters">Liters</SelectItem>
                              <SelectItem value="boxes">Boxes</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>Min Stock Level</Label>
                          <Input
                            type="number"
                            value={inventoryForm.min_stock_level}
                            onChange={(e) => setInventoryForm({ ...inventoryForm, min_stock_level: parseInt(e.target.value) })}
                          />
                        </div>
                        <div>
                          <Label>Max Stock Level</Label>
                          <Input
                            type="number"
                            value={inventoryForm.max_stock_level}
                            onChange={(e) => setInventoryForm({ ...inventoryForm, max_stock_level: parseInt(e.target.value) })}
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>Cost Price (€)</Label>
                          <Input
                            type="number"
                            step="0.01"
                            value={inventoryForm.cost_price}
                            onChange={(e) => setInventoryForm({ ...inventoryForm, cost_price: parseFloat(e.target.value) })}
                            data-testid="cost-price-input"
                          />
                        </div>
                        <div>
                          <Label>Supplier</Label>
                          <Select
                            value={inventoryForm.supplier_id}
                            onValueChange={(v) => setInventoryForm({ ...inventoryForm, supplier_id: v })}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select supplier" />
                            </SelectTrigger>
                            <SelectContent>
                              {suppliers.map(s => (
                                <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <Button type="submit" className="w-full themed-accent-btn text-white" data-testid="save-inventory-btn">
                        Add to Inventory
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item</TableHead>
                      <TableHead>Stock</TableHead>
                      <TableHead>Min/Max</TableHead>
                      <TableHead>Cost</TableHead>
                      <TableHead>Supplier</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {inventory.map(item => {
                      const status = getStockStatus(item);
                      return (
                        <TableRow key={item.id} data-testid={`inventory-row-${item.id}`}>
                          <TableCell className="font-medium">{item.menu_item_name}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <span>{item.current_stock} {item.unit}</span>
                              {status === "critical" && (
                                <Badge variant="destructive">Low</Badge>
                              )}
                              {status === "low" && (
                                <Badge variant="outline" className="border-yellow-500 text-yellow-600">Warning</Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {item.min_stock_level} / {item.max_stock_level}
                          </TableCell>
                          <TableCell>€{item.cost_price?.toFixed(2)}</TableCell>
                          <TableCell>{item.supplier_name || "-"}</TableCell>
                          <TableCell>
                            <div className="flex gap-2">
                              <Button size="sm" variant="outline" onClick={() => openAdjustDialog(item)} data-testid={`adjust-${item.id}`}>
                                <TrendingUp className="w-4 h-4" />
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => openHistoryDialog(item)}>
                                <History className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                    {inventory.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                          No inventory items. Add items to start tracking stock.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Suppliers Tab */}
          <TabsContent value="suppliers">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Suppliers</CardTitle>
                <Dialog open={isSupplierDialogOpen} onOpenChange={(open) => {
                  setIsSupplierDialogOpen(open);
                  if (!open) {
                    setEditingSupplier(null);
                    setSupplierForm({ name: "", contact_name: "", email: "", phone: "", address: "", notes: "" });
                  }
                }}>
                  <DialogTrigger asChild>
                    <Button className="themed-accent-btn text-white" data-testid="add-supplier-btn">
                      <Plus className="w-4 h-4 mr-2" /> Add Supplier
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{editingSupplier ? "Edit Supplier" : "Add Supplier"}</DialogTitle>
                      <DialogDescription>Manage your suppliers</DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleCreateSupplier} className="space-y-4">
                      <div>
                        <Label>Company Name *</Label>
                        <Input
                          value={supplierForm.name}
                          onChange={(e) => setSupplierForm({ ...supplierForm, name: e.target.value })}
                          required
                          data-testid="supplier-name-input"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>Contact Name</Label>
                          <Input
                            value={supplierForm.contact_name}
                            onChange={(e) => setSupplierForm({ ...supplierForm, contact_name: e.target.value })}
                          />
                        </div>
                        <div>
                          <Label>Phone</Label>
                          <Input
                            value={supplierForm.phone}
                            onChange={(e) => setSupplierForm({ ...supplierForm, phone: e.target.value })}
                          />
                        </div>
                      </div>
                      <div>
                        <Label>Email</Label>
                        <Input
                          type="email"
                          value={supplierForm.email}
                          onChange={(e) => setSupplierForm({ ...supplierForm, email: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label>Address</Label>
                        <Input
                          value={supplierForm.address}
                          onChange={(e) => setSupplierForm({ ...supplierForm, address: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label>Notes</Label>
                        <Input
                          value={supplierForm.notes}
                          onChange={(e) => setSupplierForm({ ...supplierForm, notes: e.target.value })}
                        />
                      </div>
                      <Button type="submit" className="w-full themed-accent-btn text-white" data-testid="save-supplier-btn">
                        {editingSupplier ? "Update Supplier" : "Add Supplier"}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Company</TableHead>
                      <TableHead>Contact</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Phone</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {suppliers.map(supplier => (
                      <TableRow key={supplier.id}>
                        <TableCell className="font-medium">{supplier.name}</TableCell>
                        <TableCell>{supplier.contact_name || "-"}</TableCell>
                        <TableCell>{supplier.email || "-"}</TableCell>
                        <TableCell>{supplier.phone || "-"}</TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button size="sm" variant="ghost" onClick={() => editSupplier(supplier)}>
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="ghost" className="text-red-500" onClick={() => handleDeleteSupplier(supplier.id)}>
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                    {suppliers.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                          No suppliers yet. Add your first supplier.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Transactions Tab */}
          <TabsContent value="transactions">
            <Card>
              <CardHeader>
                <CardTitle>Stock Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Item</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Quantity</TableHead>
                      <TableHead>Stock Change</TableHead>
                      <TableHead>By</TableHead>
                      <TableHead>Notes</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {transactions.map(tx => (
                      <TableRow key={tx.id}>
                        <TableCell className="text-muted-foreground">
                          {new Date(tx.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="font-medium">{tx.menu_item_name}</TableCell>
                        <TableCell>
                          <Badge variant={tx.transaction_type === "restock" ? "default" : tx.transaction_type === "waste" ? "destructive" : "outline"}>
                            {tx.transaction_type}
                          </Badge>
                        </TableCell>
                        <TableCell>{tx.quantity}</TableCell>
                        <TableCell>
                          {tx.previous_stock} → {tx.new_stock}
                        </TableCell>
                        <TableCell>{tx.created_by || "-"}</TableCell>
                        <TableCell className="text-muted-foreground">{tx.notes || "-"}</TableCell>
                      </TableRow>
                    ))}
                    {transactions.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                          No transactions yet.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Stock Adjustment Dialog */}
      <Dialog open={isAdjustDialogOpen} onOpenChange={setIsAdjustDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Adjust Stock</DialogTitle>
            <DialogDescription>Update stock levels</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAdjustStock} className="space-y-4">
            <div>
              <Label>Transaction Type</Label>
              <Select
                value={adjustForm.transaction_type}
                onValueChange={(v) => setAdjustForm({ ...adjustForm, transaction_type: v })}
              >
                <SelectTrigger data-testid="adjust-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="restock">Restock (Add)</SelectItem>
                  <SelectItem value="waste">Waste (Remove)</SelectItem>
                  <SelectItem value="adjustment">Set Exact Amount</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Quantity</Label>
              <Input
                type="number"
                min="0"
                value={adjustForm.quantity}
                onChange={(e) => setAdjustForm({ ...adjustForm, quantity: parseInt(e.target.value) })}
                data-testid="adjust-quantity-input"
              />
            </div>
            <div>
              <Label>Notes</Label>
              <Input
                value={adjustForm.notes}
                onChange={(e) => setAdjustForm({ ...adjustForm, notes: e.target.value })}
                placeholder="Optional notes..."
              />
            </div>
            <Button type="submit" className="w-full themed-accent-btn text-white" data-testid="submit-adjustment-btn">
              Submit Adjustment
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* History Dialog */}
      <Dialog open={isHistoryDialogOpen} onOpenChange={setIsHistoryDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Stock History</DialogTitle>
            <DialogDescription>Transaction history for this item</DialogDescription>
          </DialogHeader>
          <div className="max-h-96 overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Qty</TableHead>
                  <TableHead>Change</TableHead>
                  <TableHead>Notes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {selectedHistory.map(tx => (
                  <TableRow key={tx.id}>
                    <TableCell>{new Date(tx.created_at).toLocaleString()}</TableCell>
                    <TableCell>
                      <Badge variant={tx.transaction_type === "restock" ? "default" : "outline"}>
                        {tx.transaction_type}
                      </Badge>
                    </TableCell>
                    <TableCell>{tx.quantity}</TableCell>
                    <TableCell>{tx.previous_stock} → {tx.new_stock}</TableCell>
                    <TableCell>{tx.notes || "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
