[ENG](#ENG) || [RUS](#RUS)

# ENG

<h1 align=center>Triangle Arbitrage</h1>

This project is a program for automating the search and implementation of intra-exchange arbitrage. That is, assets are traded on one platform.
In this case, the trader earns on the difference between the rates of one asset in different trading pairs.
Since the arbitrage window in such cases is very short (from a few milliseconds to a few minutes depending on the exchange), it is very difficult to do it manually.

<h2 align=center>Contents</h2>

1. [Features](#Features)
2. [Technologies](#Technologies)
3. [Preparing to work](#Preparing-to-work)
4. [Usage](#Usage)
5. [DISCLAIMER](#DISCLAIMER)

## Features
The main features of this application include:
  + complete autonomy (the user only needs to make initial settings and run the program)
  + speed of operation (high speed of data processing was obtained by using Redis -- NoSQL database, which in this project is used to store rapidly changing prices for selected assets
  + ease of adaptation to other exchanges (in this example, Binance is used, but a similar mechanism can be implemented on other exchanges)

## Technologies

| Technology | Description |
| ----------- | ----------- |
| Python    | Programming language in which the project is implemented   |
| MySQL    | Relational database for storing transaction history   |
| Redis    | Non-relational database  |
| SQLAlchemy    | SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL   |
| Binance SDK    | This is a lightweight library that works as a connector to Binance public API   |
| requests    | An elegant and simple HTTP library for Python   |
| click    | A Python package for creating command line interfaces  |

## Preparing to work
1. Install [Python](https://www.python.org/downloads/)
2. Download the source code of the project
3. Deploy the virtual environment (venv) in the project folder. To do this, open a terminal in the project folder and enter the command:  
   `python3 -m venv venv`
4. Activate the virtual environment with the command  
   `source venv/bin/activate`
5. Install the project dependencies, which are located in the requirements.txt file. To do this, enter the command in the terminal:  
   `pip install -r requirements.txt`
6. Change the values in the file `config.py`
7. Change the values in the file `.env.example` and rename it to `.env`

## Usage
1. Run the `data_preparation.py` file, which is located in the _data_handlers_ folder, with the command:  
   `python3 /data_handlers/data_preparation.py`  
   Once this script is finished, a `divided_pairs_list.json` file will be generated to store lists with trading pairs in the format required by Binance to track changes over WebSockets.
2. Run the `price_updaters.py` file, which is located in the _data_handlers_ folder with the command:  
   `python3 /data_handlers/price_updaters.py $INDEX`  
   _You need to replace $INDEX with an integer, which will correspond to the sequence number of the list of pairs_
3. Run `main.py`

## DISCLAIMER
The user of this software acknowledges that it is provided "as is" without any express or implied warranties. 
The software developer is not liable for any direct or indirect financial losses resulting from the use of this software. 
The user is solely responsible for his/her actions and decisions related to the use of the software.

---

# RUS

<h1 align=center>Triangle Arbitrage</h1>

Этот проект представляет собой программу для автоматизации поиска и реализации внутрибиржевого арбитража. То есть активы торгуются на одной площадке.
В таком случае трейдер зарабатывает на разнице между курсами одного актива в разных торговых парах.
Поскольку арбитражное окно в таких случаях очень короткое (от нескольких милисекунд до нескольких минут в зависимости от биржи), вручную это делать очень сложно.

<h2 align=center>Содержание</h2>

1. [Особенности](#Особенности)
2. [Технологии](#Технологии)
3. [Подготовка к работе](#Подготовка-к-работе)
4. [Использование](#Использование)
5. [ОТКАЗ ОТ ОТВЕТСТВЕННОСТИ](#ОТКАЗ-ОТ-ОТВЕТСТВЕННОСТИ)

## Особенности
Основные особенности этого приложения включают в себя:
  + полная автономность (пользователю необходимо лишь сделать начальные настройки и запустить программу)
  + скорость работы (высокая скорость обработки данных была получена за счет использования Redis -- NoSQL базы данных, который в этом проекте используется для хранения быстроменяющихся цен на выбранные активы
  + простота адаптации под другие биржи (в этом примере используется биржа Binance, однако подобный механизм можно реализовать на других биржах)

## Технологии

| Технология / Библиотека | Описание |
| ----------- | ----------- |
| Python    | Язык программирования, на котором реализован проект   |
| MySQL    | Реляционная база данных для хранения истории сделок   |
| Redis    | Нереляционная база данных для хранения биржевых стаканов по отслеживаемым активам (торговым парам)   |
| SQLAlchemy    | Комплексный набор инструментов для работы с реляционными базами данных в Python   |
| Binance SDK    | Официальный SDK от для взаимодействия с биржей Binance   |
| requests    | HTTP-библиотека для Python. Используется для отправки HTTP-запросов и получения ответов   |
| click    | Парсер аргументов командной строки   |

## Подготовка к работе
1. Установите [Python](https://www.python.org/downloads/)
2. Скачайте исходный код проекта
3. Разверните виртуальное окружение (venv) в папке с проектом. Для этого откройте терминал в папке с проектом и введите команду:  
   `python3 -m venv venv`
4. Активируйте виртуальное окружение командой  
   `source venv/bin/activate`
5. Установите зависимости проекта, которые находятся в файле requirements.txt. Для этого в терминале введите команду:  
   `pip install -r requirements.txt`
6. Измените значения в файле `config.py` на подходящие Вам
7. Внесите изменения в файл `.env.example` и переименуйте его в `.env`

## Использование
1. Запустите файл `data_preparation.py`, который находится в папке _data_handlers_ командой:  
   `python3 /data_handlers/data_preparation.py`  
   После окончания работы этого скрипта будет сгенерирован файл `divided_pairs_list.json`, в котором будут храниться списки с торговыми парами в формате, который требует Binance для отслеживания изменений по WebSockets.
2. Запустите файл `price_updaters.py`, который находится в папке _data_handlers_ командой:  
   `python3 /data_handlers/price_updaters.py $INDEX`  
   _$INDEX Вам необходимо заменить на целое число, которое будет соответствовать порядковому номеру списку пар_
3. Запустите файл `main.py`

## ОТКАЗ ОТ ОТВЕТСТВЕННОСТИ
Пользователь этого программного обеспечения подтверждает, что оно предоставляется "как есть", без каких-либо явных или неявных гарантий. 
Разработчик программного обеспечения не несет ответственности за любые прямые или косвенные финансовые потери, возникшие в результате использования данного программного обеспечения. 
Пользователь несет полную ответственность за свои действия и решения, связанные с использованием программного обеспечения.
