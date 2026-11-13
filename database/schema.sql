CREATE Database Qalam;

USE Qalam;

CREATE TABLE IF NOT EXISTS `Qalam`.`Categories` (
    `ID_Category` INT NOT NULL AUTO_INCREMENT,
    `Name` VARCHAR(100) NOT NULL,

    PRIMARY KEY (`ID_Category`),
    UNIQUE INDEX `Name_UNIQUE` (`Name` ASC)
);


CREATE TABLE IF NOT EXISTS `Qalam`.`Books` (
    `ID_Books` INT NOT NULL AUTO_INCREMENT,
    `Title` VARCHAR(100) NOT NULL,
    `ISBN` VARCHAR(13) NULL,
    `Description` TEXT NULL,
    `Categories_ID_Category` INT NOT NULL,

    PRIMARY KEY (`ID_Books`),

    INDEX `fk_Books_Categories1_idx`
        (`Categories_ID_Category` ASC),

    UNIQUE INDEX `ISBN_UNIQUE` (`ISBN` ASC),

    CONSTRAINT `fk_Books_Categories1`
        FOREIGN KEY (`Categories_ID_Category`)
        REFERENCES `Qalam`.`Categories` (`ID_Category`)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);


CREATE TABLE IF NOT EXISTS `Qalam`.`Authors` (
    `ID_Authors` INT NOT NULL AUTO_INCREMENT,
    `First_Name` VARCHAR(45) NOT NULL,
    `Last_Name` VARCHAR(45) NOT NULL,

    PRIMARY KEY (`ID_Authors`)
);


CREATE TABLE IF NOT EXISTS `Qalam`.`Members` (
    `ID_Members` INT NOT NULL AUTO_INCREMENT,
    `Email` VARCHAR(75) NULL,
    `Contact` VARCHAR(15) NOT NULL,
    `Joined_Date` DATE NOT NULL DEFAULT (CURRENT_DATE),
    `First_Name` VARCHAR(45) NOT NULL,
    `Last_Name` VARCHAR(45) NOT NULL,

    PRIMARY KEY (`ID_Members`),
    UNIQUE INDEX `Email_UNIQUE` (`Email` ASC)
);


CREATE TABLE IF NOT EXISTS `Qalam`.`Copies` (
    `ID_Copies` INT NOT NULL AUTO_INCREMENT,
    `Books_ID_Books` INT NOT NULL,
    `Total_Copies` INT NOT NULL DEFAULT 0,
    `Available_Copies` INT NOT NULL DEFAULT 0,

    PRIMARY KEY (`ID_Copies`),

    UNIQUE INDEX `Books_ID_Books_UNIQUE`
        (`Books_ID_Books` ASC),

    CONSTRAINT `chk_total_copies`
        CHECK (`Total_Copies` >= 0),

    CONSTRAINT `chk_available_copies`
        CHECK (
            `Available_Copies` >= 0
            AND `Available_Copies` <= `Total_Copies`
        ),

    CONSTRAINT `fk_Copies_Books`
        FOREIGN KEY (`Books_ID_Books`)
        REFERENCES `Qalam`.`Books` (`ID_Books`)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);


CREATE TABLE IF NOT EXISTS `Qalam`.`Loans` (
    `ID_Loans` INT NOT NULL AUTO_INCREMENT,
    `Due_date` DATE NOT NULL,
    `Loan_date` DATE NOT NULL,
    `Return_date` DATE NULL DEFAULT NULL,
    `Fine_Amount` DECIMAL(10, 2) UNSIGNED NOT NULL DEFAULT 0.00,
    `Members_ID_Members` INT NOT NULL,
    `Copies_ID_Copies` INT NOT NULL,

    PRIMARY KEY (`ID_Loans`),

    INDEX `fk_Loans_Members1_idx`
        (`Members_ID_Members` ASC),

    INDEX `fk_Loans_Copies1_idx`
        (`Copies_ID_Copies` ASC),

    CONSTRAINT `fk_Loans_Members1`
        FOREIGN KEY (`Members_ID_Members`)
        REFERENCES `Qalam`.`Members` (`ID_Members`)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    CONSTRAINT `fk_Loans_Copies1`
        FOREIGN KEY (`Copies_ID_Copies`)
        REFERENCES `Qalam`.`Copies` (`ID_Copies`)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    CONSTRAINT `chk_loan_dates`
        CHECK (`Due_date` >= `Loan_date`)
);


CREATE TABLE IF NOT EXISTS `Qalam`.`Books_Authors` (
    `Books_ID_Books` INT NOT NULL,
    `Authors_ID_Authors` INT NOT NULL,

    PRIMARY KEY (`Books_ID_Books`, `Authors_ID_Authors`),

    INDEX `fk_Books_has_Authors_Authors1_idx`
        (`Authors_ID_Authors` ASC),

    CONSTRAINT `fk_Books_has_Authors_Books1`
        FOREIGN KEY (`Books_ID_Books`)
        REFERENCES `Qalam`.`Books` (`ID_Books`)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    CONSTRAINT `fk_Books_has_Authors_Authors1`
        FOREIGN KEY (`Authors_ID_Authors`)
        REFERENCES `Qalam`.`Authors` (`ID_Authors`)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);
