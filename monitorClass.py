import requests
from bs4 import BeautifulSoup
import json
import mysql.connector

def getEnrollment(classResponseSoup, enrollString, valueString):
    enroll = classResponseSoup.find('td', class_='tableHeader', string=enrollString)

    target_tr = enroll.find_parent('tr')
    enrollValue = target_tr.find('td', class_=valueString).get_text(strip=True)

    return enrollValue

def getClassResponseSoup(courseSubject, courseCode, termCode, collegeCode):
    try:
        response = requests.get(
            f'https://termmasterschedule.drexel.edu/webtms_du/collegesSubjects/{termCode}?collCode={collegeCode}', 
            timeout=15)
        response.raise_for_status()

        sectionSoup = BeautifulSoup(response.text, 'html.parser')
        classLink = sectionSoup.find('a', string=courseSubject)["href"]

        listOfSectionsResponse = requests.post(f'https://termmasterschedule.drexel.edu/{classLink}')

        listOfSectionsSoup = BeautifulSoup(listOfSectionsResponse.text, 'html.parser')
        sectionLink = listOfSectionsSoup.find('a', string=courseCode)["href"]

        classResponse = requests.post(f'https://termmasterschedule.drexel.edu/{sectionLink}')
        classResponseSoup = BeautifulSoup(classResponse.text, 'html.parser')
        
        return classResponseSoup

    except requests.exceptions.HTTPError as e:
        print("Error %s" % e)

class Class:
    def __init__(self, id, name, code, term, schoolCode, currentEnroll = None, maxEnroll = None):
        self.id = id
        self.name = name
        self.code = code
        self.currentEnroll = currentEnroll
        self.maxEnroll = maxEnroll
        self.term = term
        self.schoolCode = schoolCode

class Email(object):
    def __init__(self, subject, text):
        self.subject = subject
        self.text = text

def main():
    host='localhost'
    user='root'
    password=''
    database='drexelscraper'

    connection = mysql.connector.connect(
        host= host,
        user= user,
        password = password,
        database = database
    )

    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM classes")
    classDictionaries = cursor.fetchall()

    classes = [Class(**dictionary) for dictionary in classDictionaries]

    try:
        for i in range(len(classes)):
            classResponseSoup = getClassResponseSoup(classes[i].name, classes[i].code, classes[i].term, classes[i].schoolCode)
            
            # maxEnroll = even
            # currentEnroll = odd
            currentEnroll = getEnrollment(classResponseSoup, "Enroll", "odd")
            maxEnroll = getEnrollment(classResponseSoup, "Max Enroll", "even")

            email = {}
            update_query = (
                    "UPDATE classes "
                    "SET maxEnroll = %s, currentEnroll = %s "
                    "WHERE id = %s"
                )
            
            classUpdatedFlag = False

            if (maxEnroll != classes[i].maxEnroll and currentEnroll != classes[i].currentEnroll):
                email = {
                "subject": f"Enrollment updated for {classes[i].name}!",
                "text": f"Max Enrollment updated for {classes[i].name}!\n"
                        f"New Max Enrollment: {maxEnroll}\n"
                        f"Previous Max Enrollment: {classes[i].maxEnroll}\n\n"
                        f"Current Enrollment Updated for {classes[i].name}!\n"
                        f"Max Enrollment Value: {maxEnroll}\n"
                        f"Current Enrollment Value: {currentEnroll}\n"
                        f"Previous Enrollment Value: {classes[i].currentEnroll}"
                }
                classUpdatedFlag = True
            elif (maxEnroll != classes[i].maxEnroll and currentEnroll == classes[i].currentEnroll):
                email = {
                "subject": f"Enrollment updated for {classes[i].name}!",
                "text": f"Max Enrollment updated for {classes[i].name}!\n"
                        f"New Max Enrollment: {maxEnroll}\n"
                        f"Previous Max Enrollment: {classes[i].maxEnroll}"
                }
                classUpdatedFlag = True
            elif (currentEnroll != classes[i].currentEnroll and maxEnroll == classes[i].maxEnroll):
                email = {
                "subject": f"Enrollment updated for {classes[i].name}!",
                "text": f"Current Enrollment Updated for {classes[i].name}!\n"
                        f"Max Enrollment Value: {classes[i].maxEnroll}\n"
                        f"Current Enrollment Value: {currentEnroll}\n"
                        f"Previous Enrollment Value: {classes[i].currentEnroll}"
                }
                classUpdatedFlag = True

            update_values = (maxEnroll, currentEnroll, classes[i].id)
            cursor.execute(update_query, update_values)
            connection.commit()
            emailJson = json.dumps(email)

            if (classUpdatedFlag):
                requests.post('https://eojdo99yrtmjybk.m.pipedream.net', data=emailJson, timeout=15)

    except requests.exceptions.HTTPError as e:
        print("Error %s" % e)

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()