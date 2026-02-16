import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose, DialogDescription } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Switch } from "@/components/ui/switch";
import { Coffee, ArrowLeft, Plus, Pencil, Trash2, Upload, Image, X, Loader2 } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CATEGORIES = ["Coffee", "Tea", "Pastries", "Snacks", "Beverages", "Breakfast", "Lunch", "Desserts", "Sandwiches", "Smoothies", "Starters", "Mains", "Steaks", "Seafood", "Vegetarian", "Salads", "Sides", "Soups", "Beers", "Wines", "Pizza", "Pasta", "Burgers"];

const emptyItem = {
  name: "",
  price: "",
  category: "Coffee",
  description: "",
  image_url: "",
  available: true
};

export default function MenuManagement() {
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState(emptyItem);
  const [editingId, setEditingId] = useState(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => {
    fetchMenu();
  }, []);

  const fetchMenu = async () => {
    try {
      const res = await axios.get(`${API}/menu`);
      setMenuItems(res.data);
    } catch (err) {
      toast.error("Failed to load menu");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.price) {
      toast.error("Name and price are required");
      return;
    }

    try {
      if (editingId) {
        await axios.put(`${API}/menu/${editingId}`, {
          ...formData,
          price: parseFloat(formData.price)
        });
        toast.success("Item updated");
      } else {
        await axios.post(`${API}/menu`, {
          ...formData,
          price: parseFloat(formData.price)
        });
        toast.success("Item added");
      }
      setFormData(emptyItem);
      setEditingId(null);
      setIsDialogOpen(false);
      fetchMenu();
    } catch (err) {
      toast.error("Failed to save item");
    }
  };

  const handleEdit = (item) => {
    setFormData({
      name: item.name,
      price: item.price.toString(),
      category: item.category,
      description: item.description || "",
      available: item.available
    });
    setEditingId(item.id);
    setIsDialogOpen(true);
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await axios.delete(`${API}/menu/${deleteId}`);
      toast.success("Item deleted");
      setDeleteId(null);
      fetchMenu();
    } catch (err) {
      toast.error("Failed to delete item");
    }
  };

  const toggleAvailability = async (item) => {
    try {
      await axios.put(`${API}/menu/${item.id}`, {
        available: !item.available
      });
      fetchMenu();
      toast.success(`${item.name} is now ${!item.available ? 'available' : 'unavailable'}`);
    } catch (err) {
      toast.error("Failed to update availability");
    }
  };

  const openNewDialog = () => {
    setFormData(emptyItem);
    setEditingId(null);
    setIsDialogOpen(true);
  };

  return (
    <div className="min-h-screen" data-testid="menu-management">
      {/* Header */}
      <header className="themed-header text-white px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Coffee className="w-8 h-8 themed-accent" />
            <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'Manrope' }}>
              Menu Management
            </h1>
          </div>
          <Link to="/">
            <Button 
              variant="outline" 
              className="border-[var(--theme-accent)] themed-accent hover:bg-[var(--theme-accent)] hover:text-white btn-press"
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
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold" style={{ fontFamily: 'Manrope' }}>Menu Items</h2>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button 
                  onClick={openNewDialog}
                  className="themed-accent-btn text-white  btn-press"
                  data-testid="add-item-btn"
                >
                  <Plus className="w-4 h-4 mr-2" /> Add Item
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md" aria-describedby="menu-item-form-description">
                <DialogHeader>
                  <DialogTitle style={{ fontFamily: 'Manrope' }}>
                    {editingId ? "Edit Menu Item" : "Add Menu Item"}
                  </DialogTitle>
                  <p id="menu-item-form-description" className="sr-only">
                    Fill out the form to {editingId ? "edit" : "add"} a menu item
                  </p>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Name *</Label>
                    <Input 
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      placeholder="Item name"
                      data-testid="item-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="price">Price *</Label>
                    <Input 
                      id="price"
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.price}
                      onChange={(e) => setFormData({...formData, price: e.target.value})}
                      placeholder="0.00"
                      className="price-tag"
                      data-testid="item-price-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="category">Category</Label>
                    <Select 
                      value={formData.category} 
                      onValueChange={(val) => setFormData({...formData, category: val})}
                    >
                      <SelectTrigger data-testid="item-category-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CATEGORIES.map(cat => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Input 
                      id="description"
                      value={formData.description}
                      onChange={(e) => setFormData({...formData, description: e.target.value})}
                      placeholder="Brief description"
                      data-testid="item-description-input"
                    />
                  </div>
                  <div className="flex items-center gap-3">
                    <Switch 
                      checked={formData.available}
                      onCheckedChange={(checked) => setFormData({...formData, available: checked})}
                      data-testid="item-available-switch"
                    />
                    <Label>Available for sale</Label>
                  </div>
                  <DialogFooter className="gap-2 mt-6">
                    <DialogClose asChild>
                      <Button type="button" variant="outline">Cancel</Button>
                    </DialogClose>
                    <Button 
                      type="submit" 
                      className="themed-header hover:opacity-90"
                      data-testid="save-item-btn"
                    >
                      {editingId ? "Update" : "Add"} Item
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {/* Items Table */}
          {loading ? (
            <div className="space-y-3">
              {[1,2,3,4,5].map(i => (
                <div key={i} className="h-14 bg-muted animate-pulse rounded" />
              ))}
            </div>
          ) : (
            <div className="border border-border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50">
                    <TableHead>Name</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="price-tag">Price</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {menuItems.map(item => (
                    <TableRow key={item.id} data-testid={`menu-row-${item.id}`}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{item.name}</p>
                          {item.description && (
                            <p className="text-xs text-muted-foreground">{item.description}</p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="px-2 py-1 bg-secondary text-secondary-foreground text-xs rounded">
                          {item.category}
                        </span>
                      </TableCell>
                      <TableCell className="price-tag font-medium themed-accent">
                        ${item.price.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        <Switch 
                          checked={item.available}
                          onCheckedChange={() => toggleAvailability(item)}
                          data-testid={`toggle-${item.id}`}
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            onClick={() => handleEdit(item)}
                            className="h-8 w-8 p-0"
                            data-testid={`edit-${item.id}`}
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button 
                                size="sm" 
                                variant="ghost" 
                                onClick={() => setDeleteId(item.id)}
                                className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                                data-testid={`delete-${item.id}`}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Delete Item</DialogTitle>
                              </DialogHeader>
                              <p className="py-4">Are you sure you want to delete <strong>{item.name}</strong>?</p>
                              <DialogFooter>
                                <DialogClose asChild>
                                  <Button variant="outline">Cancel</Button>
                                </DialogClose>
                                <Button 
                                  onClick={handleDelete}
                                  className="bg-destructive hover:bg-destructive/90"
                                  data-testid="confirm-delete-btn"
                                >
                                  Delete
                                </Button>
                              </DialogFooter>
                            </DialogContent>
                          </Dialog>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {menuItems.length === 0 && !loading && (
            <div className="text-center py-12 text-muted-foreground">
              <Coffee className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No menu items yet</p>
              <p className="text-sm">Add your first item to get started</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
