import { useState, useRef, useEffect } from "react";
import { Calendar, ChevronDown, ChevronLeft, ChevronRight, Check } from "lucide-react";
import {
  AFGHAN_MONTHS,
  AFGHAN_WEEKDAYS,
  gregorianToJalali,
  jalaliToGregorianIso,
  getDaysInJalaliMonth,
  formatAfghanDate,
  localDateOnly,
  toPersianDigits,
  todayJalali
} from "../utils/afghanDate.js";

export default function AfghanDatePicker({
  value,
  onChange,
  label,
  required = false,
  error = "",
  placeholder = "انتخاب تاریخ..."
}) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  // Parse current value into Jalali year, month, day
  const currentJalali = value ? gregorianToJalali(value) : todayJalali();
  const [viewYear, setViewYear] = useState(currentJalali.year);
  const [viewMonth, setViewMonth] = useState(currentJalali.month);

  useEffect(() => {
    if (value) {
      const j = gregorianToJalali(value);
      setViewYear(j.year);
      setViewMonth(j.month);
    }
  }, [value]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    function handleKeyDown(e) {
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const daysInMonth = getDaysInJalaliMonth(viewYear, viewMonth);

  // Find weekday of first day of this month
  const firstDayGregorian = jalaliToGregorianIso(viewYear, viewMonth, 1);
  const firstDayDate = new Date(`${firstDayGregorian}T00:00:00Z`);
  // Afghan week starts on Saturday (شنبه). JavaScript getUTCDay: 0 = Sun, 1 = Mon ... 6 = Sat
  // Convert to Saturday index (Sat=0, Sun=1, Mon=2, Tue=3, Wed=4, Thu=5, Fri=6)
  const firstDayWeekdayIndex = (firstDayDate.getUTCDay() + 1) % 7;

  function selectDate(day) {
    const iso = jalaliToGregorianIso(viewYear, viewMonth, day);
    onChange(iso);
    setIsOpen(false);
  }

  function handleQuickSelect(daysToAdd = 0) {
    const today = new Date();
    today.setDate(today.getDate() + daysToAdd);
    const iso = localDateOnly(today);
    onChange(iso);
    const j = gregorianToJalali(iso);
    setViewYear(j.year);
    setViewMonth(j.month);
    setIsOpen(false);
  }

  function prevMonth() {
    if (viewMonth === 1) {
      setViewYear((y) => y - 1);
      setViewMonth(12);
    } else {
      setViewMonth((m) => m - 1);
    }
  }

  function nextMonth() {
    if (viewMonth === 12) {
      setViewYear((y) => y + 1);
      setViewMonth(1);
    } else {
      setViewMonth((m) => m + 1);
    }
  }

  const selectedJalali = value ? gregorianToJalali(value) : null;
  const isSelected = (day) =>
    selectedJalali &&
    selectedJalali.year === viewYear &&
    selectedJalali.month === viewMonth &&
    selectedJalali.day === day;

  const today = todayJalali();
  const isToday = (day) =>
    today.year === viewYear && today.month === viewMonth && today.day === day;

  return (
    <div className="afghan-datepicker-container" ref={containerRef}>
      {label && (
        <span className="datepicker-label">
          {label} {required && <i className="req-star">*</i>}
        </span>
      )}
      <button
        type="button"
        className={`datepicker-trigger ${isOpen ? "open" : ""} ${error ? "has-error" : ""}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        aria-label={label ? `${label} - ${value ? formatAfghanDate(value, { format: "full" }) : placeholder}` : "انتخاب تاریخ"}
      >
        <Calendar size={16} className="datepicker-icon" aria-hidden="true" />
        <span className="datepicker-value">
          {value ? formatAfghanDate(value, { format: "full" }) : placeholder}
        </span>
        <ChevronDown size={14} className={`datepicker-chevron ${isOpen ? "flipped" : ""}`} aria-hidden="true" />
      </button>

      {isOpen && (
        <div className="datepicker-popover" role="dialog" aria-modal="true" aria-label="تقویم انتخاب تاریخ">
          <div className="datepicker-header">
            <button
              type="button"
              className="datepicker-nav-btn"
              onClick={prevMonth}
              title="ماه قبل"
              aria-label="ماه قبل"
            >
              <ChevronRight size={16} aria-hidden="true" />
            </button>

            <div className="datepicker-title">
              <select
                className="datepicker-month-select"
                value={viewMonth}
                onChange={(e) => setViewMonth(Number(e.target.value))}
                aria-label="انتخاب ماه"
              >
                {AFGHAN_MONTHS.map((m, idx) => (
                  <option key={m} value={idx + 1}>
                    {m}
                  </option>
                ))}
              </select>

              <select
                className="datepicker-year-select"
                value={viewYear}
                onChange={(e) => setViewYear(Number(e.target.value))}
                aria-label="انتخاب سال"
              >
                {[1400, 1401, 1402, 1403, 1404, 1405, 1406, 1407, 1408, 1409, 1410].map((y) => (
                  <option key={y} value={y}>
                    {toPersianDigits(y)}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              className="datepicker-nav-btn"
              onClick={nextMonth}
              title="ماه بعد"
              aria-label="ماه بعد"
            >
              <ChevronLeft size={16} aria-hidden="true" />
            </button>
          </div>

          <div className="datepicker-weekdays">
            {["ش", "ی", "د", "س", "چ", "پ", "ج"].map((wd, i) => (
              <span key={i} title={AFGHAN_WEEKDAYS[(i + 6) % 7]}>
                {wd}
              </span>
            ))}
          </div>

          <div className="datepicker-days-grid">
            {/* Blank offsets before first day of month */}
            {Array.from({ length: firstDayWeekdayIndex }).map((_, i) => (
              <span key={`empty-${i}`} className="datepicker-empty-cell" />
            ))}

            {/* Days in current month */}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1;
              const selected = isSelected(day);
              const todayDay = isToday(day);
              return (
                <button
                  type="button"
                  key={day}
                  className={`datepicker-day-btn ${selected ? "selected" : ""} ${todayDay ? "today" : ""}`}
                  onClick={() => selectDate(day)}
                >
                  {toPersianDigits(day)}
                </button>
              );
            })}
          </div>

          <div className="datepicker-shortcuts">
            <button
              type="button"
              className="shortcut-btn"
              onClick={() => handleQuickSelect(0)}
            >
              امروز
            </button>
            <button
              type="button"
              className="shortcut-btn"
              onClick={() => handleQuickSelect(7)}
            >
              +۷ روز
            </button>
            <button
              type="button"
              className="shortcut-btn"
              onClick={() => handleQuickSelect(14)}
            >
              +۱۴ روز
            </button>
            <button
              type="button"
              className="shortcut-btn"
              onClick={() => handleQuickSelect(30)}
            >
              +۳۰ روز
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
