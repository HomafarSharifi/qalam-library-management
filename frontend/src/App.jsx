import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  NavLink, Navigate, Route, Routes, useLocation
} from "react-router-dom";
import {
  Activity, BookOpen, ChartNoAxesCombined, ChevronDown, CirclePlus,
  Clock3, LayoutDashboard, Menu, Search, Tags, Users, X,
  Pencil, Trash2, Eye, ArrowUpDown, CircleCheck, CircleAlert, Info,
  Moon, Sun, Check
} from "lucide-react";
import logoUrl from "./assets/mark.svg";
import profileUrl from "./assets/profile.png";
import {
  DashboardIcon, BookIcon, AuthorsIcon, CategoryIcon, UsersIcon, LoansIcon, ReportsIcon
} from "./components/NavIcons.jsx";
import {
  bookForCopy, categoryName, dateOnly, fullName, loadLibrary,
  nextId, saveLibrary, api, fetchFullLibraryFromBackend
} from "./data/libraryService.js";
import {
  formatAfghanDate,
  localDateOnly,
  isOverdue,
  toPersianDigits,
  todayJalali
} from "./utils/afghanDate.js";
import AfghanDatePicker from "./components/AfghanDatePicker.jsx";
import DynamicActivityChart from "./components/DynamicActivityChart.jsx";

/** Shared modal accessibility: Escape to close, body scroll lock, focus restore */
function useModalA11y(onClose) {
  const prevFocusRef = useRef(null);

  useEffect(() => {
    prevFocusRef.current = document.activeElement;
    document.body.classList.add("modal-open");

    function handleKeyDown(e) {
      if (e.key === "Escape") {
        e.stopPropagation();
        onClose();
        return;
      }
      if (e.key === "Tab") {
        const dialog = document.querySelector('[role="dialog"][aria-modal="true"]');
        if (!dialog) return;
        const items = [...dialog.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')].filter((item) => item.getClientRects().length);
        if (!items.length) { e.preventDefault(); return; }
        const first = items[0];
        const last = items[items.length - 1];
        if (e.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) {
          e.preventDefault(); last.focus();
        } else if (!e.shiftKey && (document.activeElement === last || !dialog.contains(document.activeElement))) {
          e.preventDefault(); first.focus();
        }
      }
    }
    requestAnimationFrame(() => {
      const dialog = document.querySelector('[role="dialog"][aria-modal="true"]');
      dialog?.querySelector('input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])')?.focus();
    });
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.classList.remove("modal-open");
      if (prevFocusRef.current && typeof prevFocusRef.current.focus === "function") {
        prevFocusRef.current.focus();
      }
    };
  }, [onClose]);
}

const NAV_GROUPS = [
  {
    title: "عمومی",
    items: [
      { to: "/", label: "داشبورد", icon: DashboardIcon, end: true }
    ]
  },
  {
    title: "مخزن و منابع",
    items: [
      { to: "/books", label: "کتاب‌ها", icon: BookIcon },
      { to: "/authors", label: "نویسندگان", icon: AuthorsIcon },
      { to: "/categories", label: "دسته‌بندی‌ها", icon: CategoryIcon }
    ]
  },
  {
    title: "امانت و گردش",
    items: [
      { to: "/members", label: "اعضا", icon: UsersIcon },
      { to: "/loans", label: "امانت‌ها", icon: LoansIcon },
      { to: "/reports", label: "گزارش‌ها", icon: ReportsIcon }
    ]
  }
];

const PAGE_TITLES = {
  "/": "داشبورد",
  "/books": "کتاب‌ها",
  "/authors": "نویسندگان",
  "/categories": "دسته‌بندی‌ها",
  "/members": "اعضا",
  "/loans": "امانت‌ها",
  "/reports": "گزارش‌ها"
};

function App() {
  const [db, setDb] = useState(loadLibrary);
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const [notice, setNotice] = useState(null);
  const [darkMode, setDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem("qalam-theme");
    return savedTheme ? savedTheme === "dark" : (window.matchMedia?.("(prefers-color-scheme: dark)").matches || false);
  });
  const location = useLocation();

  useEffect(() => {
    if (darkMode) {
      document.documentElement.setAttribute("data-theme", "dark");
      localStorage.setItem("qalam-theme", "dark");
    } else {
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("qalam-theme", "light");
    }
  }, [darkMode]);

  const refreshDb = async () => {
    try {
      const liveData = await fetchFullLibraryFromBackend();
      if (liveData) {
        setDb(liveData);
        setIsBackendConnected(true);
        return liveData;
      }
    } catch {
      setIsBackendConnected(false);
    }
    return null;
  };

  useEffect(() => {
    refreshDb();
  }, []);

  useEffect(() => {
    if (!isBackendConnected) {
      saveLibrary(db);
    }
  }, [db, isBackendConnected]);
  useEffect(() => {
    setMobileNav(false);
  }, [location.pathname]);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(null), 3200);
    return () => clearTimeout(timer);
  }, [notice]);

  const notify = (message, type = "success") => setNotice({ message, type });
  const pageTitle = PAGE_TITLES[location.pathname] || "کتابخانه";

  return (
    <div className="app-shell" dir="rtl">
      {mobileNav && <button className="nav-scrim" aria-label="بستن منو" onClick={() => setMobileNav(false)} />}
      <aside id="primary-navigation" className={`sidebar ${mobileNav ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-logo-container">
            <img src={logoUrl} alt="لوگوی کتابخانه قلم" className="brand-logo-img" />
          </div>
          <button className="icon-button close-nav" onClick={() => setMobileNav(false)} aria-label="بستن"><X size={19} /></button>
        </div>

        <nav className="nav-groups">
          {NAV_GROUPS.map((group) => (
            <div className="nav-group" key={group.title}>
              <div className="nav-caption">{group.title}</div>
              <div className="nav-list">
                {group.items.map(({ to, label, icon: Icon, end }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={end}
                    className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
                  >
                    <Icon size={18} />
                    <span>{label}</span>
                    {to === "/loans" && (
                      <span className="nav-count">
                        {toPersianDigits(db.Loans.filter((l) => !l.Return_date).length)}
                      </span>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="sidebar-foot">
          <div className="mini-avatar">
            <img src={profileUrl} alt="تصویر پروفایل مدیر" className="avatar-img" />
          </div>
          <div className="user-meta"><strong>مدیر کتابخانه</strong><span>همافر شریفی</span></div>
          <ChevronDown size={15} />
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setMobileNav(true)} aria-label="باز کردن منو" aria-expanded={mobileNav} aria-controls="primary-navigation"><Menu size={20} /></button>
          <div className="breadcrumb">
            <img src={logoUrl} alt="لوگو" className="breadcrumb-logo" />
            <span>/</span>
            <span>{pageTitle}</span>
          </div>
          <div className="topbar-side">
            <div
              className={`connection-badge ${isBackendConnected ? "online" : "offline"}`}
              title={isBackendConnected ? "متصل به وب‌سرویس بک‌اند (FastAPI & MySQL)" : "در حال کار در حالت محلی / آفلاین"}
            >
              <span className="status-dot" />
              <span>{isBackendConnected ? "متصل به سرور" : "حالت آفلاین"}</span>
            </div>
            <div className="today-afghan-badge" title="تقویم هجری خورشیدی (معیار رسمی افغانستان)">
              <Clock3 size={14} />
              <span>{formatAfghanDate(dateOnly(), { format: "withWeekday" })}</span>
            </div>
            <button
              type="button"
              className="icon-button theme-toggle-btn"
              onClick={() => setDarkMode((prev) => !prev)}
              title={darkMode ? "حالت روشن" : "حالت تاریک"}
              aria-label={darkMode ? "فعال کردن حالت روشن" : "فعال کردن حالت تاریک"}
            >
              {darkMode ? <Sun size={17} /> : <Moon size={17} />}
            </button>
            <div className="top-avatar" title="حساب مدیر">
              <img src={profileUrl} alt="تصویر پروفایل مدیر" className="avatar-img" />
            </div>
          </div>
        </header>

        <div className={`page-wrap${location.pathname === "/loans" ? " loans-page" : ""}`}>
          <Routes>
            <Route path="/" element={<Dashboard db={db} />} />
            <Route path="/books" element={<BooksPage db={db} setDb={setDb} notify={notify} isBackendConnected={isBackendConnected} refreshDb={refreshDb} />} />
            <Route path="/authors" element={<AuthorsPage db={db} setDb={setDb} notify={notify} isBackendConnected={isBackendConnected} refreshDb={refreshDb} />} />
            <Route path="/categories" element={<CategoriesPage db={db} setDb={setDb} notify={notify} isBackendConnected={isBackendConnected} refreshDb={refreshDb} />} />
            <Route path="/members" element={<MembersPage db={db} setDb={setDb} notify={notify} isBackendConnected={isBackendConnected} refreshDb={refreshDb} />} />
            <Route path="/loans" element={<LoansPage db={db} setDb={setDb} notify={notify} isBackendConnected={isBackendConnected} refreshDb={refreshDb} />} />
            <Route path="/reports" element={<ReportsPage db={db} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </main>

      {notice && (
        <div className={`toast ${notice.type}`} role="status" aria-live="polite">
          <span>{notice.type === "success" ? <CircleCheck size={18} /> : <CircleAlert size={18} />}</span>
          <span>{notice.message}</span>
          <button type="button" className="toast-dismiss" onClick={() => setNotice(null)} aria-label="بستن اعلان"><X size={14} /></button>
        </div>
      )}
    </div>
  );
}

function PageHeading({ title, subtitle, action }) {
  return (
    <div className="page-heading">
      <div><h1>{title}</h1><p>{subtitle}</p></div>
      {action}
    </div>
  );
}

function StatCard({ title, value, note, color, icon: Icon }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}><Icon size={18} /></div>
      <div className="stat-title">{title}</div>
      <div className={`stat-value ${color}`}>{toPersianDigits(value)}</div>
      <div className="stat-note">{note}</div>
    </div>
  );
}

function Dashboard({ db }) {
  const [bookTab, setBookTab] = useState("recent"); // "recent" | "top"
  const activeLoans = db.Loans.filter((loan) => !loan.Return_date);
  const totalCopies = db.Copies.reduce((sum, c) => sum + Number(c.Total_Copies || 0), 0);
  const available = db.Copies.reduce((sum, c) => sum + Number(c.Available_Copies || 0), 0);
  const recentLoans = [...db.Loans].sort((a, b) => b.ID_Loans - a.ID_Loans).slice(0, 5);
  const recentBooks = [...db.Books].sort((a, b) => b.ID_Books - a.ID_Books).slice(0, 5);

  const bookLoanCounts = useMemo(() => {
    const counts = {};
    (db.Loans || []).forEach((loan) => {
      const book = bookForCopy(db, loan.Copies_ID_Copies);
      if (book) {
        counts[book.ID_Books] = (counts[book.ID_Books] || 0) + 1;
      }
    });
    return counts;
  }, [db.Loans, db.Copies, db.Books]);

  const topBorrowedBooks = useMemo(() => {
    return [...db.Books]
      .map((b) => ({
        ...b,
        loanCount: bookLoanCounts[b.ID_Books] || 0
      }))
      .sort((a, b) => b.loanCount - a.loanCount || b.ID_Books - a.ID_Books)
      .slice(0, 5);
  }, [db.Books, bookLoanCounts]);

  return (
    <>
      <PageHeading title="داشبورد مدیریت" subtitle="نمای کلی از وضعیت و موجودی کتابخانه" />
      <div className="stats-grid">
        <StatCard title="مجموع کتاب‌ها" value={db.Books.length} note={`${toPersianDigits(db.Books.length)} عنوان ثبت‌شده`} color="blue" icon={BookOpen} />
        <StatCard title="نسخه‌های موجود" value={available} note={`از مجموع ${toPersianDigits(totalCopies)} نسخه`} color="green" icon={BookOpen} />
        <StatCard title="امانت‌های فعال" value={activeLoans.length} note={`${toPersianDigits(activeLoans.length)} امانت جاری`} color="yellow" icon={Clock3} />
        <StatCard title="اعضای کتابخانه" value={db.Members.length} note={`${toPersianDigits(db.Members.length)} عضو فعال`} color="purple" icon={Users} />
      </div>

      <div className="dashboard-grid">
        <section className="panel dashboard-books-panel">
          <div className="panel-heading">
            <div className="books-heading-wrap">
              <div className="heading-title-group">
                <h2>{bookTab === "recent" ? "کتاب‌های تازه" : "کتاب‌های پرامانت"}</h2>
                <p>{bookTab === "recent" ? "آخرین عنوان‌های اضافه‌شده" : "بیشترین عنوان‌های امانت گرفته‌شده"}</p>
              </div>
              <div className="books-switch" role="tablist">
                <button
                  type="button"
                  role="tab"
                  aria-selected={bookTab === "recent"}
                  className={`switch-tab ${bookTab === "recent" ? "active" : ""}`}
                  onClick={() => setBookTab("recent")}
                >
                  تازه‌ها
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={bookTab === "top"}
                  className={`switch-tab ${bookTab === "top" ? "active" : ""}`}
                  onClick={() => setBookTab("top")}
                >
                  پرامانت‌ترین‌ها
                </button>
              </div>
            </div>
            <NavLink className="text-link" to="/books">مشاهده همه</NavLink>
          </div>
          <div className="compact-list">
            {bookTab === "recent" ? (
              <>
                {recentBooks.map((book) => (
                  <div className="compact-row" key={book.ID_Books}>
                    <div className="book-cover"><BookOpen size={17} /></div>
                    <div className="compact-info">
                      <strong>{book.Title}</strong>
                      <span>{categoryName(db, book.Categories_ID_Category)}</span>
                    </div>
                    <span className="tiny-id" dir="ltr">#{toPersianDigits(book.ID_Books)}</span>
                  </div>
                ))}
                {!recentBooks.length && <EmptyState text="کتابی ثبت نشده است" />}
              </>
            ) : (
              <>
                {topBorrowedBooks.map((book, idx) => (
                  <div className="compact-row" key={book.ID_Books}>
                    <div className="book-cover top-rank"><BookOpen size={17} /></div>
                    <div className="compact-info">
                      <strong>{book.Title}</strong>
                      <span>{categoryName(db, book.Categories_ID_Category)}</span>
                    </div>
                    <span className="loan-count-badge">
                      {toPersianDigits(book.loanCount)} بار امانت
                    </span>
                  </div>
                ))}
                {!topBorrowedBooks.length && <EmptyState text="امانتی ثبت نشده است" />}
              </>
            )}
          </div>
        </section>

        <DynamicActivityChart db={db} />

        <section className="panel recent-loans">
          <div className="panel-heading">
            <div><h2>امانت‌های اخیر</h2><p>تراکنش‌های ثبت‌شده در تقویم خورشیدی</p></div>
            <NavLink className="text-link" to="/loans">همه امانت‌ها</NavLink>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>عضو</th>
                  <th>کتاب</th>
                  <th>تاریخ امانت (خورشیدی)</th>
                  <th>موعد بازگشت</th>
                  <th>وضعیت</th>
                </tr>
              </thead>
              <tbody>
                {recentLoans.map((loan) => {
                  const member = db.Members.find((m) => m.ID_Members === loan.Members_ID_Members);
                  const book = bookForCopy(db, loan.Copies_ID_Copies);
                  return (
                    <tr key={loan.ID_Loans}>
                      <td>{fullName(member)}</td>
                      <td>{book?.Title || "—"}</td>
                      <td className="date-cell">{formatAfghanDate(loan.Loan_date)}</td>
                      <td className="date-cell">{formatAfghanDate(loan.Due_date)}</td>
                      <td><StatusBadge loan={loan} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {!recentLoans.length && <EmptyState text="امانتی ثبت نشده است" />}
        </section>
      </div>
    </>
  );
}

function EmptyState({ text }) {
  return (
    <div className="empty-state">
      <div className="empty-icon"><BookOpen size={20} /></div>
      <span>{text}</span>
    </div>
  );
}

function StatusBadge({ loan }) {
  if (loan.Return_date) {
    return (
      <span className="status returned">
        <CircleCheck size={12} aria-hidden="true" />
        <span>بازگشت‌شده</span>
      </span>
    );
  }
  const overdue = isOverdue(loan.Due_date);
  return (
    <span className={`status ${overdue ? "overdue" : "active-status"}`}>
      {overdue ? (
        <CircleAlert size={12} aria-hidden="true" />
      ) : (
        <span className="status-live-dot" aria-hidden="true" />
      )}
      <span>{overdue ? "دیرشده" : "فعال"}</span>
    </span>
  );
}

const configs = {
  Books: {
    title: "کتاب‌ها", singular: "کتاب", id: "ID_Books",
    fields: [
      { key: "Title", label: "عنوان کتاب", required: true },
      { key: "ISBN", label: "ISBN", dir: "ltr" },
      { key: "Description", label: "توضیحات", type: "textarea" },
      { key: "Categories_ID_Category", label: "دسته‌بندی", type: "select", source: "Categories", sourceId: "ID_Category", sourceLabel: "Name" },
      { key: "Authors_ID_Authors", label: "نویسندگان", type: "multiselect", source: "Authors", sourceId: "ID_Authors", sourceLabel: "name" },
      { key: "Total_Copies", label: "مجموع نسخه‌ها", type: "number", min: 0 },
      { key: "Available_Copies", label: "نسخه‌های موجود", type: "number", min: 0 }
    ],
    columns: [
      ["Title", "عنوان"], ["ISBN", "ISBN"], ["Categories_ID_Category", "دسته‌بندی"], ["authors", "نویسندگان"], ["copies", "نسخه‌ها"]
    ]
  },
  Authors: {
    title: "نویسندگان", singular: "نویسنده", id: "ID_Authors",
    fields: [
      { key: "First_Name", label: "نام", required: true },
      { key: "Last_Name", label: "نام خانوادگی", required: true }
    ],
    columns: [["name", "نام نویسنده"], ["bookCount", "کتاب‌های ثبت‌شده"]]
  },
  Categories: {
    title: "دسته‌بندی‌ها", singular: "دسته‌بندی", id: "ID_Category",
    fields: [{ key: "Name", label: "نام دسته‌بندی", required: true }],
    columns: [["Name", "نام دسته‌بندی"], ["bookCount", "تعداد کتاب‌ها"]]
  },
  Members: {
    title: "اعضا", singular: "عضو", id: "ID_Members",
    fields: [
      { key: "First_Name", label: "نام", required: true },
      { key: "Last_Name", label: "نام خانوادگی", required: true },
      { key: "Email", label: "ایمیل", type: "email", dir: "ltr" },
      { key: "Contact", label: "شماره تماس", dir: "ltr" },
      { key: "Joined_Date", label: "تاریخ عضویت (خورشیدی)", type: "date" }
    ],
    columns: [["name", "نام عضو"], ["Email", "ایمیل"], ["Contact", "شماره تماس"], ["Joined_Date", "تاریخ عضویت"]]
  }
};

function getColumnValue(key, row, db) {
  if (key === "name") return fullName(row);
  if (key === "Joined_Date") return formatAfghanDate(row[key]);
  if (key === "authors") return (row.Authors_ID_Authors || []).map((id) => {
    const author = db.Authors.find((a) => a.ID_Authors === Number(id));
    return fullName(author);
  }).filter(Boolean).join("، ") || "—";
  if (key === "copies") {
    const c = db.Copies.find((item) => item.Books_ID_Books === row.ID_Books);
    return c ? `${toPersianDigits(c.Available_Copies)} از ${toPersianDigits(c.Total_Copies)}` : "—";
  }
  if (key === "bookCount") {
    const count = ("ID_Authors" in row)
      ? db.Books.filter((b) => b.Authors_ID_Authors?.includes(row.ID_Authors)).length
      : db.Books.filter((b) => b.Categories_ID_Category === row.ID_Category).length;
    return toPersianDigits(count);
  }
  if (key === "Categories_ID_Category") return categoryName(db, row[key]);
  return row[key] || "—";
}

function CrudPage({ kind, db, setDb, notify, isBackendConnected, refreshDb }) {
  const config = configs[kind];
  const [query, setQuery] = useState("");
  const [modal, setModal] = useState(null);
  const [detail, setDetail] = useState(null);
  const [sort, setSort] = useState({ key: config.columns[0][0], direction: 1 });

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = (db[kind] || []).filter((row) => {
      const searchable = `${Object.values(row).join(" ")} ${fullName(row)}`.toLowerCase();
      return searchable.includes(q);
    });
    return filtered.sort((a, b) => {
      const av = String(getColumnValue(sort.key, a, db));
      const bv = String(getColumnValue(sort.key, b, db));
      return av.localeCompare(bv, "fa") * sort.direction;
    });
  }, [db, kind, query, sort]);

  async function saveRecord(values) {
    const idField = config.id;
    const existing = modal?.row;
    const id = existing?.[idField] ?? nextId(db[kind] || [], idField);
    const record = { ...values, [idField]: id };

    if (isBackendConnected) {
      try {
        if (kind === "Books") {
          const total = Math.max(0, Number(values.Total_Copies) || 0);
          const payload = {
            Title: values.Title?.trim(),
            ISBN: values.ISBN?.trim() || null,
            Description: values.Description?.trim() || null,
            Categories_ID_Category: Number(values.Categories_ID_Category),
            Authors_ID_Authors: (values.Authors_ID_Authors || []).map(Number),
            Total_Copies: total
          };
          if (existing) {
            await api.updateBook(id, payload);
            if (values.Total_Copies !== undefined) {
              await api.updateBookCopies(id, { Total_Copies: total });
            }
          } else {
            await api.createBook(payload);
          }
        } else if (kind === "Authors") {
          const payload = {
            First_Name: values.First_Name?.trim(),
            Last_Name: values.Last_Name?.trim()
          };
          if (existing) {
            await api.updateAuthor(id, payload);
          } else {
            await api.createAuthor(payload);
          }
        } else if (kind === "Categories") {
          const payload = { Name: values.Name?.trim() };
          if (existing) {
            await api.updateCategory(id, payload);
          } else {
            await api.createCategory(payload);
          }
        } else if (kind === "Members") {
          const payload = {
            First_Name: values.First_Name?.trim(),
            Last_Name: values.Last_Name?.trim(),
            Contact: values.Contact?.trim(),
            Email: values.Email?.trim() || null,
            Joined_Date: values.Joined_Date || dateOnly()
          };
          if (existing) {
            await api.updateMember(id, payload);
          } else {
            await api.createMember(payload);
          }
        }
        await refreshDb();
        setModal(null);
        notify(existing ? "تغییرات با موفقیت در سرور ذخیره شد." : "مورد جدید با موفقیت در سرور ثبت شد.");
        return;
      } catch (err) {
        return notify(err.message || "خطا در برقراری ارتباط با سرور", "error");
      }
    }

    // Local Storage fallback
    if (kind === "Books") {
      const total = Math.max(0, Number(values.Total_Copies) || 0);
      const available = Math.max(0, Math.min(total, Number(values.Available_Copies) || 0));
      delete record.Total_Copies;
      delete record.Available_Copies;
      const copy = db.Copies.find((c) => c.Books_ID_Books === id);
      const copies = copy
        ? db.Copies.map((c) => c.Books_ID_Books === id ? { ...c, Total_Copies: total, Available_Copies: available } : c)
        : [...db.Copies, { ID_Copies: nextId(db.Copies, "ID_Copies"), Books_ID_Books: id, Total_Copies: total, Available_Copies: available }];
      setDb({ ...db, Books: existing ? db.Books.map((b) => b.ID_Books === id ? record : b) : [...db.Books, record], Copies: copies });
    } else {
      const duplicate = kind === "Categories" && db.Categories.some((c) => c.Name.trim().toLowerCase() === String(values.Name).trim().toLowerCase() && c.ID_Category !== id);
      if (duplicate) return notify("این دسته‌بندی قبلاً ثبت شده است.", "error");
      setDb({ ...db, [kind]: existing ? db[kind].map((r) => r[idField] === id ? record : r) : [...db[kind], record] });
    }
    setModal(null);
    notify(existing ? "تغییرات ذخیره شد." : "مورد جدید با موفقیت ثبت شد.");
  }

  async function remove(row) {
    if (!window.confirm(`آیا از حذف این ${config.singular} مطمئن هستید؟`)) return;

    if (isBackendConnected) {
      try {
        if (kind === "Books") {
          await api.deleteBook(row.ID_Books);
        } else if (kind === "Authors") {
          await api.deleteAuthor(row.ID_Authors);
        } else if (kind === "Categories") {
          await api.deleteCategory(row.ID_Category);
        } else if (kind === "Members") {
          await api.deleteMember(row.ID_Members);
        }
        await refreshDb();
        notify("مورد با موفقیت از سرور حذف شد.");
        return;
      } catch (err) {
        return notify(err.message || "خطا در حذف مورد از سرور", "error");
      }
    }

    // Local Storage fallback
    if (kind === "Books") {
      const copy = db.Copies.find((c) => c.Books_ID_Books === row.ID_Books);
      if (copy && db.Loans.some((l) => l.Copies_ID_Copies === copy.ID_Copies && !l.Return_date)) {
        return notify("این کتاب دارای امانت فعال است و حذف نمی‌شود.", "error");
      }
      setDb({ ...db, Books: db.Books.filter((b) => b.ID_Books !== row.ID_Books), Copies: db.Copies.filter((c) => c.Books_ID_Books !== row.ID_Books) });
    } else if (kind === "Authors") {
      setDb({ ...db, Authors: db.Authors.filter((a) => a.ID_Authors !== row.ID_Authors), Books: db.Books.map((b) => ({ ...b, Authors_ID_Authors: (b.Authors_ID_Authors || []).filter((id) => id !== row.ID_Authors) })) });
    } else if (kind === "Categories") {
      if (db.Books.some((b) => b.Categories_ID_Category === row.ID_Category)) return notify("ابتدا دسته‌بندی کتاب‌های مرتبط را تغییر دهید.", "error");
      setDb({ ...db, Categories: db.Categories.filter((c) => c.ID_Category !== row.ID_Category) });
    } else {
      if (db.Loans.some((l) => l.Members_ID_Members === row.ID_Members && !l.Return_date)) return notify("این عضو دارای امانت فعال است و حذف نمی‌شود.", "error");
      setDb({ ...db, Members: db.Members.filter((m) => m.ID_Members !== row.ID_Members) });
    }
    notify("مورد با موفقیت حذف شد.");
  }

  const formRow = modal?.row ? { ...modal.row } : kind === "Books" ? {
    Categories_ID_Category: "", Authors_ID_Authors: [],
    Total_Copies: 0, Available_Copies: 0
  } : kind === "Members" ? { Joined_Date: dateOnly() } : {};

  return (
    <>
      <PageHeading title={config.title} subtitle={`مدیریت و فهرست ${config.title}`} action={
        <button className="primary-button" onClick={() => setModal({ row: null })}><CirclePlus size={17} /> افزودن {config.singular}</button>
      } />
      <section className="panel data-panel">
        <div className="toolbar">
          <label className="search-box"><Search size={17} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={`جست‌وجو در ${config.title}...`} /></label>
          <span className="result-count">{toPersianDigits(rows.length)} مورد</span>
        </div>
        <div className="table-scroll"><table className="data-table">
          <thead><tr>{config.columns.map(([key, label]) => <th key={key}><button className="sort-button" aria-label={`مرتب‌سازی بر اساس ${label}`} onClick={() => setSort({ key, direction: sort.key === key ? -sort.direction : 1 })}>{label}<ArrowUpDown size={13} /></button></th>)}<th>عملیات</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row[config.id]}>
                {config.columns.map(([key]) => (
                  <td key={key} className={key === "Joined_Date" ? "date-cell" : ""} dir={key === "ISBN" || key === "Email" || key === "Contact" ? "ltr" : undefined}>
                    {getColumnValue(key, row, db)}
                  </td>
                ))}
                <td><div className="row-actions">
                  <button className="action-icon" title="جزئیات" aria-label="جزئیات" onClick={() => setDetail(row)}><Eye size={16} /></button>
                  <button className="action-icon" title="ویرایش" aria-label="ویرایش" onClick={() => setModal({ row })}><Pencil size={16} /></button>
                  <button className="action-icon danger" title="حذف" aria-label="حذف" onClick={() => remove(row)}><Trash2 size={16} /></button>
                </div></td>
              </tr>
            ))}
          </tbody>
        </table></div>
        {!rows.length && <EmptyState text={query ? "نتیجه‌ای پیدا نشد" : "هنوز موردی ثبت نشده است"} />}
      </section>
      {modal && <RecordModal title={`${modal.row ? "ویرایش" : "افزودن"} ${config.singular}`} fields={config.fields} initial={formRow} db={db} onClose={() => setModal(null)} onSave={saveRecord} />}
      {detail && <DetailModal kind={kind} row={detail} db={db} onClose={() => setDetail(null)} />}
    </>
  );
}

function RecordModal({ title, fields, initial, db, onClose, onSave }) {
  const [values, setValues] = useState(initial);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const stableClose = useCallback(() => onClose(), [onClose]);
  useModalA11y(stableClose);

  async function submit(e) {
    e.preventDefault();
    for (const field of fields) {
      if (field.required && !values[field.key]) return setError(`فیلد «${field.label}» الزامی است.`);
      if (field.key === "Available_Copies" && Number(values[field.key]) > Number(values.Total_Copies)) return setError("نسخه‌های موجود نمی‌تواند بیشتر از مجموع نسخه‌ها باشد.");
    }
    setError("");
    setSaving(true);
    try {
      await onSave(values);
    } finally {
      setSaving(false);
    }
  }

  function change(key, value) { setValues((v) => ({ ...v, [key]: value })); }

  return (
    <div className="modal-backdrop" role="presentation">
      <form className="modal" onSubmit={submit} role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-header">
          <div><h2>{title}</h2><p>اطلاعات را وارد نموده و ذخیره فرمایید.</p></div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="بستن"><X size={19} /></button>
        </div>
        <div className="form-grid">
          {fields.map((field) => {
            if (field.type === "date") {
              return (
                <div key={field.key} className="form-field">
                  <AfghanDatePicker
                    value={values[field.key]}
                    onChange={(isoDate) => change(field.key, isoDate)}
                    label={field.label}
                    required={field.required}
                  />
                </div>
              );
            }

            if (field.type === "multiselect") {
              const selectedIds = (values[field.key] || []).map(Number);
              return (
                <div key={field.key} className="form-field wide" role="group" aria-labelledby={`label-${field.key}`}>
                  <span id={`label-${field.key}`}>
                    {field.label}{field.required && <i className="req-star"> *</i>}
                  </span>
                  <div className="multiselect-chips">
                    {(db[field.source] || []).map((item) => {
                      const id = Number(item[field.sourceId]);
                      const isSelected = selectedIds.includes(id);
                      return (
                        <button
                          key={id}
                          type="button"
                          className={`multiselect-chip ${isSelected ? "selected" : ""}`}
                          onClick={() => {
                            const next = isSelected
                              ? selectedIds.filter((x) => x !== id)
                              : [...selectedIds, id];
                            change(field.key, next);
                          }}
                          aria-pressed={isSelected}
                        >
                          <span>{fullName(item)}</span>
                          {isSelected && <Check size={13} aria-hidden="true" />}
                        </button>
                      );
                    })}
                  </div>
                  <small className="multiselect-hint">برای انتخاب یا لغو انتخاب هر گزینه کلیک کنید.</small>
                </div>
              );
            }

            return (
              <label key={field.key} className={`form-field ${field.type === "textarea" ? "wide" : ""}`}>
                <span>{field.label}{field.required && <i className="req-star"> *</i>}</span>
                {field.type === "select" ? (
                  <select value={values[field.key] ?? ""} onChange={(e) => change(field.key, e.target.value ? Number(e.target.value) : "")}>
                    <option value="">انتخاب کنید</option>
                    {(db[field.source] || []).map((item) => (
                      <option key={item[field.sourceId]} value={item[field.sourceId]}>
                        {item[field.sourceLabel] === "name" ? fullName(item) : item[field.sourceLabel]}
                      </option>
                    ))}
                  </select>
                ) : field.type === "textarea" ? (
                  <textarea rows="3" value={values[field.key] || ""} onChange={(e) => change(field.key, e.target.value)} />
                ) : (
                  <input type={field.type || "text"} min={field.min} dir={field.dir} value={values[field.key] ?? ""} onChange={(e) => change(field.key, field.type === "number" ? e.target.value : e.target.value)} />
                )}
              </label>
            );
          })}
        </div>
        {error && <div className="form-error"><CircleAlert size={16} />{error}</div>}
        <div className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose} disabled={saving}>انصراف</button>
          <button className="primary-button" type="submit" disabled={saving}>
            {saving ? "در حال ذخیره..." : "ذخیره اطلاعات"}
          </button>
        </div>
      </form>
    </div>
  );
}

function DetailModal({ kind, row, db, onClose }) {
  const config = configs[kind];
  const stableClose = useCallback(() => onClose(), [onClose]);
  useModalA11y(stableClose);
  let extra = null;
  if (kind === "Authors") {
    const books = db.Books.filter((b) => b.Authors_ID_Authors?.includes(row.ID_Authors));
    extra = <div className="detail-related"><strong>کتاب‌های مرتبط</strong>{books.length ? books.map((b) => <span key={b.ID_Books}>{b.Title}</span>) : <span>کتابی ثبت نشده است</span>}</div>;
  } else if (kind === "Members") {
    const loans = db.Loans.filter((l) => l.Members_ID_Members === row.ID_Members);
    extra = <div className="detail-related"><strong>امانت‌های عضو</strong><span>{toPersianDigits(loans.length)} امانت ثبت‌شده</span></div>;
  } else if (kind === "Books") {
    const copy = db.Copies.find((c) => c.Books_ID_Books === row.ID_Books);
    extra = <div className="detail-related"><strong>موجودی</strong><span>{copy ? `${toPersianDigits(copy.Available_Copies)} نسخه از ${toPersianDigits(copy.Total_Copies)} نسخه موجود` : "موجودی ثبت نشده است"}</span></div>;
  }
  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal detail-modal" role="dialog" aria-modal="true" aria-label={`جزئیات ${config.singular}`}>
        <div className="modal-header">
          <div><h2>جزئیات {config.singular}</h2><p>شناسه سیستمی: <bdi>{toPersianDigits(row[config.id])}</bdi></p></div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="بستن"><X size={19} /></button>
        </div>
        <div className="detail-list">
          {config.fields.map((field) => (
            <div key={field.key}>
              <span>{field.label}</span>
              <strong>
                {field.key === "Joined_Date"
                  ? formatAfghanDate(row[field.key], { format: "withWeekday" })
                  : field.key === "Categories_ID_Category"
                  ? categoryName(db, row[field.key])
                  : field.key === "Authors_ID_Authors"
                  ? (row[field.key] || []).map((id) => fullName(db.Authors.find((a) => a.ID_Authors === id))).join("، ")
                  : row[field.key] || "—"}
              </strong>
            </div>
          ))}
        </div>
        {extra}
        <div className="modal-actions"><button type="button" className="primary-button" onClick={onClose}>بستن پنجره</button></div>
      </div>
    </div>
  );
}

function BooksPage(props) { return <CrudPage kind="Books" {...props} />; }
function AuthorsPage(props) { return <CrudPage kind="Authors" {...props} />; }
function CategoriesPage(props) { return <CrudPage kind="Categories" {...props} />; }
function MembersPage(props) { return <CrudPage kind="Members" {...props} />; }

function LoansPage({ db, setDb, notify, isBackendConnected, refreshDb }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [issueOpen, setIssueOpen] = useState(false);
  const [fineLoan, setFineLoan] = useState(null);

  const loans = [...(db.Loans || [])].sort((a, b) => b.ID_Loans - a.ID_Loans).filter((loan) => {
    const book = bookForCopy(db, loan.Copies_ID_Copies);
    const member = (db.Members || []).find((m) => m.ID_Members === loan.Members_ID_Members);
    const matchesQuery = `${book?.Title || ""} ${fullName(member)}`.toLowerCase().includes(query.toLowerCase());
    const overdue = isOverdue(loan.Due_date);
    const status = loan.Return_date ? "returned" : overdue ? "overdue" : "active";
    return matchesQuery && (filter === "all" || filter === status);
  });

  async function issue(values) {
    if (isBackendConnected) {
      try {
        await api.issueLoan({
          Members_ID_Members: Number(values.memberId),
          Books_ID_Books: Number(values.bookId),
          Loan_date: values.loanDate || dateOnly(),
          Due_date: values.dueDate
        });
        await refreshDb();
        setIssueOpen(false);
        notify("امانت جدید با موفقیت در سرور ثبت شد.");
        return;
      } catch (err) {
        return notify(err.message || "خطا در ثبت امانت در سرور", "error");
      }
    }

    // Local Storage fallback
    const copy = db.Copies.find((c) => c.Books_ID_Books === Number(values.bookId));
    if (!copy) return notify("برای این کتاب موجودی تعریف نشده است.", "error");
    if (copy.Available_Copies < 1) return notify("نسخهٔ قابل امانت موجود نیست.", "error");
    const loan = {
      ID_Loans: nextId(db.Loans, "ID_Loans"),
      Members_ID_Members: Number(values.memberId),
      Copies_ID_Copies: copy.ID_Copies,
      Loan_date: values.loanDate,
      Due_date: values.dueDate,
      Return_date: null,
      Fine_Amount: 0
    };
    setDb({
      ...db,
      Loans: [...db.Loans, loan],
      Copies: db.Copies.map((c) => c.ID_Copies === copy.ID_Copies ? { ...c, Available_Copies: c.Available_Copies - 1 } : c)
    });
    setIssueOpen(false);
    notify("امانت جدید با موفقیت ثبت شد.");
  }

  async function returnLoan(loan, fine) {
    if (!window.confirm("آیا بازگشت این کتاب به مخزن تأیید می‌شود؟")) return;

    if (isBackendConnected) {
      try {
        await api.returnLoan(loan.ID_Loans, {
          Return_date: dateOnly(),
          Fine_Amount: fine !== undefined && fine !== null && fine !== "" ? Number(fine) : undefined
        });
        await refreshDb();
        setFineLoan(null);
        notify("بازگشت کتاب در سرور ثبت و موجودی مخزن به‌روزرسانی شد.");
        return;
      } catch (err) {
        return notify(err.message || "خطا در ثبت بازگشت کتاب در سرور", "error");
      }
    }

    // Local Storage fallback
    const copy = db.Copies.find((c) => c.ID_Copies === loan.Copies_ID_Copies);
    setDb({
      ...db,
      Loans: db.Loans.map((l) => l.ID_Loans === loan.ID_Loans ? { ...l, Return_date: dateOnly(), Fine_Amount: Number(fine) || 0 } : l),
      Copies: copy ? db.Copies.map((c) => c.ID_Copies === copy.ID_Copies ? { ...c, Available_Copies: Math.min(c.Total_Copies, c.Available_Copies + 1) } : c) : db.Copies
    });
    setFineLoan(null);
    notify("بازگشت کتاب ثبت و موجودی مخزن به‌روزرسانی شد.");
  }

  const activeCount = db.Loans.filter((l) => !l.Return_date && !isOverdue(l.Due_date)).length;
  const overdueCount = db.Loans.filter((l) => !l.Return_date && isOverdue(l.Due_date)).length;
  const returnedCount = db.Loans.filter((l) => l.Return_date).length;

  return (
    <>
      <PageHeading title="امانت‌ها" subtitle="مدیریت، ثبت و پیگیری امانت کتاب‌ها" action={
        <button className="primary-button" onClick={() => setIssueOpen(true)}><CirclePlus size={17} /> ثبت امانت جدید</button>
      } />
      <div className="stats-grid loan-stats">
        <StatCard title="همه امانت‌ها" value={db.Loans.length} note={`${toPersianDigits(db.Loans.length)} مورد ثبت‌شده`} color="blue" icon={Activity} />
        <StatCard title="امانت‌های جاری" value={activeCount} note="در دست اعضا" color="green" icon={Clock3} />
        <StatCard title="دیرشده‌ها" value={overdueCount} note="گذشته از موعد بازگشت" color="yellow" icon={CircleAlert} />
        <StatCard title="بازگشت‌شده" value={returnedCount} note="تکمیل‌شده" color="purple" icon={CircleCheck} />
      </div>

      <section className="panel data-panel">
        <div className="toolbar loan-toolbar">
          <label className="search-box"><Search size={17} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="جست‌وجوی نام عضو یا کتاب..." /></label>
          <select className="filter-select" value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">همه وضعیت‌ها</option>
            <option value="active">امانت‌های جاری</option>
            <option value="overdue">دیرشده‌ها</option>
            <option value="returned">بازگشت‌شده‌ها</option>
          </select>
        </div>
        <div className="table-scroll"><table>
          <thead>
            <tr>
              <th>عضو</th>
              <th>کتاب</th>
              <th>تاریخ امانت</th>
              <th>موعد بازگشت</th>
              <th>تاریخ بازگشت</th>
              <th>جریمه (افغانی)</th>
              <th>وضعیت / عملیات</th>
            </tr>
          </thead>
          <tbody>
            {loans.map((loan) => {
              const book = bookForCopy(db, loan.Copies_ID_Copies);
              const member = db.Members.find((m) => m.ID_Members === loan.Members_ID_Members);
              return (
                <tr key={loan.ID_Loans}>
                  <td>{fullName(member) || "—"}</td>
                  <td>{book?.Title || "—"}</td>
                  <td className="date-cell">{formatAfghanDate(loan.Loan_date)}</td>
                  <td className="date-cell">{formatAfghanDate(loan.Due_date)}</td>
                  <td className="date-cell">{loan.Return_date ? formatAfghanDate(loan.Return_date) : "—"}</td>
                  <td>{toPersianDigits(Number(loan.Fine_Amount || 0))}</td>
                  <td>
                    <div className="loan-action">
                      <StatusBadge loan={loan} />
                      {!loan.Return_date && (
                        <button className="small-button" onClick={() => setFineLoan(loan)}>ثبت بازگشت</button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table></div>
        {!loans.length && <EmptyState text="امانتی با این شرایط پیدا نشد" />}
      </section>

      {issueOpen && <IssueModal db={db} onClose={() => setIssueOpen(false)} onSave={issue} />}
      {fineLoan && <ReturnModal loan={fineLoan} db={db} onClose={() => setFineLoan(null)} onSave={(amount) => returnLoan(fineLoan, amount)} />}
    </>
  );
}

function IssueModal({ db, onClose, onSave }) {
  const stableClose = useCallback(() => onClose(), [onClose]);
  useModalA11y(stableClose);

  // Default loan date is today, default due date is +14 days
  const todayIso = dateOnly();
  const defaultDue = new Date();
  defaultDue.setDate(defaultDue.getDate() + 14);
  const defaultDueIso = localDateOnly(defaultDue);

  const [form, setForm] = useState({
    memberId: "",
    bookId: "",
    loanDate: todayIso,
    dueDate: defaultDueIso
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const availableBooks = db.Books.filter((b) => {
    const copy = db.Copies.find((c) => c.Books_ID_Books === b.ID_Books);
    return copy && copy.Available_Copies > 0;
  });

  async function submit(e) {
    e.preventDefault();
    if (!form.memberId || !form.bookId || !form.loanDate || !form.dueDate) return setError("تکمیل تمام فیلدها الزامی است.");
    if (form.dueDate < form.loanDate) return setError("موعد بازگشت نباید قبل از تاریخ امانت باشد.");
    setError("");
    setSaving(true);
    try {
      await onSave(form);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <form className="modal" onSubmit={submit} role="dialog" aria-modal="true" aria-label="ثبت امانت جدید">
        <div className="modal-header">
          <div><h2>ثبت امانت جدید</h2><p>انتخاب عضو و کتاب بر اساس تقویم خورشیدی</p></div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="بستن"><X size={19} /></button>
        </div>
        <div className="form-grid">
          <label className="form-field">
            <span>عضو امانت‌گیرنده <i className="req-star">*</i></span>
            <select value={form.memberId} onChange={(e) => setForm({ ...form, memberId: e.target.value })}>
              <option value="">انتخاب عضو...</option>
              {db.Members.map((m) => <option key={m.ID_Members} value={m.ID_Members}>{fullName(m)}</option>)}
            </select>
          </label>

          <label className="form-field">
            <span>کتاب مورد نظر <i className="req-star">*</i></span>
            <select value={form.bookId} onChange={(e) => setForm({ ...form, bookId: e.target.value })}>
              <option value="">انتخاب کتاب...</option>
              {availableBooks.map((b) => <option key={b.ID_Books} value={b.ID_Books}>{b.Title}</option>)}
            </select>
          </label>

          <div className="form-field">
            <AfghanDatePicker
              label="تاریخ امانت"
              required
              value={form.loanDate}
              onChange={(val) => setForm({ ...form, loanDate: val })}
            />
          </div>

          <div className="form-field">
            <AfghanDatePicker
              label="موعد بازگشت"
              required
              value={form.dueDate}
              onChange={(val) => setForm({ ...form, dueDate: val })}
            />
          </div>
        </div>

        <div className="info-note">
          <Info size={16} />
          <span>موعد بازگشت پیش‌فرض به میزان ۱۴ روز پس از امانت تنظیم شده است.</span>
        </div>

        {error && <div className="form-error"><CircleAlert size={16} />{error}</div>}
        <div className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose} disabled={saving}>انصراف</button>
          <button className="primary-button" type="submit" disabled={saving}>
            {saving ? "در حال ثبت..." : "تأیید و ثبت امانت"}
          </button>
        </div>
      </form>
    </div>
  );
}

function ReturnModal({ loan, db, onClose, onSave }) {
  const stableClose = useCallback(() => onClose(), [onClose]);
  useModalA11y(stableClose);
  const overdue = isOverdue(loan.Due_date);
  // Calculate overdue days
  let daysLate = 0;
  if (overdue && loan.Due_date) {
    const dueTime = new Date(`${loan.Due_date}T00:00:00Z`).getTime();
    const nowTime = new Date(`${dateOnly()}T00:00:00Z`).getTime();
    daysLate = Math.max(0, Math.round((nowTime - dueTime) / 86400000));
  }
  const suggestedFine = daysLate * 5; // 5 Afghanis per day late
  const [fine, setFine] = useState(loan.Fine_Amount || suggestedFine);
  const [saving, setSaving] = useState(false);

  const book = bookForCopy(db, loan.Copies_ID_Copies);
  const member = db.Members.find((m) => m.ID_Members === loan.Members_ID_Members);

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(fine);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <form className="modal" onSubmit={submit} role="dialog" aria-modal="true" aria-label="ثبت بازگشت کتاب">
        <div className="modal-header">
          <div><h2>ثبت بازگشت کتاب</h2><p>کتاب: «{book?.Title}» — عضو: {fullName(member)}</p></div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="بستن"><X size={19} /></button>
        </div>

        <div className="detail-list" style={{ marginBottom: "14px" }}>
          <div><span>تاریخ امانت</span><strong>{formatAfghanDate(loan.Loan_date)}</strong></div>
          <div><span>موعد مقرر</span><strong>{formatAfghanDate(loan.Due_date)}</strong></div>
          <div><span>تاریخ امروز</span><strong>{formatAfghanDate(dateOnly())}</strong></div>
          <div><span>وضعیت بازگشت</span><strong style={{ color: overdue ? "#cf4e4e" : "#389e5a" }}>{overdue ? `${toPersianDigits(daysLate)} روز تاخیر` : "به‌موقع"}</strong></div>
        </div>

        <label className="form-field">
          <span>مبلغ جریمه تاخیر (افغانی)</span>
          <input type="number" min="0" value={fine} onChange={(e) => setFine(e.target.value)} />
        </label>

        {overdue && (
          <div className="info-note">
            <Info size={16} />
            <span>محاسبه پیشنهادی: {toPersianDigits(daysLate)} روز تاخیر × ۵ افغانی = {toPersianDigits(suggestedFine)} افغانی</span>
          </div>
        )}

        <div className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose} disabled={saving}>انصراف</button>
          <button className="primary-button" type="submit" disabled={saving}>
            {saving ? "در حال ثبت..." : "تأیید بازگشت و ثبت در سیستم"}
          </button>
        </div>
      </form>
    </div>
  );
}

function ReportsPage({ db }) {
  const [report, setReport] = useState("history");
  const reports = {
    history: { title: "تاریخچهٔ کامل امانت‌ها", rows: db.Loans },
    overdue: { title: "امانت‌های دیرشده و نیازمند پیگیری", rows: db.Loans.filter((l) => !l.Return_date && isOverdue(l.Due_date)) },
    availability: { title: "موجودی و تیراژ نسخه‌های کتاب", rows: db.Copies },
    categories: { title: "توزیع عناوین بر اساس دسته‌بندی‌ها", rows: db.Categories },
    fines: { title: "جریمه‌های وصول‌شده و ثبت‌شده", rows: db.Loans.filter((l) => Number(l.Fine_Amount) > 0) }
  };
  const selected = reports[report];

  return (
    <>
      <PageHeading title="گزارش‌های کتابخانه" subtitle="تحلیل و بررسی داده‌های عملیاتی در تقویم رسمی افغانستان" />
      <div className="report-tabs" role="tablist" aria-label="گزارش‌های کتابخانه">
        {[
          ["history", "تاریخچه امانت‌ها"],
          ["overdue", "دیرشده‌ها"],
          ["availability", "موجودی نسخه‌ها"],
          ["categories", "دسته‌بندی‌ها"],
          ["fines", "جریمه‌ها"]
        ].map(([key, label]) => (
          <button key={key} role="tab" aria-selected={report === key} className={report === key ? "selected" : ""} onClick={() => setReport(key)}>
            {label}
          </button>
        ))}
      </div>

      <section className="panel data-panel">
        <div className="panel-heading report-heading">
          <div><h2>{selected.title}</h2><p>{toPersianDigits(selected.rows.length)} رکورد یافت شد</p></div>
        </div>
        <ReportTable kind={report} rows={selected.rows} db={db} />
        {!selected.rows.length && <EmptyState text="داده‌ای برای این گزارش وجود ندارد" />}
      </section>
    </>
  );
}

function ReportTable({ kind, rows, db }) {
  if (kind === "availability") {
    return (
      <div className="table-scroll"><table>
        <thead><tr><th>عنوان کتاب</th><th>مجموع نسخه‌ها</th><th>نسخه‌های موجود در مخزن</th></tr></thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.ID_Copies}>
              <td>{db.Books.find((b) => b.ID_Books === c.Books_ID_Books)?.Title || "—"}</td>
              <td>{toPersianDigits(c.Total_Copies)}</td>
              <td>{toPersianDigits(c.Available_Copies)}</td>
            </tr>
          ))}
        </tbody>
      </table></div>
    );
  }

  if (kind === "categories") {
    return (
      <div className="table-scroll"><table>
        <thead><tr><th>نام دسته‌بندی</th><th>تعداد کتاب‌های ثبت‌شده</th></tr></thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.ID_Category}>
              <td>{c.Name}</td>
              <td>{toPersianDigits(db.Books.filter((b) => b.Categories_ID_Category === c.ID_Category).length)}</td>
            </tr>
          ))}
        </tbody>
      </table></div>
    );
  }

  return (
    <div className="table-scroll"><table>
      <thead>
        <tr>
          <th>عضو</th>
          <th>کتاب</th>
          <th>تاریخ امانت</th>
          <th>موعد بازگشت</th>
          <th>تاریخ بازگشت</th>
          <th>جریمه (افغانی)</th>
          <th>وضعیت</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((l) => (
          <tr key={l.ID_Loans}>
            <td>{fullName(db.Members.find((m) => m.ID_Members === l.Members_ID_Members)) || "—"}</td>
            <td>{bookForCopy(db, l.Copies_ID_Copies)?.Title || "—"}</td>
            <td className="date-cell">{formatAfghanDate(l.Loan_date)}</td>
            <td className="date-cell">{formatAfghanDate(l.Due_date)}</td>
            <td className="date-cell">{l.Return_date ? formatAfghanDate(l.Return_date) : "—"}</td>
            <td>{toPersianDigits(Number(l.Fine_Amount || 0))}</td>
            <td><StatusBadge loan={l} /></td>
          </tr>
        ))}
      </tbody>
    </table></div>
  );
}

export default App;
