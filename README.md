# Omni Pretest

## Setup Environment

- Download [docker](https://www.docker.com/get-started) and Install

- [Fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) this **pretest** project to your own repository

- Clone **pretest** project from your own repository

  ```
  git clone https://github.com/[your own account]/pretest.git
  ```

- Checkout **pretest** directory

  ```
  cd pretest
  ```

- Start docker container

  ```
  docker-compose up
  ```

- Enter activated **pretest-web-1** container

  ```
  docker exec -it pretest_web_1 bash
  ```

  Note:

  - This container codebase is connected to **pretest** project local codebase
  - If you need to migrate migration files or test testcases, make sure do it in **pretest-web-1** container

- run test case

  ```
  python manage.py test
  ```

---

## Fulfill the following requirements

- Construct **Order** Model in **api** app

- Construct **import_order** api ( POST method )

- Replace the statement of checking api access token with a decorator

- Extend Order model

  - Construct **Product** model
  - Build relationships between **Order** and **Product** model

## Get creative and Extend anything you want

- add restock api
- promote code function in import_order api
