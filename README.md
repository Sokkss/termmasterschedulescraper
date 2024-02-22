# Python Term Master Schedule Scraper
Python script that sends me an update email anytime a class in my classes database is updated on the term master schedule. BeautifulSoup is used to parse the html from the site for each class, then the current numbers are compared to the existing numbers saved in the database. If the current numbers differ from the database enrollment numbers, I am sent an email alerting me that the class enrollment has changed. This serves as essentially an alert system for enrollment for classes I am trying to get into/watching for any other reason. 
  
Set to run via a scheduled task on Windows every hour from 7am to 1am with it set to wake my computer if it's asleep. The database is connected to MySQL.
