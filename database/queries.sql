
INSERT INTO Accounts (accountName, account_details) VALUES
('Account Alpha', 'Strategic account for smart agriculture solutions'),
('Account Beta', 'Account for autonomous logistics initiatives'),
('Account Gamma', 'Renewable energy analytics account'),
('Account Delta', 'Industrial robotics solutions account');


INSERT INTO Division (divisionName) VALUES
('Division 101'),
('Division 202'),
('Division 303'),
('Division 404'),
('Division 505');


INSERT INTO Customers (accountID, customerName, customerDetails) VALUES
(1, 'GreenHarvest Cooperative', 'Large scale indoor farming consortium'),
(1, 'SunBloom Foods', 'Organic food processing company'),
(2, 'SkyCart Logistics', 'Autonomous delivery startup'),
(2, 'RapidHaul Systems', 'Warehouse automation provider'),
(3, 'NovaGrid Energy', 'Solar infrastructure operator'),
(3, 'EcoCurrent Utilities', 'Smart utility management firm'),
(4, 'RoboForge Industries', 'Industrial robotics manufacturer'),
(4, 'Titan Assembly Works', 'Advanced manufacturing facility');

INSERT INTO Companies
(companyName, companyDetails, billingAddress, contactPerson, contactNumber, identityCode, isActive)
VALUES
('Apex Digital Labs', 'Software consulting company', '17 Horizon Street, Arcadia City', 'Emma Hayes', '+1-555-1001', 'ADL-001', 1),
('BluePeak Analytics', 'Business intelligence provider', '89 Summit Avenue, Vertex Town', 'Liam Carter', '+1-555-1002', 'BPA-002', 1),
('Quantum River Systems', 'Data platform company', '4 Innovation Plaza, Rivergate', 'Sophia Reed', '+1-555-1003', 'QRS-003', 1);

INSERT INTO Product (productName, productUOM, productHSN) VALUES
('HydroSense Pod', 'EA', 'HSN9001'),
('AgriVision Camera', 'EA', 'HSN9002'),
('AutoDock Station', 'EA', 'HSN9003'),
('FleetBrain Controller', 'EA', 'HSN9004'),
('SolarPulse Monitor', 'EA', 'HSN9005'),
('EnergyFlow Gateway', 'EA', 'HSN9006'),
('ForgeBot Arm', 'EA', 'HSN9007'),
('Precision Grip Unit', 'EA', 'HSN9008');


INSERT INTO BusinessUnit (divisionID, productID) VALUES
(1,1),
(1,2),
(2,3),
(2,4),
(3,5),
(3,6),
(4,7),
(5,8);

INSERT INTO Users
(companyID, emailAddress, userPassword, userName, mobile, userRole, isSuperAdmin)
VALUES
(1, 'admin@apexlabs.demo', '$2b$dummyhash1', 'Admin User', '9000000001', 1, 1),
(1, 'sarah@apexlabs.demo', '$2b$dummyhash2', 'Sarah Kim', '9000000002', 2, 0),
(2, 'michael@bluepeak.demo', '$2b$dummyhash3', 'Michael Stone', '9000000003', 2, 0),
(2, 'olivia@bluepeak.demo', '$2b$dummyhash4', 'Olivia Turner', '9000000004', 3, 0),
(3, 'daniel@qriver.demo', '$2b$dummyhash5', 'Daniel Brooks', '9000000005', 2, 0);


INSERT INTO Milestone
(milestoneName, milestoneNickname, milestoneDataID, milestonePriority, milestoneType)
VALUES
('Design Approval', 'DESIGN', 'MS001', 1, 1),
('Prototype Delivery', 'PROTO', 'MS002', 2, 1),
('Pilot Deployment', 'PILOT', 'MS003', 3, 1),
('Field Validation', 'VALID', 'MS004', 4, 2),
('Production Release', 'RELEASE', 'MS005', 5, 2);


INSERT INTO Challenges (challengeName, createdBy) VALUES
('Supply Chain Delays', 1),
('Component Certification Pending', 2),
('Customer Site Access Restrictions', 3);




