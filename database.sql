-- Create database
CREATE DATABASE IF NOT EXISTS college_fee_management;
USE college_fee_management;

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Fee records table
CREATE TABLE IF NOT EXISTS fee_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    admission_number VARCHAR(50) NOT NULL,
    student_section VARCHAR(10),
    student_group VARCHAR(50) NOT NULL,
    semester VARCHAR(20) NOT NULL,
    address TEXT,
    managerial_convener ENUM('Management', 'College') NOT NULL,
    total_student VARCHAR(20),
    fixed_fee DECIMAL(10, 2),
    tuition_fee DECIMAL(10, 2),
    bus_fee DECIMAL(10, 2),
    pending_bus_fee DECIMAL(10, 2),
    practical_fee DECIMAL(10, 2),
    university_fee DECIMAL(10, 2),
    stationary_fee DECIMAL(10, 2),
    internship_fee DECIMAL(10, 2),
    viva_fee DECIMAL(10, 2),
    total_amount DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(10, 2) DEFAULT 0,
    paid_amount DECIMAL(10, 2) NOT NULL,
    balance_amount DECIMAL(10, 2) NOT NULL,
    date DATE NOT NULL,
    bill_number VARCHAR(50) NOT NULL,
    pending_balance DECIMAL(10, 2),
    class VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, password) VALUES 
('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW');