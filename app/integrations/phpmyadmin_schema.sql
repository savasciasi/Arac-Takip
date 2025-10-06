-- phpMyAdmin compatible schema for the Fleet & Fine Management application
-- This script targets MySQL 8.x and mirrors the SQLite structure used by the app.
-- Import the file via phpMyAdmin's "Import" tab after creating an empty database.

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS vehicles (
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
  UNIQUE KEY uq_vehicles_plate (plate),
  KEY idx_vehicles_brand (brand)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS drivers (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  first_name VARCHAR(64) NOT NULL,
  last_name VARCHAR(64) NOT NULL,
  phone VARCHAR(48) NULL,
  license_no VARCHAR(64) NULL,
  notes TEXT NULL,
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at DATETIME NULL,
  deleted_by VARCHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_drivers_last_name (last_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fines (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NOT NULL,
  driver_id INT UNSIGNED NULL,
  fine_no VARCHAR(64) NOT NULL,
  date DATE NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  description TEXT NULL,
  status ENUM('OPEN','PAID','DISPUTED') NOT NULL DEFAULT 'OPEN',
  payment_date DATE NULL,
  attachments_json JSON NOT NULL DEFAULT (JSON_ARRAY()),
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at DATETIME NULL,
  deleted_by VARCHAR(64) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_fines_no (fine_no),
  KEY idx_fines_vehicle (vehicle_id),
  KEY idx_fines_driver (driver_id),
  KEY idx_fines_date (date),
  CONSTRAINT fk_fines_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE RESTRICT,
  CONSTRAINT fk_fines_driver FOREIGN KEY (driver_id) REFERENCES drivers (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS documents (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NULL,
  driver_id INT UNSIGNED NULL,
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
  KEY idx_documents_vehicle (vehicle_id),
  KEY idx_documents_driver (driver_id),
  CONSTRAINT fk_documents_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE,
  CONSTRAINT fk_documents_driver FOREIGN KEY (driver_id) REFERENCES drivers (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS vehicle_assignments (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NOT NULL,
  driver_id INT UNSIGNED NOT NULL,
  from_date DATE NOT NULL,
  to_date DATE NULL,
  notes TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_assignments_vehicle (vehicle_id),
  KEY idx_assignments_driver (driver_id),
  CONSTRAINT fk_assignments_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE,
  CONSTRAINT fk_assignments_driver FOREIGN KEY (driver_id) REFERENCES drivers (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS maintenance_reminders (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vehicle_id INT UNSIGNED NOT NULL,
  title VARCHAR(120) NOT NULL,
  next_date DATE NOT NULL,
  done TINYINT(1) NOT NULL DEFAULT 0,
  notes TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_maintenance_vehicle (vehicle_id),
  CONSTRAINT fk_maintenance_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS app_settings (
  `key` VARCHAR(64) NOT NULL,
  `value` TEXT NOT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS brand_backgrounds (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(8) NOT NULL,
  display_name VARCHAR(64) NOT NULL,
  asset_url VARCHAR(255) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_brand_backgrounds_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
