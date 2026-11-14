"""
In-memory Mock Database for Qalam backend unit and integration testing.
Simulates MySQL behavior, autoincrement IDs, constraints, and transactions.
"""
from datetime import date
import copy


class MockDatabaseState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.categories = {}
        self.authors = {}
        self.books = {}
        self.books_authors = []
        self.copies = {}
        self.members = {}
        self.loans = {}

        self.next_category_id = 1
        self.next_author_id = 1
        self.next_book_id = 1
        self.next_copy_id = 1
        self.next_member_id = 1
        self.next_loan_id = 1

    def seed_sample_data(self):
        self.reset()
        # Categories
        self.categories[1] = {"ID_Category": 1, "Name": "ادبیات"}
        self.categories[2] = {"ID_Category": 2, "Name": "تاریخ"}
        self.next_category_id = 3

        # Authors
        self.authors[1] = {"ID_Authors": 1, "First_Name": "جلال", "Last_Name": "آل احمد"}
        self.authors[2] = {"ID_Authors": 2, "First_Name": "سیمین", "Last_Name": "دانشور"}
        self.next_author_id = 3

        # Books
        self.books[1] = {
            "ID_Books": 1,
            "Title": "مدیر مدرسه",
            "ISBN": "9789640000011",
            "Description": "داستان مدیر مدرسه",
            "Categories_ID_Category": 1
        }
        self.books[2] = {
            "ID_Books": 2,
            "Title": "سووشون",
            "ISBN": "9789640000028",
            "Description": "رمان سووشون",
            "Categories_ID_Category": 1
        }
        self.next_book_id = 3

        # Books_Authors
        self.books_authors.append({"Books_ID_Books": 1, "Authors_ID_Authors": 1})
        self.books_authors.append({"Books_ID_Books": 2, "Authors_ID_Authors": 2})

        # Copies
        self.copies[1] = {
            "ID_Copies": 1,
            "Books_ID_Books": 1,
            "Total_Copies": 5,
            "Available_Copies": 4
        }
        self.copies[2] = {
            "ID_Copies": 2,
            "Books_ID_Books": 2,
            "Total_Copies": 3,
            "Available_Copies": 2
        }
        self.next_copy_id = 3

        # Members
        self.members[1] = {
            "ID_Members": 1,
            "First_Name": "مینا",
            "Last_Name": "احمدی",
            "Contact": "0700123456",
            "Email": "mina@example.com",
            "Joined_Date": date(2025, 2, 14)
        }
        self.members[2] = {
            "ID_Members": 2,
            "First_Name": "فرید",
            "Last_Name": "رحیمی",
            "Contact": "0799234567",
            "Email": "farid@example.com",
            "Joined_Date": date(2025, 4, 2)
        }
        self.next_member_id = 3

        # Loans
        self.loans[1] = {
            "ID_Loans": 1,
            "Members_ID_Members": 1,
            "Copies_ID_Copies": 1,
            "Loan_date": date(2026, 11, 1),
            "Due_date": date(2026, 12, 1),
            "Return_date": None,
            "Fine_Amount": 0.00
        }
        self.loans[2] = {
            "ID_Loans": 2,
            "Members_ID_Members": 2,
            "Copies_ID_Copies": 2,
            "Loan_date": date(2026, 10, 1),
            "Due_date": date(2026, 10, 15),
            "Return_date": date(2026, 10, 14),
            "Fine_Amount": 0.00
        }
        self.next_loan_id = 3


class MockCursor:
    def __init__(self, state: MockDatabaseState, dictionary: bool = True):
        self.state = state
        self.dictionary = dictionary
        self._results = []
        self._lastrowid = None

    @property
    def lastrowid(self):
        return self._lastrowid

    def close(self):
        pass

    def fetchone(self):
        if self._results:
            return self._results.pop(0)
        return None

    def fetchall(self):
        res = list(self._results)
        self._results = []
        return res

    def execute(self, query: str, params=None):
        params = params or ()
        normalized = " ".join(query.strip().split())

        # --- TOP BOOKS ---
        if "GROUP BY b.ID_Books, b.Title" in normalized:
            book_loan_counts = {}
            for l in self.state.loans.values():
                cp = self.state.copies.get(l["Copies_ID_Copies"])
                if cp and cp.get("Books_ID_Books"):
                    b_id = cp["Books_ID_Books"]
                    book_loan_counts[b_id] = book_loan_counts.get(b_id, 0) + 1
            rows = []
            for b_id, b in self.state.books.items():
                cat = self.state.categories.get(b["Categories_ID_Category"], {})
                rows.append({
                    "ID_Books": b_id,
                    "Title": b["Title"],
                    "Category_Name": cat.get("Name"),
                    "Loan_Count": book_loan_counts.get(b_id, 0)
                })
            rows.sort(key=lambda x: (x["Loan_Count"], -x["ID_Books"]), reverse=True)
            limit = params[0] if params else 5
            self._results = rows[:limit]
            return

        # --- RECENT ACTIVITY ---
        if "CASE WHEN l.Return_date IS NOT NULL THEN 'returned'" in normalized:
            today = params[0]
            limit = params[1]
            rows = []
            for l in self.state.loans.values():
                m = self.state.members.get(l["Members_ID_Members"], {})
                cp = self.state.copies.get(l["Copies_ID_Copies"], {})
                bk = self.state.books.get(cp.get("Books_ID_Books"), {})
                if l["Return_date"]:
                    status = "returned"
                elif l["Due_date"] < today:
                    status = "overdue"
                else:
                    status = "active"
                rows.append({
                    "ID_Loans": l["ID_Loans"],
                    "Book_Title": bk.get("Title", ""),
                    "Member_Name": f"{m.get('First_Name', '')} {m.get('Last_Name', '')}".strip(),
                    "Loan_date": l["Loan_date"],
                    "Due_date": l["Due_date"],
                    "Return_date": l["Return_date"],
                    "Status": status
                })
            rows.sort(key=lambda x: x["ID_Loans"], reverse=True)
            self._results = rows[:limit]
            return

        # --- MONTHLY ACTIVITY ---
        if "DATE_FORMAT" in normalized and "AS Month" in normalized:
            months = {}
            for l in self.state.loans.values():
                m_key = l["Loan_date"].strftime("%Y-%m")
                if m_key not in months:
                    months[m_key] = {"Month": m_key, "Loans_Count": 0, "Returns_Count": 0}
                months[m_key]["Loans_Count"] += 1
                if l["Return_date"]:
                    months[m_key]["Returns_Count"] += 1
            self._results = list(months.values())
            return

        # --- CATEGORIES ---
        if "FROM Categories" in normalized and "SELECT" in normalized:
            if "WHERE c.ID_Category = %s" in normalized or "WHERE ID_Category = %s" in normalized:
                cat_id = params[0]
                cat = self.state.categories.get(cat_id)
                if cat:
                    book_count = sum(1 for b in self.state.books.values() if b["Categories_ID_Category"] == cat_id)
                    self._results = [{"ID_Category": cat["ID_Category"], "Name": cat["Name"], "Book_Count": book_count}]
                else:
                    self._results = []
            elif "WHERE Name = %s AND ID_Category != %s" in normalized:
                name, cat_id = params[0], params[1]
                found = any(c["Name"] == name and c["ID_Category"] != cat_id for c in self.state.categories.values())
                self._results = [{"ID_Category": 1}] if found else []
            elif "WHERE Name = %s" in normalized:
                name = params[0]
                found = any(c["Name"] == name for c in self.state.categories.values())
                self._results = [{"ID_Category": 1}] if found else []
            else:
                rows = []
                for cat in self.state.categories.values():
                    if "WHERE c.Name LIKE %s" in normalized:
                        search = params[0].strip("%")
                        if search not in cat["Name"]:
                            continue
                    book_count = sum(1 for b in self.state.books.values() if b["Categories_ID_Category"] == cat["ID_Category"])
                    rows.append({"ID_Category": cat["ID_Category"], "Name": cat["Name"], "Book_Count": book_count})
                rows.sort(key=lambda x: x["Name"])
                self._results = rows
            return

        if "INSERT INTO Categories" in normalized:
            name = params[0]
            cat_id = self.state.next_category_id
            self.state.next_category_id += 1
            self.state.categories[cat_id] = {"ID_Category": cat_id, "Name": name}
            self._lastrowid = cat_id
            return

        if "UPDATE Categories SET Name" in normalized:
            name, cat_id = params[0], params[1]
            if cat_id in self.state.categories:
                self.state.categories[cat_id]["Name"] = name
            return

        if "DELETE FROM Categories WHERE ID_Category" in normalized:
            cat_id = params[0]
            self.state.categories.pop(cat_id, None)
            return

        # --- AUTHORS ---
        if "FROM Authors" in normalized and "SELECT" in normalized:
            if "WHERE a.ID_Authors = %s" in normalized or "WHERE ID_Authors = %s" in normalized:
                a_id = params[0]
                author = self.state.authors.get(a_id)
                if author:
                    cnt = sum(1 for ba in self.state.books_authors if ba["Authors_ID_Authors"] == a_id)
                    self._results = [{**author, "Book_Count": cnt}]
                else:
                    self._results = []
            else:
                rows = []
                for author in self.state.authors.values():
                    if "WHERE a.First_Name LIKE %s OR a.Last_Name LIKE %s" in normalized:
                        term = params[0].strip("%")
                        if term not in author["First_Name"] and term not in author["Last_Name"]:
                            continue
                    cnt = sum(1 for ba in self.state.books_authors if ba["Authors_ID_Authors"] == author["ID_Authors"])
                    rows.append({**author, "Book_Count": cnt})
                rows.sort(key=lambda x: (x["Last_Name"], x["First_Name"]))
                self._results = rows
            return

        if "INSERT INTO Authors" in normalized:
            fn, ln = params[0], params[1]
            a_id = self.state.next_author_id
            self.state.next_author_id += 1
            self.state.authors[a_id] = {"ID_Authors": a_id, "First_Name": fn, "Last_Name": ln}
            self._lastrowid = a_id
            return

        if "UPDATE Authors SET First_Name" in normalized:
            fn, ln, a_id = params[0], params[1], params[2]
            if a_id in self.state.authors:
                self.state.authors[a_id]["First_Name"] = fn
                self.state.authors[a_id]["Last_Name"] = ln
            return

        if "DELETE FROM Authors WHERE ID_Authors" in normalized:
            a_id = params[0]
            self.state.authors.pop(a_id, None)
            return

        # --- BOOKS_AUTHORS ---
        if "FROM Books_Authors" in normalized and "SELECT" in normalized:
            if "COUNT(*) AS cnt" in normalized and "Authors_ID_Authors = %s" in normalized:
                a_id = params[0]
                cnt = sum(1 for ba in self.state.books_authors if ba["Authors_ID_Authors"] == a_id)
                self._results = [{"cnt": cnt}]
            elif "WHERE ba.Books_ID_Books = %s" in normalized:
                b_id = params[0]
                rows = []
                for ba in self.state.books_authors:
                    if ba["Books_ID_Books"] == b_id:
                        auth = self.state.authors.get(ba["Authors_ID_Authors"])
                        if auth:
                            rows.append({
                                "ID_Authors": auth["ID_Authors"],
                                "Full_Name": f"{auth['First_Name']} {auth['Last_Name']}".strip()
                            })
                rows.sort(key=lambda x: x["Full_Name"])
                self._results = rows
            return

        if "INSERT INTO Books_Authors" in normalized:
            b_id, a_id = params[0], params[1]
            self.state.books_authors.append({"Books_ID_Books": b_id, "Authors_ID_Authors": a_id})
            return

        if "DELETE FROM Books_Authors WHERE Books_ID_Books = %s" in normalized:
            b_id = params[0]
            self.state.books_authors = [ba for ba in self.state.books_authors if ba["Books_ID_Books"] != b_id]
            return

        # --- BOOKS ---
        if "FROM Books" in normalized and "SELECT" in normalized:
            if "COUNT(*) AS cnt FROM Books WHERE Categories_ID_Category = %s" in normalized:
                cat_id = params[0]
                cnt = sum(1 for b in self.state.books.values() if b["Categories_ID_Category"] == cat_id)
                self._results = [{"cnt": cnt}]
            elif "COUNT(*) AS total_books FROM Books" in normalized:
                self._results = [{"total_books": len(self.state.books)}]
            elif "WHERE b.ID_Books = %s" in normalized or "WHERE ID_Books = %s" in normalized:
                b_id = params[0]
                b = self.state.books.get(b_id)
                if b:
                    cat = self.state.categories.get(b["Categories_ID_Category"], {})
                    cp = next((c for c in self.state.copies.values() if c["Books_ID_Books"] == b_id), None)
                    self._results = [{
                        "ID_Books": b["ID_Books"],
                        "Title": b["Title"],
                        "ISBN": b["ISBN"],
                        "Description": b["Description"],
                        "Categories_ID_Category": b["Categories_ID_Category"],
                        "Category_Name": cat.get("Name"),
                        "ID_Copies": cp["ID_Copies"] if cp else None,
                        "Total_Copies": cp["Total_Copies"] if cp else 0,
                        "Available_Copies": cp["Available_Copies"] if cp else 0
                    }]
                else:
                    self._results = []
            elif "WHERE ISBN = %s AND ID_Books != %s" in normalized:
                isbn, b_id = params[0], params[1]
                found = any(b["ISBN"] == isbn and b["ID_Books"] != b_id for b in self.state.books.values() if b["ISBN"])
                self._results = [{"ID_Books": 1}] if found else []
            elif "WHERE ISBN = %s" in normalized:
                isbn = params[0]
                found = any(b["ISBN"] == isbn for b in self.state.books.values() if b["ISBN"])
                self._results = [{"ID_Books": 1}] if found else []
            elif "SELECT DISTINCT b.ID_Books" in normalized:
                ids = list(self.state.books.keys())
                ids.sort(reverse=True)
                self._results = [{"ID_Books": i} for i in ids]
            return

        if "INSERT INTO Books (" in normalized:
            title, isbn, desc, cat_id = params[0], params[1], params[2], params[3]
            b_id = self.state.next_book_id
            self.state.next_book_id += 1
            self.state.books[b_id] = {
                "ID_Books": b_id,
                "Title": title,
                "ISBN": isbn,
                "Description": desc,
                "Categories_ID_Category": cat_id
            }
            self._lastrowid = b_id
            return

        if "UPDATE Books SET Title" in normalized:
            title, isbn, desc, cat_id, b_id = params[0], params[1], params[2], params[3], params[4]
            if b_id in self.state.books:
                self.state.books[b_id].update({
                    "Title": title,
                    "ISBN": isbn,
                    "Description": desc,
                    "Categories_ID_Category": cat_id
                })
            return

        if "DELETE FROM Books WHERE ID_Books" in normalized:
            b_id = params[0]
            self.state.books.pop(b_id, None)
            return

        # --- COPIES ---
        if "FROM Copies" in normalized and "SELECT" in normalized:
            if "SUM(Total_Copies)" in normalized:
                tot = sum(c["Total_Copies"] for c in self.state.copies.values())
                avail = sum(c["Available_Copies"] for c in self.state.copies.values())
                self._results = [{"total_c": tot, "avail_c": avail}]
            elif "WHERE Books_ID_Books = %s" in normalized:
                b_id = params[0]
                cp = next((c for c in self.state.copies.values() if c["Books_ID_Books"] == b_id), None)
                self._results = [cp] if cp else []
            elif "WHERE cp.ID_Copies = %s" in normalized or "WHERE ID_Copies = %s" in normalized:
                c_id = params[0]
                cp = self.state.copies.get(c_id)
                if cp:
                    bk = self.state.books.get(cp["Books_ID_Books"], {})
                    self._results = [{**cp, "Book_Title": bk.get("Title", "")}]
                else:
                    self._results = []
            return

        if "INSERT INTO Copies" in normalized:
            b_id, tot, avail = params[0], params[1], params[2]
            cp_id = self.state.next_copy_id
            self.state.next_copy_id += 1
            self.state.copies[cp_id] = {
                "ID_Copies": cp_id,
                "Books_ID_Books": b_id,
                "Total_Copies": tot,
                "Available_Copies": avail
            }
            self._lastrowid = cp_id
            return

        if "UPDATE Copies SET Total_Copies = %s, Available_Copies = %s" in normalized:
            tot, avail, cp_id = params[0], params[1], params[2]
            if cp_id in self.state.copies:
                self.state.copies[cp_id]["Total_Copies"] = tot
                self.state.copies[cp_id]["Available_Copies"] = avail
            return

        if "UPDATE Copies SET Available_Copies = Available_Copies - 1" in normalized:
            cp_id = params[0]
            if cp_id in self.state.copies:
                self.state.copies[cp_id]["Available_Copies"] -= 1
            return

        if "UPDATE Copies SET Available_Copies = LEAST(Total_Copies, Available_Copies + 1)" in normalized:
            cp_id = params[0]
            if cp_id in self.state.copies:
                cp = self.state.copies[cp_id]
                cp["Available_Copies"] = min(cp["Total_Copies"], cp["Available_Copies"] + 1)
            return

        if "DELETE FROM Copies WHERE ID_Copies" in normalized:
            cp_id = params[0]
            self.state.copies.pop(cp_id, None)
            return

        # --- MEMBERS ---
        if "FROM Members" in normalized and "SELECT" in normalized:
            if "COUNT(*) AS total_members" in normalized:
                self._results = [{"total_members": len(self.state.members)}]
            elif "WHERE m.ID_Members = %s" in normalized or "WHERE ID_Members = %s" in normalized:
                m_id = params[0]
                m = self.state.members.get(m_id)
                if m:
                    active = sum(1 for l in self.state.loans.values() if l["Members_ID_Members"] == m_id and l["Return_date"] is None)
                    self._results = [{**m, "Active_Loans_Count": active}]
                else:
                    self._results = []
            elif "WHERE Email = %s AND ID_Members != %s" in normalized:
                email, m_id = params[0], params[1]
                found = any(m["Email"] == email and m["ID_Members"] != m_id for m in self.state.members.values() if m["Email"])
                self._results = [{"ID_Members": 1}] if found else []
            elif "WHERE Email = %s" in normalized:
                email = params[0]
                found = any(m["Email"] == email for m in self.state.members.values() if m["Email"])
                self._results = [{"ID_Members": 1}] if found else []
            else:
                rows = []
                for m in self.state.members.values():
                    if "WHERE 1=1 AND" in normalized:
                        search = params[0].strip("%")
                        if (search not in m["First_Name"] and search not in m["Last_Name"]
                                and search not in m["Contact"] and (not m["Email"] or search not in m["Email"])):
                            continue
                    active = sum(1 for l in self.state.loans.values() if l["Members_ID_Members"] == m["ID_Members"] and l["Return_date"] is None)
                    rows.append({**m, "Active_Loans_Count": active})
                rows.sort(key=lambda x: x["ID_Members"], reverse=True)
                self._results = rows
            return

        if "INSERT INTO Members" in normalized:
            fn, ln, cont, em, jd = params[0], params[1], params[2], params[3], params[4]
            m_id = self.state.next_member_id
            self.state.next_member_id += 1
            self.state.members[m_id] = {
                "ID_Members": m_id,
                "First_Name": fn,
                "Last_Name": ln,
                "Contact": cont,
                "Email": em,
                "Joined_Date": jd
            }
            self._lastrowid = m_id
            return

        if "UPDATE Members SET First_Name" in normalized:
            fn, ln, cont, em, jd, m_id = params[0], params[1], params[2], params[3], params[4], params[5]
            if m_id in self.state.members:
                self.state.members[m_id].update({
                    "First_Name": fn,
                    "Last_Name": ln,
                    "Contact": cont,
                    "Email": em,
                    "Joined_Date": jd
                })
            return

        if "DELETE FROM Members WHERE ID_Members" in normalized:
            m_id = params[0]
            self.state.members.pop(m_id, None)
            return

        # --- LOANS ---
        if "FROM Loans" in normalized and "SELECT" in normalized:
            if "COUNT(*) AS active_loans" in normalized:
                cnt = sum(1 for l in self.state.loans.values() if l["Return_date"] is None)
                self._results = [{"active_loans": cnt}]
            elif "COUNT(*) AS overdue_loans" in normalized:
                today = params[0]
                cnt = sum(1 for l in self.state.loans.values() if l["Return_date"] is None and l["Due_date"] < today)
                self._results = [{"overdue_loans": cnt}]
            elif "SUM(Fine_Amount)" in normalized:
                fines = sum(l["Fine_Amount"] for l in self.state.loans.values())
                self._results = [{"total_fines": fines}]
            elif "COUNT(*) AS active_count" in normalized:
                if "Copies_ID_Copies = %s" in normalized:
                    c_id = params[0]
                    cnt = sum(1 for l in self.state.loans.values() if l["Copies_ID_Copies"] == c_id and l["Return_date"] is None)
                elif "Members_ID_Members = %s" in normalized:
                    m_id = params[0]
                    cnt = sum(1 for l in self.state.loans.values() if l["Members_ID_Members"] == m_id and l["Return_date"] is None)
                else:
                    cnt = 0
                self._results = [{"active_count": cnt}]
            elif "WHERE l.ID_Loans = %s" in normalized or "WHERE ID_Loans = %s" in normalized:
                l_id = params[0]
                l = self.state.loans.get(l_id)
                if l:
                    m = self.state.members.get(l["Members_ID_Members"], {})
                    cp = self.state.copies.get(l["Copies_ID_Copies"], {})
                    bk = self.state.books.get(cp.get("Books_ID_Books"), {})
                    self._results = [{
                        **l,
                        "Books_ID_Books": cp.get("Books_ID_Books"),
                        "Book_Title": bk.get("Title"),
                        "Member_Name": f"{m.get('First_Name', '')} {m.get('Last_Name', '')}".strip()
                    }]
                else:
                    self._results = []
            elif "DATEDIFF" in normalized and "WHERE l.Return_date IS NULL AND l.Due_date < %s" in normalized:
                today = params[0]
                rows = []
                for l in self.state.loans.values():
                    if l["Return_date"] is None and l["Due_date"] < today:
                        m = self.state.members.get(l["Members_ID_Members"], {})
                        cp = self.state.copies.get(l["Copies_ID_Copies"], {})
                        bk = self.state.books.get(cp.get("Books_ID_Books"), {})
                        days = (today - l["Due_date"]).days
                        rows.append({
                            "ID_Loans": l["ID_Loans"],
                            "Due_date": l["Due_date"],
                            "Loan_date": l["Loan_date"],
                            "Days_Overdue": days,
                            "Estimated_Fine": days * 5.0,
                            "ID_Members": l["Members_ID_Members"],
                            "Member_Name": f"{m.get('First_Name', '')} {m.get('Last_Name', '')}".strip(),
                            "Member_Contact": m.get("Contact"),
                            "Member_Email": m.get("Email"),
                            "ID_Books": bk.get("ID_Books"),
                            "Book_Title": bk.get("Title")
                        })
                self._results = rows
            else:
                rows = []
                for l in self.state.loans.values():
                    m = self.state.members.get(l["Members_ID_Members"], {})
                    cp = self.state.copies.get(l["Copies_ID_Copies"], {})
                    bk = self.state.books.get(cp.get("Books_ID_Books"), {})
                    if "AND l.Return_date IS NULL" in normalized and l["Return_date"] is not None:
                        continue
                    if "AND l.Return_date IS NOT NULL" in normalized and l["Return_date"] is None:
                        continue
                    rows.append({
                        **l,
                        "Books_ID_Books": cp.get("Books_ID_Books"),
                        "Book_Title": bk.get("Title"),
                        "Member_Name": f"{m.get('First_Name', '')} {m.get('Last_Name', '')}".strip()
                    })
                rows.sort(key=lambda x: x["ID_Loans"], reverse=True)
                self._results = rows
            return

        if "INSERT INTO Loans" in normalized:
            m_id, cp_id, ld, dd = params[0], params[1], params[2], params[3]
            l_id = self.state.next_loan_id
            self.state.next_loan_id += 1
            self.state.loans[l_id] = {
                "ID_Loans": l_id,
                "Members_ID_Members": m_id,
                "Copies_ID_Copies": cp_id,
                "Loan_date": ld,
                "Due_date": dd,
                "Return_date": None,
                "Fine_Amount": 0.00
            }
            self._lastrowid = l_id
            return

        if "UPDATE Loans SET Return_date" in normalized:
            rd, fine, l_id = params[0], params[1], params[2]
            if l_id in self.state.loans:
                self.state.loans[l_id]["Return_date"] = rd
                self.state.loans[l_id]["Fine_Amount"] = fine
            return

        if "DELETE FROM Loans WHERE Copies_ID_Copies = %s" in normalized:
            cp_id = params[0]
            self.state.loans = {k: v for k, v in self.state.loans.items() if v["Copies_ID_Copies"] != cp_id}
            return

        if "DELETE FROM Loans WHERE Members_ID_Members = %s" in normalized:
            m_id = params[0]
            self.state.loans = {k: v for k, v in self.state.loans.items() if v["Members_ID_Members"] != m_id}
            return

        if "DELETE FROM Loans WHERE ID_Loans = %s" in normalized:
            l_id = params[0]
            self.state.loans.pop(l_id, None)
            return


class MockConnection:
    def __init__(self, state: MockDatabaseState):
        self.state = state
        self._snapshot = None
        self._is_connected = True

    def is_connected(self):
        return self._is_connected

    def cursor(self, dictionary: bool = True):
        return MockCursor(self.state, dictionary=dictionary)

    def commit(self):
        self._snapshot = None

    def rollback(self):
        if self._snapshot is not None:
            self.state.categories = copy.deepcopy(self._snapshot["categories"])
            self.state.authors = copy.deepcopy(self._snapshot["authors"])
            self.state.books = copy.deepcopy(self._snapshot["books"])
            self.state.books_authors = copy.deepcopy(self._snapshot["books_authors"])
            self.state.copies = copy.deepcopy(self._snapshot["copies"])
            self.state.members = copy.deepcopy(self._snapshot["members"])
            self.state.loans = copy.deepcopy(self._snapshot["loans"])

    def close(self):
        self._is_connected = False
