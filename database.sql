-- ============================================
-- AI-Based Attendance System - Database Schema
-- Run this in phpMyAdmin (WAMP) or MySQL CLI
-- ============================================

CREATE DATABASE IF NOT EXISTS attendance_system;
USE attendance_system;

-- ------------------------------------------------
-- Table: admin  (login credentials for admin panel)
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL   -- stored as SHA-256 hash
);

-- Default admin -> username: admin | password: admin123
INSERT INTO admin (username, password)
VALUES ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a')
ON DUPLICATE KEY UPDATE username = username;

-- ------------------------------------------------
-- Table: students
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    course VARCHAR(100),
    semester VARCHAR(20),
    email VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------
-- Table: attendance
-- ------------------------------------------------
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('Present', 'Absent') NOT NULL DEFAULT 'Absent',
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (student_id, attendance_date)
);

-- ------------------------------------------------
-- Sample data (optional - for testing)
-- ------------------------------------------------
INSERT INTO students (roll_no, name, course, semester, email, phone) VALUES
('R001', 'Aarav Sharma', 'B.Tech CSE', '5', 'aarav@example.com', '9000000001'),
('R002', 'Priya Patel', 'B.Tech CSE', '5', 'priya@example.com', '9000000002'),
('R003', 'Rohan Mehta', 'B.Tech IT', '5', 'rohan@example.com', '9000000003'),
('R004', 'Sneha Iyer', 'B.Tech CSE', '5', 'sneha@example.com', '9000000004'),
('R005', 'Karan Verma', 'B.Tech IT', '5', 'karan@example.com', '9000000005');
