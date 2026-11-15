const field = (key, label, read = (row) => row[key]) => ({ key, label, read });

export function buildExportTables(db) {
  const copiesByBook = new Map((db.Copies || []).map((copy) => [Number(copy.Books_ID_Books), copy]));
  const table = (id, label, columns, rows) => ({ id, label, columns, rows });

  return [
    table("Categories", "دسته‌بندی‌ها", [field("ID_Category", "شناسه"), field("Name", "نام")], db.Categories || []),
    table("Books", "کتاب‌ها", [
      field("ID_Books", "شناسه"), field("Title", "عنوان"), field("ISBN", "ISBN"), field("Description", "توضیحات"),
      field("Categories_ID_Category", "شناسه دسته‌بندی"),
      field("Authors_ID_Authors", "شناسه نویسندگان", (row) => (row.Authors_ID_Authors || []).join("، ")),
      field("Total_Copies", "مجموع نسخه‌ها", (row) => copiesByBook.get(Number(row.ID_Books))?.Total_Copies ?? 0),
      field("Available_Copies", "نسخه‌های موجود", (row) => copiesByBook.get(Number(row.ID_Books))?.Available_Copies ?? 0)
    ], db.Books || []),
    table("Authors", "نویسندگان", [field("ID_Authors", "شناسه"), field("First_Name", "نام"), field("Last_Name", "نام خانوادگی")], db.Authors || []),
    table("Members", "اعضا", [
      field("ID_Members", "شناسه"), field("First_Name", "نام"), field("Last_Name", "نام خانوادگی"),
      field("Email", "ایمیل"), field("Contact", "شماره تماس"), field("Joined_Date", "تاریخ عضویت")
    ], db.Members || []),
    table("Copies", "نسخه‌ها", [
      field("ID_Copies", "شناسه"), field("Books_ID_Books", "شناسه کتاب"),
      field("Total_Copies", "مجموع نسخه‌ها"), field("Available_Copies", "نسخه‌های موجود")
    ], db.Copies || []),
    table("Loans", "امانت‌ها", [
      field("ID_Loans", "شناسه"), field("Due_date", "موعد بازگشت"), field("Loan_date", "تاریخ امانت"),
      field("Return_date", "تاریخ بازگشت"), field("Fine_Amount", "جریمه"),
      field("Members_ID_Members", "شناسه عضو"), field("Copies_ID_Copies", "شناسه نسخه")
    ], db.Loans || []),
    table("Books_Authors", "ارتباط کتاب و نویسنده", [
      field("Books_ID_Books", "شناسه کتاب"), field("Authors_ID_Authors", "شناسه نویسنده")
    ], (db.Books || []).flatMap((book) => (book.Authors_ID_Authors || []).map((authorId) => ({
      Books_ID_Books: book.ID_Books,
      Authors_ID_Authors: authorId
    }))))
  ];
}

export function csvForTable(table) {
  const escape = (value) => {
    let text = value == null ? "" : String(value);
    if (/^[\s]*[=+\-@]/.test(text)) text = `'${text}`;
    return `"${text.replaceAll('"', '""')}"`;
  };
  return `\uFEFF${[
    table.columns.map((column) => escape(column.label)).join(","),
    ...table.rows.map((row) => table.columns.map((column) => escape(column.read(row))).join(","))
  ].join("\r\n")}`;
}

export function htmlForTablePrint(table) {
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
  const headings = table.columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("");
  const rows = table.rows.map((row) => `<tr>${table.columns.map((column) => `<td>${escapeHtml(column.read(row))}</td>`).join("")}</tr>`).join("");

  return `<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>${escapeHtml(table.label)}</title><style>
    @page{size:landscape;margin:14mm}*{box-sizing:border-box}body{font-family:"Yekan Bakh",Tahoma,sans-serif;color:#202938;margin:0}h1{font-size:20px;margin:0 0 4px}p{font-size:11px;color:#687386;margin:0 0 18px}table{width:100%;border-collapse:collapse;font-size:10px}thead{display:table-header-group}tr{break-inside:avoid}th,td{padding:7px 8px;border:1px solid #dfe4ec;text-align:right;vertical-align:top;overflow-wrap:anywhere}th{background:#edf4ff;color:#1f52b8;font-weight:700}tbody tr:nth-child(even){background:#f8fafc}@media print{body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
  </style></head><body><h1>${escapeHtml(table.label)}</h1><p>گزارش خروجی • ${escapeHtml(new Date().toLocaleString("fa-AF"))} • ${table.rows.length} ردیف</p><table><thead><tr>${headings}</tr></thead><tbody>${rows}</tbody></table><script>window.addEventListener('load',()=>setTimeout(()=>window.print(),250))<\/script></body></html>`;
}

export async function jpgBlobForTable(table) {
  const maxRows = 900;
  if (table.rows.length > maxRows) {
    throw new Error(`برای خروجی تصویری حداکثر ${maxRows} ردیف پشتیبانی می‌شود؛ برای جدول کامل PDF یا CSV را انتخاب کنید.`);
  }
  await document.fonts?.ready;
  const width = 1600;
  const padding = 44;
  const titleHeight = 86;
  const headerHeight = 48;
  const rowHeight = table.rows.length > 500 ? 20 : 32;
  const height = padding * 2 + titleHeight + headerHeight + table.rows.length * rowHeight;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);
  context.direction = "rtl";
  context.textAlign = "right";
  context.fillStyle = "#202938";
  context.font = '700 30px "Yekan Bakh", Tahoma, sans-serif';
  context.fillText(table.label, width - padding, padding + 28);
  context.fillStyle = "#788396";
  context.font = '16px "Yekan Bakh", Tahoma, sans-serif';
  context.fillText(`${table.rows.length} ردیف • ${new Date().toLocaleDateString("fa-AF")}`, width - padding, padding + 58);

  const columnWidth = (width - padding * 2) / table.columns.length;
  const tableTop = padding + titleHeight;
  table.columns.forEach((column, index) => {
    const right = width - padding - index * columnWidth;
    context.fillStyle = "#edf4ff";
    context.fillRect(right - columnWidth, tableTop, columnWidth, headerHeight);
    context.fillStyle = "#1f52b8";
    context.font = '700 16px "Yekan Bakh", Tahoma, sans-serif';
    context.fillText(String(column.label), right - 12, tableTop + headerHeight / 2, columnWidth - 24);
  });
  table.rows.forEach((row, rowIndex) => {
    const top = tableTop + headerHeight + rowIndex * rowHeight;
    context.fillStyle = rowIndex % 2 ? "#f8fafc" : "#ffffff";
    context.fillRect(padding, top, width - padding * 2, rowHeight);
    context.strokeStyle = "#dfe4ec";
    context.beginPath();
    context.moveTo(padding, top + rowHeight);
    context.lineTo(width - padding, top + rowHeight);
    context.stroke();
    table.columns.forEach((column, index) => {
      const right = width - padding - index * columnWidth;
      context.fillStyle = "#303947";
      context.font = '14px "Yekan Bakh", Tahoma, sans-serif';
      const value = String(column.read(row) ?? "").replace(/\s+/g, " ");
      context.fillText(value, right - 12, top + rowHeight / 2, columnWidth - 24);
    });
  });
  return new Promise((resolve, reject) => canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error("ساخت تصویر خروجی ناموفق بود.")), "image/jpeg", 0.92));
}
