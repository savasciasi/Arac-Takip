-- ======================================================================
-- Single-DB schema for KNK & NKK (table prefixes: knk_*, nkk_*)
-- Import into a SELECTED database in phpMyAdmin (no CREATE DATABASE / USE)
-- Charset/Collation: utf8mb4 / utf8mb4_unicode_ci
-- ======================================================================

SET NAMES utf8mb4;
SET sql_mode = '';
SET FOREIGN_KEY_CHECKS = 0;

-- ==============================
-- KNK TABLES
-- ==============================

-- Drop in safe order (children first)
DROP TABLE IF EXISTS knk_documents;
DROP TABLE IF EXISTS knk_vehicle_assignments;
DROP TABLE IF EXISTS knk_maintenance_reminders;
DROP TABLE IF EXISTS knk_fines;
DROP TABLE IF EXISTS knk_drivers;
DROP TABLE IF EXISTS knk_vehicles;
DROP TABLE IF EXISTS knk_app_settings;

-- Vehicles (KNK)
CREATE TABLE knk_vehicles (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  plate VARCHAR(32) NOT NULL,
  brand VARCHAR(64) NOT NULL,
  model VARCHAR(64) NOT NULL,
  year SMALLINT NULL,
  notes TEXT NULL,
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at DATETIME NULL,
  deleted_by VARCHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_knk_vehicles_plate (plate),
  KEY idx_knk_vehicles_brand (brand)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Drivers (KNK)
CREATE TABLE knk_drivers (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  first_name VARCHAR(64) NOT NULL,
  last_name  VARCHAR(64) NOT NULL,
  phone      VARCHAR(48) NULL,
  license_no VARCHAR(64) NULL,
  notes TEXT NULL,
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at DATETIME NULL,
  deleted_by VARCHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_knk_drivers_last_name (last_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Fines (KNK)
CREATE TABLE knk_fines (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NOT NULL,
  driver_id  INT UNSIGNED NULL,
  fine_no VARCHAR(64) NOT NULL,
  `date` DATE NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  description TEXT NULL,
  status ENUM('OPEN','PAID','DISPUTED') NOT NULL DEFAULT 'OPEN',
  payment_date DATE NULL,
  attachments_json TEXT NOT NULL DEFAULT '[]',
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at DATETIME NULL,
  deleted_by VARCHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_knk_fines_no (fine_no),
  KEY idx_knk_fines_vehicle (vehicle_id),
  KEY idx_knk_fines_driver  (driver_id),
  KEY idx_knk_fines_date    (`date`),
  CONSTRAINT fk_knk_fines_vehicle FOREIGN KEY (vehicle_id)
    REFERENCES knk_vehicles (id) ON DELETE RESTRICT,
  CONSTRAINT fk_knk_fines_driver FOREIGN KEY (driver_id)
    REFERENCES knk_drivers (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Documents (KNK)
CREATE TABLE knk_documents (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NULL,
  driver_id  INT UNSIGNED NULL,
  title VARCHAR(120) NOT NULL,
  path VARCHAR(255) NOT NULL,
  preview_path VARCHAR(255) NULL,
  tags VARCHAR(255) NULL,
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at DATETIME NULL,
  deleted_by VARCHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_knk_documents_vehicle (vehicle_id),
  KEY idx_knk_documents_driver  (driver_id),
  CONSTRAINT fk_knk_documents_vehicle FOREIGN KEY (vehicle_id)
    REFERENCES knk_vehicles (id) ON DELETE CASCADE,
  CONSTRAINT fk_knk_documents_driver FOREIGN KEY (driver_id)
    REFERENCES knk_drivers (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Vehicle Assignments (KNK)
CREATE TABLE knk_vehicle_assignments (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NOT NULL,
  driver_id  INT UNSIGNED NOT NULL,
  from_date DATE NOT NULL,
  to_date   DATE NULL,
  notes TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_knk_assignments_vehicle (vehicle_id),
  KEY idx_knk_assignments_driver  (driver_id),
  CONSTRAINT fk_knk_assignments_vehicle FOREIGN KEY (vehicle_id)
    REFERENCES knk_vehicles (id) ON DELETE CASCADE,
  CONSTRAINT fk_knk_assignments_driver FOREIGN KEY (driver_id)
    REFERENCES knk_drivers (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Maintenance Reminders (KNK)
CREATE TABLE knk_maintenance_reminders (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NOT NULL,
  title VARCHAR(120) NOT NULL,
  next_date DATE NOT NULL,
  done TINYINT(1) NOT NULL DEFAULT 0,
  notes TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_knk_maintenance_vehicle (vehicle_id),
  CONSTRAINT fk_knk_maintenance_vehicle FOREIGN KEY (vehicle_id)
    REFERENCES knk_vehicles (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- App Settings (KNK)
CREATE TABLE knk_app_settings (
  `key` VARCHAR(64) NOT NULL,
  `value` TEXT NOT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==============================
-- NKK TABLES
-- ==============================

-- Drop in safe order (children first)
DROP TABLE IF EXISTS nkk_documents;
DROP TABLE IF EXISTS nkk_vehicle_assignments;
DROP TABLE IF EXISTS nkk_maintenance_reminders;
DROP TABLE IF EXISTS nkk_fines;
DROP TABLE IF EXISTS nkk_drivers;
DROP TABLE IF EXISTS nkk_vehicles;
DROP TABLE IF EXISTS nkk_app_settings;

-- Vehicles (NKK)
CREATE TABLE nkk_vehicles (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  plate VARCHAR(32) NOT NULL,
  brand VARCHAR(64) NOT NULL,
  model VARCHAR(64) NOT NULL,
  year SMALLINT NULL,
  notes TEXT NULL,
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at DATETIME NULL,
  deleted_by VARCHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_nkk_vehicles_plate (plate),
  KEY idx_nkk_vehicles_brand (brand)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Drivers (NKK)
CREATE TABLE nkk_drivers (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  first_name VARCHAR(64) NOT NULL,
  last_name  VARCHAR(64) NOT NULL,
  phone      VARCHAR(48) NULL,
  license_no VARCHAR(64) NULL,
  notes TEXT NULL,
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at DATETIME NULL,
  deleted_by VARCHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_nkk_drivers_last_name (last_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Fines (NKK)
CREATE TABLE nkk_fines (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NOT NULL,
  driver_id  INT UNSIGNED NULL,
  fine_no VARCHAR(64) NOT NULL,
  `date` DATE NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  description TEXT NULL,
  status ENUM('OPEN','PAID','DISPUTED') NOT NULL DEFAULT 'OPEN',
  payment_date DATE NULL,
  attachments_json TEXT NOT NULL DEFAULT '[]',
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at DATETIME NULL,
  deleted_by VARCHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_nkk_fines_no (fine_no),
  KEY idx_nkk_fines_vehicle (vehicle_id),
  KEY idx_nkk_fines_driver  (driver_id),
  KEY idx_nkk_fines_date    (`date`),
  CONSTRAINT fk_nkk_fines_vehicle FOREIGN KEY (vehicle_id)
    REFERENCES nkk_vehicles (id) ON DELETE RESTRICT,
  CONSTRAINT fk_nkk_fines_driver FOREIGN KEY (driver_id)
    REFERENCES nkk_drivers (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Documents (NKK)
CREATE TABLE nkk_documents (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NULL,
  driver_id  INT UNSIGNED NULL,
  title VARCHAR(120) NOT NULL,
  path VARCHAR(255) NOT NULL,
  preview_path VARCHAR(255) NULL,
  tags VARCHAR(255) NULL,
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at DATETIME NULL,
  deleted_by VARCHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_nkk_documents_vehicle (vehicle_id),
  KEY idx_nkk_documents_driver  (driver_id),
  CONSTRAINT fk_nkk_documents_vehicle FOREIGN KEY (vehicle_id)
    REFERENCES nkk_vehicles (id) ON DELETE CASCADE,
  CONSTRAINT fk_nkk_documents_driver FOREIGN KEY (driver_id)
    REFERENCES nkk_drivers (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Vehicle Assignments (NKK)
CREATE TABLE nkk_vehicle_assignments (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NOT NULL,
  driver_id  INT UNSIGNED NOT NULL,
  from_date DATE NOT NULL,
  to_date   DATE NULL,
  notes TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_nkk_assignments_vehicle (vehicle_id),
  KEY idx_nkk_assignments_driver  (driver_id),
  CONSTRAINT fk_nkk_assignments_vehicle FOREIGN KEY (vehicle_id)
    REFERENCES nkk_vehicles (id) ON DELETE CASCADE,
  CONSTRAINT fk_nkk_assignments_driver FOREIGN KEY (driver_id)
    REFERENCES nkk_drivers (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Maintenance Reminders (NKK)
CREATE TABLE nkk_maintenance_reminders (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NOT NULL,
  title VARCHAR(120) NOT NULL,
  next_date DATE NOT NULL,
  done TINYINT(1) NOT NULL DEFAULT 0,
  notes TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_nkk_maintenance_vehicle (vehicle_id),
  CONSTRAINT fk_nkk_maintenance_vehicle FOREIGN KEY (vehicle_id)
    REFERENCES nkk_vehicles (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- App Settings (NKK)
CREATE TABLE nkk_app_settings (
  `key` VARCHAR(64) NOT NULL,
  `value` TEXT NOT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
