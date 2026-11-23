CREATE DATABASE IF NOT EXISTS tutorial;
USE tutorial;
CREATE TABLE IF NOT EXISTS planet (
  id INT UNSIGNED AUTO_INCREMENT,
  name VARCHAR(30),
  PRIMARY KEY(id));
INSERT INTO planet (name) VALUES ("Mercury"), ("Venus"), ("Earth"), ("Mars"),
  ("Jupiter"), ("Saturn"), ("Uranus"), ("Neptune");