CREATE TABLE "users" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(120) NOT NULL
);
CREATE TABLE "dreams" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    dream_description TEXT NOT NULL,
    interpretation TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user
        FOREIGN KEY(user_id) 
        REFERENCES "user"(id)
);
INSERT INTO "user" (username, email, password) VALUES 
('john_doe', 'john@example.com', 'password123'),
('jane_smith', 'jane@example.com', 'password456'),
('alice_jones', 'alice@example.com', 'password789');
INSERT INTO "dream" (user_id, dream_description, interpretation) VALUES 
(1, 'I was flying over the city and felt very free.', 'Dreaming of flying often represents a desire for freedom.'),
(2, 'I was being chased by a shadow but could not see what it was.', 'Being chased in dreams usually represents avoidance or fear.'),
(1, 'I was swimming in clear blue water and felt very peaceful.', 'Swimming in clear water often represents a desire for clarity and peace.'),
(3, 'I found a hidden door in my house that led to a beautiful garden.', 'Discovering new spaces can symbolize personal growth and discovery.');
