from rest_framework import status

from .test_setup import TestSetUp

class TestViews(TestSetUp):
    def test_getCustomQuestion_success(self):
        """
        API: /api/questions/
        Test get user created custom questions
        """
        response = self.client.get(self.question_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(len(response_json), 1)  # should have 1 question

    def test_postCustomQuestion_success(self):
        """
        API: /api/questions/
        Test create custom questions with valid inputs
        """
        data = {"question": "question1",
                "section": "1",
                "answers": [
                    {"answer":"answer1", "is_correct":"True"},
                    {"answer":"answer2", "is_correct":"False"},
                    {"answer":"answer3", "is_correct":"False"},
                    {"answer":"answer4", "is_correct":"False"}
                ]}
        response = self.client.post(self.question_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = response.json()
        # new custom question
        self.assertEqual(response_json["question"],"question1")
        self.assertEqual(response_json["section"],"subtopicnametest1 (worldnametest1)")
        self.assertEqual(response_json["answers"][0]["answer"], "answer1")
        self.assertEqual(response_json["answers"][1]["answer"], "answer2")
        self.assertEqual(response_json["answers"][2]["answer"], "answer3")
        self.assertEqual(response_json["answers"][3]["answer"], "answer4")

    def test_postCustomQuestion_fail_is_correct(self):
        """
        API: /api/questions/
        Test create custom questions with invalid number of correct answers
        """
        data = {"question": "question1",
                "section": "1",
                "answers": [
                    {"answer":"answer1", "is_correct":"True"},
                    {"answer":"answer2", "is_correct":"True"},
                    {"answer":"answer3", "is_correct":"False"},
                    {"answer":"answer4", "is_correct":"False"}
                ]}
        response = self.client.post(self.question_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_postCustomQuestion_fail_number_of_answers(self):
        """
        API: /api/questions/
        Test create custom questions with invalid number of answers
        """
        data = {"question": "question1",
                "section": "1",
                "answers": [
                    {"answer":"answer1", "is_correct":"True"},
                    {"answer":"answer2", "is_correct":"False"},
                    {"answer":"answer3", "is_correct":"False"}
                ]}
        response = self.client.post(self.question_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_getSelectedCustomQuestion_success(self):
        """
        API: api/questions/<int:pk>/
        Test get question with specific id
        """
        response = self.client.get("/api/questions/1/", format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(response_json["id"], 1)  # get question id = 1

    def test_deleteSelectedCustomQuestion_success(self):
        """
        API: api/questions/<int:pk>/
        Test delete question with specific id
        """
        response = self.client.delete("/api/questions/1/", format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_putSelectedCustomQuestion_success(self):
        """
        API: api/questions/<int:pk>/
        Test edit question with specific id
        """
        response = self.client.put("/api/questions/1/", format='json',
                                    data = {"question": "question99",
                                             "answers": [
                                                 {"answer":"answer1", "is_correct":"False"},
                                                 {"answer":"answer2", "is_correct":"False"},
                                                 {"answer":"answer3", "is_correct":"False"},
                                                 {"answer":"answer4", "is_correct":"True"}
                                             ]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(response_json["question"], "question99") #question name updated
        self.assertEqual(response_json["answers"][0]["is_correct"], False) #answer1 is updated to False
        self.assertEqual(response_json["answers"][3]["is_correct"], True) #answer4 is updated to True
