// src/App.jsx

import React, { useState, useEffect, useCallback, useMemo, useRef, createContext, useContext } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useNavigate,
  useLocation
} from "react-router-dom";
import axios from "axios";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import {
  LogIn,
  LogOut,
  UserPlus,
  CalendarDays,
  Clock,
  Users,
  PieChart,
  Play,
  StopCircle,
  BarChart3,
  Loader2,
  Camera // <-- Includes your previous fix
} from "lucide-react";

// --- NEW ---
// Import Chart.js components
import { Doughnut, Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  Title
} from "chart.js";

// --- NEW ---
// Register Chart.js elements
ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  Title,
  CategoryScale,
  LinearScale,
  BarElement
);
// --- END NEW ---

const API_URL = "http://127.0.0.1:8000";
const api = axios.create({ baseURL: API_URL });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("authToken");
  if (token) config.headers["Authorization"] = `Bearer ${token}`;
  return config;
});

const AuthContext = createContext();
function useAuth() {
  return useContext(AuthContext);
}

// ... (No changes to AuthProvider, ProtectedRoute, getKolkataDateString, App, LoginPage, Dashboard) ...
function AuthProvider({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [token, setToken] = useState(localStorage.getItem("authToken"));

  const login = async (username, password) => {
    try {
      const form = new URLSearchParams();
      form.append("username", username);
      form.append("password", password);
      const res = await axios.post(`${API_URL}/token`, form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      localStorage.setItem("authToken", res.data.access_token);
      setToken(res.data.access_token);
      toast.success("Login Successful!");
      navigate(location.state?.from?.pathname || "/");
    } catch {
      toast.error("Invalid credentials!");
    }
  };

  const logout = () => {
    localStorage.removeItem("authToken");
    setToken(null);
    navigate("/login");
  };

  const value = useMemo(() => ({ token, login, logout }), [token]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function ProtectedRoute({ children }) {
  const { token } = useAuth();
  const location = useLocation();
  if (!token) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}

// Time helper functions
function getKolkataDateString(date) {
  const dtf = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  });
  const parts = dtf.formatToParts(date);
  const y = parts.find((p) => p.type === "year").value;
  const m = parts.find((p) => p.type === "month").value;
  const d = parts.find((p) => p.type === "day").value;
  return `${y}-${m}-${d}`;
}

// ───────────────────────────────────────────────

export default function App() {
  return (
    <>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
      <ToastContainer position="bottom-right" autoClose={3000} />
    </>
  );
}

// ───────────────────────────────────────────────

function LoginPage() {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("password");
  const { login } = useAuth();

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-md bg-white shadow-xl rounded-lg p-6">
        <h2 className="text-2xl font-semibold text-center mb-6">Admin Login</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            login(username, password);
          }}
          className="space-y-4"
        >
          <input
            className="w-full border px-3 py-2 rounded"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            className="w-full border px-3 py-2 rounded"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="w-full py-2 bg-blue-600 text-white rounded flex items-center justify-center">
            <LogIn className="w-4 h-4 mr-2" /> Sign In
          </button>
        </form>
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────

function Dashboard() {
  const { logout } = useAuth();
  const [active, setActive] = useState("analytics");

  const tabs = [
    { id: "register", name: "Register User", icon: UserPlus },
    { id: "reports", name: "Daily Log", icon: CalendarDays },
    { id: "hours", name: "Work Hours", icon: Clock },
    { id: "analytics", name: "Overall Analytics", icon: PieChart },
    { id: "personal", name: "Personal Analytics", icon: BarChart3 },
    { id: "control", name: "Attendance Control", icon: Play },
    { id: "users", name: "Manage Users", icon: Users }
  ];

  return (
    <div className="flex h-screen bg-gray-100">
      <nav className="w-64 bg-white shadow-lg p-4 flex flex-col">
        <h2 className="text-xl font-bold mb-6 text-blue-700">Attendance System</h2>
        <ul className="space-y-1 flex-1">
          {tabs.map((t) => (
            <li key={t.id}>
              <button
                onClick={() => setActive(t.id)}
                className={`flex items-center w-full px-3 py-2 rounded ${
                  active === t.id
                    ? "bg-blue-100 text-blue-700 font-semibold"
                    : "hover:bg-gray-50 text-gray-600"
                }`}
              >
                <t.icon className="w-4 h-4 mr-2" /> {t.name}
              </button>
            </li>
          ))}
        </ul>
        <button
          onClick={logout}
          className="mt-auto bg-red-100 hover:bg-red-200 text-red-600 rounded px-3 py-2 flex items-center"
        >
          <LogOut className="w-4 h-4 mr-2" /> Logout
        </button>
      </nav>

      <main className="flex-1 p-6 overflow-auto">
        {active === "register" && <RegisterSection />}
        {active === "reports" && <DailyReport />}
        {active === "hours" && <HoursReport />}
        {active === "analytics" && <OverallAnalytics />}
        {active === "personal" && <PersonalAnalytics />}
        {active === "control" && <AttendanceControl />}
        {active === "users" && <ManageUsers />}
      </main>
    </div>
  );
}

// ... (No changes to CameraRegister, RegisterSection, DailyReport, HoursReport) ...
// ───────────────────────────────────────────────
// Registration

function CameraRegister({ onCapture }) {
  const videoRef = useRef();
  const streamRef = useRef();
  useEffect(() => {
    let active = true;
    async function start() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (!active) return;
        streamRef.current = stream;
        videoRef.current.srcObject = stream;
      } catch {
        toast.error("Camera permission denied!");
      }
    }
    start();
    return () => {
      active = false;
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const capture = () => {
    const v = videoRef.current;
    if (!v) return;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(v, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) onCapture(blob);
    }, "image/jpeg", 0.9);
  };

  return (
    <div>
      <video ref={videoRef} autoPlay playsInline muted className="w-64 h-48 border rounded" />
      <button
        onClick={capture}
        className="mt-2 px-3 py-1 bg-blue-600 text-white rounded flex items-center"
      >
        <Camera className="w-4 h-4 mr-2" /> Capture
      </button>
    </div>
  );
}

function RegisterSection() {
  const [name, setName] = useState("");
  const [useCamera, setUseCamera] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);

  const handleRegister = async () => {
    if (!name || !file) return toast.error("Name & Photo required");
    const form = new FormData();
    form.append("name", name);
    form.append("file", file);
    try {
      await api.post("/api/register", form);
      toast.success("User Registered");
      setName("");
      setFile(null);
      setPreview(null);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Registration failed");
    }
  };

  return (
    <div className="bg-white p-6 rounded shadow-md">
      <h2 className="text-xl font-semibold mb-3">Register User</h2>
      <input
        placeholder="Name"
        className="border w-full mb-3 px-3 py-2 rounded"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <div className="mb-3">
        <button
          onClick={() => setUseCamera(!useCamera)}
          className="px-3 py-1 bg-gray-100 rounded mr-2"
        >
          {useCamera ? "Use File" : "Use Camera"}
        </button>
      </div>
      {useCamera ? (
        <CameraRegister
          onCapture={(blob) => {
            setFile(new File([blob], "capture.jpg"));
            setPreview(URL.createObjectURL(blob));
          }}
        />
      ) : (
        <input
          type="file"
          accept="image/*"
          onChange={(e) => {
            const f = e.target.files[0];
            if (f) {
              setFile(f);
              setPreview(URL.createObjectURL(f));
            }
          }}
        />
      )}
      {preview && (
        <img src={preview} alt="preview" className="mt-3 w-40 h-40 object-cover rounded" />
      )}
      <button
        onClick={handleRegister}
        className="mt-3 px-4 py-2 bg-blue-600 text-white rounded"
      >
        Register
      </button>
    </div>
  );
}

// ───────────────────────────────────────────────
// Daily Report

function DailyReport() {
  const [date, setDate] = useState(new Date());
  const [data, setData] = useState([]);
  const fetch = async () => {
    try {
      const res = await api.get(`/api/report/${getKolkataDateString(date)}`);
      setData(res.data);
    } catch {
      toast.error("Failed to load report");
    }
  };
  useEffect(() => { fetch(); }, [date]); // --- UPDATED --- (Added date to dependency array)

  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="text-xl mb-3 font-semibold">Daily Log</h2>
      <DatePicker selected={date} onChange={setDate} className="border px-2 py-1 mb-3" />
      <button onClick={fetch} className="px-3 py-1 bg-blue-50 rounded">Refresh</button>
      <table className="w-full mt-3 border">
        <thead className="bg-blue-600 text-white">
          <tr>
            <th className="p-2 text-left">Name</th>
            <th className="p-2 text-left">Timestamp</th>
            <th className="p-2 text-left">Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map((r, i) => (
            <tr key={i} className="border-t">
              <td className="p-2">{r.name}</td>
              <td className="p-2">{new Date(r.timestamp).toLocaleString("en-IN")}</td>
              <td className="p-2">{r.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ───────────────────────────────────────────────
// Work Hours (existing API)

function HoursReport() {
  const [date, setDate] = useState(new Date());
  const [rows, setRows] = useState([]);

  const fetch = async () => {
    try {
      const res = await api.get(`/api/report/hours/${getKolkataDateString(date)}`);
      setRows(res.data);
    } catch {
      toast.error("Failed to fetch work hours");
    }
  };

  useEffect(() => { fetch(); }, [date]); // --- UPDATED --- (Added date to dependency array)

  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="text-xl mb-3 font-semibold">Work Hours</h2>
      <DatePicker selected={date} onChange={setDate} className="border px-2 py-1 mb-3" />
      <button onClick={fetch} className="px-3 py-1 bg-blue-50 rounded">Refresh</button>
      <table className="w-full mt-3 border">
        <thead className="bg-blue-600 text-white">
          <tr>
            <th className="p-2">Name</th>
            <th className="p-2">Hours Worked</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t">
              <td className="p-2">{r.name}</td>
              <td className="p-2">{r.total_hours} hrs</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ───────────────────────────────────────────────
// Analytics

// --- UPDATED (Whole Component) ---
function OverallAnalytics() {
  const [date, setDate] = useState(new Date());
  const [records, setRecords] = useState([]);

  const fetch = async () => {
    const d = getKolkataDateString(date);
    try {
      const res = await api.get(`/api/report/hours/${d}`);
      setRecords(res.data);
    } catch {
      toast.error("Failed to fetch analytics");
    }
  };
  useEffect(() => { fetch(); }, [date]); // Update when date changes

  const totalUsers = records.length;
  const avgHours =
    totalUsers > 0
      ? (records.reduce((s, r) => s + r.total_hours, 0) / totalUsers)
      : 0;
  
  // Data for Doughnut Chart (Average)
  const avgChartData = {
    labels: ["Avg. Hours IN", "Avg. Hours OUT"],
    datasets: [
      {
        data: [avgHours, 24 - avgHours],
        backgroundColor: ["#36A2EB", "#FF6384"],
        hoverBackgroundColor: ["#36A2EB", "#FF6384"],
      },
    ],
  };

  // Data for Bar Chart (Individual)
  const barChartData = {
    labels: records.map(r => r.name),
    datasets: [
      {
        label: "Hours Worked",
        data: records.map(r => r.total_hours),
        backgroundColor: "rgba(75, 192, 192, 0.6)",
      },
    ],
  };

  const barOptions = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Work Hours per User" },
    },
  };

  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="text-xl mb-3 font-semibold">Overall Analytics</h2>
      <DatePicker selected={date} onChange={setDate} className="border px-2 py-1 mb-3" />
      <button onClick={fetch} className="px-3 py-1 bg-blue-50 rounded">Refresh</button>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Stat Cards */}
        <div className="bg-blue-50 p-4 rounded-lg shadow-inner text-center">
          <h3 className="text-gray-600">Total Users</h3>
          <p className="text-3xl font-bold text-blue-700">{totalUsers}</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg shadow-inner text-center">
          <h3 className="text-gray-600">Avg. Hours</h3>
          <p className="text-3xl font-bold text-green-700">{avgHours.toFixed(2)}</p>
        </div>
        
        {/* Doughnut Chart */}
        <div className="md:col-span-1 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold text-center mb-2">Average Hours</h3>
          {totalUsers > 0 ? (
            <Doughnut data={avgChartData} />
          ) : (
            <p className="text-center text-gray-500">No data</p>
          )}
        </div>
      </div>
      
      {/* Bar Chart */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-semibold text-center mb-2">Individual Hours</h3>
        {totalUsers > 0 ? (
          <Bar options={barOptions} data={barChartData} />
        ) : (
          <p className="text-center text-gray-500">No data to display</p>
        )}
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────
// Personal Analytics (per user breakdown)

// --- UPDATED (Whole Component) ---
function PersonalAnalytics() {
  const [name, setName] = useState("");
  const [data, setData] = useState(null); // Use null for no data
  const [chartData, setChartData] = useState(null);

  const fetch = async () => {
    if (!name) return toast.error("Please enter a name");
    setData(null); // Clear previous data
    setChartData(null);
    try {
      const res = await api.get("/api/report/hours/" + getKolkataDateString(new Date()));
      const rec = res.data.find((r) => r.name.toLowerCase() === name.toLowerCase());
      
      if (!rec) {
        return toast.info(`No record found for "${name}" today.`);
      }
      
      const out = 24 - rec.total_hours;
      const userData = { ...rec, out };
      setData(userData);

      // Prepare chart data
      setChartData({
        labels: ["Hours IN", "Hours OUT"],
        datasets: [
          {
            data: [userData.total_hours, userData.out],
            backgroundColor: ["#4BC0C0", "#FF9F40"],
            hoverBackgroundColor: ["#4BC0C0", "#FF9F40"],
          },
        ],
      });

    } catch {
      toast.error("Error fetching analytics");
    }
  };

  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="text-xl mb-3 font-semibold">Personal Analytics</h2>
      <div className="flex">
        <input
          className="border px-3 py-2 rounded-l mr-0"
          placeholder="Enter Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button onClick={fetch} className="px-4 py-2 bg-blue-600 text-white rounded-r">
          View
        </button>
      </div>

      {data && chartData && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
          {/* Text Summary */}
          <div>
            <h3 className="text-2xl font-medium text-blue-700">{data.name}</h3>
            <p className="text-lg text-green-700">
              Worked: <strong>{data.total_hours} hrs</strong>
            </p>
            <p className="text-lg text-orange-700">
              Spent Outside: <strong>{data.out.toFixed(2)} hrs</strong>
            </p>
          </div>
          {/* Doughnut Chart */}
          <div className="max-w-xs mx-auto">
            <Doughnut
              data={chartData}
              options={{
                responsive: true,
                plugins: {
                  legend: { position: "top" },
                  title: { display: true, text: `Hours for ${data.name}` },
                },
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// ───────────────────────────────────────────────
// Attendance Control
// ... (No changes to AttendanceControl, ManageUsers) ...

function AttendanceControl() {
  const [cmd, setCmd] = useState("unknown");
  const [busy, setBusy] = useState(false);

  const fetch = async () => {
    try {
      const res = await api.get("/api/kiosk/control");
      setCmd(res.data.command);
    } catch {
      setCmd("error");
    }
  };

  useEffect(() => { fetch(); }, []);

  const send = async (c) => {
    setBusy(true);
    try {
      await api.post("/api/kiosk/control", { command: c });
      toast.success(`Command: ${c}`);
      setCmd(c);
    } catch {
      toast.error("Failed to send command");
    }
    setBusy(false);
  };

  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="text-xl font-semibold mb-3">Attendance Control</h2>
      <p className="mb-2">Current Command: <strong>{cmd}</strong></p>
      <div className="space-x-2">
        <button onClick={() => send("run")} disabled={busy} className="px-3 py-2 bg-green-600 text-white rounded">
          <Play className="w-4 h-4 inline mr-1" /> Resume
        </button>
        <button onClick={() => send("pause")} disabled={busy} className="px-3 py-2 bg-yellow-600 text-white rounded">
          <StopCircle className="w-4 h-4 inline mr-1" /> Pause
        </button>
        <button onClick={() => send("shutdown")} disabled={busy} className="px-3 py-2 bg-red-600 text-white rounded">
          <StopCircle className="w-4 h-4 inline mr-1" /> Shutdown
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-3">
        Pause: recognition stops temporarily but stays live. Resume to continue. Shutdown fully ends kiosk process.
      </p>
    </div>
  );
}

// ───────────────────────────────────────────────
// Manage Users

function ManageUsers() {
  const [users, setUsers] = useState([]);
  const fetch = async () => {
    try {
      const res = await api.get("/api/users");
      setUsers(res.data);
    } catch {
      toast.error("Failed to fetch users");
    }
  };
  useEffect(() => { fetch(); }, []);

  const del = async (id) => {
    if (!window.confirm("Delete this user?")) return;
    try {
      await api.delete(`/api/users/${id}`);
      toast.success("User deleted");
      fetch();
    } catch {
      toast.error("Delete failed");
    }
  };

  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="text-xl font-semibold mb-3">Manage Users</h2>
      <table className="w-full border">
        <thead className="bg-blue-600 text-white">
          <tr><th className="p-2">ID</th><th className="p-2">Name</th><th className="p-2">Action</th></tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} className="border-t">
              <td className="p-2">{u.id}</td>
              <td className="p-2">{u.name}</td>
              <td className="p-2">
                <button onClick={() => del(u.id)} className="px-2 py-1 bg-red-100 text-red-600 rounded">
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}