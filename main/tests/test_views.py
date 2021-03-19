from rest_framework import status

from .test_setup import TestSetUp

class TestViews(TestSetUp):
    def test_getCustomQuestion_success(self):
        response = self.client.get(self.question_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_postCustomQuestion_success(self):
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

    def test_createquestion_fail_is_correct(self):
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

    def test_createquestion_fail_number_of_answers(self):
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
        response = self.client.get("/api/questions/1/", format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_getSelectedCustomQuestion_fail_not_your_question(self):
        response = self.client.get("/api/questions/2/", format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deleteSelectedCustomQuestion_success(self):
        response = self.client.delete("/api/questions/1/", format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_putSelectedCustomQuestion_success(self):
        response = self.client.put("/api/questions/1/", format='json',
                                    data = {"question": "question99",
                                             "answers": [
                                                 {"answer":"answer1", "is_correct":"False"},
                                                 {"answer":"answer2", "is_correct":"False"},
                                                 {"answer":"answer3", "is_correct":"False"},
                                                 {"answer":"answer4", "is_correct":"True"}
                                             ]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)