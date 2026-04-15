import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://127.0.0.1:8000';

const styles = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, Roboto; background: #fef9f3; }
  .sw-app { max-width: 428px; margin: 0 auto; min-height: 100vh; background: #fef9f3; padding-bottom: 70px; }
  .header { background: linear-gradient(135deg, #7c9cbf 0%, #8fa9c9 100%); color: #fff; padding: 20px; text-align: center; font-weight: 700; }
  .content { padding: 20px; }
  .btn { width: 100%; padding: 16px; border: none; background: #8b9dc3; color: #fff; font-size: 16px; cursor: pointer; border-radius: 8px; margin-top: 10px; }
  .btn-secondary { background: #c9c9c9; color: #333; }
  .btn:hover { background: #7a88b0; }
  .btn-secondary:hover { background: #ababab; }
  .form-group { margin-bottom: 20px; }
  .form-group label { display: block; margin-bottom: 8px; font-weight: 600; }
  .form-group input, .form-group select { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
  .form-group input:focus, .form-group select:focus { outline: none; border-color: #8b9dc3; }
  .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: #fff; display: flex; justify-content: space-around; border-top: 2px solid #ddd; z-index: 100; }
  .nav-item { flex: 1; text-align: center; padding: 10px; cursor: pointer; font-size: 20px; }
  .nav-item.active { color: #8b9dc3; }
  .toast { position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%); background: #2d3748; color: #fff; padding: 12px 20px; border-radius: 8px; z-index: 200; }
  .welcome { text-align: center; padding: 50px 20px; }
  .welcome h1 { color: #7c9cbf; font-size: 32px; margin-bottom: 30px; }
  .tab-buttons { display: flex; gap: 20px; justify-content: center; margin-bottom: 30px; }
  .tab-btn { border: none; background: none; cursor: pointer; padding: 5px 10px; font-size: 16px; border-bottom: 3px solid transparent; }
  .tab-btn.active { border-color: #7c9cbf; font-weight: bold; }

  /* Dashboard */
  .card { background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  .card-title { font-size: 14px; color: #666; font-weight: 600; margin-bottom: 8px; }
  .card-value { font-size: 28px; color: #7c9cbf; font-weight: 700; }
  .card-subtext { font-size: 12px; color: #999; margin-top: 8px; }

  /* Expense Breakdown */
  .expense-table { font-size: 14px; }
  .expense-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #eee; }
  .expense-col1 { flex: 2; color: #333; }
  .expense-col2 { flex: 1; text-align: right; color: #7c9cbf; font-weight: 600; }
  .expense-col3 { flex: 1; text-align: right; color: #999; font-size: 12px; }

  /* Period Filter */
  .period-filter { display: flex; gap: 8px; margin-bottom: 15px; flex-wrap: wrap; }
  .period-btn { padding: 8px 12px; border: 1px solid #ddd; background: #fff; border-radius: 6px; cursor: pointer; font-size: 12px; }
  .period-btn.active { background: #8b9dc3; color: #fff; border-color: #8b9dc3; }

  /* Alert Box */
  .alert-box { background: #fff3cd; border-left: 4px solid #ffc107; padding: 14px; margin-bottom: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
  .alert-box.danger { background: #fff5f5; border-left-color: #ff6b6b; }
  .alert-box.success { background: #f0fdf4; border-left-color: #22c55e; }
  .alert-box.info { background: #e7f5ff; border-left-color: #4dabf7; }
  .alert-box.error { background: #ffe0e0; border-left-color: #fa5252; }
  .alert-box.unread { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  .alert-box.read { opacity: 0.7; }
  .alert-msg { font-size: 14px; color: #555; line-height: 1.5; }
  .alert-title { font-weight: 600; margin-bottom: 5px; }

  /* Loading & Error */
  .loading { text-align: center; padding: 20px; color: #999; }
  .error { background: #fff5f5; border-left: 4px solid #ff6b6b; padding: 12px; margin-bottom: 15px; border-radius: 4px; color: #c53030; }

  /* Import bulk delete */
  .import-toolbar { display: flex; gap: 10px; align-items: center; justify-content: space-between; margin: 10px 0 20px; }
  .pill { display: inline-flex; align-items: center; justify-content: center; padding: 6px 10px; border-radius: 999px; background: #f1f5f9; color: #334155; font-size: 12px; font-weight: 600; }
  .checkbox { width: 18px; height: 18px; cursor: pointer; }
  .section-title { font-size: 14px; font-weight: 700; color: #475569; margin: 20px 0 10px; }
`;

export default function UserInterface() {
  // Tokens (from localStorage)
  const [token, setToken] = useState(localStorage.getItem('access_token') || '');
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refresh_token') || '');

  // ✅ NEW: store user id for import bulk delete endpoint
  const [userId, setUserId] = useState(() => {
    const saved = localStorage.getItem('user_id');
    return saved ? parseInt(saved, 10) : null;
  });

  const [page, setPage] = useState(token ? 'app' : 'welcome');
  const [activePage, setActivePage] = useState('dashboard');
  const [isLogin, setIsLogin] = useState(true);
  const [toast, setToast] = useState(null);

  // Auth forms
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [setupData, setSetupData] = useState({ MonthlyIncome: '', HouseholdSize: '', TransportationTypes: ['default'] });

  // Dashboard state
  const [dashboardSummary, setDashboardSummary] = useState(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [dashboardExtras, setDashboardExtras] = useState({
    inflation: null,
    pir: null,
    forecast: null,
    breakdown: null,
    trend: null
  });

  // Expenses state
  const [expenses, setExpenses] = useState([]);
  const [expForm, setExpForm] = useState({
    Type: 'Food',
    ItemName: '',
    AmountSpent: '',
    DatePurchased: new Date().toISOString().split('T')[0],
    Note: ''
  });
  const [loadingExpenses, setLoadingExpenses] = useState(false);
  const [period, setPeriod] = useState('all_time');

  // Budget state
  const [budgetData, setBudgetData] = useState(null);
  const [budgetForm, setBudgetForm] = useState({
    AutoBudget: true,
    TotalBudget: 0,
    Food: 0,
    Transport: 0,
    Utilities: 0,
    Entertainment: 0,
    Shopping: 0,
    Healthcare: 0,
    Other: 0
  });
  const [loadingBudget, setLoadingBudget] = useState(false);

  // Alerts state
  const [alerts, setAlerts] = useState([]);
  const [loadingAlerts, setLoadingAlerts] = useState(false);

  // User settings state
  const [userSettings, setUserSettings] = useState(null);
  const [loadingSettings, setLoadingSettings] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  const [settingsForm, setSettingsForm] = useState({
    MonthlyIncome: 0,
    HouseholdSize: 1,
    TransportationTypes: 'default',
    AlertThreshold: 80,
    PriceIncreaseAlerts: true,
    BudgetThresholdAlerts: true
  });

  // Import expenses state
  const [importedExpenses, setImportedExpenses] = useState([]);
  const [loadingImported, setLoadingImported] = useState(false);
  const [importPage, setImportPage] = useState(1);
  const [importYear, setImportYear] = useState(null);
  const [importForm, setImportForm] = useState([
    { Month: '', Food: 0, Transport: 0, Utilities: 0, Entertainment: 0, Shopping: 0, Healthcare: 0 }
  ]);
  const [loadingImport, setLoadingImport] = useState(false);
  const importPageSize = 6;

  // multiselect + delete for imported expenses
  const [selectedImportedIds, setSelectedImportedIds] = useState(new Set());
  const [loadingDeleteImported, setLoadingDeleteImported] = useState(false);

  // Basket state
  const [basketItems, setBasketItems] = useState([]);
  const [loadingBasket, setLoadingBasket] = useState(false);
  const [basketForm, setBasketForm] = useState({ Type: 'Food', ItemName: '', AmountSpent: '', Note: '' });
  const [selectedBasketIds, setSelectedBasketIds] = useState(new Set());
  const [loadingDeleteBasket, setLoadingDeleteBasket] = useState(false);

  // Account security state
  const [securityForm, setSecurityForm] = useState({
    currentPassword: '',
    newPassword: '',
    reNewPassword: '',
    forgotEmail: '',
    deletePassword: '',
    deleteConfirm: false
  });
  const [savingSecurity, setSavingSecurity] = useState(false);

  const expenseCategories = ['Food', 'Transport', 'Utilities', 'Entertainment', 'Shopping', 'Healthcare', 'Other'];
  const importCategories = ['Food', 'Transport', 'Utilities', 'Entertainment', 'Shopping', 'Healthcare'];
  const periodOptions = ['all_time', 'this_month', '6_months', 'past_year'];

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const mapSettingsToForm = (settings) => ({
    MonthlyIncome: settings?.MonthlyIncome ?? 0,
    HouseholdSize: settings?.HouseholdSize ?? 1,
    TransportationTypes: settings?.TransportationTypes ?? 'default',
    AlertThreshold: settings?.AlertThreshold ?? 80,
    PriceIncreaseAlerts: settings?.PriceIncreaseAlerts ?? true,
    BudgetThresholdAlerts: settings?.BudgetThresholdAlerts ?? true
  });

  const normalizeExpenseTypeForDisplay = (value) => {
    if (value === 'Food & Dining') return 'Food';
    return value;
  };

  const clearTokens = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    setToken('');
    setRefreshToken('');
    setUserId(null);
  };

  // Refresh flow: POST /refresh with refresh token
  const refreshAccessToken = async () => {
    const rt = localStorage.getItem('refresh_token');
    if (!rt) return null;

    const res = await fetch(`${API_BASE_URL}/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rt)
    });

    if (!res.ok) return null;

    const data = await res.json();
    if (!data?.AccessToken) return null;

    localStorage.setItem('access_token', data.AccessToken);
    setToken(data.AccessToken);
    return data.AccessToken;
  };

  // Centralized fetch that retries once on 401 by refreshing the access token
  const fetchWithAuth = async (url, options = {}) => {
    const access = localStorage.getItem('access_token') || token;

    const headers = {
      ...(options.headers || {}),
      Authorization: `Bearer ${access}`
    };

    const finalOpts = { ...options, headers };

    let res = await fetch(url, finalOpts);

    if (res.status === 401) {
      const newAccess = await refreshAccessToken();
      if (!newAccess) {
        clearTokens();
        setPage('welcome');
        showToast('Session expired. Please sign in again.');
        return res;
      }

      const retryHeaders = {
        ...(options.headers || {}),
        Authorization: `Bearer ${newAccess}`
      };
      res = await fetch(url, { ...options, headers: retryHeaders });
    }

    return res;
  };

  // ─────── AUTH HANDLERS ───────
  const handleLogin = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('username', loginForm.username);
    formData.append('password', loginForm.password);

    try {
      const response = await fetch(`${API_BASE_URL}/login`, { method: 'POST', body: formData });
      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('access_token', data.AccessToken);
        localStorage.setItem('refresh_token', data.RefreshToken);

        setToken(data.AccessToken);
        setRefreshToken(data.RefreshToken);

        const settingsRes = await fetchWithAuth(`${API_BASE_URL}/settings`);
        if (settingsRes.ok) {
          const settings = await settingsRes.json();
          setUserSettings(settings);
          setSettingsForm(mapSettingsToForm(settings));
          setPage(settings?.SetupCompleted ? 'app' : 'setup');
        } else {
          setPage('setup');
        }

        showToast('Login successful!');
      } else {
        showToast(data.detail || 'Login failed!');
      }
    } catch (err) {
      showToast('Error connecting to server: ' + err.message);
    }
  };

  // Password validation rules
  const validatePassword = (password) => {
    const rules = {
      length: password.length >= 8,
      number: /\d/.test(password),
      uppercase: /[A-Z]/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>+]/.test(password)
    };
    return rules;
  };

  const [passwordRules, setPasswordRules] = useState({ length: false, number: false, uppercase: false, special: false });

  const handleSignup = async (e) => {
    e.preventDefault();
    
    // Validate password before submission
    const rules = validatePassword(loginForm.password);
    if (!rules.length || !rules.number || !rules.uppercase || !rules.special) {
      showToast('Password must meet all criteria');
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Email: loginForm.username, Password: loginForm.password })
      });
      const data = await res.json();
      if (res.ok) {
        showToast('Account created! Sign in now.');
        setIsLogin(true);
        setLoginForm({ username: '', password: '' });
        setPasswordRules({ length: false, number: false, uppercase: false, special: false });
      } else {
        showToast(data.detail || 'Failed to create account');
      }
    } catch (err) {
      showToast('Error: ' + err.message);
    }
  };

  const handlePasswordChange = (e) => {
    const pwd = e.target.value;
    setLoginForm({ ...loginForm, password: pwd });
    setPasswordRules(validatePassword(pwd));
  };

  const handleSetup = async (e) => {
    e.preventDefault();

    const monthlyIncome = parseFloat(setupData.MonthlyIncome);
    const householdSize = parseInt(setupData.HouseholdSize, 10);
    if (Number.isNaN(monthlyIncome) || monthlyIncome < 0) {
      showToast('Monthly income must be 0 or more.');
      return;
    }
    if (Number.isNaN(householdSize) || householdSize < 1) {
      showToast('Household size must be at least 1.');
      return;
    }

    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/settings/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          MonthlyIncome: monthlyIncome,
          HouseholdSize: householdSize,
          TransportationTypes: Array.isArray(setupData.TransportationTypes)
            ? setupData.TransportationTypes[0]
            : setupData.TransportationTypes
        })
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setPage('app');
        showToast('Setup complete!');
      } else {
        showToast(data.detail || 'Setup failed');
      }
    } catch (err) {
      showToast('Error: ' + err.message);
    }
  };

  const handleQuickSetup = async () => {
    const monthlyIncome = parseFloat(setupData.MonthlyIncome);
    if (Number.isNaN(monthlyIncome) || monthlyIncome < 0) {
      showToast('Monthly income must be 0 or more.');
      return;
    }

    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/settings/quick-setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ MonthlyIncome: monthlyIncome })
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setPage('app');
        showToast('Quick setup complete!');
      } else {
        showToast(data.detail || 'Quick setup failed');
      }
    } catch (err) {
      showToast('Error: ' + err.message);
    }
  };

  const handleFillLater = async () => {
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/settings/fill-later`, {
        method: 'POST'
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setPage('app');
        showToast('Setup skipped. You can update settings later.');
      } else {
        showToast(data.detail || 'Unable to skip setup');
      }
    } catch (err) {
      showToast('Error: ' + err.message);
    }
  };

  const handleLogout = async () => {
    try {
      if (localStorage.getItem('access_token')) {
        await fetchWithAuth(`${API_BASE_URL}/logout`, { method: 'POST' });
      }
    } catch {
      // ignore
    } finally {
      clearTokens();
      setPage('welcome');
      setLoginForm({ username: '', password: '' });
      showToast('Logged out');
    }
  };

  // ─────── DASHBOARD HANDLERS ───────
  useEffect(() => {
    if (page === 'app' && activePage === 'dashboard' && token) {
      fetchDashboardSummary();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePage, token, page]);

  const fetchDashboardSummary = async () => {
    setLoadingDashboard(true);
    try {
      const [summaryRes, inflationRes, pirRes, forecastRes, breakdownRes, trendRes] = await Promise.all([
        fetchWithAuth(`${API_BASE_URL}/dashboard/summary`),
        fetchWithAuth(`${API_BASE_URL}/dashboard/inflation-rates`),
        fetchWithAuth(`${API_BASE_URL}/dashboard/calculate-pir`),
        fetchWithAuth(`${API_BASE_URL}/dashboard/forecast`),
        fetchWithAuth(`${API_BASE_URL}/dashboard/spending-breakdown`),
        fetchWithAuth(`${API_BASE_URL}/dashboard/trend`)
      ]);

      if (summaryRes.ok) {
        const data = await summaryRes.json();
        setDashboardSummary(data);
      } else {
        showToast('Failed to load dashboard');
      }

      setDashboardExtras({
        inflation: inflationRes.ok ? await inflationRes.json().catch(() => null) : null,
        pir: pirRes.ok ? await pirRes.json().catch(() => null) : null,
        forecast: forecastRes.ok ? await forecastRes.json().catch(() => null) : null,
        breakdown: breakdownRes.ok ? await breakdownRes.json().catch(() => null) : null,
        trend: trendRes.ok ? await trendRes.json().catch(() => null) : null
      });
    } catch (err) {
      showToast('Error: ' + err.message);
    } finally {
      setLoadingDashboard(false);
    }
  };

  // ─────── BASKET HANDLERS ───────
  useEffect(() => {
    if (page === 'app' && activePage === 'basket' && token) {
      fetchBasket();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePage, token, page]);

  const fetchBasket = async () => {
    setLoadingBasket(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/basket/`);
      if (res.ok) {
        const data = await res.json();
        setBasketItems(Array.isArray(data) ? data : []);
      } else {
        setBasketItems([]);
      }
    } catch {
      setBasketItems([]);
    } finally {
      setLoadingBasket(false);
    }
  };

  const handleAddBasket = async (e) => {
    e.preventDefault();
    const amount = parseFloat(basketForm.AmountSpent);
    if (!basketForm.ItemName.trim()) {
      showToast('Basket item name is required.');
      return;
    }
    if (Number.isNaN(amount) || amount <= 0) {
      showToast('Basket amount must be greater than 0.');
      return;
    }

    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/basket/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          Type: basketForm.Type,
          ItemName: basketForm.ItemName.trim(),
          AmountSpent: amount,
          Note: basketForm.Note || null
        })
      });
      if (res.ok) {
        setBasketForm({ Type: 'Food', ItemName: '', AmountSpent: '', Note: '' });
        showToast('Basket item added.');
        fetchBasket();
      } else {
        const data = await res.json().catch(() => ({}));
        showToast(data.detail || 'Failed to add basket item');
      }
    } catch (err) {
      showToast('Error adding basket item: ' + err.message);
    }
  };

  const toggleBasketSelection = (id) => {
    setSelectedBasketIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleDeleteBasket = async () => {
    const ids = Array.from(selectedBasketIds);
    if (ids.length === 0) {
      showToast('Select basket items to delete.');
      return;
    }

    try {
      setLoadingDeleteBasket(true);
      const res = await fetchWithAuth(`${API_BASE_URL}/basket/`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ BasketExpensesId: ids })
      });
      if (res.ok) {
        showToast('Basket items deleted.');
        setSelectedBasketIds(new Set());
        fetchBasket();
      } else {
        const data = await res.json().catch(() => ({}));
        showToast(data.detail || 'Failed to delete basket items');
      }
    } catch (err) {
      showToast('Error deleting basket items: ' + err.message);
    } finally {
      setLoadingDeleteBasket(false);
    }
  };

  // ─────── EXPENSES HANDLERS ───────
  useEffect(() => {
    if (page === 'app' && activePage === 'expenses' && token) {
      fetchExpenses();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePage, token, period, page]);

  // backend returns list[CategorySummary] => we flatten to display in current table
  const fetchExpenses = async () => {
    setLoadingExpenses(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/categories/?period=${period}`);
      if (res.ok) {
        const data = await res.json();

        if (Array.isArray(data)) {
          const flattened = data.flatMap((cat) =>
            Array.isArray(cat?.expenses)
              ? cat.expenses.map((e) => ({
                  ...e,
                  _categoryName: cat.category,
                  _categoryTotal: cat.total
                }))
              : []
          );

          setExpenses(flattened);
        } else {
          setExpenses([]);
        }
      } else {
        const errData = await res.json().catch(() => ({}));
        showToast(errData.detail || `Failed to load expenses (HTTP ${res.status})`);
      }
    } catch (err) {
      showToast('Error: ' + err.message);
    } finally {
      setLoadingExpenses(false);
    }
  };

  const handleAddExpense = async (e) => {
    e.preventDefault();

    const amount = parseFloat(expForm.AmountSpent);
    if (!expForm.ItemName.trim()) {
      showToast('Item name is required.');
      return;
    }
    if (Number.isNaN(amount) || amount <= 0) {
      showToast('Amount must be greater than 0.');
      return;
    }

    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/expenses/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          Type: expForm.Type,
          ItemName: expForm.ItemName.trim(),
          AmountSpent: amount,
          DatePurchased: expForm.DatePurchased,
          Note: expForm.Note
        })
      });

      if (res.ok) {
        showToast('Expense added!');
        setExpForm({
          Type: 'Food',
          ItemName: '',
          AmountSpent: '',
          DatePurchased: new Date().toISOString().split('T')[0],
          Note: ''
        });
        fetchExpenses();
      } else {
        const data = await res.json().catch(() => ({}));
        showToast(data.detail || `Error adding expense (HTTP ${res.status})`);
      }
    } catch (err) {
      showToast('Error adding expense: ' + err.message);
    }
  };

  // ─────── BUDGET HANDLERS ───────
  useEffect(() => {
    if (page === 'app' && activePage === 'budget' && token) {
      fetchBudget();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePage, token, page]);

  const fetchBudget = async () => {
    setLoadingBudget(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/budget`);
      if (res.ok) {
        const data = await res.json();
        setBudgetData(data);
        if (data?.Settings) {
          setBudgetForm((prev) => ({ ...prev, ...data.Settings }));
        }
      }
    } catch (err) {
      showToast('Error loading budget');
    } finally {
      setLoadingBudget(false);
    }
  };

  const handleSaveBudget = async (e) => {
    e.preventDefault();
    if (!budgetForm.AutoBudget && (Number.isNaN(parseInt(budgetForm.TotalBudget, 10)) || parseInt(budgetForm.TotalBudget, 10) < 0)) {
      showToast('Total budget must be 0 or more.');
      return;
    }

    try {
      const payload = {
        AutoBudget: budgetForm.AutoBudget,
        ...(budgetForm.AutoBudget
          ? {}
          : {
              TotalBudget: parseInt(budgetForm.TotalBudget, 10) || 0,
              CategoryBudgets: {
                Food: parseInt(budgetForm.Food, 10) || 0,
                Transport: parseInt(budgetForm.Transport, 10) || 0,
                Utilities: parseInt(budgetForm.Utilities, 10) || 0,
                Entertainment: parseInt(budgetForm.Entertainment, 10) || 0,
                Shopping: parseInt(budgetForm.Shopping, 10) || 0,
                Healthcare: parseInt(budgetForm.Healthcare, 10) || 0,
                Other: parseInt(budgetForm.Other, 10) || 0
              }
            })
      };

      const res = await fetchWithAuth(`${API_BASE_URL}/budget/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        showToast('Budget saved!');
        fetchBudget();
      } else {
        const data = await res.json().catch(() => ({}));
        showToast(data.detail || 'Error saving budget');
      }
    } catch (err) {
      showToast('Error saving budget');
    }
  };

  // ─────── ALERTS HANDLERS ───────
  useEffect(() => {
    if (page === 'app' && activePage === 'alerts' && token) {
      fetchAlerts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePage, token, page]);

  const fetchAlerts = async () => {
    setLoadingAlerts(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/dashboard/`);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (err) {
      console.log('Error fetching alerts:', err);
    } finally {
      setLoadingAlerts(false);
    }
  };

  const handleMarkAlertRead = async (alertId) => {
    try {
      await fetchWithAuth(`${API_BASE_URL}/dashboard/${alertId}/read`, {
        method: 'PUT'
      });
      fetchAlerts();
    } catch (err) {
      showToast('Error marking alert as read');
    }
  };

  const handleDeleteAlert = async (alertId) => {
    try {
      await fetchWithAuth(`${API_BASE_URL}/dashboard/${alertId}`, {
        method: 'DELETE'
      });
      fetchAlerts();
      showToast('Alert deleted');
    } catch (err) {
      showToast('Error deleting alert');
    }
  };

  // ─────── SETTINGS HANDLERS ───────
  useEffect(() => {
    if (page === 'app' && activePage === 'settings' && token) {
      fetchUserSettings();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePage, token, page]);

  const fetchUserSettings = async () => {
    setLoadingSettings(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/settings/`);
      if (res.ok) {
        const data = await res.json();
        setUserSettings(data);
        setSettingsForm(mapSettingsToForm(data));
      } else {
        console.error('Settings fetch failed:', res.status);
      }
    } catch (err) {
      console.log('Error fetching settings:', err);
    } finally {
      setLoadingSettings(false);
    }
  };

  const handleSaveSettings = async (e) => {
    e.preventDefault();

    const monthlyIncome = parseFloat(settingsForm.MonthlyIncome);
    const householdSize = parseInt(settingsForm.HouseholdSize, 10);
    const alertThreshold = parseInt(settingsForm.AlertThreshold, 10);

    if (Number.isNaN(monthlyIncome) || monthlyIncome < 0) {
      showToast('Monthly income must be 0 or more.');
      return;
    }
    if (Number.isNaN(householdSize) || householdSize < 1) {
      showToast('Household size must be at least 1.');
      return;
    }
    if (Number.isNaN(alertThreshold) || alertThreshold < 1 || alertThreshold > 100) {
      showToast('Budget alert threshold must be between 1 and 100.');
      return;
    }

    setSavingSettings(true);

    try {
      const payload = {
        MonthlyIncome: monthlyIncome,
        HouseholdSize: householdSize,
        TransportationTypes: settingsForm.TransportationTypes,
        AlertThreshold: alertThreshold,
        PriceIncreaseAlerts: !!settingsForm.PriceIncreaseAlerts,
        BudgetThresholdAlerts: !!settingsForm.BudgetThresholdAlerts
      };

      const res = await fetchWithAuth(`${API_BASE_URL}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const updated = await res.json();
        setUserSettings(updated);
        setSettingsForm(mapSettingsToForm(updated));
        showToast('Settings saved!');
      } else {
        const data = await res.json().catch(() => ({}));
        showToast(data.detail || 'Failed to save settings');
      }
    } catch (err) {
      showToast('Error saving settings: ' + err.message);
    } finally {
      setSavingSettings(false);
    }
  };

  const handleVerifyPassword = async () => {
    if (!securityForm.currentPassword) {
      showToast('Enter current password.');
      return;
    }
    setSavingSecurity(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/users/verify-password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Password: securityForm.currentPassword })
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        showToast('Password verified.');
      } else {
        showToast(data.detail || 'Password verification failed');
      }
    } catch (err) {
      showToast('Error verifying password: ' + err.message);
    } finally {
      setSavingSecurity(false);
    }
  };

  const handleChangePassword = async () => {
    if (!securityForm.newPassword || !securityForm.reNewPassword) {
      showToast('Enter new password and confirmation.');
      return;
    }
    setSavingSecurity(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/users/change-password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Password: securityForm.newPassword, RePassword: securityForm.reNewPassword })
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        showToast('Password updated.');
        setSecurityForm((prev) => ({ ...prev, newPassword: '', reNewPassword: '' }));
      } else {
        showToast(data.detail || 'Failed to update password');
      }
    } catch (err) {
      showToast('Error changing password: ' + err.message);
    } finally {
      setSavingSecurity(false);
    }
  };

  const handleForgotPassword = async () => {
    const email = (securityForm.forgotEmail || loginForm.username || '').trim();
    if (!email) {
      showToast('Enter an email for recovery.');
      return;
    }
    setSavingSecurity(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/users/forgot-password?email=${encodeURIComponent(email)}`, {
        method: 'POST'
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        showToast(data.msg || 'Recovery flow started.');
      } else {
        showToast(data.detail || 'Failed to start recovery flow');
      }
    } catch (err) {
      showToast('Error starting recovery flow: ' + err.message);
    } finally {
      setSavingSecurity(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!securityForm.deleteConfirm) {
      showToast('Please confirm account deletion checkbox first.');
      return;
    }
    if (!securityForm.deletePassword) {
      showToast('Enter your password to delete account.');
      return;
    }

    const confirmed = window.confirm('Delete your account and all data permanently?');
    if (!confirmed) return;

    setSavingSecurity(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/users/delete`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          Password: securityForm.deletePassword,
          IsSure: true,
          DataDelete: true
        })
      });

      if (res.ok || res.status === 204) {
        clearTokens();
        setPage('welcome');
        showToast('Account deleted.');
      } else {
        const data = await res.json().catch(() => ({}));
        showToast(data.detail || 'Failed to delete account');
      }
    } catch (err) {
      showToast('Error deleting account: ' + err.message);
    } finally {
      setSavingSecurity(false);
    }
  };

  // ─────── IMPORT EXPENSES HANDLERS ───────
  useEffect(() => {
    if (page === 'app' && activePage === 'import' && token) {
      fetchImportedExpenses();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePage, token, importPage, importYear, page]);

  const fetchImportedExpenses = async () => {
    setLoadingImported(true);
    try {
      let url = `${API_BASE_URL}/import/previous-expenses?page=${importPage}&size=6`;
      if (importYear) url += `&year=${importYear}`;

      const res = await fetchWithAuth(url);

      if (res.ok) {
        const data = await res.json();
        setImportedExpenses(Array.isArray(data) ? data : []);
        if (Array.isArray(data) && data.length > 0 && userId == null && data[0]?.UserId != null) {
          localStorage.setItem('user_id', String(data[0].UserId));
          setUserId(data[0].UserId);
        }
        setSelectedImportedIds(new Set());
        return;
      }

      // toast on "none"
      if (res.status === 404) {
        const errData = await res.json().catch(() => ({}));
        showToast(errData.detail || 'No expenses found.');
        setImportedExpenses([]);
        setSelectedImportedIds(new Set());
        return;
      }

      const errData = await res.json().catch(() => ({}));
      showToast(errData.detail || `Failed to load imported expenses (HTTP ${res.status})`);
    } catch (err) {
      showToast('Error loading imported expenses: ' + err.message);
    } finally {
      setLoadingImported(false);
    }
  };

  const handleImportExpenses = async (e) => {
    e.preventDefault();

    const invalidMonth = importForm.find((row) => !/^\d{4}-\d{2}$/.test(String(row.Month).trim()));
    if (invalidMonth) {
      showToast('Month must be in YYYY-MM format.');
      return;
    }

    const hasNegative = importForm.some((row) =>
      importCategories.some((cat) => {
        const value = parseFloat(row[cat]);
        return Number.isNaN(value) || value < 0;
      })
    );
    if (hasNegative) {
      showToast('Imported values must be 0 or more.');
      return;
    }

    setLoadingImport(true);
    try {
      const payload = importForm.map((row) => ({
        Month: String(row.Month).trim(),
        Food: parseFloat(row.Food) || 0,
        Transport: parseFloat(row.Transport) || 0,
        Utilities: parseFloat(row.Utilities) || 0,
        Entertainment: parseFloat(row.Entertainment) || 0,
        Shopping: parseFloat(row.Shopping) || 0,
        Healthcare: parseFloat(row.Healthcare) || 0
      }));

      const res = await fetchWithAuth(`${API_BASE_URL}/import/previous-expenses`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        showToast('Expenses imported!');
        setImportForm([
          { Month: '', Food: 0, Transport: 0, Utilities: 0, Entertainment: 0, Shopping: 0, Healthcare: 0 }
        ]);
        fetchImportedExpenses();
      } else {
        const data = await res.json().catch(() => ({}));
        showToast(data.detail || 'Error importing');
      }
    } catch (err) {
      showToast('Error importing');
    } finally {
      setLoadingImport(false);
    }
  };

  const toggleSelectImported = (id) => {
    setSelectedImportedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAllImportedOnPage = () => {
    setSelectedImportedIds((prev) => {
      const next = new Set(prev);
      importedExpenses.forEach((e) => {
        if (e?.Id != null) next.add(e.Id);
      });
      return next;
    });
  };

  const clearImportedSelection = () => {
    setSelectedImportedIds(new Set());
  };

  const handleDeleteSelectedImported = async () => {
    const ids = Array.from(selectedImportedIds);

    if (ids.length === 0) {
      showToast('Select at least one month to delete.');
      return;
    }

    let targetUserId = userId;
    if (targetUserId == null) {
      const selectedRows = importedExpenses.filter((row) => selectedImportedIds.has(row.Id));
      const discoveredUserId = selectedRows.find((row) => row?.UserId != null)?.UserId;
      if (discoveredUserId != null) {
        targetUserId = discoveredUserId;
        localStorage.setItem('user_id', String(discoveredUserId));
        setUserId(discoveredUserId);
      }
    }

    if (targetUserId == null) {
      showToast('Cannot delete: user id not available. Reload import data and try again.');
      return;
    }

    const confirmed = window.confirm(`Delete ${ids.length} imported month(s)? This cannot be undone.`);
    if (!confirmed) return;

    try {
      setLoadingDeleteImported(true);

      const res = await fetchWithAuth(`${API_BASE_URL}/import/${targetUserId}/previous-expenses/delete`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expenses_ids: ids })
      });

      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        showToast(`Deleted ${data.deleted_count ?? ids.length} item(s).`);
        setSelectedImportedIds(new Set());
        fetchImportedExpenses();
      } else {
        const data = await res.json().catch(() => ({}));
        showToast(data.detail || `Delete failed (HTTP ${res.status})`);
      }
    } catch (err) {
      showToast('Error deleting imported expenses: ' + err.message);
    } finally {
      setLoadingDeleteImported(false);
    }
  };

  // ─────── RENDER ───────
  return (
    <div className="sw-app">
      <style>{styles}</style>

      {page === 'welcome' && (
        <div className="welcome">
          <h1>SpendWise</h1>
          <div className="tab-buttons">
            <button className={`tab-btn ${isLogin ? 'active' : ''}`} onClick={() => setIsLogin(true)}>
              Sign In
            </button>
            <button className={`tab-btn ${!isLogin ? 'active' : ''}`} onClick={() => setIsLogin(false)}>
              Sign Up
            </button>
          </div>

          {isLogin ? (
            <form onSubmit={handleLogin}>
              <div className="form-group">
                <input
                  type="email"
                  placeholder="Email"
                  value={loginForm.username}
                  onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <input
                  type="password"
                  placeholder="Password"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                  required
                />
              </div>
              <button type="submit" className="btn">
                Sign In
              </button>
            </form>
          ) : (
            <form onSubmit={handleSignup}>
              <div className="form-group">
                <input
                  type="email"
                  placeholder="Email"
                  value={loginForm.username}
                  onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  placeholder="Password"
                  value={loginForm.password}
                  onChange={handlePasswordChange}
                  required
                />
                {loginForm.password && (
                  <div style={{ fontSize: '12px', marginTop: '8px', color: '#666' }}>
                    <div style={{ color: passwordRules.length ? '#22c55e' : '#999' }}>✓ At least 8 characters</div>
                    <div style={{ color: passwordRules.number ? '#22c55e' : '#999' }}>✓ Contains a number</div>
                    <div style={{ color: passwordRules.uppercase ? '#22c55e' : '#999' }}>✓ Contains uppercase letter</div>
                    <div style={{ color: passwordRules.special ? '#22c55e' : '#999' }}>✓ Contains special character</div>
                  </div>
                )}
              </div>
              <button type="submit" className="btn" disabled={!passwordRules.length || !passwordRules.number || !passwordRules.uppercase || !passwordRules.special}>
                Sign Up
              </button>
            </form>
          )}
        </div>
      )}

      {page === 'setup' && (
        <div className="content">
          <h2 style={{ marginBottom: '20px' }}>Complete Setup</h2>
          <form onSubmit={handleSetup}>
            <div className="form-group">
              <label>Monthly Income</label>
              <input
                type="number"
                value={setupData.MonthlyIncome}
                onChange={(e) => setSetupData({ ...setupData, MonthlyIncome: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Household Size</label>
              <input
                type="number"
                value={setupData.HouseholdSize}
                onChange={(e) => setSetupData({ ...setupData, HouseholdSize: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Transportation Type</label>
              <select
                value={setupData.TransportationTypes[0]}
                onChange={(e) => setSetupData({ ...setupData, TransportationTypes: [e.target.value] })}
                required
              >
                <option value="default">Default</option>
                <option value="bus">Bus</option>
                <option value="train">Train</option>
                <option value="bike">Bike</option>
                <option value="walking">Walking</option>
                <option value="electric">Electric</option>
                <option value="hybrid">Hybrid</option>
                <option value="gasoline">Gasoline</option>
                <option value="taxi">Taxi</option>
                <option value="privatehire">Private Hire</option>
              </select>
            </div>
            <button type="button" className="btn btn-secondary" onClick={handleQuickSetup}>
              Quick Setup (Income only)
            </button>
            <button type="button" className="btn btn-secondary" onClick={handleFillLater}>
              Fill In Later
            </button>
            <button type="submit" className="btn">
              Continue
            </button>
          </form>
        </div>
      )}

      {page === 'app' && (
        <>
          <div className="header">
            🎯 {activePage === 'dashboard' && 'DASHBOARD'}
            {activePage === 'expenses' && '📁 EXPENSES'}
            {activePage === 'add' && '➕ ADD EXPENSE'}
            {activePage === 'budget' && '💰 BUDGET'}
            {activePage === 'basket' && '🧺 BASKET'}
            {activePage === 'import' && '📤 IMPORT'}
            {activePage === 'alerts' && '🔔 ALERTS'}
            {activePage === 'settings' && '⚙️ SETTINGS'}
          </div>

          <div className="content">
            {/* DASHBOARD PAGE */}
            {activePage === 'dashboard' && (
              <div>
                {loadingDashboard ? (
                  <div className="loading">Loading dashboard...</div>
                ) : dashboardSummary ? (
                  <>
                    <div className="card">
                      <div className="card-title">Budget Used</div>
                      <div style={{ marginBottom: '10px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px' }}>
                          <span>${dashboardSummary.total_spent?.toFixed(2) || '0.00'}</span>
                          <span>${dashboardSummary.total_budget?.toFixed(2) || '0.00'}</span>
                        </div>
                        <div style={{
                          width: '100%',
                          height: '24px',
                          backgroundColor: '#e5e7eb',
                          borderRadius: '12px',
                          overflow: 'hidden',
                          border: '1px solid #d1d5db'
                        }}>
                          <div style={{
                            width: `${Math.min(dashboardSummary.budget_percent ?? 0, 100)}%`,
                            height: '100%',
                            backgroundColor: (dashboardSummary.budget_percent ?? 0) > 100 ? '#ef4444' : (dashboardSummary.budget_percent ?? 0) > 75 ? '#f59e0b' : '#10b981',
                            transition: 'width 0.3s ease',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            fontSize: '12px',
                            fontWeight: 'bold'
                          }}>
                            {(dashboardSummary.budget_percent ?? 0) > 10 && `${dashboardSummary.budget_percent ?? 0}%`}
                          </div>
                        </div>
                      </div>
                      <div style={{ fontSize: '12px', color: '#666', marginTop: '8px', textAlign: 'center' }}>
                        {(dashboardSummary.budget_percent ?? 0) > 100 ? '⚠️ Over budget' : (dashboardSummary.budget_percent ?? 0) > 75 ? '⚡ Getting close' : '✓ On track'}
                      </div>
                    </div>

                    <div className="card">
                      <div className="card-title">Realtime Savings</div>
                      <div className="card-value">${dashboardSummary.savings?.toFixed(2) || '0.00'}</div>
                    </div>

                    <div className="card">
                      <div className="card-title">Personal Inflation Rate</div>
                      <div className="card-value">{dashboardExtras?.inflation?.personal_inflation_rate?.toFixed?.(2) ?? '-'}%</div>
                      <div className="card-subtext">National: {dashboardExtras?.inflation?.national_inflation_rate ?? '-'}%</div>
                    </div>

                    {dashboardExtras?.forecast?.data?.length > 0 && (
                      <div className="card">
                        <div className="card-title">6-Month Forecast</div>
                        <svg viewBox="0 0 400 250" style={{ width: '100%', height: '250px', marginTop: '20px' }}>
                          {(() => {
                            const data = dashboardExtras.forecast.data.map(d => Number(d) || 0);
                            const maxValue = Math.max(...data, 1);
                            const padding = 40;
                            const graphWidth = 400 - 2 * padding;
                            const graphHeight = 250 - 2 * padding;
                            const pointSpacing = graphWidth / (data.length - 1 || 1);
                            
                            const points = data.map((value, idx) => {
                              const x = padding + (idx * pointSpacing);
                              const y = padding + graphHeight - (value / maxValue) * graphHeight;
                              return { x, y, value, idx };
                            });
                            
                            const pathData = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
                            
                            return (
                              <>
                                {/* Grid lines */}
                                {[0, 1, 2, 3, 4].map((i) => (
                                  <line key={`grid-${i}`} x1={padding} y1={padding + (graphHeight / 4) * i} x2={400 - padding} y2={padding + (graphHeight / 4) * i} stroke="#e5e7eb" strokeWidth="1" />
                                ))}
                                
                                {/* Axes */}
                                <line x1={padding} y1={padding} x2={padding} y2={padding + graphHeight} stroke="#333" strokeWidth="2" />
                                <line x1={padding} y1={padding + graphHeight} x2={400 - padding} y2={padding + graphHeight} stroke="#333" strokeWidth="2" />
                                
                                {/* Line */}
                                <path d={pathData} stroke="#3b82f6" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                                
                                {/* Points */}
                                {points.map((p) => (
                                  <circle key={`point-${p.idx}`} cx={p.x} cy={p.y} r="4" fill="#3b82f6" stroke="#fff" strokeWidth="2" />
                                ))}
                                
                                {/* Labels */}
                                {points.map((p) => {
                                  const label = dashboardExtras.forecast.labels?.[p.idx] || `M${p.idx + 1}`;
                                  return (
                                    <text key={`label-${p.idx}`} x={p.x} y={padding + graphHeight + 20} textAnchor="middle" fontSize="12" fill="#666">
                                      {label}
                                    </text>
                                  );
                                })}
                                
                                {/* Value labels */}
                                {points.map((p) => (
                                  <text key={`value-${p.idx}`} x={p.x} y={p.y - 10} textAnchor="middle" fontSize="11" fill="#3b82f6" fontWeight="bold">
                                    ${p.value.toFixed(0)}
                                  </text>
                                ))}
                              </>
                            );
                          })()}
                        </svg>
                      </div>
                    )}

                    {dashboardExtras?.breakdown?.labels?.length > 0 && (
                      <div className="card">
                        <div className="card-title">Current Month Breakdown</div>
                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '280px', marginTop: '20px' }}>
                          <svg viewBox="0 0 200 200" style={{ width: '200px', height: '200px' }}>
                            {(() => {
                              const total = dashboardExtras.breakdown.data.reduce((a, b) => a + (Number(b) || 0), 0);
                              let currentAngle = -90;
                              const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#14b8a6'];
                              
                              return dashboardExtras.breakdown.labels.map((label, idx) => {
                                const value = Number(dashboardExtras.breakdown.data?.[idx] || 0);
                                if (total === 0) return null;
                                const sliceAngle = (value / total) * 360;
                                const startAngle = currentAngle;
                                const endAngle = currentAngle + sliceAngle;
                                currentAngle = endAngle;
                                
                                const startRad = (startAngle * Math.PI) / 180;
                                const endRad = (endAngle * Math.PI) / 180;
                                const x1 = 100 + 80 * Math.cos(startRad);
                                const y1 = 100 + 80 * Math.sin(startRad);
                                const x2 = 100 + 80 * Math.cos(endRad);
                                const y2 = 100 + 80 * Math.sin(endRad);
                                const largeArc = sliceAngle > 180 ? 1 : 0;
                                
                                const path = `M 100 100 L ${x1} ${y1} A 80 80 0 ${largeArc} 1 ${x2} ${y2} Z`;
                                
                                return (
                                  <path key={`${label}-${idx}`} d={path} fill={colors[idx % colors.length]} stroke="#fff" strokeWidth="2" />
                                );
                              });
                            })()}
                          </svg>
                        </div>
                        <div style={{ marginTop: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                          {dashboardExtras.breakdown.labels.map((label, idx) => {
                            const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#14b8a6'];
                            return (
                              <div key={`legend-${idx}`} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
                                <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: colors[idx % colors.length] }}></div>
                                <span>{label}: ${Number(dashboardExtras.breakdown.data?.[idx] || 0).toFixed(2)}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {Array.isArray(dashboardExtras?.trend) && dashboardExtras.trend.length > 0 && (
                      <div className="card">
                        <div className="card-title">3-Month Trend (Actual vs Budget)</div>
                        <div className="expense-table">
                          {dashboardExtras.trend.map((row, idx) => (
                            <div key={`${row.month || 'm'}-${idx}`} className="expense-row">
                              <div className="expense-col1">{row.month || `M${idx + 1}`}</div>
                              <div className="expense-col2">${Number(row.actual || 0).toFixed(2)}</div>
                              <div className="expense-col3">/${Number(row.budget || 0).toFixed(2)}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="card" style={{ textAlign: 'center' }}>
                    No dashboard data yet
                  </div>
                )}
              </div>
            )}

            {/* EXPENSES PAGE */}
            {activePage === 'expenses' && (
              <div>
                <div className="period-filter">
                  {periodOptions.map((opt) => (
                    <button
                      type="button"
                      key={opt}
                      className={`period-btn ${period === opt ? 'active' : ''}`}
                      onClick={() => setPeriod(opt)}
                    >
                      {opt.replace(/_/g, ' ').toUpperCase()}
                    </button>
                  ))}
                </div>

                {loadingExpenses ? (
                  <div className="loading">Loading expenses...</div>
                ) : expenses.length > 0 ? (
                  <div className="expense-table">
                    {expenseCategories.map((cat) => {
                      const catExpenses = expenses.filter(exp => normalizeExpenseTypeForDisplay(exp.Type) === cat);
                      if (catExpenses.length === 0) return null;
                      const catTotal = catExpenses.reduce((sum, exp) => sum + (exp.AmountSpent || 0), 0);
                      
                      return (
                        <div key={cat} style={{ marginBottom: '20px' }}>
                          <div style={{ 
                            display: 'flex', 
                            justifyContent: 'space-between', 
                            padding: '10px', 
                            background: '#f3f4f6', 
                            borderRadius: '8px',
                            fontWeight: 'bold',
                            marginBottom: '10px'
                          }}>
                            <span>{cat}</span>
                            <span>${catTotal.toFixed(2)}</span>
                          </div>
                          {catExpenses.map((exp, idx) => (
                            <div key={idx} className="expense-row" style={{ paddingLeft: '15px', borderBottom: '1px solid #eee' }}>
                              <div className="expense-col1">{exp.ItemName}</div>
                              <div className="expense-col2">${exp.AmountSpent?.toFixed(2) || '0.00'}</div>
                              <div className="expense-col3">{exp.DatePurchased}</div>
                            </div>
                          ))}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="card" style={{ textAlign: 'center' }}>
                    No expenses
                  </div>
                )}
              </div>
            )}

            {/* BUDGET PAGE */}
            {activePage === 'budget' && (
              <div>
                {loadingBudget ? (
                  <div className="loading">Loading budget...</div>
                ) : (
                  <form onSubmit={handleSaveBudget}>
                    <div className="form-group">
                      <label>Auto Budget</label>
                      <select
                        value={budgetForm.AutoBudget ? 'true' : 'false'}
                        onChange={(e) => setBudgetForm((prev) => ({ ...prev, AutoBudget: e.target.value === 'true' }))}
                      >
                        <option value="true">Enabled</option>
                        <option value="false">Disabled</option>
                      </select>
                    </div>

                    {!budgetForm.AutoBudget && (
                      <div className="form-group">
                        <label>Total Budget</label>
                        <input
                          type="number"
                          value={budgetForm.TotalBudget}
                          onChange={(e) => setBudgetForm((prev) => ({ ...prev, TotalBudget: e.target.value }))}
                          min="0"
                          required
                        />
                      </div>
                    )}

                    {!budgetForm.AutoBudget && expenseCategories.map((cat) => (
                      <div key={cat} className="form-group">
                        <label>{cat}</label>
                        <input
                          type="number"
                          min="0"
                          value={budgetForm[cat]}
                          onChange={(e) => setBudgetForm((prev) => ({ ...prev, [cat]: e.target.value }))}
                        />
                      </div>
                    ))}

                    <button type="submit" className="btn">
                      Save Budget
                    </button>
                  </form>
                )}

                {budgetData?.Suggestions?.length > 0 && (
                  <div style={{ marginTop: '20px' }}>
                    <div className="card-title" style={{ marginBottom: '10px' }}>Suggestions</div>
                    {budgetData.Suggestions.map((item, idx) => (
                      <div className="card" key={`${item.title}-${idx}`}>
                        <div className="alert-title">{item.title}</div>
                        <div className="alert-msg">{item.description}</div>
                        <div className="card-subtext">Potential savings: ${item.savings?.toFixed(2) || '0.00'}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* BASKET PAGE */}
            {activePage === 'basket' && (
              <div>
                <div className="card-title" style={{ marginBottom: '12px' }}>Monthly Basket</div>
                <form onSubmit={handleAddBasket}>
                  <div className="form-group">
                    <label>Category</label>
                    <select value={basketForm.Type} onChange={(e) => setBasketForm((prev) => ({ ...prev, Type: e.target.value }))}>
                      {expenseCategories.map((cat) => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Item Name</label>
                    <input type="text" value={basketForm.ItemName} onChange={(e) => setBasketForm((prev) => ({ ...prev, ItemName: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label>Amount</label>
                    <input type="number" step="0.01" min="0" value={basketForm.AmountSpent} onChange={(e) => setBasketForm((prev) => ({ ...prev, AmountSpent: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label>Note</label>
                    <input type="text" value={basketForm.Note} onChange={(e) => setBasketForm((prev) => ({ ...prev, Note: e.target.value }))} />
                  </div>
                  <button type="submit" className="btn">Add Basket Item</button>
                </form>

                <div className="import-toolbar">
                  <span className="pill">{selectedBasketIds.size} selected</span>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ width: 'auto', padding: '10px 12px', marginTop: 0, fontSize: '12px', background: '#ffe0e0', color: '#7f1d1d' }}
                    onClick={handleDeleteBasket}
                    disabled={selectedBasketIds.size === 0 || loadingDeleteBasket}
                  >
                    {loadingDeleteBasket ? 'Deleting...' : 'Delete selected'}
                  </button>
                </div>

                {loadingBasket ? (
                  <div className="loading">Loading basket...</div>
                ) : basketItems.length > 0 ? (
                  basketItems.map((item) => (
                    <div key={item.Id} className="card">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                        <input type="checkbox" className="checkbox" checked={selectedBasketIds.has(item.Id)} onChange={() => toggleBasketSelection(item.Id)} />
                        <span style={{ fontWeight: 700 }}>{item.ItemName}</span>
                      </div>
                      <div className="expense-row">
                        <div className="expense-col1">{item.Type}</div>
                        <div className="expense-col2">${Number(item.AmountSpent || 0).toFixed(2)}</div>
                      </div>
                      {item.Note && <div className="card-subtext">{item.Note}</div>}
                    </div>
                  ))
                ) : (
                  <div className="card" style={{ textAlign: 'center' }}>No basket items yet</div>
                )}
              </div>
            )}

            {/* ADD EXPENSE PAGE */}
            {activePage === 'add' && (
              <div>
                <form onSubmit={handleAddExpense}>
                  <div className="form-group">
                    <label>Category</label>
                    <select value={expForm.Type} onChange={(e) => setExpForm({ ...expForm, Type: e.target.value })} required>
                      {expenseCategories.map((cat) => (
                        <option key={cat} value={cat}>
                          {cat}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Item Name</label>
                    <input
                      type="text"
                      value={expForm.ItemName}
                      onChange={(e) => setExpForm({ ...expForm, ItemName: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Amount</label>
                    <input
                      type="number"
                      step="0.01"
                      value={expForm.AmountSpent}
                      onChange={(e) => setExpForm({ ...expForm, AmountSpent: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Date</label>
                    <input
                      type="date"
                      value={expForm.DatePurchased}
                      onChange={(e) => setExpForm({ ...expForm, DatePurchased: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Note</label>
                    <input type="text" value={expForm.Note} onChange={(e) => setExpForm({ ...expForm, Note: e.target.value })} />
                  </div>
                  <button type="submit" className="btn">
                    Add Expense
                  </button>
                </form>
              </div>
            )}

            {/* IMPORT PAGE */}
            {activePage === 'import' && (
              <div>
                <div style={{ marginBottom: '20px' }}>
                  <div className="period-filter">
                    <button
                      type="button"
                      className={`period-btn ${importYear === null ? 'active' : ''}`}
                      onClick={() => {
                        setImportYear(null);
                        setImportPage(1);
                      }}
                    >
                      All Years
                    </button>
                    {[2024, 2025, 2026].map((y) => (
                      <button
                        type="button"
                        key={y}
                        className={`period-btn ${importYear === y ? 'active' : ''}`}
                        onClick={() => {
                          setImportYear(y);
                          setImportPage(1);
                        }}
                      >
                        {y}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="card-title" style={{ marginBottom: '15px' }}>
                  📋 Add Previous Expenses
                </div>

                <form onSubmit={handleImportExpenses}>
                  {importForm.map((row, idx) => (
                    <div key={idx}>
                      <div className="form-group">
                        <label>Month (YYYY-MM)</label>
                        <input
                          type="text"
                          placeholder="2024-01"
                          value={row.Month}
                          onChange={(e) => {
                            const newForm = [...importForm];
                            newForm[idx].Month = e.target.value;
                            setImportForm(newForm);
                          }}
                        />
                      </div>
                      {importCategories.map((cat) => (
                        <div key={cat} className="form-group">
                          <label>{cat}</label>
                          <input
                            type="number"
                            step="0.01"
                            value={row[cat]}
                            onChange={(e) => {
                              const newForm = [...importForm];
                              newForm[idx][cat] = parseFloat(e.target.value) || 0;
                              setImportForm(newForm);
                            }}
                          />
                        </div>
                      ))}
                    </div>
                  ))}
                  <button type="submit" className="btn" disabled={loadingImport}>
                    {loadingImport ? 'Importing...' : 'Import'}
                  </button>
                </form>

                <div className="import-toolbar">
                  <span className="pill">{selectedImportedIds.size} selected</span>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ width: 'auto', padding: '10px 12px', marginTop: 0, fontSize: '12px' }}
                      onClick={selectAllImportedOnPage}
                      disabled={importedExpenses.length === 0}
                    >
                      Select all (page)
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ width: 'auto', padding: '10px 12px', marginTop: 0, fontSize: '12px' }}
                      onClick={clearImportedSelection}
                      disabled={selectedImportedIds.size === 0}
                    >
                      Clear
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{
                        width: 'auto',
                        padding: '10px 12px',
                        marginTop: 0,
                        fontSize: '12px',
                        background: '#ffe0e0',
                        color: '#7f1d1d'
                      }}
                      onClick={handleDeleteSelectedImported}
                      disabled={selectedImportedIds.size === 0 || loadingDeleteImported}
                    >
                      {loadingDeleteImported ? 'Deleting...' : 'Delete selected'}
                    </button>
                  </div>
                </div>

                {loadingImported ? (
                  <div className="loading">Loading imported expenses...</div>
                ) : importedExpenses.length > 0 ? (
                  <>
                    {importedExpenses.map((exp) => (
                      <div key={exp.Id} className="card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', alignItems: 'center' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <input
                              className="checkbox"
                              type="checkbox"
                              checked={selectedImportedIds.has(exp.Id)}
                              onChange={() => toggleSelectImported(exp.Id)}
                            />
                            <span style={{ fontWeight: 700 }}>{exp.Month}</span>
                          </div>
                        </div>

                        <div className="expense-table">
                          {importCategories.map(
                            (cat) =>
                              exp[cat] > 0 && (
                                <div key={cat} className="expense-row">
                                  <div className="expense-col1">{cat}</div>
                                  <div className="expense-col2">${exp[cat]?.toFixed(2) || '0.00'}</div>
                                </div>
                              )
                          )}
                        </div>
                      </div>
                    ))}

                    <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginTop: '20px' }}>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ fontSize: '12px', padding: '8px 12px', marginTop: 0 }}
                        onClick={() => setImportPage(Math.max(1, importPage - 1))}
                        disabled={importPage === 1}
                      >
                        Previous
                      </button>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ fontSize: '12px', padding: '8px 12px', marginTop: 0 }}
                        onClick={() => setImportPage(importPage + 1)}
                        disabled={loadingImported || importedExpenses.length < importPageSize}
                      >
                        Next
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="card" style={{ textAlign: 'center' }}>
                    No imported expenses yet
                  </div>
                )}
              </div>
            )}

            {/* SETTINGS PAGE */}
            {activePage === 'settings' && (
              <div>
                {loadingSettings ? (
                  <div className="loading">Loading settings...</div>
                ) : userSettings ? (
                  <form onSubmit={handleSaveSettings}>
                    <div className="form-group">
                      <label>Monthly Income</label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={settingsForm.MonthlyIncome}
                        onChange={(e) => setSettingsForm((prev) => ({ ...prev, MonthlyIncome: e.target.value }))}
                      />
                    </div>

                    <div className="form-group">
                      <label>Household Size</label>
                      <input
                        type="number"
                        min="1"
                        value={settingsForm.HouseholdSize}
                        onChange={(e) => setSettingsForm((prev) => ({ ...prev, HouseholdSize: e.target.value }))}
                      />
                    </div>

                    <div className="form-group">
                      <label>Transportation Type</label>
                      <select
                        value={settingsForm.TransportationTypes}
                        onChange={(e) => setSettingsForm((prev) => ({ ...prev, TransportationTypes: e.target.value }))}
                      >
                        <option value="default">Default</option>
                        <option value="bus">Bus</option>
                        <option value="train">Train</option>
                        <option value="bike">Bike</option>
                        <option value="walking">Walking</option>
                        <option value="electric">Electric</option>
                        <option value="hybrid">Hybrid</option>
                        <option value="gasoline">Gasoline</option>
                        <option value="taxi">Taxi</option>
                        <option value="privatehire">Private Hire</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>Budget Alert Threshold (%)</label>
                      <input
                        type="number"
                        min="1"
                        max="100"
                        value={settingsForm.AlertThreshold}
                        onChange={(e) => setSettingsForm((prev) => ({ ...prev, AlertThreshold: e.target.value }))}
                      />
                    </div>

                    <div className="form-group">
                      <label>Price Increase Alerts</label>
                      <select
                        value={settingsForm.PriceIncreaseAlerts ? 'true' : 'false'}
                        onChange={(e) => setSettingsForm((prev) => ({ ...prev, PriceIncreaseAlerts: e.target.value === 'true' }))}
                      >
                        <option value="true">Enabled</option>
                        <option value="false">Disabled</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>Budget Alerts</label>
                      <select
                        value={settingsForm.BudgetThresholdAlerts ? 'true' : 'false'}
                        onChange={(e) => setSettingsForm((prev) => ({ ...prev, BudgetThresholdAlerts: e.target.value === 'true' }))}
                      >
                        <option value="true">Enabled</option>
                        <option value="false">Disabled</option>
                      </select>
                    </div>

                    <button className="btn" type="submit" disabled={savingSettings}>
                      {savingSettings ? 'Saving...' : 'Save Settings'}
                    </button>

                    <button className="btn btn-secondary" type="button" style={{ marginTop: '12px' }} onClick={handleLogout}>
                      Logout
                    </button>

                    <div className="section-title">Account Security</div>
                    <div className="form-group">
                      <label>Current Password</label>
                      <input
                        type="password"
                        value={securityForm.currentPassword}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, currentPassword: e.target.value }))}
                      />
                    </div>
                    <button className="btn btn-secondary" type="button" onClick={handleVerifyPassword} disabled={savingSecurity}>
                      Verify Current Password
                    </button>

                    <div className="form-group" style={{ marginTop: '12px' }}>
                      <label>New Password</label>
                      <input
                        type="password"
                        value={securityForm.newPassword}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, newPassword: e.target.value }))}
                      />
                    </div>
                    <div className="form-group">
                      <label>Re-enter New Password</label>
                      <input
                        type="password"
                        value={securityForm.reNewPassword}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, reNewPassword: e.target.value }))}
                      />
                    </div>
                    <button className="btn btn-secondary" type="button" onClick={handleChangePassword} disabled={savingSecurity}>
                      Change Password
                    </button>

                    <div className="form-group" style={{ marginTop: '12px' }}>
                      <label>Recovery Email</label>
                      <input
                        type="email"
                        value={securityForm.forgotEmail}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, forgotEmail: e.target.value }))}
                        placeholder="you@example.com"
                      />
                    </div>
                    <button className="btn btn-secondary" type="button" onClick={handleForgotPassword} disabled={savingSecurity}>
                      Forgot Password
                    </button>

                    <div className="section-title">Danger Zone</div>
                    <div className="form-group">
                      <label>Confirm Password To Delete Account</label>
                      <input
                        type="password"
                        value={securityForm.deletePassword}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, deletePassword: e.target.value }))}
                      />
                    </div>
                    <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <input
                        type="checkbox"
                        className="checkbox"
                        checked={securityForm.deleteConfirm}
                        onChange={(e) => setSecurityForm((prev) => ({ ...prev, deleteConfirm: e.target.checked }))}
                      />
                      <label style={{ margin: 0 }}>I understand this permanently deletes my account and data.</label>
                    </div>
                    <button
                      className="btn btn-secondary"
                      type="button"
                      style={{ marginTop: '8px', background: '#ffe0e0', color: '#7f1d1d' }}
                      onClick={handleDeleteAccount}
                      disabled={savingSecurity}
                    >
                      Delete Account
                    </button>
                  </form>
                ) : (
                  <div className="error">Failed to load settings</div>
                )}
              </div>
            )}

            {/* ALERTS PAGE */}
            {activePage === 'alerts' && (
              <div>
                {loadingAlerts ? (
                  <div className="loading">Loading alerts...</div>
                ) : alerts.length > 0 ? (
                  alerts.map((alert) => (
                    <div key={alert.Id} className={`alert-box ${alert.Type || 'info'} ${alert.IsRead ? 'read' : 'unread'}`}>
                      <div className="alert-title">{alert.Title}</div>
                      <div className="alert-msg">{alert.Message}</div>
                      <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                        {!alert.IsRead && (
                          <button
                            type="button"
                            className="btn btn-secondary"
                            style={{ width: 'auto', marginTop: 0, padding: '8px 12px', fontSize: '12px' }}
                            onClick={() => handleMarkAlertRead(alert.Id)}
                          >
                            Mark Read
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn btn-secondary"
                          style={{ width: 'auto', marginTop: 0, padding: '8px 12px', fontSize: '12px', background: '#ffe0e0', color: '#7f1d1d' }}
                          onClick={() => handleDeleteAlert(alert.Id)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="card" style={{ textAlign: 'center' }}>
                    No alerts yet
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="bottom-nav">
            <div className={`nav-item ${activePage === 'dashboard' ? 'active' : ''}`} onClick={() => setActivePage('dashboard')} title="Dashboard">
              📊
            </div>
            <div className={`nav-item ${activePage === 'expenses' ? 'active' : ''}`} onClick={() => setActivePage('expenses')} title="Expenses">
              📁
            </div>
            <div className={`nav-item ${activePage === 'add' ? 'active' : ''}`} onClick={() => setActivePage('add')} title="Add Expense">
              ➕
            </div>
            <div className={`nav-item ${activePage === 'budget' ? 'active' : ''}`} onClick={() => setActivePage('budget')} title="Budget">
              💰
            </div>
            <div className={`nav-item ${activePage === 'basket' ? 'active' : ''}`} onClick={() => setActivePage('basket')} title="Basket">
              🧺
            </div>
            <div className={`nav-item ${activePage === 'import' ? 'active' : ''}`} onClick={() => setActivePage('import')} title="Import">
              📤
            </div>
            <div className={`nav-item ${activePage === 'alerts' ? 'active' : ''}`} onClick={() => setActivePage('alerts')} title="Alerts">
              🔔
            </div>
            <div className={`nav-item ${activePage === 'settings' ? 'active' : ''}`} onClick={() => setActivePage('settings')} title="Settings">
              ⚙️
            </div>
          </div>
        </>
      )}

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
