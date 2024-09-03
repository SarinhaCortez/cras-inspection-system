CREATE TABLE users (
    username TEXT PRIMARY KEY,  -- Unique identifier for each user
    name TEXT NOT NULL,         -- Full name of the user
    pic TEXT,                   -- Path or URL to the user's profile picture
    password TEXT NOT NULL      -- Password for the user (ideally hashed and salted)
);

-- Create the 'reports' table
CREATE TABLE reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique identifier for each report
    name TEXT NOT NULL,                         -- Title of the report
    content TEXT NOT NULL,                       -- Content of the report
    username TEXT NOT NULL,                      -- Foreign key to the 'users' table
    FOREIGN KEY (username) REFERENCES users(username) -- Enforce referential integrity
);