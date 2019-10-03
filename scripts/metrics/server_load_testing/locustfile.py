"""
Simulate server load under a few scenarios.

Sample usage:
    locust --host=http://staging.locuszoom.org

    To run web UI, see: https://docs.locust.io/en/stable/quickstart.html#open-up-locust-s-web-interface
    Eg, from local machine, visit: http://127.0.0.1:8089/

**PLEASE DO NOT RUN ROUTINE LOAD TESTING AGAINST THE PRODUCTION SERVER**

Although this is tracked in the repo, this is not an administrative CLI task, and its dependencies are not tracked as
    part of the app. The code is tracked so that future developers can continue to check the server according to the
    same metrics.

You may, therefore, need to install separate dependencies. See: https://docs.locust.io/en/stable/installation.html
"""
from locust import HttpLocust, TaskSet, task

# Hardcoding this is inelegant. Eventually, every task will grab an item from the API sp that this script
# is server-agnostic
SAMPLE_STUDY_ID = '785722'


class ViewOnlyBehavior(TaskSet):
    @task(1)
    def index(self):
        self.client.get("/")

    @task(2)
    def summary(self):
        self.client.get(f"/gwas/{SAMPLE_STUDY_ID}/")
        self.client.get(f"/gwas/{SAMPLE_STUDY_ID}/data/manhattan/")
        self.client.get(f"/gwas/{SAMPLE_STUDY_ID}/data/qq/")

    @task(2)
    def region(self):
        # Visit html page and api endpoints that power it, simulating a complete user visit to this page
        # A general region where we know there is some data, optionally with a small offset if we ever add caching
        offset = 0  # random.randint(500, 1000)
        start = 21_090_000 + offset
        end = 21_490_000 + offset
        self.client.get(f"/gwas/{SAMPLE_STUDY_ID}/region/?chrom=2&start={start}&end={end}")
        self.client.get(f"/api/v1/gwas/{SAMPLE_STUDY_ID}/data/?chrom=2&start={start}&end={end}")


class WebsiteVisitor(HttpLocust):
    weight = 100

    task_set = ViewOnlyBehavior
    min_wait = 100
    max_wait = 3000
