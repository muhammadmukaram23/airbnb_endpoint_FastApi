-- Airbnb-style Database Schema
-- MySQL Database Creation and Table Definitions


USE airbnb_system;

-- Users table (both guests and hosts)
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    profile_picture_url VARCHAR(500),
    bio TEXT,
    is_host BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    government_id_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_is_host (is_host)
);

-- User addresses
CREATE TABLE user_addresses (
    address_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    address_type ENUM('home', 'billing', 'other') DEFAULT 'home',
    street_address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Property categories
CREATE TABLE property_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Properties/Listings
CREATE TABLE properties (
    property_id INT AUTO_INCREMENT PRIMARY KEY,
    host_id INT NOT NULL,
    category_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    property_type ENUM('entire_place', 'private_room', 'shared_room') NOT NULL,
    max_guests INT NOT NULL DEFAULT 1,
    bedrooms INT NOT NULL DEFAULT 0,
    beds INT NOT NULL DEFAULT 1,
    bathrooms DECIMAL(3,1) NOT NULL DEFAULT 1.0,
    price_per_night DECIMAL(10,2) NOT NULL,
    cleaning_fee DECIMAL(10,2) DEFAULT 0.00,
    service_fee_percentage DECIMAL(5,2) DEFAULT 3.00,
    minimum_nights INT DEFAULT 1,
    maximum_nights INT DEFAULT 365,
    check_in_time TIME DEFAULT '15:00:00',
    check_out_time TIME DEFAULT '11:00:00',
    instant_book BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES property_categories(category_id),
    INDEX idx_host_id (host_id),
    INDEX idx_category_id (category_id),
    INDEX idx_property_type (property_type),
    INDEX idx_price (price_per_night),
    INDEX idx_is_active (is_active)
);

-- Property addresses
CREATE TABLE property_addresses (
    address_id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    street_address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    neighborhood VARCHAR(100),
    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE,
    INDEX idx_property_id (property_id),
    INDEX idx_location (latitude, longitude),
    INDEX idx_city (city),
    INDEX idx_country (country)
);

-- Amenities
CREATE TABLE amenities (
    amenity_id INT AUTO_INCREMENT PRIMARY KEY,
    amenity_name VARCHAR(100) UNIQUE NOT NULL,
    amenity_category VARCHAR(50) NOT NULL,
    icon_url VARCHAR(500),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Property amenities junction table
CREATE TABLE property_amenities (
    property_id INT NOT NULL,
    amenity_id INT NOT NULL,
    PRIMARY KEY (property_id, amenity_id),
    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE,
    FOREIGN KEY (amenity_id) REFERENCES amenities(amenity_id) ON DELETE CASCADE
);

-- Property photos
CREATE TABLE property_photos (
    photo_id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    photo_url VARCHAR(500) NOT NULL,
    caption VARCHAR(255),
    is_cover_photo BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE,
    INDEX idx_property_id (property_id),
    INDEX idx_is_cover (is_cover_photo)
);

-- House rules
CREATE TABLE house_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    rule_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE,
    INDEX idx_property_id (property_id)
);

-- Bookings/Reservations
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    guest_id INT NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    num_guests INT NOT NULL,
    total_nights INT NOT NULL,
    base_price DECIMAL(10,2) NOT NULL,
    cleaning_fee DECIMAL(10,2) DEFAULT 0.00,
    service_fee DECIMAL(10,2) NOT NULL,
    taxes DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL,
    booking_status ENUM('pending', 'confirmed', 'cancelled', 'completed', 'in_progress') DEFAULT 'pending',
    payment_status ENUM('pending', 'paid', 'partially_paid', 'refunded', 'failed') DEFAULT 'pending',
    special_requests TEXT,
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(property_id),
    FOREIGN KEY (guest_id) REFERENCES users(user_id),
    INDEX idx_property_id (property_id),
    INDEX idx_guest_id (guest_id),
    INDEX idx_check_in_date (check_in_date),
    INDEX idx_booking_status (booking_status),
    INDEX idx_dates (check_in_date, check_out_date)
);

-- Payment methods
CREATE TABLE payment_methods (
    payment_method_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    payment_type ENUM('credit_card', 'debit_card', 'paypal', 'bank_account') NOT NULL,
    last_four_digits VARCHAR(4),
    card_brand VARCHAR(50),
    expiry_month INT,
    expiry_year INT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Payments
CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    payment_method_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_type ENUM('booking', 'security_deposit', 'additional_fees', 'refund') DEFAULT 'booking',
    payment_status ENUM('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded') DEFAULT 'pending',
    transaction_id VARCHAR(255),
    payment_gateway VARCHAR(50),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    failure_reason TEXT,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(payment_method_id),
    INDEX idx_booking_id (booking_id),
    INDEX idx_payment_status (payment_status),
    INDEX idx_payment_date (payment_date)
);

-- Reviews (guests reviewing properties and hosts reviewing guests)
CREATE TABLE reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    reviewer_id INT NOT NULL,
    reviewee_id INT NOT NULL,
    review_type ENUM('guest_to_host', 'host_to_guest') NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    cleanliness_rating INT CHECK (cleanliness_rating >= 1 AND cleanliness_rating <= 5),
    communication_rating INT CHECK (communication_rating >= 1 AND communication_rating <= 5),
    check_in_rating INT CHECK (check_in_rating >= 1 AND check_in_rating <= 5),
    accuracy_rating INT CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
    location_rating INT CHECK (location_rating >= 1 AND location_rating <= 5),
    value_rating INT CHECK (value_rating >= 1 AND value_rating <= 5),
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    FOREIGN KEY (reviewer_id) REFERENCES users(user_id),
    FOREIGN KEY (reviewee_id) REFERENCES users(user_id),
    INDEX idx_booking_id (booking_id),
    INDEX idx_reviewer_id (reviewer_id),
    INDEX idx_reviewee_id (reviewee_id),
    INDEX idx_rating (rating)
);

-- Messages between hosts and guests
CREATE TABLE messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT,
    sender_id INT NOT NULL,
    recipient_id INT NOT NULL,
    message_text TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    message_type ENUM('inquiry', 'booking_related', 'general') DEFAULT 'general',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    FOREIGN KEY (sender_id) REFERENCES users(user_id),
    FOREIGN KEY (recipient_id) REFERENCES users(user_id),
    INDEX idx_booking_id (booking_id),
    INDEX idx_sender_id (sender_id),
    INDEX idx_recipient_id (recipient_id),
    INDEX idx_is_read (is_read)
);

-- Wishlists/Favorites
CREATE TABLE wishlists (
    wishlist_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    wishlist_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Wishlist items
CREATE TABLE wishlist_items (
    wishlist_id INT NOT NULL,
    property_id INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (wishlist_id, property_id),
    FOREIGN KEY (wishlist_id) REFERENCES wishlists(wishlist_id) ON DELETE CASCADE,
    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE
);

-- Property availability calendar
CREATE TABLE property_availability (
    availability_id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    available_date DATE NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    price_override DECIMAL(10,2) NULL,
    minimum_nights_override INT NULL,
    notes TEXT,
    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE,
    UNIQUE KEY unique_property_date (property_id, available_date),
    INDEX idx_property_id (property_id),
    INDEX idx_available_date (available_date),
    INDEX idx_is_available (is_available)
);

-- Host earnings
CREATE TABLE host_earnings (
    earning_id INT AUTO_INCREMENT PRIMARY KEY,
    host_id INT NOT NULL,
    booking_id INT NOT NULL,
    gross_amount DECIMAL(10,2) NOT NULL,
    platform_fee DECIMAL(10,2) NOT NULL,
    net_amount DECIMAL(10,2) NOT NULL,
    payout_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    payout_date DATE NULL,
    payout_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES users(user_id),
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    INDEX idx_host_id (host_id),
    INDEX idx_booking_id (booking_id),
    INDEX idx_payout_status (payout_status)
);

-- Cancellation policies
CREATE TABLE cancellation_policies (
    policy_id INT AUTO_INCREMENT PRIMARY KEY,
    policy_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    refund_percentage_24h INT DEFAULT 100,
    refund_percentage_7d INT DEFAULT 50,
    refund_percentage_30d INT DEFAULT 0,
    service_fee_refundable BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Link properties to cancellation policies
ALTER TABLE properties ADD COLUMN cancellation_policy_id INT,
ADD FOREIGN KEY (cancellation_policy_id) REFERENCES cancellation_policies(policy_id);

-- Property pricing rules (seasonal pricing, etc.)
CREATE TABLE pricing_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    price_modifier_type ENUM('fixed_amount', 'percentage') NOT NULL,
    price_modifier_value DECIMAL(10,2) NOT NULL,
    minimum_nights_override INT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE,
    INDEX idx_property_id (property_id),
    INDEX idx_dates (start_date, end_date)
);

-- Insert sample data for property categories
INSERT INTO property_categories (category_name, description) VALUES
('Apartment', 'Modern apartments in urban areas'),
('House', 'Entire houses for families and groups'),
('Villa', 'Luxury villas with premium amenities'),
('Condo', 'Comfortable condominiums'),
('Cabin', 'Cozy cabins in nature settings'),
('Loft', 'Stylish lofts with unique architecture'),
('Cottage', 'Charming cottages for peaceful stays'),
('Studio', 'Compact studios perfect for solo travelers');

-- Insert sample amenities
INSERT INTO amenities (amenity_name, amenity_category, description) VALUES
('WiFi', 'Technology', 'High-speed wireless internet'),
('Air Conditioning', 'Climate', 'Central air conditioning system'),
('Heating', 'Climate', 'Central heating system'),
('Kitchen', 'Cooking', 'Fully equipped kitchen'),
('Parking', 'Transportation', 'Free parking on premises'),
('Pool', 'Recreation', 'Swimming pool access'),
('Gym', 'Recreation', 'Fitness center access'),
('Pet Friendly', 'Policies', 'Pets allowed'),
('Smoking Allowed', 'Policies', 'Smoking permitted'),
('TV', 'Entertainment', 'Television with cable/streaming'),
('Washer', 'Laundry', 'Washing machine'),
('Dryer', 'Laundry', 'Clothes dryer'),
('Hot Tub', 'Recreation', 'Private hot tub/jacuzzi'),
('Fireplace', 'Comfort', 'Indoor fireplace'),
('Balcony', 'Outdoor', 'Private balcony or patio');

-- Insert sample cancellation policies
INSERT INTO cancellation_policies (policy_name, description, refund_percentage_24h, refund_percentage_7d, refund_percentage_30d) VALUES
('Flexible', 'Full refund 1 day prior to arrival', 100, 100, 100),
('Moderate', 'Full refund 5 days prior to arrival', 100, 50, 0),
('Strict', 'Full refund 14 days prior to arrival', 100, 50, 0),
('Super Strict', 'Full refund 60 days prior to arrival', 50, 0, 0);

-- Create indexes for better performance
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_properties_created_at ON properties(created_at);
CREATE INDEX idx_bookings_created_at ON bookings(created_at);
CREATE INDEX idx_reviews_created_at ON reviews(created_at);
CREATE INDEX idx_properties_max_guests ON properties(max_guests);
CREATE INDEX idx_property_addresses_city_country ON property_addresses(city, country);

-- Views for common queries
CREATE VIEW property_summary AS
SELECT 
    p.property_id,
    p.title,
    p.property_type,
    p.max_guests,
    p.bedrooms,
    p.bathrooms,
    p.price_per_night,
    pa.city,
    pa.country,
    COALESCE(AVG(r.rating), 0) as average_rating,
    COUNT(r.review_id) as review_count,
    u.first_name as host_first_name,
    u.last_name as host_last_name
FROM properties p
JOIN property_addresses pa ON p.property_id = pa.property_id
JOIN users u ON p.host_id = u.user_id
LEFT JOIN bookings b ON p.property_id = b.property_id
LEFT JOIN reviews r ON b.booking_id = r.booking_id AND r.review_type = 'guest_to_host'
WHERE p.is_active = TRUE
GROUP BY p.property_id, p.title, p.property_type, p.max_guests, p.bedrooms, p.bathrooms, 
         p.price_per_night, pa.city, pa.country, u.first_name, u.last_name;

-- View for host dashboard
CREATE VIEW host_dashboard AS
SELECT 
    u.user_id as host_id,
    u.first_name,
    u.last_name,
    COUNT(DISTINCT p.property_id) as total_properties,
    COUNT(DISTINCT b.booking_id) as total_bookings,
    COALESCE(SUM(he.net_amount), 0) as total_earnings,
    COALESCE(AVG(r.rating), 0) as average_rating
FROM users u
LEFT JOIN properties p ON u.user_id = p.host_id AND p.is_active = TRUE
LEFT JOIN bookings b ON p.property_id = b.property_id AND b.booking_status = 'completed'
LEFT JOIN host_earnings he ON b.booking_id = he.booking_id
LEFT JOIN reviews r ON b.booking_id = r.booking_id AND r.review_type = 'guest_to_host'
WHERE u.is_host = TRUE
GROUP BY u.user_id, u.first_name, u.last_name;

ALTER TABLE property_addresses 
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;