-- ==========================================================
-- EventEase - Full Event Management System Database Schema
-- Database: eventease_db
-- ==========================================================

CREATE DATABASE IF NOT EXISTS eventease_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE eventease_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(30) NULL,
    avatar VARCHAR(255) DEFAULT 'default-avatar.png',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_admin_username (username),
    INDEX idx_admin_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    slug VARCHAR(80) NOT NULL UNIQUE,
    description TEXT NULL,
    icon VARCHAR(60) DEFAULT 'fas fa-calendar-alt',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Events Table
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(220) NOT NULL UNIQUE,
    category_id INT NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(255) NOT NULL,
    venue_name VARCHAR(180) NOT NULL,
    event_date DATETIME NOT NULL,
    banner_image VARCHAR(255) NOT NULL,
    ticket_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total_tickets INT NOT NULL,
    available_tickets INT NOT NULL,
    status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
    created_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_event_slug (slug),
    INDEX idx_event_date (event_date),
    INDEX idx_event_category (category_id),
    INDEX idx_event_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Bookings Table
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_code VARCHAR(30) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    tickets_count INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    booking_status ENUM('confirmed', 'cancelled', 'attended') DEFAULT 'confirmed',
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancellation_date DATETIME NULL,
    notes TEXT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE RESTRICT,
    INDEX idx_booking_code (booking_code),
    INDEX idx_booking_user (user_id),
    INDEX idx_booking_event (event_id),
    INDEX idx_booking_status (booking_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(64) NOT NULL UNIQUE,
    booking_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) DEFAULT 'credit_card',
    payment_status ENUM('completed', 'refunded', 'failed') DEFAULT 'completed',
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    INDEX idx_payment_transaction (transaction_id),
    INDEX idx_payment_booking (booking_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
