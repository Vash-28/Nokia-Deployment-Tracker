# Nokia-Deployment-Tracker Redesign

A full-stack web application developed during my Summer Internship at Nokia to redesign and modernize the internal Deployment Tracker portal. The system streamlines opportunity, purchase order, and milestone management through an intuitive workflow-driven interface, role-based access control, and enhanced deployment tracking capabilities.

---

## Project Overview

The Deployment Tracker is an internal portal used by project teams to monitor and manage deployment progress across multiple customers and divisions.

The application enables teams to:

* Create and manage opportunities
* Associate products and quantities
* Manage Purchase Orders (POs)
* Track milestone-level deployment progress
* Compare planned vs actual deployment quantities
* Monitor deployment status throughout the project lifecycle

The workflow follows the hierarchy:

**Accounts → Customers → Opportunities → Products → Purchase Orders → Milestones**

---

## Problem Statement

The legacy portal presented several usability and technical challenges:

* Spreadsheet-like interface with poor user experience
* No clear visibility into deployment stages
* Repetitive manual data entry
* Lack of role-based access control
* Limited analytics and reporting capabilities
* Database inconsistencies and technical debt

The goal of this project was to redesign the portal while preserving the existing business workflow.

---

## Key Features

### Drill-Down Navigation

Implemented a seamless workflow allowing users to navigate:

**Opportunities → Products → POs → Milestones**

This significantly reduces navigation complexity and improves data accessibility.

### Role-Based Access Control (RBAC)

Introduced multiple user roles:

* Super Admin
* Manager
* Project Team
* Viewer

Users can only access data relevant to their assigned customers and divisions.

### Milestone Tracking

* Track monthly planned and actual deployment quantities
* Monitor milestone progress across deployment stages
* Capture remarks and variance explanations
* Highlight deviations automatically

### Deployment Journey Visualization

Visual representation of deployment progress across stages:

**Hub → Warehouse → Site → Installation → Integration → RFS**

Allows users to quickly identify delays and bottlenecks.

### Analytics & Reporting (Planned)

* Division-level KPIs
* Planned vs Actual variance analysis
* PO expiry alerts
* Monthly activity reports
* Dashboard-based insights

---

## Technical Improvements

* Clean layered architecture (Model → Route → Service)
* Normalized relational database schema
* Consistent foreign key relationships
* Secure authentication and authorization
* Dynamic frontend using Fetch API
* Audit trail for transactional records
* Modular and scalable codebase

---

## Phase-wise Development

### Phase 1 (Completed)

* User Authentication
* Login with actual user information
* Opportunities listing page
* Product drill-down workflow
* Purchase Order management
* Milestone tracking layout

### Phase 2 (Planned)

* Analytics dashboard
* PO expiry alerts
* Bulk Excel upload
* Activity logs
* Export to Excel/PDF

### Phase 3 (Planned)

* Email notifications
* Smart autofill
* Automated monthly reports
* Mobile responsiveness

---

## Tech Stack

**Backend**

* Python
* Flask

**Frontend**

* HTML
* CSS
* JavaScript
* Bootstrap 5

**Database**

* SQL

**Additional Technologies**

* Fetch API
* DataTables

---

## Architecture

The application follows a layered architecture:

```text
Presentation Layer (HTML/CSS/JS)
            ↓
Routes Layer (Flask)
            ↓
Service Layer
            ↓
Model Layer
            ↓
Database
```

---

## Internship Context

This project was developed as part of my Summer Internship at Nokia, where I was responsible for understanding the existing Deployment Tracker, identifying usability and architectural challenges, and redesigning the system to improve user experience, efficiency, maintainability, and scalability.

---

## Future Enhancements

* Bulk milestone uploads via Excel
* Automated notifications and reminders
* Dashboard-driven analytics
* Enhanced audit logging
* Customer read-only portal access
* Responsive mobile interface

