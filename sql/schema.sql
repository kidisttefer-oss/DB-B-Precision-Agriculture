-- Structured, fixed-schema readings: soil moisture, temperature, light.
-- Nutrient data is NOT here because its fields vary by probe model - that
-- belongs in MongoDB instead. See databases/mongo_writer.py.
CREATE TABLE IF NOT EXISTS readings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    zone_id VARCHAR(50) NOT NULL,
    sensor_id VARCHAR(50) NOT NULL,
    soil_moisture FLOAT,
    temperature FLOAT,
    light_lux FLOAT,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Audit table: automatically filled by the trigger below whenever a
-- reading crosses a critical threshold. This keeps a permanent record
-- of every dangerous condition, separate from the raw readings stream.
CREATE TABLE IF NOT EXISTS critical_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    zone_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(40) NOT NULL,
    soil_moisture FLOAT,
    temperature FLOAT,
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- View: average soil moisture/temperature per crop zone, used by the dashboard
CREATE OR REPLACE VIEW zone_averages AS
SELECT
    zone_id,
    AVG(soil_moisture) AS avg_soil_moisture,
    AVG(temperature) AS avg_temperature,
    COUNT(*) AS reading_count
FROM readings
GROUP BY zone_id;

-- Trigger: after every reading is inserted, MySQL itself checks the
-- thresholds and logs a critical event automatically - no Python needed.
-- This shows database-side logic: the alerting rule lives in the database.
DELIMITER $$
CREATE TRIGGER trg_log_critical
AFTER INSERT ON readings
FOR EACH ROW
BEGIN
    IF NEW.soil_moisture < 30 THEN
        INSERT INTO critical_events (zone_id, event_type, soil_moisture, temperature)
        VALUES (NEW.zone_id, 'irrigation_needed', NEW.soil_moisture, NEW.temperature);
    ELSEIF NEW.temperature > 38 THEN
        INSERT INTO critical_events (zone_id, event_type, soil_moisture, temperature)
        VALUES (NEW.zone_id, 'heat_stress', NEW.soil_moisture, NEW.temperature);
    END IF;
END $$
DELIMITER ;

-- Stored procedure: fetch recent readings for one crop zone
DELIMITER $$
CREATE PROCEDURE GetRecentReadings(IN in_zone_id VARCHAR(50), IN in_minutes INT)
BEGIN
    SELECT *
    FROM readings
    WHERE zone_id = in_zone_id
      AND recorded_at >= NOW() - INTERVAL in_minutes MINUTE
    ORDER BY recorded_at DESC;
END $$
DELIMITER ;
