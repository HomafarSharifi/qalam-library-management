import { localDateOnly } from "../utils/afghanDate.js";

/**
 * Library Service & Backend API Client for Qalam
 * Handles communication with the FastAPI backend with offline fallback.
 */

const KEY = "qalam-library-v1";
const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export const initialData = {
  Categories: [
    { ID_Category: 1, Name: "ادبیات" },
    { ID_Category: 2, Name: "تاریخ" },
    { ID_Category: 3, Name: "علوم" }
  ],
  Authors: [
    { ID_Authors: 1, First_Name: "جلال", Last_Name: "آل احمد" },
    { ID_Authors: 2, First_Name: "سیمین", Last_Name: "دانشور" },
    { ID_Authors: 3, First_Name: "محمد", Last_Name: "غبار" }
  ],
  Books: [
    {
      ID_Books: 1, Title: "مدیر مدرسه", ISBN: "978-964-00-0001-1",
      Description: "رمانی از جلال آل احمد", Categories_ID_Category: 1,
      Authors_ID_Authors: [1]
    },
    {
      ID_Books: 2, Title: "سووشون", ISBN: "978-964-00-0002-8",
      Description: "رمانی از سیمین دانشور", Categories_ID_Category: 1,
      Authors_ID_Authors: [2]
    },
    {
      ID_Books: 3, Title: "افغانستان در مسیر تاریخ", ISBN: "",
      Description: "نگاهی به تاریخ افغانستان", Categories_ID_Category: 2,
      Authors_ID_Authors: [3]
    }
  ],
  Members: [
    {
      ID_Members: 1, Email: "mina@example.com", Contact: "0700 123 456",
      Joined_Date: "2025-02-14", First_Name: "مینا", Last_Name: "احمدی"
    },
    {
      ID_Members: 2, Email: "farid@example.com", Contact: "0799 234 567",
      Joined_Date: "2025-04-02", First_Name: "فرید", Last_Name: "رحیمی"
    }
  ],
  Copies: [
    { ID_Copies: 1, Books_ID_Books: 1, Total_Copies: 8, Available_Copies: 5 },
    { ID_Copies: 2, Books_ID_Books: 2, Total_Copies: 5, Available_Copies: 3 },
    { ID_Copies: 3, Books_ID_Books: 3, Total_Copies: 4, Available_Copies: 4 }
  ],
  Loans: [
    {
      ID_Loans: 1, Due_date: "2026-12-01", Loan_date: "2026-11-01",
      Return_date: null, Fine_Amount: 0, Members_ID_Members: 1, Copies_ID_Copies: 1
    },
    {
      ID_Loans: 2, Due_date: "2026-11-20", Loan_date: "2026-11-06",
      Return_date: null, Fine_Amount: 0, Members_ID_Members: 2, Copies_ID_Copies: 2
    }
  ]
};

// --- Local Storage Helpers ---
export function loadLibrary() {
  try {
    const saved = localStorage.getItem(KEY);
    return saved ? JSON.parse(saved) : structuredClone(initialData);
  } catch {
    return structuredClone(initialData);
  }
}

export function saveLibrary(data) {
  try {
    localStorage.setItem(KEY, JSON.stringify(data));
  } catch (err) {
    console.warn("Could not save to localStorage:", err);
  }
}

export function nextId(rows, field) {
  return Math.max(0, ...rows.map((row) => Number(row[field]) || 0)) + 1;
}

export function dateOnly() {
  return localDateOnly();
}

export function fullName(person) {
  return [person?.First_Name, person?.Last_Name].filter(Boolean).join(" ");
}

export function bookForCopy(db, copyId) {
  const copy = db.Copies.find((item) => item.ID_Copies === Number(copyId));
  return db.Books.find((book) => book.ID_Books === copy?.Books_ID_Books);
}

export function categoryName(db, id) {
  return db.Categories.find((item) => item.ID_Category === Number(id))?.Name || "—";
}

// --- API Helpers ---
async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    let detail = `Error ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson && errorJson.detail) {
        detail = errorJson.detail;
      }
    } catch {
      // ignore json parse error
    }
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }

  // Handle empty 204 or responses with no body
  if (response.status === 204) return null;
  return response.json();
}

export async function checkBackendHealth() {
  try {
    const res = await request("/health");
    return res?.status === "healthy";
  } catch {
    return false;
  }
}

export async function fetchFullLibraryFromBackend() {
  const [categories, authors, books, members, loans] = await Promise.all([
    request("/api/categories"),
    request("/api/authors"),
    request("/api/books"),
    request("/api/members"),
    request("/api/loans")
  ]);

  // Extract Copies from Books response (since backend /api/books includes copy info)
  const copies = books.map((b) => ({
    ID_Copies: b.ID_Copies || b.ID_Books,
    Books_ID_Books: b.ID_Books,
    Total_Copies: b.Total_Copies ?? 0,
    Available_Copies: b.Available_Copies ?? 0
  }));

  return {
    Categories: categories,
    Authors: authors,
    Books: books.map((b) => ({
      ID_Books: b.ID_Books,
      Title: b.Title,
      ISBN: b.ISBN || "",
      Description: b.Description || "",
      Categories_ID_Category: b.Categories_ID_Category,
      Authors_ID_Authors: b.Authors_ID_Authors || []
    })),
    Members: members.map((m) => ({
      ID_Members: m.ID_Members,
      First_Name: m.First_Name,
      Last_Name: m.Last_Name,
      Contact: m.Contact,
      Email: m.Email || "",
      Joined_Date: m.Joined_Date
    })),
    Copies: copies,
    Loans: loans.map((l) => ({
      ID_Loans: l.ID_Loans,
      Members_ID_Members: l.Members_ID_Members,
      Copies_ID_Copies: l.Copies_ID_Copies,
      Loan_date: l.Loan_date,
      Due_date: l.Due_date,
      Return_date: l.Return_date,
      Fine_Amount: l.Fine_Amount || 0
    }))
  };
}

// --- CRUD API Calls ---
export const api = {
  // Categories
  createCategory: (data) => request("/api/categories", { method: "POST", body: JSON.stringify(data) }),
  updateCategory: (id, data) => request(`/api/categories/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteCategory: (id) => request(`/api/categories/${id}`, { method: "DELETE" }),

  // Authors
  createAuthor: (data) => request("/api/authors", { method: "POST", body: JSON.stringify(data) }),
  updateAuthor: (id, data) => request(`/api/authors/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteAuthor: (id) => request(`/api/authors/${id}`, { method: "DELETE" }),

  // Books
  createBook: (data) => request("/api/books", { method: "POST", body: JSON.stringify(data) }),
  updateBook: (id, data) => request(`/api/books/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  updateBookCopies: (id, data) => request(`/api/books/${id}/copies`, { method: "PUT", body: JSON.stringify(data) }),
  deleteBook: (id) => request(`/api/books/${id}`, { method: "DELETE" }),

  // Members
  createMember: (data) => request("/api/members", { method: "POST", body: JSON.stringify(data) }),
  updateMember: (id, data) => request(`/api/members/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteMember: (id) => request(`/api/members/${id}`, { method: "DELETE" }),

  // Loans
  issueLoan: (data) => request("/api/loans", { method: "POST", body: JSON.stringify(data) }),
  returnLoan: (id, data) => request(`/api/loans/${id}/return`, { method: "POST", body: JSON.stringify(data) }),
  deleteLoan: (id) => request(`/api/loans/${id}`, { method: "DELETE" }),

  // Reports
  getDashboardStats: () => request("/api/reports/stats"),
  getTopBooks: (limit = 5) => request(`/api/reports/top-books?limit=${limit}`),
  getRecentActivity: (limit = 5) => request(`/api/reports/recent?limit=${limit}`),
  getOverdueReport: () => request("/api/reports/overdue"),
  getMonthlyActivity: (months = 6) => request(`/api/reports/activity?months=${months}`)
};

