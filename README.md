##SnappFood Sentiment Analysis and Web Scraping
#Project Overview
This project allows users to input a neighborhood (e.g., Qeytariyeh) and a specific dish (e.g., Pepperoni Pizza) to retrieve a list of restaurants in that area offering the selected dish on the SnappFood platform. Using Selenium for web scraping, the application collects user reviews and ratings for each restaurant. It then performs sentiment analysis on the reviews to determine customer satisfaction levels, helping users make informed dining choices.

#Features
User Input: Users can enter a neighborhood and a specific dish to search for relevant restaurants on SnappFood.
Web Scraping with Selenium: Efficiently collects data from the SnappFood platform, including restaurant names, reviews, and ratings for the specified dish.
Sentiment Analysis: Analyzes the sentiment of collected reviews to assess overall customer satisfaction.
Restaurant Listing: Displays a ranked list of restaurants based on user feedback, highlighting positive and negative sentiments.
Issue Identification: Identifies common complaints and issues mentioned in user reviews, such as:
Food arriving cold
Quality of food
Delivery times
#Technologies Used
Python: The primary programming language for the project.
Selenium: For web scraping and automating browser interactions.
NLTK/TextBlob: For performing sentiment analysis on user reviews.
Flask/Django: For building the user interface (you can choose based on your preference).
Pandas: For data manipulation and analysis.

overview of application/project:
step1)enter neighborhood (e.g., Qeytariyeh) and a specific dish (e.g., Pepperoni Pizza): 
<img width="606" height="520" alt="image" src="https://github.com/user-attachments/assets/0c27b3d3-a120-4edd-ae0e-dcd618bec58a" />
the data outomaticly start to collect from snapfood ,there is no need to manual things😅
<img width="975" height="548" alt="image" src="https://github.com/user-attachments/assets/15bf79b3-a3fc-4193-b246-842b1338bf62" />
<img width="975" height="486" alt="image" src="https://github.com/user-attachments/assets/18d512f4-f64c-4c65-8d27-c3629af6840d" />

<img width="975" height="496" alt="image" src="https://github.com/user-attachments/assets/daaff269-39d9-498d-836a-09ae4ef18f93" />

data is text of restuant overwie look like blow:

step3) big picture about resturants exists in thid nighborhood with there rank for this specifict food:
<img width="975" height="854" alt="image" src="https://github.com/user-attachments/assets/c84c47b1-f357-45c3-bfbb-ee5d63be8d56" />
step4) detailed report :
<img width="975" height="712" alt="image" src="https://github.com/user-attachments/assets/780d6067-4f63-458a-94a4-553b723c59db" />
<img width="975" height="712" alt="image" src="https://github.com/user-attachments/assets/e85de886-7d08-452f-9ccf-ab5e0ec5195e" />





