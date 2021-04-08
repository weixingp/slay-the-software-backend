import time
from locust import HttpUser, task, between


class QuickstartUser(HttpUser):
    wait_time = between(1, 10)
    headers = None

    @task(1)
    def login(self):
        data = {
            "username": "loadtest",
            "password": "fDcHw7d3tmHmgdBB"
        }
        self.client.post("/account/login/", json=data)

    @task(1)
    def logout(self):
        self.client.get("/account/logout/", headers=self.headers)

    @task(100)
    def get_position(self):
        self.client.get("/position/", headers=self.headers)

    @task(60)
    def get_question(self):
        self.client.get("/questions/world/", headers=self.headers)

    @task(30)
    def get_world(self):
        self.client.get("/worlds/", headers=self.headers)

    @task(30)
    def get_leaderboard(self):
        self.client.get("/leaderboard/", headers=self.headers)

    @task(100)
    def get_score(self):
        self.client.get("/score/", headers=self.headers)

    @task(100)
    def get_difficulty(self):
        self.client.get("/difficulty/", headers=self.headers)

    def on_start(self):
        data = {
            "username": "loadtest",
            "password": "fDcHw7d3tmHmgdBB"
        }
        res = self.client.post("/account/login/", json=data)
        if res.status_code == 200:
            token = res.json()["token"]
            self.headers = {"authorization": "Token " + token}
        else:
            raise Exception("Unable to login, pls check account.")
