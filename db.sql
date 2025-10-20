SET search_path = srvana;

-- Drop tables if they exist to allow for easy re-creation
DROP TABLE IF EXISTS VERIFICATION_DOCUMENT CASCADE;
DROP TABLE IF EXISTS MEDIA CASCADE;
DROP TABLE IF EXISTS COMPLAINT CASCADE;
DROP TABLE IF EXISTS PROJECT_OFFER CASCADE;
DROP TABLE IF EXISTS TECHNICIAN_SKILL CASCADE;
DROP TABLE IF EXISTS TECHNICIAN_AVAILABILITY CASCADE;
DROP TABLE IF EXISTS REVIEW CASCADE;
DROP TABLE IF EXISTS PAYMENT CASCADE;
DROP TABLE IF EXISTS "ORDER" CASCADE; -- "ORDER" is a reserved keyword
DROP TABLE IF EXISTS SERVICE CASCADE;
DROP TABLE IF EXISTS SERVICE_CATEGORY CASCADE;
DROP TABLE IF EXISTS "USER" CASCADE; -- "USER" is a reserved keyword
DROP TABLE IF EXISTS USER_TYPE CASCADE;

-- Table: USER_TYPE
CREATE TABLE USER_TYPE (
    user_type_id SERIAL PRIMARY KEY,
    user_type_name VARCHAR(255) UNIQUE NOT NULL
);

-- Table: USER
CREATE TABLE "USER" (
    user_id SERIAL PRIMARY KEY,
    user_type_id INTEGER NOT NULL REFERENCES USER_TYPE(user_type_id),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(255) UNIQUE,
    password VARCHAR(255) NOT NULL,
    address TEXT,
    account_status VARCHAR(255),
    registration_date DATE NOT NULL,
    last_login_date DATE,
    notification_preferences TEXT,
    bio TEXT,
    profile_picture VARCHAR(255),
    overall_rating NUMERIC,
    num_jobs_completed INTEGER,
    average_response_time NUMERIC,
    verification_status VARCHAR(255),
    username VARCHAR(255) UNIQUE,
    access_level VARCHAR(255)
);

-- Table: SERVICE_CATEGORY
CREATE TABLE SERVICE_CATEGORY (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url VARCHAR(255)
);

-- Table: SERVICE
CREATE TABLE SERVICE (
    service_id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES SERVICE_CATEGORY(category_id),
    service_name VARCHAR(255) NOT NULL,
    description TEXT,
    service_type VARCHAR(255) NOT NULL,
    base_inspection_fee NUMERIC NOT NULL,
    estimated_price_range_min NUMERIC,
    estimated_price_range_max NUMERIC,
    emergency_surcharge_percentage NUMERIC
);

-- Table: ORDER
CREATE TABLE "ORDER" (
    order_id SERIAL PRIMARY KEY,
    client_user_id INTEGER NOT NULL REFERENCES "USER"(user_id),
    service_id INTEGER NOT NULL REFERENCES SERVICE(service_id),
    technician_user_id INTEGER REFERENCES "USER"(user_id),
    order_type VARCHAR(255) NOT NULL,
    problem_description TEXT NOT NULL,
    requested_location TEXT NOT NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time_start VARCHAR(255) NOT NULL,
    scheduled_time_end VARCHAR(255) NOT NULL,
    order_status VARCHAR(255) NOT NULL,
    creation_timestamp DATE NOT NULL,
    job_start_timestamp DATE,
    job_completion_timestamp DATE,
    final_price NUMERIC,
    commission_percentage NUMERIC,
    platform_commission_amount NUMERIC,
    service_fee_percentage NUMERIC,
    service_fee_amount NUMERIC,
    total_amount_paid_by_client NUMERIC,
    amount_to_technician NUMERIC
);

-- Table: PAYMENT
CREATE TABLE PAYMENT (
    payment_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES "ORDER"(order_id),
    client_user_id INTEGER NOT NULL REFERENCES "USER"(user_id),
    payment_method VARCHAR(255) NOT NULL,
    transaction_id VARCHAR(255) NOT NULL,
    amount NUMERIC NOT NULL,
    payment_date DATE NOT NULL,
    payment_status VARCHAR(255) NOT NULL,
    is_deposit BOOLEAN NOT NULL
);

-- Table: REVIEW
CREATE TABLE REVIEW (
    review_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES "ORDER"(order_id),
    client_user_id INTEGER NOT NULL REFERENCES "USER"(user_id),
    technician_user_id INTEGER NOT NULL REFERENCES "USER"(user_id),
    rating INTEGER NOT NULL,
    comment TEXT,
    review_date DATE NOT NULL
);

-- Table: TECHNICIAN_AVAILABILITY
CREATE TABLE TECHNICIAN_AVAILABILITY (
    availability_id SERIAL PRIMARY KEY,
    technician_user_id INTEGER NOT NULL REFERENCES "USER"(user_id),
    day_of_week VARCHAR(255) NOT NULL,
    start_time VARCHAR(255) NOT NULL,
    end_time VARCHAR(255) NOT NULL,
    is_available BOOLEAN NOT NULL
);

-- Table: TECHNICIAN_SKILL
CREATE TABLE TECHNICIAN_SKILL (
    technician_user_id INTEGER NOT NULL REFERENCES "USER"(user_id),
    service_id INTEGER NOT NULL REFERENCES SERVICE(service_id),
    experience_level VARCHAR(255) NOT NULL,
    PRIMARY KEY (technician_user_id, service_id)
);

-- Table: PROJECT_OFFER
CREATE TABLE PROJECT_OFFER (
    offer_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES "ORDER"(order_id),
    technician_user_id INTEGER NOT NULL REFERENCES "USER"(user_id),
    proposed_price NUMERIC NOT NULL,
    estimated_completion_time VARCHAR(255),
    offer_notes TEXT,
    offer_date DATE NOT NULL,
    offer_status VARCHAR(255) NOT NULL
);

-- Table: COMPLAINT
CREATE TABLE COMPLAINT (
    complaint_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES "ORDER"(order_id),
    client_user_id INTEGER NOT NULL REFERENCES "USER"(user_id),
    technician_user_id INTEGER REFERENCES "USER"(user_id),
    complaint_details TEXT NOT NULL,
    submission_date DATE NOT NULL,
    status VARCHAR(255) NOT NULL,
    admin_user_id INTEGER REFERENCES "USER"(user_id),
    resolution_details TEXT,
    resolution_date DATE
);

-- Table: MEDIA
CREATE TABLE MEDIA (
    media_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES "ORDER"(order_id),
    technician_user_id INTEGER REFERENCES "USER"(user_id),
    client_user_id INTEGER REFERENCES "USER"(user_id),
    media_url VARCHAR(255) NOT NULL,
    media_type VARCHAR(255) NOT NULL,
    upload_date DATE NOT NULL,
    context TEXT
);

-- Table: VERIFICATION_DOCUMENT
CREATE TABLE VERIFICATION_DOCUMENT (
    doc_id SERIAL PRIMARY KEY,
    technician_user_id INTEGER NOT NULL REFERENCES "USER"(user_id),
    document_type VARCHAR(255) NOT NULL,
    document_url VARCHAR(255) NOT NULL,
    upload_date DATE NOT NULL,
    verification_status VARCHAR(255) NOT NULL,
    rejection_reason TEXT
);