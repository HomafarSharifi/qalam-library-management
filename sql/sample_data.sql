USE `Qalam`;

-- 1. Categories
INSERT INTO `Categories` (`ID_Category`, `Name`) VALUES
(1, 'ادبیات'),
(2, 'تاریخ'),
(3, 'علوم'),
(4, 'فلسفه و حکمت'),
(5, 'هنر و معماری')
ON DUPLICATE KEY UPDATE `Name` = VALUES(`Name`);

-- 2. Authors
INSERT INTO `Authors` (`ID_Authors`, `First_Name`, `Last_Name`) VALUES
(1, 'جلال', 'آل احمد'),
(2, 'سیمین', 'دانشور'),
(3, 'محمد', 'غبار'),
(4, 'عبدالحی', 'حبیبی'),
(5, 'مولانا جلال‌الدین', 'بلخی')
ON DUPLICATE KEY UPDATE `First_Name` = VALUES(`First_Name`), `Last_Name` = VALUES(`Last_Name`);

-- 3. Books
INSERT INTO `Books` (`ID_Books`, `Title`, `ISBN`, `Description`, `Categories_ID_Category`) VALUES
(1, 'مدیر مدرسه', '9789640000011', 'داستان تجربیات و چالش‌های یک مدیر مدرسه در جامعه‌ای سنتی', 1),
(2, 'سووشون', '9789640000028', 'رمانی ماندگار از سیمین دانشور درباره مقاومت و زندگی در شیراز جنگ جهانی دوم', 1),
(3, 'افغانستان در مسیر تاریخ', NULL, 'پژوهشی عمیق و مستند در تاریخ معاصر و کهن افغانستان توسط میر غلام محمد غبار', 2),
(4, 'مثنوی معنوی', '9789640000042', 'شاهکار شعر عرفانی و حکمت اسلامی سروده مولانا جلال‌الدین محمد بلخی', 1),
(5, 'تاریخ بیهقی', '9789640000059', 'تاریخ نگاری ماندگار و شاهکار نثر فارسی از ابوالفضل بیهقی', 2)
ON DUPLICATE KEY UPDATE `Title` = VALUES(`Title`);

-- 4. Books_Authors
INSERT INTO `Books_Authors` (`Books_ID_Books`, `Authors_ID_Authors`) VALUES
(1, 1),
(2, 2),
(3, 3),
(4, 5),
(5, 4)
ON DUPLICATE KEY UPDATE `Authors_ID_Authors` = VALUES(`Authors_ID_Authors`);

-- 5. Copies
INSERT INTO `Copies` (`ID_Copies`, `Books_ID_Books`, `Total_Copies`, `Available_Copies`) VALUES
(1, 1, 8, 7),
(2, 2, 5, 4),
(3, 3, 4, 4),
(4, 4, 10, 9),
(5, 5, 6, 6)
ON DUPLICATE KEY UPDATE `Total_Copies` = VALUES(`Total_Copies`), `Available_Copies` = VALUES(`Available_Copies`);

-- 6. Members
INSERT INTO `Members` (`ID_Members`, `First_Name`, `Last_Name`, `Contact`, `Email`, `Joined_Date`) VALUES
(1, 'مینا', 'احمدی', '0700123456', 'mina@example.com', '2025-02-14'),
(2, 'فرید', 'رحیمی', '0799234567', 'farid@example.com', '2025-04-02'),
(3, 'مریم', 'حسینی', '0788345678', 'maryam@example.com', '2025-06-10'),
(4, 'احمد', 'صادقی', '0777456789', 'ahmad@example.com', '2025-08-20')
ON DUPLICATE KEY UPDATE `Contact` = VALUES(`Contact`);

-- 7. Loans
INSERT INTO `Loans` (`ID_Loans`, `Due_date`, `Loan_date`, `Return_date`, `Fine_Amount`, `Members_ID_Members`, `Copies_ID_Copies`) VALUES
(1, '2026-12-01', '2026-11-01', NULL, 0.00, 1, 1),
(2, '2026-11-20', '2026-11-06', NULL, 0.00, 2, 2),
(3, '2026-11-10', '2026-10-25', NULL, 0.00, 3, 4),
(4, '2026-10-15', '2026-10-01', '2026-10-14', 0.00, 4, 5)
ON DUPLICATE KEY UPDATE `Fine_Amount` = VALUES(`Fine_Amount`);
