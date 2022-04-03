#!/bin/bash

rm -rf allure_result/*
pytest -v --alluredir allure_result
allure serve allure_result/