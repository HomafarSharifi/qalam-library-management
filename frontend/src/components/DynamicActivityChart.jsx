import { useState, useMemo } from "react";
import {
  AFGHAN_MONTHS,
  gregorianToJalali,
  toPersianDigits,
  todayJalali
} from "../utils/afghanDate.js";

export default function DynamicActivityChart({ db }) {
  const [range, setRange] = useState("6m"); // '6m' or '12m'
  const [hoveredIndex, setHoveredIndex] = useState(null);

  const currentJalali = todayJalali();

  // Compute monthly stats for Afghan months in proper calendar order
  const monthlyData = useMemo(() => {
    const months = [];

    if (range === "12m") {
      // All 12 Afghan months in proper calendar order: حمل (1) to حوت (12)
      for (let mIndex = 0; mIndex < 12; mIndex++) {
        months.push({
          year: currentJalali.year,
          monthIndex: mIndex,
          monthNumber: mIndex + 1,
          name: AFGHAN_MONTHS[mIndex]
        });
      }
    } else {
      // 6 recent months in chronological order leading up to current month
      for (let i = 5; i >= 0; i--) {
        let mIndex = currentJalali.month - 1 - i;
        let y = currentJalali.year;
        while (mIndex < 0) {
          mIndex += 12;
          y -= 1;
        }
        months.push({
          year: y,
          monthIndex: mIndex,
          monthNumber: mIndex + 1,
          name: AFGHAN_MONTHS[mIndex]
        });
      }
    }

    return months.map((m) => {
      // Find loans in this Jalali year and month
      const loansInMonth = (db.Loans || []).filter((loan) => {
        if (!loan.Loan_date) return false;
        const j = gregorianToJalali(loan.Loan_date);
        return j.year === m.year && j.month === m.monthNumber;
      });

      // Find returns in this Jalali year and month
      const returnsInMonth = (db.Loans || []).filter((loan) => {
        if (!loan.Return_date) return false;
        const j = gregorianToJalali(loan.Return_date);
        return j.year === m.year && j.month === m.monthNumber;
      });

      return {
        ...m,
        loansCount: loansInMonth.length,
        returnsCount: returnsInMonth.length
      };
    });
  }, [db.Loans, range, currentJalali.year, currentJalali.month]);

  const maxVal = useMemo(() => {
    let max = 5;
    for (const d of monthlyData) {
      if (d.loansCount > max) max = d.loansCount;
      if (d.returnsCount > max) max = d.returnsCount;
    }
    // Round up to nice number
    return Math.ceil(max * 1.25);
  }, [monthlyData]);

  // SVG dimensions
  const svgWidth = 620;
  const svgHeight = 160;
  const paddingX = 40;
  const paddingY = 20;
  const usableWidth = svgWidth - paddingX * 2;
  const usableHeight = svgHeight - paddingY * 2;

  // Calculate coordinates for points - Right to Left (RTL) progression
  const pointsLoans = useMemo(() => {
    const step = usableWidth / Math.max(1, monthlyData.length - 1);
    return monthlyData.map((d, idx) => {
      // In RTL, index 0 starts on the right (svgWidth - paddingX) and progresses left
      const x = svgWidth - paddingX - idx * step;
      const y = svgHeight - paddingY - (d.loansCount / maxVal) * usableHeight;
      return { x, y, value: d.loansCount, month: d.name, year: d.year };
    });
  }, [monthlyData, maxVal, usableWidth, usableHeight, svgHeight, svgWidth]);

  const pointsReturns = useMemo(() => {
    const step = usableWidth / Math.max(1, monthlyData.length - 1);
    return monthlyData.map((d, idx) => {
      // In RTL, index 0 starts on the right (svgWidth - paddingX) and progresses left
      const x = svgWidth - paddingX - idx * step;
      const y = svgHeight - paddingY - (d.returnsCount / maxVal) * usableHeight;
      return { x, y, value: d.returnsCount, month: d.name, year: d.year };
    });
  }, [monthlyData, maxVal, usableWidth, usableHeight, svgHeight, svgWidth]);

  // Generate smooth cubic bezier SVG path
  function createSmoothPath(points) {
    if (!points.length) return "";
    if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;

    let path = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i === 0 ? 0 : i - 1];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[i + 2 < points.length ? i + 2 : i + 1];

      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      path += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
    }
    return path;
  }

  // Create area fill path (closed to bottom)
  function createAreaPath(points) {
    if (!points.length) return "";
    const linePath = createSmoothPath(points);
    const lastX = points[points.length - 1].x;
    const firstX = points[0].x;
    const bottomY = svgHeight - paddingY;
    return `${linePath} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`;
  }

  const loansLine = createSmoothPath(pointsLoans);
  const loansArea = createAreaPath(pointsLoans);
  const returnsLine = createSmoothPath(pointsReturns);
  const returnsArea = createAreaPath(pointsReturns);

  // Y-axis grid levels (4 levels)
  const yLevels = [
    { label: maxVal, y: paddingY },
    { label: Math.round(maxVal * 0.75), y: paddingY + usableHeight * 0.25 },
    { label: Math.round(maxVal * 0.5), y: paddingY + usableHeight * 0.5 },
    { label: Math.round(maxVal * 0.25), y: paddingY + usableHeight * 0.75 },
    { label: 0, y: svgHeight - paddingY }
  ];

  return (
    <section className="panel activity-panel">
      <div className="panel-heading">
        <div>
          <h2>فعالیت ماهانه کتابخانه</h2>
          <p>امانت‌ها و بازگشت‌های ثبت‌شده در ماه‌های خورشیدی (افغانستان)</p>
        </div>
        <div className="chart-range-buttons">
          <button
            type="button"
            className={`range-btn ${range === "6m" ? "active" : ""}`}
            onClick={() => setRange("6m")}
          >
            ۶ ماه اخیر
          </button>
          <button
            type="button"
            className={`range-btn ${range === "12m" ? "active" : ""}`}
            onClick={() => setRange("12m")}
          >
            ۱۲ ماه سال
          </button>
        </div>
      </div>

      <div className="chart-legend">
        <span>
          <i className="legend-dot blue-dot" /> امانت‌های ثبت‌شده
        </span>
        <span>
          <i className="legend-dot green-dot" /> بازگشت‌های ثبت‌شده
        </span>
      </div>

      <div className="chart-wrap">
        <div className="chart-ylabels">
          {yLevels.map((lvl, idx) => (
            <span key={idx}>{toPersianDigits(lvl.label)}</span>
          ))}
        </div>

        <div className="chart-svg-container">
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            preserveAspectRatio="none"
            role="img"
            aria-label="نمودار فعالیت امانت‌ها"
          >
            <defs>
              <linearGradient id="blueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2864d7" stopOpacity="0.22" />
                <stop offset="100%" stopColor="#2864d7" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="greenGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#55b77a" stopOpacity="0.22" />
                <stop offset="100%" stopColor="#55b77a" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Horizontal Grid Lines */}
            {yLevels.map((lvl, idx) => (
              <line
                key={idx}
                x1={paddingX}
                y1={lvl.y}
                x2={svgWidth - paddingX}
                y2={lvl.y}
                stroke="#eef0f4"
                strokeWidth="1"
                strokeDasharray={idx === yLevels.length - 1 ? "none" : "3 3"}
              />
            ))}

            {/* Area Fills */}
            {loansArea && <path d={loansArea} fill="url(#blueGradient)" />}
            {returnsArea && <path d={returnsArea} fill="url(#greenGradient)" />}

            {/* Stroke Lines */}
            {loansLine && (
              <path
                d={loansLine}
                fill="none"
                stroke="#2864d7"
                strokeWidth="2.5"
                strokeLinecap="round"
                className="animated-chart-line"
              />
            )}
            {returnsLine && (
              <path
                d={returnsLine}
                fill="none"
                stroke="#55b77a"
                strokeWidth="2.5"
                strokeLinecap="round"
                className="animated-chart-line"
              />
            )}

            {/* Data Points */}
            {pointsLoans.map((pt, idx) => (
              <g
                key={`pt-l-${idx}`}
                onMouseEnter={() => setHoveredIndex(idx)}
                onMouseLeave={() => setHoveredIndex(null)}
                style={{ cursor: "pointer" }}
              >
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={hoveredIndex === idx ? 5.5 : 3.5}
                  fill="#2864d7"
                  stroke="#ffffff"
                  strokeWidth="2"
                  className="chart-point"
                />
              </g>
            ))}

            {pointsReturns.map((pt, idx) => (
              <g
                key={`pt-r-${idx}`}
                onMouseEnter={() => setHoveredIndex(idx)}
                onMouseLeave={() => setHoveredIndex(null)}
                style={{ cursor: "pointer" }}
              >
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={hoveredIndex === idx ? 5.5 : 3.5}
                  fill="#55b77a"
                  stroke="#ffffff"
                  strokeWidth="2"
                  className="chart-point"
                />
              </g>
            ))}
          </svg>

          {/* Interactive Tooltip */}
          {hoveredIndex !== null && (
            <div
              className="chart-tooltip"
              style={{
                left: `${(pointsLoans[hoveredIndex].x / svgWidth) * 100}%`
              }}
            >
              <strong>
                {monthlyData[hoveredIndex].name} {toPersianDigits(monthlyData[hoveredIndex].year)}
              </strong>
              <div className="tooltip-row blue">
                امانت: {toPersianDigits(monthlyData[hoveredIndex].loansCount)} مورد
              </div>
              <div className="tooltip-row green">
                بازگشت: {toPersianDigits(monthlyData[hoveredIndex].returnsCount)} مورد
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="chart-xlabels">
        {monthlyData.map((d, idx) => (
          <span
            key={idx}
            className={`xlabel ${hoveredIndex === idx ? "active" : ""}`}
            onMouseEnter={() => setHoveredIndex(idx)}
            onMouseLeave={() => setHoveredIndex(null)}
          >
            {d.name}
          </span>
        ))}
      </div>
    </section>
  );
}
