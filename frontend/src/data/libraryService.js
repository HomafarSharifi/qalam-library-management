const KEY = "qalam-library-v1";

// These rules affect only the local demo. A real backend should determine
// availability, loan status, and any fine amount.
export const MOCK_RULES = {
  checkAvailabilityOnIssue: true,
  calculateFines: false
};

const initialData = {
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

export function loadLibrary() {
  try {
    const saved = localStorage.getItem(KEY);
    return saved ? JSON.parse(saved) : structuredClone(initialData);
  } catch {
    return structuredClone(initialData);
  }
}

export function saveLibrary(data) {
  localStorage.setItem(KEY, JSON.stringify(data));
}

export function nextId(rows, field) {
  return Math.max(0, ...rows.map((row) => Number(row[field]) || 0)) + 1;
}

export function dateOnly() {
  return new Date().toISOString().slice(0, 10);
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
