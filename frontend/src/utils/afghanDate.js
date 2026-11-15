/**
 * Afghan Solar Hijri (Jalali) Calendar Utilities
 * Standardized for Afghanistan (Dari month names: حمل، ثور، جوزا، سرطان، اسد، سنبله، میزان، عقرب، قوس، جدی، دلو، حوت)
 */

export const AFGHAN_MONTHS = [
  "حمل",
  "ثور",
  "جوزا",
  "سرطان",
  "اسد",
  "سنبله",
  "میزان",
  "عقرب",
  "قوس",
  "جدی",
  "دلو",
  "حوت"
];

export const AFGHAN_WEEKDAYS = [
  "یک‌شنبه",
  "دوشنبه",
  "سه‌شنبه",
  "چهارشنبه",
  "پنج‌شنبه",
  "جمعه",
  "شنبه"
];

const PERSIAN_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];
const ARABIC_DIGITS = ["٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"];

/**
 * Converts English digits to Persian/Dari digits
 */
export function toPersianDigits(value) {
  if (value === null || value === undefined) return "";
  return String(value).replace(/\d/g, (d) => PERSIAN_DIGITS[parseInt(d, 10)]);
}

/**
 * Converts Persian/Arabic digits to English digits
 */
export function toEnglishDigits(value) {
  if (!value) return "";
  return String(value)
    .replace(/[۰-۹]/g, (d) => PERSIAN_DIGITS.indexOf(d).toString())
    .replace(/[٠-٩]/g, (d) => ARABIC_DIGITS.indexOf(d).toString());
}

/** Return the local calendar day as YYYY-MM-DD without converting through UTC. */
export function localDateOnly(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/** Add calendar days in local time, avoiding DST/UTC date shifts. */
export function addLocalDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

/**
 * Converts any Date object or ISO string (YYYY-MM-DD) to Jalali { year, month, day }
 */
export function gregorianToJalali(dateInput) {
  if (!dateInput) return todayJalali();
  let d;
  if (typeof dateInput === "string") {
    // If already in Jalali format YYYY-MM-DD (e.g. 1400+)
    const parts = dateInput.split(/[-/]/).map((p) => parseInt(toEnglishDigits(p), 10));
    if (parts.length === 3 && parts[0] >= 1300 && parts[0] <= 1500) {
      return { year: parts[0], month: parts[1], day: parts[2] };
    }
    d = new Date(`${dateInput.slice(0, 10)}T00:00:00Z`);
  } else if (dateInput instanceof Date) {
    d = dateInput;
  } else {
    d = new Date();
  }

  if (isNaN(d.getTime())) d = new Date();

  try {
    const formatter = new Intl.DateTimeFormat("en-US-u-ca-persian", {
      timeZone: "UTC",
      year: "numeric",
      month: "numeric",
      day: "numeric"
    });
    const partsMap = {};
    for (const part of formatter.formatToParts(d)) {
      partsMap[part.type] = part.value;
    }
    return {
      year: parseInt(partsMap.year, 10),
      month: parseInt(partsMap.month, 10),
      day: parseInt(partsMap.day, 10)
    };
  } catch {
    // Fallback if Intl persian is unavailable
    const gy = d.getUTCFullYear();
    const gm = d.getUTCMonth() + 1;
    const gd = d.getUTCDate();
    const g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
    let jy = (gy <= 1600) ? 0 : 979;
    let gy2 = (gy <= 1600) ? gy - 621 : gy - 1600;
    const gy3 = (gm > 2) ? (gy2 + 1) : gy2;
    let days = (365 * gy2) + Math.floor((gy3 + 3) / 4) - Math.floor((gy3 + 99) / 100) + Math.floor((gy3 + 399) / 400) - 80 + gd + g_d_m[gm - 1];
    jy += 33 * Math.floor(days / 12053);
    days %= 12053;
    jy += 4 * Math.floor(days / 1461);
    days %= 1461;
    jy += Math.floor((days - 1) / 365);
    if (days > 0) days = (days - 1) % 365;
    const jm = (days < 186) ? 1 + Math.floor(days / 31) : 7 + Math.floor((days - 186) / 30);
    const jd = 1 + ((days < 186) ? (days % 31) : ((days - 186) % 30));
    return { year: jy, month: jm, day: jd };
  }
}

/**
 * Converts Jalali year, month, day to Gregorian ISO string (YYYY-MM-DD)
 */
export function jalaliToGregorianIso(year, month, day) {
  const jy = parseInt(toEnglishDigits(year), 10);
  const jm = parseInt(toEnglishDigits(month), 10);
  const jd = parseInt(toEnglishDigits(day), 10);

  let gDate = new Date(Date.UTC(jy + 621, jm - 1, jd));
  let cur = gregorianToJalali(gDate);
  let diff = (jy - cur.year) * 365 + (jm - cur.month) * 30 + (jd - cur.day);
  gDate = new Date(gDate.getTime() + diff * 86400000);
  cur = gregorianToJalali(gDate);

  let maxIterations = 25;
  while ((cur.year !== jy || cur.month !== jm || cur.day !== jd) && maxIterations-- > 0) {
    if (cur.year > jy || (cur.year === jy && cur.month > jm) || (cur.year === jy && cur.month === jm && cur.day > jd)) {
      gDate = new Date(gDate.getTime() - 86400000);
    } else {
      gDate = new Date(gDate.getTime() + 86400000);
    }
    cur = gregorianToJalali(gDate);
  }
  return gDate.toISOString().slice(0, 10);
}

/**
 * Gets total days in a given Jalali month (1-12)
 */
export function getDaysInJalaliMonth(year, month) {
  const m = parseInt(month, 10);
  if (m >= 1 && m <= 6) return 31;
  if (m >= 7 && m <= 11) return 30;
  // Month 12 (Hoot): test whether day 30 exists in this year
  const g30 = jalaliToGregorianIso(year, 12, 30);
  const j30 = gregorianToJalali(g30);
  return (j30.year === year && j30.month === 12 && j30.day === 30) ? 30 : 29;
}

/**
 * Returns today's date in Jalali
 */
export function todayJalali() {
  return gregorianToJalali(localDateOnly());
}

/**
 * Formats a Gregorian date (or ISO string) into Afghan Jalali standard text
 * Examples:
 *   formatAfghanDate("2026-11-13") => "۲۲ عقرب ۱۴۰۵"
 *   formatAfghanDate("2026-11-13", { format: "numeric" }) => "۱۴۰۵/۰۸/۲۲"
 *   formatAfghanDate("2026-11-13", { format: "withWeekday" }) => "جمعه، ۲۲ عقرب ۱۴۰۵"
 */
export function formatAfghanDate(dateInput, options = {}) {
  if (!dateInput) return "—";
  const { format = "full", persianNumbers = true } = options;
  const jalali = gregorianToJalali(dateInput);
  const monthName = AFGHAN_MONTHS[jalali.month - 1] || "";

  if (format === "numeric") {
    const mm = String(jalali.month).padStart(2, "0");
    const dd = String(jalali.day).padStart(2, "0");
    const str = `${jalali.year}/${mm}/${dd}`;
    return persianNumbers ? toPersianDigits(str) : str;
  }

  if (format === "iso") {
    const mm = String(jalali.month).padStart(2, "0");
    const dd = String(jalali.day).padStart(2, "0");
    return `${jalali.year}-${mm}-${dd}`;
  }

  if (format === "withWeekday") {
    let d;
    if (typeof dateInput === "string") {
      d = new Date(`${dateInput.slice(0, 10)}T00:00:00Z`);
    } else if (dateInput instanceof Date) {
      d = dateInput;
    } else {
      d = new Date();
    }
    const weekday = AFGHAN_WEEKDAYS[d.getUTCDay()];
    const day = persianNumbers ? toPersianDigits(jalali.day) : jalali.day;
    const year = persianNumbers ? toPersianDigits(jalali.year) : jalali.year;
    return `${weekday}، ${day} ${monthName} ${year}`;
  }

  // Default "full": "۲۲ عقرب ۱۴۰۵"
  const day = persianNumbers ? toPersianDigits(jalali.day) : jalali.day;
  const year = persianNumbers ? toPersianDigits(jalali.year) : jalali.year;
  return `${day} ${monthName} ${year}`;
}

/**
 * Checks if a given due date is overdue compared to today
 */
export function isOverdue(dueDate) {
  if (!dueDate) return false;
  const todayIso = localDateOnly();
  const dueIso = typeof dueDate === "string" ? dueDate.slice(0, 10) : dueDate;
  return dueIso < todayIso;
}
