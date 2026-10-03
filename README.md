# ⚡ CanteenFlow — Smart Pre-Order & Queue Management System

> **Eliminating college canteen congestion with real-time pre-ordering, digital token tracking, and automated live counter voice announcements.**

---

## 📌 Overview

**CanteenFlow** is a modern full-stack web application designed for campus canteens to solve peak-hour recess overcrowding, reduce order wait times, and eliminate physical queuing at food counters. Built tailored for **100% Pure Veg college dining**, CanteenFlow offers students a seamless web ordering platform and provides kitchen staff with a real-time order fulfillment dashboard paired with a public TV counter display.

---

## ✨ Key Features

### 🍱 Student Ordering Portal
* **100% Pure Veg Menu Catalog:** Categorized dish selection (Snacks, Main Course, Beverages, Desserts) with instant search filtering.
* **Interactive Cart & Quantity Counter:** Real-time AJAX item counters (`- 1 +`), floating cart summary, and instant toast feedback without full page reloads.
* **Dish Lightbox Preview:** Full-screen high-definition dish photos with prep times, star ratings, and direct add-to-cart controls.
* **🎰 Food Roulette Decision Maker:** Integrated spin-wheel modal to help indecisive students pick what to eat.
* **🟢 Rush-O-Meter:** Dynamic wait time calculation based on active kitchen order volume.
* **🛡️ Anti-Spam Order Limit:** Smart cap preventing users from placing more than 2 concurrent active orders until previous meals are collected.

### 🍳 Kitchen & Staff Operations (`/staff/dashboard`)
* **Live Order Fulfillment Dashboard:** Real-time status update pipeline (`PLACED` ➔ `ACCEPTED` ➔ `PREPARING` ➔ `READY FOR PICKUP` ➔ `COLLECTED`).
* **Menu Stock Controls:** Instant toggle for item availability when kitchen stock runs out.
* **Sales Analytics & CSV Export:** Daily revenue tracking, top-selling dish breakdown, and downloadable CSV financial reports.

### 📺 Public TV Counter Display & Voice Announcer (`/queue`)
* **Real-Time Token Board:** Split-screen TV display for kitchen preparation vs. ready-for-pickup tokens.
* **🔊 Automated Text-to-Speech (TTS):** Instant audio chime and spoken voice announcement whenever an order status turns `READY`.
* **Zero-Lag State Sync:** Optimized MySQL autocommit and cache-busting JSON polling for instant state reflection across devices.

---

## 🎨 CanteenFlow Standard Design System

CanteenFlow follows an executive dark-first visual identity built for high readability and food platform aesthetics:

| Token Name | Color / Value | Usage |
| :--- | :--- | :--- |
| **Canteen Orange** | `#FF8A00` | Primary brand accent, CTAs, prices, and active states |
| **Midnight Charcoal** | `#0B0D10` | Main application background |
| **Graphite Surface** | `#191C21` | Cards, modals, panels, and header navigation |
| **Warm White** | `#F7F7F5` | Primary headings and prominent text |
| **Fresh Green** | `#25B879` | Success banners, ready status, and veg indicators |
| **Alert Red** | `#E65353` | Errors, cancellations, and logout controls |
| **Typography** | `Poppins` (Google Fonts) | Standard geometric brand typeface |

---

## 🛠️ Tech Stack

* **Backend:** Python 3.10+, Flask
* **Database:** MySQL Server, PyMySQL
* **Frontend:** HTML5, CSS3 (Custom Design System & Glassmorphic UI), JavaScript (ES6 AJAX, Web Speech API)
* **Authentication:** Werkzeug Password Hashing, Flask Session Management

---

## 📁 Repository Directory Structure

```text
Team-CodeBite-CanteenFlow/
├── static/
│   ├── css/
│   │   └── style.css            # Unified CanteenFlow Brand CSS
│   └── js/
│       └── app.js               # AJAX Cart, Toasts, Particles & Lightbox
├── templates/
│   ├── login.html               # Authentication Login View
│   ├── registeration.html       # Student Registration View
│   ├── menu.html                # Main Pure Veg Menu & Ordering
│   ├── cart.html                # Cart Review, Promo Code & Token Schedule
│   ├── my_orders.html           # Active & Past Order History
│   ├── order.html               # Live Ticket Status & Receipt
│   ├── queue.html               # Public TV Display & Voice Announcer
│   ├── staff_dashboard.html     # Kitchen Order Management
│   ├── staff_menu.html          # Menu Stock Controls
│   └── staff_analytics.html     # Revenue Summaries
├── app.py                       # Main Flask Application Entry Point
├── auth.py                      # Login, Registration & Session Blueprint
├── orders.py                    # Student Ordering & AJAX Blueprint
├── staff.py                     # Staff Operations & TV Queue Blueprint
├── db.py                        # Database Connection & Autocommit Handlers
├── config.py                    # Application & MySQL Configurations
├── domain.py                    # Business Logic Helpers
├── schema.sql                   # Relational Database Schema & Sample Data
├── .env                         # Environment Secrets & Credentials
├── .gitignore                   # Git Exclusion Standard
└── README.md                    # Project Documentation
