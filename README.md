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

## Requirements

- Construct **Order** Model in **api** app

  The below information is necessary in **Order** model:

  - Order-number
  - Total-price
  - Created-time

- Construct **import_order** api ( POST method )

  - Validate access token from request data

    ( accepted token is defined in **api/views.py** )

  - Parse data and Save to corresponding fields

- Construct api unittest

---

## Advanced Requirements ( optional )

- Replace the statement of checking api access token with a decorator

- Extend Order model

  - Construct **Product** model
  - Build relationships between **Order** and **Product** model

- Get creative and Extend anything you want
  - add restock api
  - promote code function in import_order api

---

## Submit

- After receiving this pretest, you have to finish it in 7 days
- Create a [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork) and name it with your name (using your Chinese and English name as provided on your resume) ( 王小明(Apple) - 面試 )

- Feel free to let us know if there is any question: sophie.lee@bebit-tech.com
