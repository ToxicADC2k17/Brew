import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Coffee, ArrowLeft, Download, TrendingUp, Receipt, ShoppingBag, DollarSign, Calendar } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CURRENCIES = {
  EUR: "€", USD: "$", GBP: "£", BRL: "R$", CHF: "CHF"
};

export default function SalesReport() {
  const [dailyReport, setDailyReport] = useState(null);
  const [rangeReport, setRangeReport] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDailyReport(selectedDate);
  }, []);

  const fetchDailyReport = async (date) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/reports/daily?date=${date}`);
      setDailyReport(res.data);
    } catch (err) {
      toast.error("Failed to load daily report");
    } finally {
      setLoading(false);
    }
  };

  const fetchRangeReport = async () => {
    if (!startDate || !endDate) {
      toast.error("Please select both dates");
      return;
    }
    setLoading(true);
    try {
      const res = await axios.get(`${API}/reports/range?start_date=${startDate}&end_date=${endDate}`);
      setRangeReport(res.data);
    } catch (err) {
      toast.error("Failed to load range report");
    } finally {
      setLoading(false);
    }
  };

  const handleDateChange = (date) => {
    setSelectedDate(date);
    fetchDailyReport(date);
  };

  const getCurrencySymbol = (currency) => CURRENCIES[currency] || "€";

  const exportToCSV = (report, type) => {
    let csv = "";
    const sym = getCurrencySymbol(report.currency);
    
    if (type === "daily") {
      csv = `Daily Sales Report - ${report.date}\n\n`;
      csv += `Total Bills,${report.total_bills}\n`;
      csv += `Total Revenue,${sym}${report.total_revenue.toFixed(2)}\n`;
      csv += `Total Items Sold,${report.total_items_sold}\n`;
      csv += `Average Bill Value,${sym}${report.avg_bill_value.toFixed(2)}\n\n`;
      csv += `Top Items\nItem,Quantity,Revenue\n`;
      report.top_items.forEach(item => {
        csv += `${item.name},${item.quantity},${sym}${item.revenue.toFixed(2)}\n`;
      });
    } else {
      csv = `Sales Report - ${report.start_date} to ${report.end_date}\n\n`;
      csv += `Total Bills,${report.total_bills}\n`;
      csv += `Total Revenue,${sym}${report.total_revenue.toFixed(2)}\n`;
      csv += `Total Items Sold,${report.total_items_sold}\n`;
      csv += `Average Bill Value,${sym}${report.avg_bill_value.toFixed(2)}\n\n`;
      csv += `Daily Breakdown\nDate,Bills,Revenue\n`;
      report.daily_breakdown.forEach(day => {
        csv += `${day.date},${day.bills},${sym}${day.revenue.toFixed(2)}\n`;
      });
      csv += `\nTop Items\nItem,Quantity,Revenue\n`;
      report.top_items.forEach(item => {
        csv += `${item.name},${item.quantity},${sym}${item.revenue.toFixed(2)}\n`;
      });
    }
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = type === "daily" ? `daily-report-${report.date}.csv` : `sales-report-${report.start_date}-to-${report.end_date}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Report exported");
  };

  return (
    <div className="min-h-screen" data-testid="sales-report">
      {/* Header */}
      <header className="themed-header text-white px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Coffee className="w-8 h-8 themed-accent" />
            <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'Manrope' }}>
              Sales Reports
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
        <Tabs defaultValue="daily" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="daily" data-testid="daily-tab">Daily Report</TabsTrigger>
            <TabsTrigger value="range" data-testid="range-tab">Date Range Report</TabsTrigger>
          </TabsList>

          {/* Daily Report Tab */}
          <TabsContent value="daily">
            <div className="flex items-center gap-4 mb-6">
              <div>
                <label className="text-sm text-muted-foreground block mb-1">Select Date</label>
                <Input 
                  type="date"
                  value={selectedDate}
                  onChange={(e) => handleDateChange(e.target.value)}
                  className="w-48"
                  data-testid="daily-date-input"
                />
              </div>
              {dailyReport && dailyReport.total_bills > 0 && (
                <Button 
                  onClick={() => exportToCSV(dailyReport, "daily")}
                  variant="outline"
                  className="mt-5"
                  data-testid="export-daily-btn"
                >
                  <Download className="w-4 h-4 mr-2" /> Export CSV
                </Button>
              )}
            </div>

            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[1,2,3,4].map(i => (
                  <div key={i} className="h-32 bg-muted animate-pulse rounded-lg" />
                ))}
              </div>
            ) : dailyReport ? (
              <>
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Total Bills</CardTitle>
                      <Receipt className="w-4 h-4 themed-accent" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold" style={{ fontFamily: 'Manrope' }}>
                        {dailyReport.total_bills}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Total Revenue</CardTitle>
                      <DollarSign className="w-4 h-4 themed-accent" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold font-mono themed-accent">
                        {getCurrencySymbol(dailyReport.currency)}{dailyReport.total_revenue.toFixed(2)}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Items Sold</CardTitle>
                      <ShoppingBag className="w-4 h-4 themed-accent" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold" style={{ fontFamily: 'Manrope' }}>
                        {dailyReport.total_items_sold}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Avg Bill Value</CardTitle>
                      <TrendingUp className="w-4 h-4 themed-accent" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold font-mono">
                        {getCurrencySymbol(dailyReport.currency)}{dailyReport.avg_bill_value.toFixed(2)}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Top Items */}
                {dailyReport.top_items.length > 0 ? (
                  <Card>
                    <CardHeader>
                      <CardTitle style={{ fontFamily: 'Manrope' }}>Top Selling Items</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Rank</TableHead>
                            <TableHead>Item</TableHead>
                            <TableHead className="text-right">Quantity</TableHead>
                            <TableHead className="text-right">Revenue</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {dailyReport.top_items.map((item, idx) => (
                            <TableRow key={idx}>
                              <TableCell className="font-medium">#{idx + 1}</TableCell>
                              <TableCell>{item.name}</TableCell>
                              <TableCell className="text-right font-mono">{item.quantity}</TableCell>
                              <TableCell className="text-right font-mono themed-accent">
                                {getCurrencySymbol(dailyReport.currency)}{item.revenue.toFixed(2)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                ) : (
                  <Card>
                    <CardContent className="py-12 text-center text-muted-foreground">
                      <Calendar className="w-12 h-12 mx-auto mb-3 opacity-30" />
                      <p>No sales data for this date</p>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : null}
          </TabsContent>

          {/* Range Report Tab */}
          <TabsContent value="range">
            <div className="flex items-end gap-4 mb-6">
              <div>
                <label className="text-sm text-muted-foreground block mb-1">Start Date</label>
                <Input 
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-48"
                  data-testid="range-start-input"
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground block mb-1">End Date</label>
                <Input 
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-48"
                  data-testid="range-end-input"
                />
              </div>
              <Button 
                onClick={fetchRangeReport}
                className="themed-header hover:opacity-90"
                data-testid="generate-range-report-btn"
              >
                Generate Report
              </Button>
              {rangeReport && rangeReport.total_bills > 0 && (
                <Button 
                  onClick={() => exportToCSV(rangeReport, "range")}
                  variant="outline"
                  data-testid="export-range-btn"
                >
                  <Download className="w-4 h-4 mr-2" /> Export CSV
                </Button>
              )}
            </div>

            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[1,2,3,4].map(i => (
                  <div key={i} className="h-32 bg-muted animate-pulse rounded-lg" />
                ))}
              </div>
            ) : rangeReport ? (
              <>
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Total Bills</CardTitle>
                      <Receipt className="w-4 h-4 themed-accent" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold" style={{ fontFamily: 'Manrope' }}>
                        {rangeReport.total_bills}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Total Revenue</CardTitle>
                      <DollarSign className="w-4 h-4 themed-accent" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold font-mono themed-accent">
                        {getCurrencySymbol(rangeReport.currency)}{rangeReport.total_revenue.toFixed(2)}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Items Sold</CardTitle>
                      <ShoppingBag className="w-4 h-4 themed-accent" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold" style={{ fontFamily: 'Manrope' }}>
                        {rangeReport.total_items_sold}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Avg Bill Value</CardTitle>
                      <TrendingUp className="w-4 h-4 themed-accent" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold font-mono">
                        {getCurrencySymbol(rangeReport.currency)}{rangeReport.avg_bill_value.toFixed(2)}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {rangeReport.total_bills > 0 ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Daily Breakdown */}
                    <Card>
                      <CardHeader>
                        <CardTitle style={{ fontFamily: 'Manrope' }}>Daily Breakdown</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Date</TableHead>
                              <TableHead className="text-right">Bills</TableHead>
                              <TableHead className="text-right">Revenue</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {rangeReport.daily_breakdown.map((day, idx) => (
                              <TableRow key={idx}>
                                <TableCell>{day.date}</TableCell>
                                <TableCell className="text-right font-mono">{day.bills}</TableCell>
                                <TableCell className="text-right font-mono themed-accent">
                                  {getCurrencySymbol(rangeReport.currency)}{day.revenue.toFixed(2)}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>

                    {/* Top Items */}
                    <Card>
                      <CardHeader>
                        <CardTitle style={{ fontFamily: 'Manrope' }}>Top Selling Items</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Rank</TableHead>
                              <TableHead>Item</TableHead>
                              <TableHead className="text-right">Qty</TableHead>
                              <TableHead className="text-right">Revenue</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {rangeReport.top_items.map((item, idx) => (
                              <TableRow key={idx}>
                                <TableCell className="font-medium">#{idx + 1}</TableCell>
                                <TableCell>{item.name}</TableCell>
                                <TableCell className="text-right font-mono">{item.quantity}</TableCell>
                                <TableCell className="text-right font-mono themed-accent">
                                  {getCurrencySymbol(rangeReport.currency)}{item.revenue.toFixed(2)}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>
                  </div>
                ) : (
                  <Card>
                    <CardContent className="py-12 text-center text-muted-foreground">
                      <Calendar className="w-12 h-12 mx-auto mb-3 opacity-30" />
                      <p>No sales data for this date range</p>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : (
              <Card>
                <CardContent className="py-12 text-center text-muted-foreground">
                  <Calendar className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>Select a date range and click Generate Report</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
