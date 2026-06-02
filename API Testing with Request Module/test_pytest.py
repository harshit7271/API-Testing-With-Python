"""class TestClass:
    def testMethod(self):
        print("This is method 1")

    def testMethod2(self):
        print("This is method 2")
        
"""
import pytest


@pytest.mark.dependency()
@pytest.mark.order(1)
def test_open_app():
    print("APP Opened")


@pytest.mark.dependency(depends=["test_login"])
@pytest.mark.order(3)
def test_dashboard():
    print("dashboard Loaded")


@pytest.mark.dependency(depends=["test_open_app"])
@pytest.mark.order(2)
def test_login():
    print("Login successful")
