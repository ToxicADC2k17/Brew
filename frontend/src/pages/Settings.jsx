import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Coffee, ArrowLeft, Palette, RotateCcw, Save, Plus, Trash2, GripVertical } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PRESET_THEMES = [
  {
    name: "Espresso & Crema",
    primary_color: "#2C1A1D",
    accent_color: "#D97706",
    background_color: "#FDFCF8",
    card_color: "#FFFFFF",
    text_color: "#2C1A1D",
    muted_color: "#6B5E5F",
    border_color: "#E5E0D8"
  },
  {
    name: "Ocean Blue",
    primary_color: "#1E3A5F",
    accent_color: "#0EA5E9",
    background_color: "#F0F9FF",
    card_color: "#FFFFFF",
    text_color: "#1E3A5F",
    muted_color: "#64748B",
    border_color: "#E2E8F0"
  },
  {
    name: "Forest Green",
    primary_color: "#14532D",
    accent_color: "#22C55E",
    background_color: "#F0FDF4",
    card_color: "#FFFFFF",
    text_color: "#14532D",
    muted_color: "#4B5563",
    border_color: "#D1FAE5"
  },
  {
    name: "Royal Purple",
    primary_color: "#4C1D95",
    accent_color: "#A855F7",
    background_color: "#FAF5FF",
    card_color: "#FFFFFF",
    text_color: "#4C1D95",
    muted_color: "#6B7280",
    border_color: "#E9D5FF"
  },
  {
    name: "Sunset Orange",
    primary_color: "#7C2D12",
    accent_color: "#F97316",
    background_color: "#FFF7ED",
    card_color: "#FFFFFF",
    text_color: "#7C2D12",
    muted_color: "#78716C",
    border_color: "#FED7AA"
  },
  {
    name: "Midnight Dark",
    primary_color: "#F8FAFC",
    accent_color: "#3B82F6",
    background_color: "#0F172A",
    card_color: "#1E293B",
    text_color: "#F8FAFC",
    muted_color: "#94A3B8",
    border_color: "#334155"
  },
  {
    name: "Rose Gold",
    primary_color: "#881337",
    accent_color: "#F43F5E",
    background_color: "#FFF1F2",
    card_color: "#FFFFFF",
    text_color: "#881337",
    muted_color: "#6B7280",
    border_color: "#FECDD3"
  },
  {
    name: "Slate Modern",
    primary_color: "#1E293B",
    accent_color: "#6366F1",
    background_color: "#F8FAFC",
    card_color: "#FFFFFF",
    text_color: "#1E293B",
    muted_color: "#64748B",
    border_color: "#E2E8F0"
  }
];

const emptyModifier = {
  name: "",
  type: "single",
  required: false,
  options: [{ name: "", price_adjustment: 0 }]
};

export default function Settings() {
  const [theme, setTheme] = useState(PRESET_THEMES[0]);
  const [modifiers, setModifiers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modifierForm, setModifierForm] = useState(emptyModifier);
  const [editingModifier, setEditingModifier] = useState(null);
  const [isModifierDialogOpen, setIsModifierDialogOpen] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const [themeRes, modifiersRes] = await Promise.all([
        axios.get(`${API}/config/theme`),
        axios.get(`${API}/modifiers`)
      ]);
      setTheme(themeRes.data);
      setModifiers(modifiersRes.data);
    } catch (err) {
      console.error("Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  const saveTheme = async () => {
    try {
      await axios.put(`${API}/config/theme`, theme);
      toast.success("Theme saved! Refresh to see changes.");
      // Apply theme immediately
      applyTheme(theme);
    } catch (err) {
      toast.error("Failed to save theme");
    }
  };

  const resetTheme = async () => {
    try {
      const res = await axios.post(`${API}/config/theme/reset`);
      setTheme(res.data);
      applyTheme(res.data);
      toast.success("Theme reset to default");
    } catch (err) {
      toast.error("Failed to reset theme");
    }
  };

  const applyPreset = (preset) => {
    setTheme({ ...theme, ...preset });
  };

  const applyTheme = (t) => {
    document.documentElement.style.setProperty('--theme-primary', t.primary_color);
    document.documentElement.style.setProperty('--theme-accent', t.accent_color);
    document.documentElement.style.setProperty('--theme-background', t.background_color);
    document.documentElement.style.setProperty('--theme-card', t.card_color);
    document.documentElement.style.setProperty('--theme-text', t.text_color);
    document.documentElement.style.setProperty('--theme-muted', t.muted_color);
    document.documentElement.style.setProperty('--theme-border', t.border_color);
  };

  // Modifier functions
  const openNewModifierDialog = () => {
    setModifierForm(emptyModifier);
    setEditingModifier(null);
    setIsModifierDialogOpen(true);
  };

  const openEditModifierDialog = (mod) => {
    setModifierForm({
      name: mod.name,
      type: mod.type,
      required: mod.required,
      options: mod.options
    });
    setEditingModifier(mod.id);
    setIsModifierDialogOpen(true);
  };

  const addOption = () => {
    setModifierForm({
      ...modifierForm,
      options: [...modifierForm.options, { name: "", price_adjustment: 0 }]
    });
  };

  const removeOption = (idx) => {
    setModifierForm({
      ...modifierForm,
      options: modifierForm.options.filter((_, i) => i !== idx)
    });
  };

  const updateOption = (idx, field, value) => {
    const newOptions = [...modifierForm.options];
    newOptions[idx] = { ...newOptions[idx], [field]: value };
    setModifierForm({ ...modifierForm, options: newOptions });
  };

  const saveModifier = async () => {
    if (!modifierForm.name || modifierForm.options.length === 0) {
      toast.error("Name and at least one option required");
      return;
    }
    
    // Filter out empty options
    const validOptions = modifierForm.options.filter(o => o.name.trim());
    if (validOptions.length === 0) {
      toast.error("At least one valid option required");
      return;
    }

    try {
      const data = { ...modifierForm, options: validOptions };
      if (editingModifier) {
        await axios.put(`${API}/modifiers/${editingModifier}`, data);
        toast.success("Modifier updated");
      } else {
        await axios.post(`${API}/modifiers`, data);
        toast.success("Modifier created");
      }
      setIsModifierDialogOpen(false);
      fetchSettings();
    } catch (err) {
      toast.error("Failed to save modifier");
    }
  };

  const deleteModifier = async (id) => {
    try {
      await axios.delete(`${API}/modifiers/${id}`);
      toast.success("Modifier deleted");
      fetchSettings();
    } catch (err) {
      toast.error("Failed to delete modifier");
    }
  };

  return (
    <div className="min-h-screen" data-testid="settings-page">
      {/* Header */}
      <header className="bg-[#2C1A1D] text-white px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Coffee className="w-8 h-8 text-[#D97706]" />
            <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'Manrope' }}>
              Settings
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
        <Tabs defaultValue="theme" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="theme" data-testid="theme-tab">
              <Palette className="w-4 h-4 mr-2" /> Theme & Colors
            </TabsTrigger>
            <TabsTrigger value="modifiers" data-testid="modifiers-tab">
              <GripVertical className="w-4 h-4 mr-2" /> Item Modifiers
            </TabsTrigger>
          </TabsList>

          {/* Theme Tab */}
          <TabsContent value="theme">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Color Pickers */}
              <div className="lg:col-span-2 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle style={{ fontFamily: 'Manrope' }}>Color Scheme</CardTitle>
                    <CardDescription>Customize your cafe's brand colors</CardDescription>
                  </CardHeader>
                  <CardContent className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Primary Color</Label>
                      <div className="flex gap-2">
                        <Input 
                          type="color" 
                          value={theme.primary_color}
                          onChange={(e) => setTheme({...theme, primary_color: e.target.value})}
                          className="w-12 h-10 p-1 cursor-pointer"
                          data-testid="primary-color-input"
                        />
                        <Input 
                          value={theme.primary_color}
                          onChange={(e) => setTheme({...theme, primary_color: e.target.value})}
                          className="font-mono"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Accent Color</Label>
                      <div className="flex gap-2">
                        <Input 
                          type="color" 
                          value={theme.accent_color}
                          onChange={(e) => setTheme({...theme, accent_color: e.target.value})}
                          className="w-12 h-10 p-1 cursor-pointer"
                          data-testid="accent-color-input"
                        />
                        <Input 
                          value={theme.accent_color}
                          onChange={(e) => setTheme({...theme, accent_color: e.target.value})}
                          className="font-mono"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Background Color</Label>
                      <div className="flex gap-2">
                        <Input 
                          type="color" 
                          value={theme.background_color}
                          onChange={(e) => setTheme({...theme, background_color: e.target.value})}
                          className="w-12 h-10 p-1 cursor-pointer"
                        />
                        <Input 
                          value={theme.background_color}
                          onChange={(e) => setTheme({...theme, background_color: e.target.value})}
                          className="font-mono"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Card Color</Label>
                      <div className="flex gap-2">
                        <Input 
                          type="color" 
                          value={theme.card_color}
                          onChange={(e) => setTheme({...theme, card_color: e.target.value})}
                          className="w-12 h-10 p-1 cursor-pointer"
                        />
                        <Input 
                          value={theme.card_color}
                          onChange={(e) => setTheme({...theme, card_color: e.target.value})}
                          className="font-mono"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Text Color</Label>
                      <div className="flex gap-2">
                        <Input 
                          type="color" 
                          value={theme.text_color}
                          onChange={(e) => setTheme({...theme, text_color: e.target.value})}
                          className="w-12 h-10 p-1 cursor-pointer"
                        />
                        <Input 
                          value={theme.text_color}
                          onChange={(e) => setTheme({...theme, text_color: e.target.value})}
                          className="font-mono"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Muted Text Color</Label>
                      <div className="flex gap-2">
                        <Input 
                          type="color" 
                          value={theme.muted_color}
                          onChange={(e) => setTheme({...theme, muted_color: e.target.value})}
                          className="w-12 h-10 p-1 cursor-pointer"
                        />
                        <Input 
                          value={theme.muted_color}
                          onChange={(e) => setTheme({...theme, muted_color: e.target.value})}
                          className="font-mono"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Border Color</Label>
                      <div className="flex gap-2">
                        <Input 
                          type="color" 
                          value={theme.border_color}
                          onChange={(e) => setTheme({...theme, border_color: e.target.value})}
                          className="w-12 h-10 p-1 cursor-pointer"
                        />
                        <Input 
                          value={theme.border_color}
                          onChange={(e) => setTheme({...theme, border_color: e.target.value})}
                          className="font-mono"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <div className="flex gap-3">
                  <Button onClick={saveTheme} className="bg-[#D97706] hover:bg-[#b86505]" data-testid="save-theme-btn">
                    <Save className="w-4 h-4 mr-2" /> Save Theme
                  </Button>
                  <Button onClick={resetTheme} variant="outline" data-testid="reset-theme-btn">
                    <RotateCcw className="w-4 h-4 mr-2" /> Reset to Default
                  </Button>
                </div>
              </div>

              {/* Preset Themes */}
              <div>
                <Card>
                  <CardHeader>
                    <CardTitle style={{ fontFamily: 'Manrope' }}>Preset Themes</CardTitle>
                    <CardDescription>Quick color schemes</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {PRESET_THEMES.map((preset, idx) => (
                      <button
                        key={idx}
                        onClick={() => applyPreset(preset)}
                        className="w-full flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-muted transition-colors text-left"
                        data-testid={`preset-${idx}`}
                      >
                        <div className="flex gap-1">
                          <div 
                            className="w-6 h-6 rounded-full border" 
                            style={{ backgroundColor: preset.primary_color }}
                          />
                          <div 
                            className="w-6 h-6 rounded-full border" 
                            style={{ backgroundColor: preset.accent_color }}
                          />
                          <div 
                            className="w-6 h-6 rounded-full border" 
                            style={{ backgroundColor: preset.background_color }}
                          />
                        </div>
                        <span className="text-sm font-medium">{preset.name}</span>
                      </button>
                    ))}
                  </CardContent>
                </Card>

                {/* Preview */}
                <Card className="mt-4">
                  <CardHeader>
                    <CardTitle style={{ fontFamily: 'Manrope' }}>Preview</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div 
                      className="p-4 rounded-lg border"
                      style={{ 
                        backgroundColor: theme.background_color,
                        borderColor: theme.border_color
                      }}
                    >
                      <div 
                        className="p-3 rounded-lg mb-3"
                        style={{ backgroundColor: theme.primary_color }}
                      >
                        <span style={{ color: '#fff', fontWeight: 600 }}>Header</span>
                      </div>
                      <div 
                        className="p-3 rounded-lg border mb-3"
                        style={{ 
                          backgroundColor: theme.card_color,
                          borderColor: theme.border_color
                        }}
                      >
                        <p style={{ color: theme.text_color, fontWeight: 500 }}>Menu Item</p>
                        <p style={{ color: theme.muted_color, fontSize: '0.875rem' }}>Description</p>
                        <p style={{ color: theme.accent_color, fontWeight: 600 }}>€9.99</p>
                      </div>
                      <button
                        className="w-full py-2 rounded-lg text-white text-sm font-medium"
                        style={{ backgroundColor: theme.accent_color }}
                      >
                        Add to Order
                      </button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Modifiers Tab */}
          <TabsContent value="modifiers">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle style={{ fontFamily: 'Manrope' }}>Item Modifiers</CardTitle>
                  <CardDescription>Configure options like size, cooking preference, extras</CardDescription>
                </div>
                <Dialog open={isModifierDialogOpen} onOpenChange={setIsModifierDialogOpen}>
                  <DialogTrigger asChild>
                    <Button onClick={openNewModifierDialog} className="bg-[#D97706] hover:bg-[#b86505]" data-testid="add-modifier-btn">
                      <Plus className="w-4 h-4 mr-2" /> Add Modifier
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-lg">
                    <DialogHeader>
                      <DialogTitle style={{ fontFamily: 'Manrope' }}>
                        {editingModifier ? "Edit Modifier" : "New Modifier"}
                      </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 mt-4">
                      <div className="space-y-2">
                        <Label>Modifier Name</Label>
                        <Input 
                          value={modifierForm.name}
                          onChange={(e) => setModifierForm({...modifierForm, name: e.target.value})}
                          placeholder="e.g., Size, Cooking Preference"
                          data-testid="modifier-name-input"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Selection Type</Label>
                          <Select 
                            value={modifierForm.type} 
                            onValueChange={(val) => setModifierForm({...modifierForm, type: val})}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="single">Single Choice</SelectItem>
                              <SelectItem value="multiple">Multiple Choices</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Required?</Label>
                          <div className="flex items-center gap-2 h-10">
                            <Switch 
                              checked={modifierForm.required}
                              onCheckedChange={(checked) => setModifierForm({...modifierForm, required: checked})}
                            />
                            <span className="text-sm">{modifierForm.required ? "Yes" : "No"}</span>
                          </div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Label>Options</Label>
                          <Button type="button" size="sm" variant="outline" onClick={addOption}>
                            <Plus className="w-3 h-3 mr-1" /> Add Option
                          </Button>
                        </div>
                        <div className="space-y-2 max-h-[200px] overflow-y-auto">
                          {modifierForm.options.map((opt, idx) => (
                            <div key={idx} className="flex gap-2 items-center">
                              <Input 
                                value={opt.name}
                                onChange={(e) => updateOption(idx, "name", e.target.value)}
                                placeholder="Option name"
                                className="flex-1"
                              />
                              <Input 
                                type="number"
                                step="0.01"
                                value={opt.price_adjustment}
                                onChange={(e) => updateOption(idx, "price_adjustment", parseFloat(e.target.value) || 0)}
                                placeholder="+/-€"
                                className="w-24 font-mono"
                              />
                              {modifierForm.options.length > 1 && (
                                <Button 
                                  type="button" 
                                  size="sm" 
                                  variant="ghost" 
                                  onClick={() => removeOption(idx)}
                                  className="text-destructive"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                    <DialogFooter className="mt-6">
                      <DialogClose asChild>
                        <Button variant="outline">Cancel</Button>
                      </DialogClose>
                      <Button onClick={saveModifier} className="bg-[#2C1A1D] hover:bg-[#3d2628]" data-testid="save-modifier-btn">
                        {editingModifier ? "Update" : "Create"} Modifier
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="space-y-3">
                    {[1,2,3].map(i => <div key={i} className="h-20 bg-muted animate-pulse rounded-lg" />)}
                  </div>
                ) : modifiers.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <GripVertical className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p>No modifiers yet</p>
                    <p className="text-sm">Create modifiers like Size, Extras, Cooking Preference</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {modifiers.map(mod => (
                      <div key={mod.id} className="border border-border rounded-lg p-4" data-testid={`modifier-${mod.id}`}>
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold flex items-center gap-2">
                              {mod.name}
                              {mod.required && (
                                <span className="text-xs bg-destructive/10 text-destructive px-2 py-0.5 rounded">Required</span>
                              )}
                              <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded">
                                {mod.type === "single" ? "Single Choice" : "Multiple"}
                              </span>
                            </h3>
                            <div className="flex flex-wrap gap-2 mt-2">
                              {mod.options.map((opt, idx) => (
                                <span 
                                  key={idx} 
                                  className="text-sm bg-secondary text-secondary-foreground px-2 py-1 rounded"
                                >
                                  {opt.name}
                                  {opt.price_adjustment !== 0 && (
                                    <span className="ml-1 font-mono text-xs">
                                      {opt.price_adjustment > 0 ? "+" : ""}{opt.price_adjustment.toFixed(2)}€
                                    </span>
                                  )}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button 
                              size="sm" 
                              variant="ghost" 
                              onClick={() => openEditModifierDialog(mod)}
                            >
                              Edit
                            </Button>
                            <Button 
                              size="sm" 
                              variant="ghost" 
                              className="text-destructive"
                              onClick={() => deleteModifier(mod.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
