import React, { useMemo, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import {
  Calendar,
  Download,
  FileText,
  Loader2,
  FileSpreadsheet,
  Wallet,
  Package,
  Receipt,
  RotateCcw,
  Building2,
  MapPinned,
  PackageSearch,
  CheckCircle2,
  Clock,
  Layers,
  Sparkles,
  Info
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8001";

export default function ReportsPage() {
  const REPORT_CONFIG = {
    payment: {
      name: "Payment Report",
      description: "Detailed transactions including payment modes, status, and fee breakdowns.",
      icon: Wallet,
      generate: `${API_BASE}/api/payment-report`,
      download: `${API_BASE}/api/payment-download`,
      filename: "payment_report.csv",
      requiresDates: true,
      successMessage: "Payment Report generated successfully.",
    },

    order_report: {
      name: "Order Report",
      description: "Complete logs of customer orders, line items, fulfillment, and revenue.",
      icon: Package,
      generate: `${API_BASE}/api/order-report`,
      download: `${API_BASE}/api/order-download`,
      filename: "order_report.csv",
      requiresDates: true,
      successMessage: "Order Report generated successfully.",
    },

    ar_report: {
      name: "AR Aging Report",
      description: "Accounts receivable balance distribution split into age buckets.",
      icon: Receipt,
      generate: `${API_BASE}/api/ar-report`,
      download: `${API_BASE}/api/ar-download`,
      filename: "ar_aging_report.csv",
      requiresDates: true,
      onlyEndDate: true,
      successMessage: "AR Report generated successfully.",
    },

    refund_report: {
      name: "Refund Report",
      description: "Summary of processed returns, store credits, and reversed payments.",
      icon: RotateCcw,
      generate: `${API_BASE}/api/refund-report`,
      download: `${API_BASE}/api/refund-download`,
      filename: "refund_report.csv",
      requiresDates: true,
      successMessage: "Refund Report generated successfully.",
    },

    partner_master: {
      name: "Partner Master - Company",
      description: "Master list of registered B2B vendor and enterprise company accounts.",
      icon: Building2,
      generate: `${API_BASE}/api/partner-master`,
      download: `${API_BASE}/api/partner-master-download`,
      filename: "partner_master.csv",
      requiresDates: false,
      successMessage: "Partner Master generated successfully.",
    },

    partner_master_ll: {
      name: "Partner Master - Location",
      description: "Geographic registry of partner branches, warehouses, and fulfillment hubs.",
      icon: MapPinned,
      generate: `${API_BASE}/api/partner-location-master`,
      download: `${API_BASE}/api/partner-location-master-download`,
      filename: "partner_location_master.csv",
      requiresDates: false,
      successMessage: "Partner Location generated successfully.",
    },

    product_master: {
      name: "Product Master",
      description: "Full SKU dictionary including tax groups, categories, and unit pricing.",
      icon: PackageSearch,
      generate: `${API_BASE}/api/product-master`,
      download: `${API_BASE}/api/product-master-download`,
      filename: "product_master.csv",
      requiresDates: false,
      successMessage: "Product Master generated successfully.",
    },
  };

  const [selectedReport, setSelectedReport] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [downloadReady, setDownloadReady] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [lastGenerated, setLastGenerated] = useState(null);

  const currentReport = REPORT_CONFIG[selectedReport];
  const totalReports = Object.keys(REPORT_CONFIG).length;

  const selectedConfig = useMemo(
    () => REPORT_CONFIG[selectedReport],
    [selectedReport]
  );

  const requiresDates = selectedConfig?.requiresDates ?? false;

  const SelectedIcon = currentReport?.icon || FileSpreadsheet;

  const resetState = () => {
    setDownloadReady(false);
    setStatusMessage("");
  };

  const validateForm = () => {
    if (!selectedReport) {
      toast.error("Please select a report.");
      return false;
    }

    if (!selectedConfig) {
      toast.error("Invalid report selected.");
      return false;
    }

    if (!selectedConfig.requiresDates) {
      return true;
    }

    if (selectedConfig.onlyEndDate) {
      if (!endDate) {
        toast.error("Please select the End Date.");
        return false;
      }
      return true;
    }

    if (!startDate || !endDate) {
      toast.error("Please select both Start Date and End Date.");
      return false;
    }

    if (startDate > endDate) {
      toast.error("Start Date cannot be greater than End Date.");
      return false;
    }

    return true;
  };

  const handleGenerate = async () => {
    if (!validateForm()) return;

    resetState();

    try {
      setIsGenerating(true);

      const payload = selectedConfig.requiresDates
        ? selectedConfig.onlyEndDate
          ? { endDate }
          : { startDate, endDate }
        : {};

      const response = await fetch(selectedConfig.generate, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(result.error || "Unable to generate report.");
      }

      setDownloadReady(true);
      setStatusMessage(selectedConfig.successMessage);
      setLastGenerated(new Date().toLocaleString());
      toast.success(selectedConfig.successMessage);
    } catch (err) {
      console.error(err);
      setStatusMessage("");
      toast.error(err.message || "Something went wrong.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = async () => {
    if (!selectedConfig) return;

    try {
      const response = await fetch(selectedConfig.download);

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || "Unable to download report.");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = selectedConfig.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Download started!");
    } catch (err) {
      console.error(err);
      toast.error(err.message || "Download failed.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col justify-between p-4 sm:p-6 md:p-10 transition-colors duration-200 relative">
      <Toaster position="top-right" reverseOrder={false} />

      {/* Full-Page Loading Overlay */}
      {isGenerating && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-900/60 backdrop-blur-md transition-all duration-300">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 rounded-2xl shadow-2xl flex flex-col items-center max-w-sm w-full mx-4 text-center transform scale-100 animate-in fade-in zoom-in duration-200">
            <div className="relative flex items-center justify-center mb-4">
              <div className="absolute inset-0 rounded-full bg-blue-500/20 blur-xl animate-pulse"></div>
              <Loader2 className="w-12 h-12 text-blue-600 dark:text-blue-400 animate-spin relative z-10" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-1">
              Generating Report...
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Please wait while we compile your requested analytics data.
            </p>
          </div>
        </div>
      )}

      {/* Main Container */}
      <div className="w-full max-w-4xl mx-auto space-y-6">
        
        {/* Header Banner */}
        <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-indigo-800 dark:from-blue-900 dark:via-indigo-950 dark:to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl shadow-indigo-900/10 border border-indigo-600/20 relative overflow-hidden">
          <div className="absolute -right-10 -bottom-10 opacity-10 pointer-events-none">
            <FileSpreadsheet size={280} />
          </div>
          <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 shadow-inner">
                <FileSpreadsheet className="w-8 h-8 sm:w-10 sm:h-10 text-blue-200" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
                    Finance Reports
                  </h1>
                  <span className="bg-blue-500/30 text-blue-100 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-blue-400/30">
                    Enterprise
                  </span>
                </div>
                <p className="text-blue-100/80 text-sm sm:text-base mt-1 max-w-xl">
                  Generate Payment, Order, AR Aging, Refund, Partner, and Product Reports instantly.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Dashboard Cards Section */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Total Reports */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-200 flex items-center gap-4 group">
            <div className="p-3.5 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-900/40 group-hover:scale-105 transition-transform">
              <Layers className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Total Reports
              </p>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-0.5">
                {totalReports}
              </h2>
            </div>
          </div>

          {/* Selected Report */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-200 flex items-center gap-4 group">
            <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/40 group-hover:scale-105 transition-transform">
              <SelectedIcon className="w-6 h-6" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Selected Report
              </p>
              <h2 className="text-base font-bold text-slate-900 dark:text-white mt-0.5 truncate">
                {currentReport ? currentReport.name : "None Selected"}
              </h2>
            </div>
          </div>

          {/* Last Generated */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-200 flex items-center gap-4 group">
            <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-100 dark:border-amber-900/40 group-hover:scale-105 transition-transform">
              <Clock className="w-6 h-6" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Last Generated
              </p>
              <h2 className="text-xs font-semibold text-slate-900 dark:text-white mt-1 truncate">
                {lastGenerated || "Not generated yet"}
              </h2>
            </div>
          </div>
        </div>

        {/* Form Container */}
        <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 border border-slate-200/80 dark:border-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-none space-y-6">
          
          {/* Select Report Field */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Select Report Type
            </label>
            <div className="relative">
              <select
                value={selectedReport}
                disabled={isGenerating}
                onChange={(e) => {
                  setSelectedReport(e.target.value);
                  resetState();
                  setStartDate("");
                  setEndDate("");
                }}
                className="w-full appearance-none rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/50 px-4 py-3.5 pr-10 text-slate-900 dark:text-white font-medium focus:bg-white dark:focus:bg-slate-800 focus:ring-2 focus:ring-blue-600 dark:focus:ring-blue-500 focus:border-transparent focus:outline-none transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                <option value="" disabled className="dark:bg-slate-900">
                  Choose a report from the catalog...
                </option>
                {Object.entries(REPORT_CONFIG).map(([key, value]) => (
                  <option key={key} value={key} className="dark:bg-slate-900">
                    {value.name}
                  </option>
                ))}
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                <Sparkles className="w-4 h-4" />
              </div>
            </div>
          </div>

          {/* Dynamic Report Preview Card */}
          {currentReport && (
            <div className="rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-700/60 p-4 sm:p-5 flex items-start gap-4 transition-all animate-in fade-in duration-200">
              <div className="p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-blue-600 dark:text-blue-400 shrink-0 shadow-sm">
                <SelectedIcon className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-slate-900 dark:text-white text-base">
                    {currentReport.name}
                  </h3>
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 dark:text-slate-400 bg-slate-200/60 dark:bg-slate-700 px-2 py-0.5 rounded-md">
                    <Info className="w-3 h-3" />
                    {currentReport.filename}
                  </span>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
                  {currentReport.description}
                </p>
              </div>
            </div>
          )}

          {/* Date Picker Section */}
          {requiresDates && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2 border-t border-slate-100 dark:border-slate-800">
              {!selectedConfig?.onlyEndDate && (
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Start Date
                  </label>
                  <div className="relative">
                    <Calendar
                      size={18}
                      className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                    />
                    <input
                      type="date"
                      value={startDate}
                      disabled={isGenerating}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full pl-10 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/50 px-4 py-3 text-slate-900 dark:text-white font-medium focus:bg-white dark:focus:bg-slate-800 focus:ring-2 focus:ring-blue-600 dark:focus:ring-blue-500 focus:border-transparent focus:outline-none transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
                    />
                  </div>
                </div>
              )}

              <div className={selectedConfig?.onlyEndDate ? "md:col-span-2" : ""}>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  End Date
                </label>
                <div className="relative">
                  <Calendar
                    size={18}
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                  />
                  <input
                    type="date"
                    value={endDate}
                    disabled={isGenerating}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full pl-10 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/50 px-4 py-3 text-slate-900 dark:text-white font-medium focus:bg-white dark:focus:bg-slate-800 focus:ring-2 focus:ring-blue-600 dark:focus:ring-blue-500 focus:border-transparent focus:outline-none transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            <button
              onClick={handleGenerate}
              disabled={!selectedReport || isGenerating}
              className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold px-6 py-3.5 rounded-xl shadow-lg shadow-blue-600/20 hover:shadow-blue-600/30 active:scale-[0.99] transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-blue-600 disabled:hover:to-indigo-600 disabled:shadow-none"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  Generating...
                </>
              ) : (
                <>
                  <FileText size={18} />
                  Generate Report
                </>
              )}
            </button>

            <button
              onClick={handleDownload}
              disabled={!downloadReady || isGenerating}
              className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold px-6 py-3.5 rounded-xl shadow-lg shadow-emerald-600/20 hover:shadow-emerald-600/30 active:scale-[0.99] transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-emerald-600 disabled:hover:to-teal-600 disabled:shadow-none"
            >
              <Download size={18} />
              Download Report
            </button>
          </div>

          {/* Success Status Box */}
          {statusMessage && (
            <div className="rounded-2xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/60 dark:bg-emerald-950/30 p-5 transition-all animate-in fade-in duration-200">
              <div className="flex items-start justify-between gap-3">
                <div className="flex gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-bold text-emerald-900 dark:text-emerald-200 text-sm">
                      Report Generated Successfully
                    </h3>
                    <p className="text-emerald-700 dark:text-emerald-400 text-sm mt-0.5">
                      {statusMessage}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-12 text-center text-xs text-slate-500 dark:text-slate-400 py-4 border-t border-slate-200/60 dark:border-slate-800/60 max-w-4xl mx-auto w-full">
        <span>Finance Reports Portal</span>
        <span className="mx-2">•</span>
        <span>Version 1.0</span>
        <span className="mx-2">•</span>
        <span>Powered by FastAPI & React</span>
      </footer>
    </div>
  );
}