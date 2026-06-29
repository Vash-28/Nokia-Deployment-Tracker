DROP DATABASE IF EXISTS DeploymentTrackerDB;
CREATE DATABASE DeploymentTrackerDB;
USE DeploymentTrackerDB;

CREATE TABLE Accounts(
	accountID INT PRIMARY KEY AUTO_INCREMENT,
    accountName VARCHAR(255) NOT NULL,
    account_details VARCHAR(255),
    isActive BOOL NOT NULL DEFAULT 1,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Division(
	divisionID INT PRIMARY KEY AUTO_INCREMENT,
	divisionName VARCHAR(255) NOT NULL,
	isActive BOOL NOT NULL DEFAULT '1',
	createdAt datetime DEFAULT CURRENT_TIMESTAMP,
	updatedAt datetime DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Customers(
    accountID INT NOT NULL,
	customerID INT PRIMARY KEY AUTO_INCREMENT,
    customerName VARCHAR(255) NOT NULL,
    customerDetails VARCHAR(255),
    isActive BOOL NOT NULL DEFAULT 1,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (accountID)
    REFERENCES Accounts(accountID)
);

CREATE TABLE Companies(
	createdAt datetime DEFAULT CURRENT_TIMESTAMP,
	updatedAt datetime DEFAULT CURRENT_TIMESTAMP,
	companyID int PRIMARY KEY AUTO_INCREMENT,
	companyName varchar(255) NOT NULL,
	companyDetails text,
	billingAddress text,
	contactPerson varchar(255) DEFAULT NULL,
	contactNumber varchar(255) NOT NULL,
	identityCode varchar(255) DEFAULT NULL,
	isActive BOOL DEFAULT NULL
);

CREATE TABLE Product(
	productID INT PRIMARY KEY AUTO_INCREMENT,
    productName varchar(255) DEFAULT NULL,
	productUOM char(4) DEFAULT NULL,
	productHSN varchar(255) DEFAULT NULL,
    isActive BOOL NOT NULL DEFAULT 1,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE BusinessUnit(
	businessUnitID INT PRIMARY KEY AUTO_INCREMENT,
    divisionID INT DEFAULT NULL,
	productID INT DEFAULT NULL,
    isActive BOOL NOT NULL DEFAULT 1,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (divisionID)
    REFERENCES Division(divisionID),
	FOREIGN KEY (productID)
    REFERENCES Product(productID)
);

CREATE TABLE Users(
	userID INT PRIMARY KEY AUTO_INCREMENT,
    companyID INT DEFAULT NULL,
    FOREIGN KEY (companyID)
	REFERENCES Companies(companyID),
    emailAddress VARCHAR(255) DEFAULT NULL,
    userPassword VARCHAR(255) DEFAULT NULL,
    userName VARCHAR(255) DEFAULT NULL,
    mobile VARCHAR(255) DEFAULT NULL,
    avatar VARCHAR(255) DEFAULT NULL,
    isSuperAdmin BOOL DEFAULT 0,
    passwordResetToken VARCHAR(255) DEFAULT NULL,
    passwordResetTokenExpiresat DOUBLE DEFAULT NULL,
    userRole INT DEFAULT NULL,
    isActive BOOL NOT NULL DEFAULT 1,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Milestone(
	milestoneID INT PRIMARY KEY AUTO_INCREMENT,
	milestoneName varchar(512) NOT NULL,
	milestoneNickname varchar(100) DEFAULT NULL,
	milestoneDataID varchar(15) NOT NULL,
	milestonePriority tinyint NOT NULL,
	milestoneType tinyint NOT NULL,
	createdAt datetime DEFAULT CURRENT_TIMESTAMP,
	updatedAt datetime DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Opportunity(
	opportunityID INT PRIMARY KEY AUTO_INCREMENT,
	opportunityName varchar(512) NOT NULL,
	opportunityNumber varchar(255) DEFAULT NULL,
    customerID INT NOT NULL,
    FOREIGN KEY (customerID)
    REFERENCES Customers(customerID),
	divisionID int DEFAULT NULL,
	isActive BOOL NOT NULL DEFAULT 1,
	startDate date NOT NULL,
	endDate date DEFAULT NULL,
	totalValue double NOT NULL,
	createdBy int NOT NULL,
    FOREIGN KEY (createdBy)
    REFERENCES Users(userID),
	createdAt datetime DEFAULT CURRENT_TIMESTAMP,
	updatedAt datetime DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Opportunity_Details(
    opportunityDetailID INT PRIMARY KEY AUTO_INCREMENT,
    opportunityID INT NOT NULL,
    productID INT NOT NULL,
    productQuantity INT NOT NULL,
    productRate DOUBLE NOT NULL,
    productTotal DOUBLE NOT NULL,
    productRemark TEXT,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunityID) REFERENCES Opportunity(opportunityID),
    FOREIGN KEY (productID) REFERENCES Product(productID)
);

CREATE TABLE PO(
	poID bigint PRIMARY KEY AUTO_INCREMENT,
	pOName varchar(512) NOT NULL,
    opportunityID INT NOT NULL,
    FOREIGN KEY (opportunityID)
    REFERENCES Opportunity(opportunityID),
	isActive BOOL NOT NULL DEFAULT '1',
	startDate date DEFAULT NULL,
	endDate date DEFAULT NULL,
	totalValue double NOT NULL,
	poRemark text,
	createdBy int NOT NULL,
    FOREIGN KEY (createdBy)
    REFERENCES Users(userID),
	createdAt datetime DEFAULT CURRENT_TIMESTAMP,
	updatedAt datetime DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE PO_Details(
    poDetailsID INT PRIMARY KEY AUTO_INCREMENT,
    poID BIGINT NOT NULL,
    productID INT NOT NULL,
    productQuantity DOUBLE NOT NULL,
    poActualQuantity DOUBLE DEFAULT 0,
    productRate DOUBLE NOT NULL,
    productTotal DOUBLE NOT NULL,
    productRemark TEXT,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (poID) REFERENCES PO(poID),
    FOREIGN KEY (productID) REFERENCES Product(productID)
);

CREATE TABLE Challenges(
	challengeID int PRIMARY KEY AUTO_INCREMENT,
	challengeName varchar(512) DEFAULT NULL,
	createdBy bigint DEFAULT NULL,
	isActive BOOL NOT NULL DEFAULT '1',
	createdAt datetime DEFAULT CURRENT_TIMESTAMP,
	updatedAt datetime DEFAULT CURRENT_TIMESTAMP
);

-- Milestone plan header (per opportunity+product+milestone+quarter)
CREATE TABLE Milestone_Plans(
    milestonePlansID INT PRIMARY KEY AUTO_INCREMENT,
    opportunityID INT NOT NULL,
    productID INT NOT NULL,
    poID BIGINT NOT NULL,
    milestoneID INT NOT NULL,
    planType TINYINT NOT NULL,
    quarterName VARCHAR(30) NOT NULL,
    milestoneStartDate DATE,
    milestoneEndDate DATE,
    createdBy INT NOT NULL,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunityID) REFERENCES Opportunity(opportunityID),
    FOREIGN KEY (poID) REFERENCES PO(poID),
    FOREIGN KEY (productID) REFERENCES Product(productID),
    FOREIGN KEY (milestoneID) REFERENCES Milestone(milestoneID),
    FOREIGN KEY (createdBy) REFERENCES Users(userID)
);

-- Quarter broken into 3 monthly planned values
CREATE TABLE Milestone_Plan_Details(
    milestonePlanDetailsID INT PRIMARY KEY AUTO_INCREMENT,
    milestonePlansID INT NOT NULL,
    m1Value DOUBLE DEFAULT 0,
    m2Value DOUBLE DEFAULT 0,
    m3Value DOUBLE DEFAULT 0,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (milestonePlansID) REFERENCES Milestone_Plans(milestonePlansID)
);

-- Actual achieved quantity per month, tied to a specific plan_details row
CREATE TABLE Milestone_Records(
    milestoneRecordsID INT PRIMARY KEY AUTO_INCREMENT,
    planDetailsID INT NOT NULL,
    milestoneID INT NOT NULL,
    actualMonth DATE NOT NULL,
    actualQuantity DOUBLE NOT NULL,
    planQuantity DOUBLE NOT NULL,
    actualRemark TEXT,
    createdBy INT NOT NULL,
    updatedBy INT,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (planDetailsID) REFERENCES Milestone_Plan_Details(milestonePlanDetailsID),
    FOREIGN KEY (milestoneID) REFERENCES Milestone(milestoneID),
    FOREIGN KEY (createdBy) REFERENCES Users(userID)
);

CREATE TABLE Bulk_Uploads(
    bulkUploadsID INT PRIMARY KEY AUTO_INCREMENT,
    excelName VARCHAR(512) NOT NULL,
    excelPath VARCHAR(512) DEFAULT NULL,
    excelType TINYINT NOT NULL,
    excelStatus TINYINT NOT NULL DEFAULT 1 COMMENT '1 for upload, 2 for uploaded, 3 for delete',
    createdBy INT NOT NULL,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (createdBy) REFERENCES Users(userID)
);

CREATE TABLE Challenge_Plans(
    challengePlansID INT PRIMARY KEY AUTO_INCREMENT,
    planName TEXT NOT NULL,
    challengeID INT DEFAULT NULL,
    createdBy INT DEFAULT NULL,
    isActive BOOL NOT NULL DEFAULT 1,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (challengeID) REFERENCES Challenges(challengeID),
    FOREIGN KEY (createdBy) REFERENCES Users(userID)
);

CREATE TABLE User_Customers(
    userCustomerID INT PRIMARY KEY AUTO_INCREMENT,
    userID INT DEFAULT NULL,
    customerID INT DEFAULT NULL,
    isActive BOOL NOT NULL DEFAULT 1,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userID) REFERENCES Users(userID),
    FOREIGN KEY (customerID) REFERENCES Customers(customerID)
);

CREATE TABLE User_Divisions(
    userDivisionID INT PRIMARY KEY AUTO_INCREMENT,
    userID INT DEFAULT NULL,
    divisionID INT DEFAULT NULL,
    isActive BOOL NOT NULL DEFAULT 1,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userID) REFERENCES Users(userID),
    FOREIGN KEY (divisionID) REFERENCES Division(divisionID)
);

CREATE TABLE User_Activity_Log(
    logID INT PRIMARY KEY AUTO_INCREMENT,
    userID INT NOT NULL,
    tableName VARCHAR(100) NOT NULL,
    recordID BIGINT NOT NULL,
    action ENUM('CREATE','UPDATE','DELETE') NOT NULL,
    loggedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userID) REFERENCES Users(userID)
);