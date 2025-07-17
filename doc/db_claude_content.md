





# Sindicato Database Schema Reference

## Complete Tables, Columns & Foreign Keys Listing

### 1. users
**Columns:**
- `id` SERIAL PRIMARY KEY
- `code` VARCHAR(20) NOT NULL UNIQUE
- `password` VARCHAR(150) NOT NULL
- `first_name` VARCHAR(150) NOT NULL
- `last_name` VARCHAR(150) NOT NULL
- `email` VARCHAR(150) NOT NULL UNIQUE
- `phone` VARCHAR(20) CHECK (phone ~ '^\+?[0-9\s\-\(\)]+$')
- `default_group_id` INTEGER NOT NULL
- `is_active` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `default_group_id` → `groups(id)`

---

### 2. groups
**Columns:**
- `id` SERIAL PRIMARY KEY
- `code` VARCHAR(20) NOT NULL UNIQUE
- `title` VARCHAR(150) NOT NULL
- `is_active` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- None

---

### 3. roles
**Columns:**
- `id` SERIAL PRIMARY KEY
- `code` VARCHAR(20) NOT NULL UNIQUE
- `title` VARCHAR(150) NOT NULL
- `is_active` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- None

---

### 4. role_permissions
**Columns:**
- `id` SERIAL PRIMARY KEY
- `role_id` INTEGER NOT NULL
- `permission` VARCHAR(50) NOT NULL
- `operation` VARCHAR(50) NOT NULL
- `level` VARCHAR(1)
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- UNIQUE (role_id, permission, operation)

**Foreign Keys:**
- `role_id` → `roles(id)` ON DELETE CASCADE

---

### 5. user_groups
**Columns:**
- `user_id` INTEGER NOT NULL
- `group_id` INTEGER NOT NULL
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- PRIMARY KEY (user_id, group_id)

**Foreign Keys:**
- `user_id` → `users(id)` ON DELETE CASCADE
- `group_id` → `groups(id)` ON DELETE CASCADE

---

### 6. user_roles
**Columns:**
- `user_id` INTEGER NOT NULL
- `role_id` INTEGER NOT NULL
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- PRIMARY KEY (user_id, role_id)

**Foreign Keys:**
- `user_id` → `users(id)` ON DELETE CASCADE
- `role_id` → `roles(id)` ON DELETE CASCADE

---

### 7. audit_log
**Columns:**
- `id` BIGSERIAL PRIMARY KEY
- `table_name` VARCHAR(100) NOT NULL
- `record_id` INTEGER NOT NULL
- `operation` VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE'))
- `user_id` INTEGER
- `changed_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `old_values` JSONB
- `new_values` JSONB
- `ip_address` INET
- `user_agent` TEXT

**Foreign Keys:**
- `user_id` → `users(id)`

---

### 8. provinces
**Columns:**
- `id` SERIAL PRIMARY KEY
- `code` VARCHAR(2) NOT NULL UNIQUE
- `name` VARCHAR(100) NOT NULL

**Foreign Keys:**
- None

---

### 9. municipalities
**Columns:**
- `id` SERIAL PRIMARY KEY
- `name` VARCHAR(200) NOT NULL
- `province_id` INTEGER NOT NULL
- UNIQUE (name, province_id)

**Foreign Keys:**
- `province_id` → `provinces(id)`

---

### 10. addresses
**Columns:**
- `id` SERIAL PRIMARY KEY
- `street_name` VARCHAR(200)
- `street_number` VARCHAR(20)
- `floor` VARCHAR(10)
- `door` VARCHAR(10)
- `complement` VARCHAR(50)
- `postal_code` VARCHAR(10)
- `municipality_id` INTEGER
- `google_place_id` VARCHAR(100)
- `full_address` TEXT NOT NULL
- `coordinates` POINT
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `municipality_id` → `municipalities(id)`

---

### 11. lookup_categories
**Columns:**
- `id` SERIAL PRIMARY KEY
- `code` VARCHAR(50) NOT NULL UNIQUE
- `name` VARCHAR(100) NOT NULL
- `description` TEXT

**Foreign Keys:**
- None

---

### 12. lookup_values
**Columns:**
- `id` SERIAL PRIMARY KEY
- `category_id` INTEGER NOT NULL
- `code` VARCHAR(50) NOT NULL
- `name` VARCHAR(200) NOT NULL
- `name_es` VARCHAR(200)
- `display_order` INTEGER DEFAULT 0
- `is_active` BOOLEAN NOT NULL DEFAULT TRUE
- `metadata` JSONB
- UNIQUE (category_id, code)

**Foreign Keys:**
- `category_id` → `lookup_categories(id)`

---

### 13. persons
**Columns:**
- `id` SERIAL PRIMARY KEY
- `tax_id` VARCHAR(20) UNIQUE CHECK (tax_id ~ '^[A-Z0-9]{8,20}$')
- `gender` CHAR(1) CHECK (gender IN ('M', 'F', 'X'))
- `first_name` VARCHAR(100) NOT NULL
- `last_name` VARCHAR(100)
- `email` VARCHAR(150)
- `phone` VARCHAR(20) CHECK (phone ~ '^\+?[0-9\s\-\(\)]+$')
- `wants_newsletter` BOOLEAN DEFAULT FALSE
- `wants_communications` BOOLEAN DEFAULT TRUE
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- None

---

### 14. collectives
**Columns:**
- `id` SERIAL PRIMARY KEY
- `name` VARCHAR(200) NOT NULL
- `description` TEXT
- `email` VARCHAR(150) NOT NULL
- `phone` VARCHAR(20)
- `contact_person` VARCHAR(200)
- `contact_phone` VARCHAR(20)
- `allows_payments` BOOLEAN DEFAULT FALSE
- `allows_advisories` BOOLEAN DEFAULT FALSE
- `allows_direct_debit` BOOLEAN DEFAULT FALSE
- `default_fee` DECIMAL(10, 2)
- `serial_prefix` VARCHAR(8)
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- None

---

### 15. union_sections
**Columns:**
- `id` SERIAL PRIMARY KEY
- `name` VARCHAR(100) NOT NULL UNIQUE
- `postal_codes` TEXT[]
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- None

---

### 16. commissions
**Columns:**
- `id` SERIAL PRIMARY KEY
- `name` VARCHAR(100) NOT NULL UNIQUE
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- None

---

### 17. members
**Columns:**
- `id` SERIAL PRIMARY KEY
- `person_id` INTEGER NOT NULL
- `collective_id` INTEGER
- `member_type` VARCHAR(20) NOT NULL CHECK (member_type IN ('affiliate', 'non_affiliate', 'sympathizer'))
- `status` VARCHAR(20) NOT NULL CHECK (status IN ('active', 'inactive', 'suspended', 'cancelled'))
- `joined_at` DATE NOT NULL
- `left_at` DATE
- `origin_id` INTEGER
- `participation_level_id` INTEGER
- `union_section_id` INTEGER
- `commission_id` INTEGER
- `payment_method` CHAR(1) CHECK (payment_method IN ('B', 'E', 'T'))
- `payment_frequency` CHAR(1) CHECK (payment_frequency IN ('M', 'T', 'S', 'A'))
- `bank_account` VARCHAR(24) CHECK (bank_account ~ '^[A-Z]{2}[0-9]{22}$')
- `fee_amount` DECIMAL(10, 2)
- `last_followup_date` DATE
- `followup_type_id` INTEGER
- `notes` TEXT
- `internal_comments` TEXT
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- CONSTRAINT chk_member_payment CHECK ((member_type = 'affiliate' AND payment_method IS NOT NULL) OR (member_type != 'affiliate' AND payment_method IS NULL))

**Foreign Keys:**
- `person_id` → `persons(id)`
- `collective_id` → `collectives(id)`
- `origin_id` → `lookup_values(id)`
- `participation_level_id` → `lookup_values(id)`
- `union_section_id` → `union_sections(id)`
- `commission_id` → `commissions(id)`
- `followup_type_id` → `lookup_values(id)`

---

### 18. property_networks
**Columns:**
- `id` SERIAL PRIMARY KEY
- `name` VARCHAR(100) NOT NULL UNIQUE
- `description` TEXT
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- None

---

### 19. companies
**Columns:**
- `id` SERIAL PRIMARY KEY
- `tax_id` VARCHAR(20) UNIQUE CHECK (tax_id ~ '^[A-Z0-9]{8,20}$')
- `name` VARCHAR(200) NOT NULL
- `is_api` BOOLEAN DEFAULT FALSE
- `website` VARCHAR(200)
- `email` VARCHAR(150)
- `phone` VARCHAR(20)
- `address_id` INTEGER
- `network_id` INTEGER
- `description` TEXT
- `info_url` VARCHAR(200)
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `address_id` → `addresses(id)`
- `network_id` → `property_networks(id)`

---

### 20. buildings
**Columns:**
- `id` SERIAL PRIMARY KEY
- `address_id` INTEGER NOT NULL
- `status_id` INTEGER
- `construction_year` INTEGER CHECK (construction_year BETWEEN 1800 AND EXTRACT(YEAR FROM CURRENT_DATE))
- `total_homes` INTEGER CHECK (total_homes >= 0)
- `total_shops` INTEGER CHECK (total_shops >= 0)
- `has_vertical_property` BOOLEAN
- `has_elevator` BOOLEAN
- `has_parking` BOOLEAN
- `is_empty` BOOLEAN DEFAULT FALSE
- `empty_since` DATE
- `surface_m2` INTEGER CHECK (surface_m2 > 0)
- `owner_company_id` INTEGER
- `api_company_id` INTEGER
- `ownership_last_updated` DATE
- `is_hpo` BOOLEAN DEFAULT FALSE
- `hpo_end_date` DATE
- `observations` TEXT
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `address_id` → `addresses(id)`
- `status_id` → `lookup_values(id)`
- `owner_company_id` → `companies(id)`
- `api_company_id` → `companies(id)`

---

### 21. building_groups
**Columns:**
- `id` SERIAL PRIMARY KEY
- `name` VARCHAR(200) NOT NULL UNIQUE
- `owner_company_id` INTEGER NOT NULL
- `api_company_id` INTEGER
- `ownership_last_updated` DATE
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `owner_company_id` → `companies(id)`
- `api_company_id` → `companies(id)`

---

### 22. building_group_members
**Columns:**
- `building_group_id` INTEGER NOT NULL
- `building_id` INTEGER NOT NULL
- PRIMARY KEY (building_group_id, building_id)

**Foreign Keys:**
- `building_group_id` → `building_groups(id)` ON DELETE CASCADE
- `building_id` → `buildings(id)` ON DELETE CASCADE

---

### 23. housing_units
**Columns:**
- `id` SERIAL PRIMARY KEY
- `building_id` INTEGER NOT NULL
- `address_id` INTEGER NOT NULL
- `floor` VARCHAR(10)
- `door` VARCHAR(10)
- `status_id` INTEGER
- `surface_m2` INTEGER CHECK (surface_m2 > 0)
- `bedrooms` INTEGER CHECK (bedrooms >= 0)
- `has_habitability_cert` BOOLEAN
- `has_energy_cert` BOOLEAN
- `is_empty` BOOLEAN DEFAULT FALSE
- `empty_since` DATE
- `owner_company_id` INTEGER
- `api_company_id` INTEGER
- `ownership_last_updated` DATE
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `building_id` → `buildings(id)`
- `address_id` → `addresses(id)`
- `status_id` → `lookup_values(id)`
- `owner_company_id` → `companies(id)`
- `api_company_id` → `companies(id)`

---

### 24. rental_contracts
**Columns:**
- `id` SERIAL PRIMARY KEY
- `member_id` INTEGER NOT NULL
- `housing_unit_id` INTEGER
- `regime` CHAR(1) NOT NULL CHECK (regime IN ('P', 'L', 'H', 'A'))
- `regime_other` VARCHAR(50)
- `is_normalized_address` BOOLEAN DEFAULT TRUE
- `custom_address` TEXT
- `start_date` DATE NOT NULL
- `is_indefinite` BOOLEAN DEFAULT FALSE
- `duration_months` INTEGER CHECK (duration_months > 0)
- `extensions` INTEGER DEFAULT 0
- `monthly_rent` DECIMAL(10, 2) CHECK (monthly_rent >= 0)
- `inhabitants` INTEGER CHECK (inhabitants > 0)
- `monthly_income` DECIMAL(10, 2) CHECK (monthly_income >= 0)
- `is_active` BOOLEAN DEFAULT TRUE
- `end_date` DATE
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- CONSTRAINT chk_contract_dates CHECK (end_date IS NULL OR end_date >= start_date)
- CONSTRAINT chk_regime_other CHECK ((regime = 'A' AND regime_other IS NOT NULL) OR (regime != 'A' AND regime_other IS NULL))

**Foreign Keys:**
- `member_id` → `members(id)`
- `housing_unit_id` → `housing_units(id)`

---

### 25. conflicts
**Columns:**
- `id` SERIAL PRIMARY KEY
- `status` VARCHAR(20) NOT NULL CHECK (status IN ('open', 'hibernating', 'closed'))
- `scope` CHAR(1) NOT NULL CHECK (scope IN ('I', 'C', 'B'))
- `affected_member_id` INTEGER
- `affected_building_id` INTEGER
- `affected_building_group_id` INTEGER
- `affected_network_id` INTEGER
- `cause_id` INTEGER NOT NULL
- `delegate_user_id` INTEGER
- `opened_at` DATE NOT NULL
- `last_assembly_at` DATE
- `hibernated_at` DATE
- `closed_at` DATE
- `next_eviction_at` DATE
- `actions_taken` JSONB DEFAULT '{}'
- `resolution_id` INTEGER
- `resolution_result` CHAR(1) CHECK (resolution_result IN ('W', 'L', 'P'))
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- CONSTRAINT chk_conflict_scope CHECK ((scope = 'I' AND affected_member_id IS NOT NULL) OR (scope = 'C' AND affected_building_id IS NOT NULL) OR (scope = 'B' AND (affected_building_group_id IS NOT NULL OR affected_network_id IS NOT NULL)))

**Foreign Keys:**
- `affected_member_id` → `members(id)`
- `affected_building_id` → `buildings(id)`
- `affected_building_group_id` → `building_groups(id)`
- `affected_network_id` → `property_networks(id)`
- `cause_id` → `lookup_values(id)`
- `delegate_user_id` → `users(id)`
- `resolution_id` → `lookup_values(id)`

---

### 26. conflict_delegates
**Columns:**
- `conflict_id` INTEGER NOT NULL
- `member_id` INTEGER NOT NULL
- `assigned_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- PRIMARY KEY (conflict_id, member_id)

**Foreign Keys:**
- `conflict_id` → `conflicts(id)` ON DELETE CASCADE
- `member_id` → `members(id)`

---

### 27. conflict_negotiations
**Columns:**
- `id` SERIAL PRIMARY KEY
- `conflict_id` INTEGER NOT NULL
- `negotiation_date` DATE NOT NULL
- `status` TEXT NOT NULL
- `tasks` TEXT
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `conflict_id` → `conflicts(id)`

---

### 28. technicians
**Columns:**
- `id` SERIAL PRIMARY KEY
- `name` VARCHAR(200) NOT NULL UNIQUE
- `email` VARCHAR(150) NOT NULL
- `phone` VARCHAR(20)
- `specialty_id` INTEGER NOT NULL
- `is_active` BOOLEAN DEFAULT TRUE
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `specialty_id` → `lookup_values(id)`

---

### 29. advisories
**Columns:**
- `id` SERIAL PRIMARY KEY
- `member_id` INTEGER
- `type_id` INTEGER NOT NULL
- `technician_id` INTEGER
- `status` VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled'))
- `contact_date` DATE
- `advisory_date` DATE
- `completion_date` DATE
- `description` TEXT
- `internal_comments` TEXT
- `result_id` INTEGER
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `member_id` → `members(id)`
- `type_id` → `lookup_values(id)`
- `technician_id` → `technicians(id)`
- `result_id` → `lookup_values(id)`

---

### 30. legal_services
**Columns:**
- `id` SERIAL PRIMARY KEY
- `member_id` INTEGER NOT NULL
- `type_id` INTEGER NOT NULL
- `technician_id` INTEGER
- `status` VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled'))
- `service_date` DATE
- `price` DECIMAL(10, 2)
- `description` TEXT
- `internal_comments` TEXT
- `result` CHAR(1) CHECK (result IN ('W', 'L', 'P', 'O'))
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `member_id` → `members(id)`
- `type_id` → `lookup_values(id)`
- `technician_id` → `technicians(id)`

---

### 31. documents
**Columns:**
- `id` SERIAL PRIMARY KEY
- `file_name` VARCHAR(400) NOT NULL
- `file_hash` VARCHAR(100) NOT NULL UNIQUE
- `title` VARCHAR(200) NOT NULL
- `description` TEXT
- `mime_type` VARCHAR(100) NOT NULL
- `file_size` BIGINT NOT NULL CHECK (file_size > 0)
- `is_public` BOOLEAN DEFAULT FALSE
- `is_image` BOOLEAN DEFAULT FALSE
- `image_width` INTEGER
- `image_height` INTEGER
- `uploaded_by` INTEGER NOT NULL
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `uploaded_by` → `users(id)`

---

### 32. document_associations
**Columns:**
- `id` SERIAL PRIMARY KEY
- `document_id` INTEGER NOT NULL
- `entity_type` VARCHAR(50) NOT NULL
- `entity_id` INTEGER NOT NULL
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
- UNIQUE (document_id, entity_type, entity_id)

**Foreign Keys:**
- `document_id` → `documents(id)` ON DELETE CASCADE

---

### 33. direct_debit_batches
**Columns:**
- `id` SERIAL PRIMARY KEY
- `issue_date` DATE NOT NULL
- `file_document_id` INTEGER
- `total_amount` DECIMAL(12, 2)
- `total_receipts` INTEGER
- `status` VARCHAR(20) DEFAULT 'pending'
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `file_document_id` → `documents(id)`

---

### 34. member_receipts
**Columns:**
- `id` SERIAL PRIMARY KEY
- `member_id` INTEGER NOT NULL
- `batch_id` INTEGER
- `amount` DECIMAL(10, 2) NOT NULL
- `concept` VARCHAR(200)
- `due_date` DATE NOT NULL
- `paid_date` DATE
- `status` VARCHAR(20) NOT NULL DEFAULT 'pending'
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `member_id` → `members(id)`
- `batch_id` → `direct_debit_batches(id)`

---

### 35. app_settings
**Columns:**
- `id` SERIAL PRIMARY KEY
- `section` VARCHAR(50) NOT NULL
- `key` VARCHAR(100) NOT NULL
- `value` TEXT
- `description` TEXT
- UNIQUE (section, key)

**Foreign Keys:**
- None

---

### 36. user_preferences
**Columns:**
- `user_id` INTEGER NOT NULL
- `page_code` VARCHAR(100) NOT NULL
- `preference_key` VARCHAR(100) NOT NULL
- `preference_value` TEXT
- PRIMARY KEY (user_id, page_code, preference_key)

**Foreign Keys:**
- `user_id` → `users(id)` ON DELETE CASCADE

---

### 37. import_templates
**Columns:**
- `id` SERIAL PRIMARY KEY
- `import_type` VARCHAR(50) NOT NULL
- `name` VARCHAR(100) NOT NULL
- `content` TEXT
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- None

---

### 38. application_forms
**Columns:**
- `id` SERIAL PRIMARY KEY
- `form_type` VARCHAR(20) NOT NULL DEFAULT 'membership'
- `status` VARCHAR(20) NOT NULL DEFAULT 'pending'
- `form_data` JSONB NOT NULL
- `processed_at` TIMESTAMP
- `processed_by` INTEGER
- `processing_notes` TEXT
- `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

**Foreign Keys:**
- `processed_by` → `users(id)`

---

## Summary Statistics

**Total Tables:** 38
**Total Foreign Key Relationships:** 65
**Tables with Multiple Foreign Keys:** 19
**Tables with No Foreign Keys:** 9

## Key Lookup Categories (Pre-populated)

The schema includes the following lookup categories:
- `housing_status` - Estats Habitatge
- `member_origin` - Origens Afiliació
- `participation_level` - Nivells Participació
- `conflict_cause` - Causes Conflicte
- `conflict_resolution` - Resolucions Conflicte
- `follow_up_type` - Tipus Seguiment
- `advisory_type` - Tipus Assessoraments
- `advisory_result` - Resultats Assessoraments
- `legal_service_type` - Tipus Serveis Jurídics
- `specialty` - Especialitats