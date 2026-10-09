import psycopg
from psycopg.conninfo import make_conninfo
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import *
from hashlib import sha256
import configparser
import os
from pathlib import Path
from typing import Optional
from matplotlib import pyplot
from datetime import datetime

cfg = configparser.ConfigParser()
cfg.read(os.environ.get("BUDGET_CFG", Path(__file__).resolve().parent / "cfg.ini"), encoding="utf-8")

def openWindow(self, s, f: Optional[bool] = True, mes: Optional[str] = ""):
    try:
        isTableWindow = (Data.titles.get(s) != None)
        isBalanceWindow = (s == "BalanceWindow")
        self.w = Data.windows.get(s)
        if self.w == None:
            if s == "MainWindow":
                self.w = MainWindow()
            elif s == "SignInWindow":
                self.w = SignInWindow()
            elif s == "UserQueryWindow":
                self.w = UserQueryWindow()
            elif s == "AddOperationWindow":
                self.w = AddOperationWindow()
            elif s == "ModOperationWindow":
                self.w = ModOperationWindow()
            elif s == "DelOperationWindow":
                self.w = DelOperationWindow()
            elif s == "AddArticleWindow":
                self.w = AddArticleWindow()
            elif s == "ModArticleWindow":
                self.w = ModArticleWindow()
            elif s == "DelArticleWindow":
                self.w = DelArticleWindow()
            elif isBalanceWindow:
                self.w = BalanceWindow()
            elif s == "AddBalanceWindow":
                self.w = AddBalanceWindow()
            elif s == "DelBalanceWindow":
                self.w = DelBalanceWindow()
            elif s == "DebitCreditWindow":
                self.w = DebitCreditWindow()
            elif s == "PercentsFlowsWindow":
                self.w = PercentsFlowsWindow()
            elif s == "ReportDialog":
                self.w = ReportDialog()
            elif s == "ReportsWindow":
                self.w = ReportsWindow()
            elif s == "ErrorWindow":
                self.w = ErrorWindow(mes)
            elif isTableWindow:
                self.w = TablesWindow(s)
            else:
                print("EEROROETJGNBSDJLVBHGJ", s)
            Data.windows[s] = self.w
        if isTableWindow or isBalanceWindow:
            self.w.fetch()
        if s == "ErrorWindow":
            self.w.label.setText(mes)
        self.w.show()
        if f:
            self.hide()
    except Exception as e:
        print(f"{repr(e)}")

def fetch(s):
    if Data.windows.get(s) != None:
        Data.windows.get(s).fetch()

class Data:
    conn = None
    f = 0
    windows = {}
    titles = {
        "ops":"Операции и их внешние параметры",
        "arts":"Статьи"
    }
    columns = {
        "ops":["id", "article_id", "article_name", "op_debit", "op_credit", "op_create_date", "bal_id", "bal_create_date", "bal_debit", "bal_credit", "bal_amount"],
        "arts":["id", "name"],
        "BalanceWindow":["id", "create_date", "debit", "credit", "amount"]
    }
    querys = {
        "ops":"SELECT * FROM (SELECT oa.id, article_id, name, oa.debit as o_debit, oa.credit as o_credit, oa.create_date as o_create_date, " +
                            "balance_id, b.create_date as b_create_date, b.debit as b_debit, b.credit as b_credit, b.amount as b_amount " +
                            "FROM (SELECT o.id, article_id, name, debit, credit, create_date, balance_id " +
                            "FROM operations o LEFT JOIN articles a ON o.article_id = a.id) oa LEFT JOIN balance b ON oa.balance_id = b.id) t",
        "arts":"SELECT * FROM articles",
        "BalanceWindow":"SELECT * FROM balance"
    }
    modifyes = ["AddOperationWindow", "ModOperationWindow", "DelOperationWindow", "AddArticleWindow", "ModArticleWindow", "DelArticleWindow"]


class SignInWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Вход")
        self.label = QLabel("Введите логин и пароль")
        self.line1 = QLineEdit()
        self.line2 = QLineEdit()
        self.line2.setEchoMode(QLineEdit.EchoMode.Password)
        button = QPushButton("Войти")
        button.setCheckable(True)
        button.clicked.connect(self.logIn)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.line1)
        layout.addWidget(self.line2)
        layout.addWidget(button)

        container = QWidget()
        container.setLayout(layout)
        self.setFixedSize(QSize(400, 300))

        self.setCentralWidget(container)

    def logIn(self):
        login = sha256(str(self.line1.text()).encode('utf-8')).hexdigest()
        password = sha256(str(self.line2.text()).encode('utf-8')).hexdigest()
        if login == cfg["root"]["login"] and password == cfg["root"]["password"]:
            Data.f = 1
        elif login == cfg["user"]["login"] and password == cfg["user"]["password"]:
            Data.f = 2
        else:
            self.label.setText("Неверный логин или пароль, попробуйте еще")
            return
        try:
            Data.conn = psycopg.connect(make_conninfo(
                host=cfg["db"]["host"], port=cfg["db"]["port"], dbname=cfg["db"]["dbname"],
                user=self.line1.text(), password=self.line2.text()))
            Data.conn.set_autocommit(True)
        except psycopg.Error as e:
            self.label.setText("Не удалось подключиться к БД: " + str(e).strip().splitlines()[0])
            return
        self.line1.clear();
        self.line2.clear();
        openWindow(self, "MainWindow")



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Семейный бюджет")
        label = QLabel("Главное меню")
        opsButton = QPushButton("Просмотр операций")
        opsButton.setCheckable(True)
        opsButton.clicked.connect(self.opsButton)
        artsButton = QPushButton("Просмотр статей")
        artsButton.setCheckable(True)
        artsButton.clicked.connect(self.artsButton)
        balsButton = QPushButton("Журнал балансов")
        balsButton.setCheckable(True)
        balsButton.clicked.connect(self.balsButton)
        dinsButton = QPushButton("Динамика доходов/расходов")
        dinsButton.setCheckable(True)
        dinsButton.clicked.connect(self.dinsButton)
        flowButton = QPushButton("Анализ финансовых потоков по статьям")
        flowButton.setCheckable(True)
        flowButton.clicked.connect(self.flowButton)
        amntButton = QPushButton("Анализ чистой прибыли бюджета")
        amntButton.setCheckable(True)
        amntButton.clicked.connect(self.amntButton)
        repsButton = QPushButton("Формирование отчетов")
        repsButton.setCheckable(True)
        repsButton.clicked.connect(self.repsButton)
        userButton = QPushButton("Пользовательский запрос")
        userButton.setCheckable(True)
        userButton.clicked.connect(self.userButton)
        exitButton = QPushButton("Выйти")
        exitButton.setCheckable(True)
        exitButton.clicked.connect(self.exitButton)
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(opsButton)
        layout.addWidget(artsButton)
        layout.addWidget(balsButton)
        layout.addWidget(dinsButton)
        layout.addWidget(flowButton)
        layout.addWidget(amntButton)
        layout.addWidget(repsButton)
        layout.addWidget(userButton)
        layout.addWidget(exitButton)

        container = QWidget()
        container.setLayout(layout)
        self.setMinimumSize(QSize(400, 300))

        self.setCentralWidget(container)

    def artsButton(self):
        openWindow(self, "arts")

    def opsButton(self):
        openWindow(self, "ops")
        
    def balsButton(self):
        openWindow(self, "BalanceWindow")
        
    def dinsButton(self):
        openWindow(self, "DebitCreditWindow")
        
    def flowButton(self):
        openWindow(self, "PercentsFlowsWindow")

    def amntButton(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute("CALL print_amounts(null)")
                r = cur.fetchall()
                print(r)
                self.pyplotShow(r)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            Data.conn.rollback()

    def pyplotShow(self, r):
        try:
            temp = r[0][0]
            s1 = temp.split('"(\\"')
            s2 = []
            for st in s1:
                s2.append(st.split(')"'))
            print("s2:", s2)
            s1 = sum(s2, [])
            print("s1:", s1)
            s2 = []
            for i in range(len(s1)):
                if i % 2 == 1:
                    s2.append(s1[i].split('\\",'))
            s1 = sum(s2, [])
            print("s1:", s1)
            yd = {}
            for i in range(0, len(s1), 2):
                d = s1[i]
                dt = d[0:10]
                sm = int(s1[i + 1])
                yd[dt] = sm
            print("dict:", yd)
            x = []
            y = []
            for k, v in yd.items():
                x.append(k)
                y.append(v)
            pyplot.plot(x, y, marker='o', linestyle='solid')
            pyplot.title('Прибыль')
            pyplot.show()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def repsButton(self):
        openWindow(self, "ReportsWindow")

    def userButton(self):
        openWindow(self, "UserQueryWindow")

    def exitButton(self):
        openWindow(self, "SignInWindow")



class UserQueryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.setWindowTitle("Пользовательский запрос")
            label = QLabel("Введите запрос без кавычек")
            self.line = QLineEdit()
            button = QPushButton("Обработать")
            button.setCheckable(True)
            button.clicked.connect(self.proceed)
            exitButton = QPushButton("Назад, в главное меню")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(label)
            layout.addWidget(self.line)
            layout.addWidget(button)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)
            self.setFixedSize(QSize(400, 300))

            self.setCentralWidget(container)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def proceed(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute(str(self.line.text()))
                for record in cur:
                    print(record)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            with Data.conn.cursor() as cur:
                cur.execute("rollback")

    def exitButton(self):
        openWindow(self, "MainWindow")
        fetch("ops")
        fetch("arts")



class TablesWindow(QMainWindow):
    def __init__(self, s):
        super().__init__()
        try:
            self.s = s
            self.setWindowTitle(Data.titles.get(s))
            v = Data.columns.get(s)
            self.length = len(v)
            self.table = QTableWidget()
            self.table.setColumnCount(self.length)
            for i in range (self.length):
                self.table.setHorizontalHeaderItem(i, QTableWidgetItem(v[i]))
            addButton = QPushButton("Добавить")
            addButton.setCheckable(True)
            addButton.clicked.connect(self.addButton)
            modButton = QPushButton("Изменить")
            modButton.setCheckable(True)
            modButton.clicked.connect(self.modButton)
            delButton = QPushButton("Удалить")
            delButton.setCheckable(True)
            delButton.clicked.connect(self.delButton)

            exitButton = QPushButton("Назад, в главное меню")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(self.table)
            layout.addWidget(addButton)
            layout.addWidget(modButton)
            layout.addWidget(delButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)
            if s == "ops":
                self.setMinimumSize(QSize(1160, 500))
            elif s == "arts":
                self.setMinimumSize(QSize(300, 500))

            self.setCentralWidget(container)
            self.fetch()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def fetch(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute(Data.querys.get(self.s))
                records = cur.fetchall()
                self.table.setRowCount(len(records))
                for i in range (self.length):
                    for row, record in enumerate(records):
                        self.table.setItem(row, i, QTableWidgetItem(str(record[i])))
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            with Data.conn.cursor() as cur:
                cur.execute("rollback")

    def addButton(self):
        if self.s == "ops":
            openWindow(self, "AddOperationWindow", False)
        elif self.s == "arts":
            openWindow(self, "AddArticleWindow", False)
        else:
            openWindow(self, "ErrorWindow", False, "NO ADD")
        
    def modButton(self):
        if self.s == "ops":
            openWindow(self, "ModOperationWindow", False)
        elif self.s == "arts":
            openWindow(self, "ModArticleWindow", False)
        else:
            openWindow(self, "ErrorWindow", False, "NO MOD")

    def delButton(self):
        if self.s == "ops":
            openWindow(self, "DelOperationWindow", False)
        elif self.s == "arts":
            openWindow(self, "DelArticleWindow", False)
        else:
            openWindow(self, "ErrorWindow", False, "NO DEL")

    def exitButton(self):
        for w in Data.modifyes:
            if Data.windows.get(w) != None and Data.windows.get(w).isVisible():
                self.hide()
                return
        openWindow(self, "MainWindow")



class BalanceWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.s = "BalanceWindow"
            self.setWindowTitle("Балансы")
            v = Data.columns.get(self.s)
            self.length = len(v)
            self.table = QTableWidget()
            self.table.setColumnCount(self.length)
            for i in range (self.length):
                self.table.setHorizontalHeaderItem(i, QTableWidgetItem(v[i]))
            addButton = QPushButton("Сформировать")
            addButton.setCheckable(True)
            addButton.clicked.connect(self.addButton)
            delButton = QPushButton("Расформировать")
            delButton.setCheckable(True)
            delButton.clicked.connect(self.delButton)

            exitButton = QPushButton("Назад, в главное меню")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(self.table)
            layout.addWidget(addButton)
            layout.addWidget(delButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)
            self.setMinimumSize(QSize(1160, 500))

            self.setCentralWidget(container)
            self.fetch()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def fetch(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute(Data.querys.get(self.s))
                records = cur.fetchall()
                self.table.setRowCount(len(records))
                for i in range (self.length):
                    for row, record in enumerate(records):
                        self.table.setItem(row, i, QTableWidgetItem(str(record[i])))
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            with Data.conn.cursor() as cur:
                cur.execute("rollback")

    def addButton(self):
        openWindow(self, "AddBalanceWindow", False)

    def delButton(self):
        openWindow(self, "DelBalanceWindow", False)

    def exitButton(self):
        openWindow(self, "MainWindow")



class AddBalanceWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setWindowTitle("Формирование баланса")
            self.label = QLabel("Введите дату, которая будет закрывать баланс")
            self.line = QLineEdit()
            addButton = QPushButton("Сформировать")
            addButton.setCheckable(True)
            addButton.clicked.connect(self.addButton)
            exitButton = QPushButton("Закрыть")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(self.label)
            layout.addWidget(self.line)
            layout.addWidget(addButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)

            self.setCentralWidget(container)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def addButton(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute("CALL insert_balance('" + self.line.text() + "');")
                Data.conn.commit()
            self.exitButton()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            Data.conn.rollback()

    def exitButton(self):
        openWindow(self, "BalanceWindow")



class DelBalanceWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setWindowTitle("Расформирование баланса")
            self.line = QLineEdit()
            delButton = QPushButton("Удалить")
            delButton.setCheckable(True)
            delButton.clicked.connect(self.delButton)
            exitButton = QPushButton("Назад, к балансам")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Введите id баланса, который хотите расформировать"))
            layout.addWidget(self.line)
            layout.addWidget(delButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)

            self.setCentralWidget(container)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def delButton(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute("DELETE FROM balance WHERE id = " + self.line.text())
                Data.conn.commit()
            self.exitButton()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            Data.conn.rollback()

    def exitButton(self):
        openWindow(self, "BalanceWindow")



class DebitCreditWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setWindowTitle("Построение динамики доходов/расходов")
            self.check1 = QCheckBox("Доходы")
            self.check1.setCheckable(True)
            self.check2 = QCheckBox("Расходы")
            self.check2.setCheckable(True)
            self.line1 = QLineEdit()
            self.line2 = QLineEdit()
            self.checks = []
            with Data.conn.cursor() as cur:
                cur.execute("SELECT name FROM articles")
                self.names = cur.fetchall()
                cur.execute("SELECT id FROM articles")
                self.ids = cur.fetchall()
                for i in range(len(self.ids)):
                    self.checks.append(QCheckBox(self.names[i][0]))
                    self.checks[i].setCheckable(True)
            opsButton = QPushButton("Просмотр операций")
            opsButton.setCheckable(True)
            opsButton.clicked.connect(self.opsButton)
            artsButton = QPushButton("Просмотр статей")
            artsButton.setCheckable(True)
            artsButton.clicked.connect(self.artsButton)
            addButton = QPushButton("Построить")
            addButton.setCheckable(True)
            addButton.clicked.connect(self.addButton)
            exitButton = QPushButton("Назад, в главное меню")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(self.check1)
            layout.addWidget(self.check2)
            layout.addWidget(QLabel("Введите дату начала периода анализа"))
            layout.addWidget(self.line1)
            layout.addWidget(QLabel("Введите дату конца периода анализа"))
            layout.addWidget(self.line2)
            for check in self.checks:
                layout.addWidget(check)
            layout.addWidget(artsButton)
            layout.addWidget(opsButton)
            layout.addWidget(addButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)

            self.setCentralWidget(container)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def artsButton(self):
        openWindow(self, "arts", False)

    def opsButton(self):
        openWindow(self, "ops", False)

    def addButton(self):
        try:
            isDebit = self.check1.isChecked()
            isCredit = self.check2.isChecked()
            isArticle = []
            f = False
            for check in self.checks:
                isArticle.append(check.isChecked())
                if check.isChecked():
                    f = True
            if f == False:
                raise RuntimeError("Вы не выбрали ни одной статьи")
            fl = 0
            if not(isDebit or isCredit):
                raise RuntimeError("Вы не выбрали ни доходы, ни расходы")
            elif isDebit and isCredit:
                fl += 6
            elif isDebit:
                fl += 2
            else:
                fl += 3
            beg = self.line1.text()
            end = self.line2.text()
            idsChecked = []
            namesChecked = []
            for i in range(len(isArticle)):
                if isArticle[i]:
                    idsChecked.append(self.ids[i][0])
                    namesChecked.append(self.names[i][0])
            s = str(idsChecked)
            s = s.replace('[', '{')
            s = s.replace('(', '')
            s = s.replace(',)', '')
            s = s.replace(']', '}')
            with Data.conn.cursor() as cur:
                cur.execute("CALL print_debit_credit_on_period(" + str(fl) + ", '" + beg + "', '" + end + "', '" + s + "', null, null, null)")
                r = cur.fetchall()
                x = r[0][2]
                xi = []
                for i in x:
                    xi.append(str(i)[0:10])
                x = xi
                if fl % 2 == 0:
                    self.pyplotShow(0, x, r)
                if fl % 3 == 0:
                    self.pyplotShow(1, x, r)
            self.exitButton()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            Data.conn.rollback()

    def pyplotShow(self, n, x, r):
        try:
            temp = r[0][n]
            s1 = temp.split('"(')
            s2 = []
            for st in s1:
                s2.append(st.split(')"'))
            print("s2:", s2)
            s1 = sum(s2, [])
            print("s1:", s1)
            s2 = []
            for i in range(len(s1)):
                if i % 2 == 1:
                    s2.append(s1[i].split('\\"'))
            s1 = sum(s2, [])
            print("s1:", s1)
            s2 = []
            for st in s1:
                s2.append(st.split(','))
            s1 = sum(s2, [])
            print("s1:", s1)
            for i in range(int(2 * len(s1) / 5)):
                s1.remove('')
            print("s1:", s1)
            yd = {}
            for i in range(0, len(s1), 3):
                d = s1[i + 1]
                dt = d[0:10]
                sm = int(s1[i + 2])
                yd.setdefault(int(s1[i]), []).append((dt, sm))
            print("dict:", yd)
            for k, v in yd.items():
                yi = [0]*(len(x))
                for s in v:
                    i = x.index(s[0])
                    yi[i] = s[1]
                print("yi:", yi)
                s = 'debit' if n == 0 else 'credit'
                s += ' of ' + str(k) + 'article'
                pyplot.plot(x, yi, marker='o', linestyle='solid', label=s)
                pyplot.title('Доходы' if n == 0 else 'Расходы')
                pyplot.legend()
                pyplot.show()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def exitButton(self):
        openWindow(self, "MainWindow")



class PercentsFlowsWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setWindowTitle("Построение анализа финансовых потоков по статьям")
            self.check1 = QCheckBox("Доходы")
            self.check1.setCheckable(True)
            self.check2 = QCheckBox("Расходы")
            self.check2.setCheckable(True)
            self.check3 = QCheckBox("Прибыль")
            self.check3.setCheckable(True)
            self.line1 = QLineEdit()
            self.line2 = QLineEdit()
            self.checks = []
            with Data.conn.cursor() as cur:
                cur.execute("SELECT name FROM articles")
                self.names = cur.fetchall()
                cur.execute("SELECT id FROM articles")
                self.ids = cur.fetchall()
                for i in range(len(self.names)):
                    self.checks.append(QCheckBox(self.names[i][0]))
                    self.checks[i].setCheckable(True)
            addButton = QPushButton("Построить")
            addButton.setCheckable(True)
            addButton.clicked.connect(self.addButton)
            exitButton = QPushButton("Назад, в главное меню")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Выберите один тип потоков для анализа"))
            layout.addWidget(self.check1)
            layout.addWidget(self.check2)
            layout.addWidget(self.check3)
            layout.addWidget(QLabel("Введите дату начала периода анализа"))
            layout.addWidget(self.line1)
            layout.addWidget(QLabel("Введите дату конца периода анализа"))
            layout.addWidget(self.line2)
            layout.addWidget(QLabel("Выберите статьи для анализа"))
            for check in self.checks:
                layout.addWidget(check)
            layout.addWidget(addButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)

            self.setCentralWidget(container)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def addButton(self):
        try:
            isDebit = self.check1.isChecked()
            isCredit = self.check2.isChecked()
            isAmount = self.check3.isChecked()
            isArticle = []
            f = False
            for check in self.checks:
                isArticle.append(check.isChecked())
                if check.isChecked():
                    f = True
            if f == False:
                raise RuntimeError("Вы не выбрали ни одной статьи")
            fl = ""
            if not(isDebit or isCredit or isAmount):
                raise RuntimeError("Вы не выбрали ни один тип потоков")
            elif (isDebit and isCredit) or (isDebit and isAmount) or (isCredit and isAmount):
                raise RuntimeError("Вы выбрали слишком много типов потоков")
            elif isDebit:
                fl += "debit"
            elif isCredit:
                fl += "credit"
            elif isAmount:
                fl += "amount"
            self.idsChecked = []
            self.namesChecked = []
            for i in range(len(isArticle)):
                if isArticle[i]:
                    self.idsChecked.append(self.ids[i][0])
                    self.namesChecked.append(self.names[i][0])
            s = str(self.namesChecked)
            s = s.replace('[', '{')
            s = s.replace('(', '')
            s = s.replace(',)', '')
            s = s.replace(']', '}')
            s = s.replace("'", '"')
            beg = self.line1.text()
            end = self.line2.text()
            with Data.conn.cursor() as cur:
                cur.execute("CALL calculate_percents_flow_p('" + beg + "', '" + end + "', '" + s + "', '" + fl + "', null)")
                r = cur.fetchall()
                self.pyplotShow(r)
            self.exitButton()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            Data.conn.rollback()

    def pyplotShow(self, r):
        try:
            temp = r[0][0]
            s1 = temp.split('"(')
            s2 = []
            for st in s1:
                s2.append(st.split(')"'))
            s1 = sum(s2, [])
            s2 = []
            for i in range(len(s1)):
                if i % 2 == 1:
                    s2.append(s1[i].split(','))
            s1 = sum(s2, [])
            yd = {}
            for i in range(0, len(s1), 2):
                yd[int(s1[i])] = float(s1[i + 1])
            y = []
            x = []
            for k, v in yd.items():
                if v > 0:
                    y.append(v)
                    x.append(self.namesChecked[self.idsChecked.index(k)])
            pyplot.pie(y, labels=x)
            pyplot.title('Финансовые потоки')
            pyplot.show()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def exitButton(self):
        openWindow(self, "MainWindow")



class ReportDialog(QDialog):
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle("Выбор имени файла")
            layout = QVBoxLayout()
            self.name_input = QLineEdit()
            layout.addWidget(QLabel("""Введите имя txt файла, в который выгрузится таблица"""))
            layout.addWidget(self.name_input)
            addButton = QPushButton("Экспорт")
            addButton.setCheckable(True)
            addButton.clicked.connect(self.addButton)
            addButton.clicked.connect(self.accept)
            exitButton = QPushButton("Назад")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            exitButton.clicked.connect(self.reject)
            layout.addWidget(addButton)
            layout.addWidget(exitButton)
            self.setLayout(layout)
        except Exception as e:
            self.message.information(self, "Ошибка", f"{repr(e)}")
            print(f"Произошла ошибка: {repr(e)}")

    def get_data(self):
        try:
            return self.name_input.text()
        except Exception as e:
            print(f"Произошла ошибка: {repr(e)}")

    def addButton(self):
        openWindow(self, "ReportsWindow")
            
    def exitButton(self):
        openWindow(self, "MainWindow")


class ReportsWindow(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle("Отчеты")
            self.setFixedSize(QSize(400,200))
            button1= QPushButton("""Эскпорт балансов за все время существования бюджета в txt""")
            button1.setCheckable(True)
            button1.clicked.connect(self.save_balance)
            button2= QPushButton("Экспорт списка всех проведенных операций в txt")
            button2.setCheckable(True)
            button2.clicked.connect(self.save_operations)
            button3 = QPushButton("Назад, в главное меню")
            button3.setCheckable(True)
            button3.clicked.connect(self.back_to_the_main_menu)
            self.message = QMessageBox()
            self.layout = QVBoxLayout()
            self.layout.addWidget(button1)
            self.layout.addWidget(button2)
            self.s1 = "BalanceWindow"
            v = Data.columns.get(self.s1)
            self.length1 = len(v)
            self.table1 = QTableWidget()
            self.table1.setColumnCount(self.length1)
            for i in range (self.length1):
                self.table1.setHorizontalHeaderItem(i, QTableWidgetItem(v[i]))
            with Data.conn.cursor() as cur:
                cur.execute(Data.querys.get(self.s1))
                records = cur.fetchall()
                self.table1.setRowCount(len(records))
                for i in range (self.length1):
                    for row, record in enumerate(records):
                        self.table1.setItem(row, i, QTableWidgetItem(str(record[i])))
            self.s2 = "ops"
            v = Data.columns.get(self.s2)
            self.length2 = len(v)
            self.table2 = QTableWidget()
            self.table2.setColumnCount(self.length2)
            for i in range (self.length2):
                self.table2.setHorizontalHeaderItem(i, QTableWidgetItem(v[i]))
            with Data.conn.cursor() as cur:
                cur.execute(Data.querys.get(self.s2))
                records = cur.fetchall()
                self.table2.setRowCount(len(records))
                for i in range (self.length2):
                    for row, record in enumerate(records):
                        self.table2.setItem(row, i, QTableWidgetItem(str(record[i])))
            self.layout.addWidget(button3)
            self.table1.hide()
            self.table2.hide()
            self.layout.addWidget(self.table1)
            self.layout.addWidget(self.table2)
            self.container = QWidget()
            self.container.setLayout(self.layout)
            self.setCentralWidget(self.container)
        except Exception as e:
            print(f"Произошла ошибка: {repr(e)}")

    def save_balance(self):
        try:
            dialog = ReportDialog()
            if dialog.exec():
                name = dialog.get_data()
                self.export_table_to_txt(self.table1, name + ".txt")
        except Exception as e:            
            self.message.information(self, "Ошибка", f"{repr(e)}")
            print(f"Произошла ошибка: {repr(e)}")

    def save_operations(self):
        try:
            dialog = ReportDialog()
            if dialog.exec():
                name = dialog.get_data()
                self.export_table_to_txt(self.table2, name + ".txt")
        except Exception as e:
            self.message.information(self, "Ошибка", f"{repr(e)}")
            print(f"Произошла ошибка: {repr(e)}")

    def calculate_column_widths(self,table_widget):
        max_widths = []
        for col in range(table_widget.columnCount()):
            max_width = 0
            for row in range(1):
                item = table_widget.item(row, col)
                if item:
                    text_width = len(item.text())
                    max_width = max(max_width, text_width)
            max_widths.append(max_width)
        return max_widths

    def export_table_to_txt(self, table_widget, filename):
        try:
            max_widths = self.calculate_column_widths(table_widget)
            max_w = max(max_widths)
            data = []
            headers = []
            headers = [table_widget.horizontalHeaderItem(i).text() + ' ' *(max_w - len(table_widget.horizontalHeaderItem(i).text())) for i in range(table_widget.columnCount())]
            for row in range(table_widget.rowCount()):
                row_data = []
                for col in range(table_widget.columnCount()):
                    item = table_widget.item(row, col)
                    if item:
                        text = item.text()
                        padding = ' ' * (max_w - len(text))
                        row_data.append(text + padding)
                    else:
                        row_data.append('')
                data.append(row_data)
            with open(filename, 'w') as f:
                f.write('\t'.join(headers) + '\n')
                for row in data:
                    formatted_row = '\t'.join(row)
                    f.write(formatted_row + '\n')
            self.message.information(self, "Успех", f"Данные таблицы успешно сохранены в файл {filename}")
        except Exception as e:
            print(f"Произошла ошибка при экспорте в txt-файл: {repr(e)}")
    def back_to_the_main_menu(self):
        openWindow(self, "MainWindow")



class AddOperationWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setWindowTitle("Добавление операции")
            self.line1 = QLineEdit()
            self.line2 = QLineEdit()
            self.line3 = QLineEdit()
            self.line4 = QLineEdit()
            opsButton = QPushButton("Просмотр операций")
            opsButton.setCheckable(True)
            opsButton.clicked.connect(self.opsButton)
            artsButton = QPushButton("Просмотр статей")
            artsButton.setCheckable(True)
            artsButton.clicked.connect(self.artsButton)
            addButton = QPushButton("Добавить")
            addButton.setCheckable(True)
            addButton.clicked.connect(self.addButton)
            exitButton = QPushButton("Назад, к операциям")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Введите название статьи новой операции"))
            layout.addWidget(self.line1)
            layout.addWidget(QLabel("Введите доход от новой операции"))
            layout.addWidget(self.line2)
            layout.addWidget(QLabel("Введите расход от новой операции"))
            layout.addWidget(self.line3)
            layout.addWidget(QLabel("Введите дату проведения новой операции в формате дд-мм-гггг"))
            layout.addWidget(self.line4)
            layout.addWidget(artsButton)
            layout.addWidget(opsButton)
            layout.addWidget(addButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)

            self.setCentralWidget(container)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def artsButton(self):
        openWindow(self, "arts", False)

    def opsButton(self):
        openWindow(self, "ops", False)

    def addButton(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute("INSERT INTO operations (article_id, debit, credit, create_date) VALUES " + "((SELECT id FROM articles WHERE name = '"  +
                            self.line1.text() + "' LIMIT 1), " + self.line2.text() + ", " + self.line3.text() + ", '" + self.line4.text() + "')")
                Data.conn.commit()
            self.exitButton()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            Data.conn.rollback()

    def exitButton(self):
        openWindow(self, "ops")
        fetch("arts")



class ModOperationWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setWindowTitle("Изменение операции")
            self.line1 = QLineEdit()
            self.line2 = QLineEdit()
            self.line3 = QLineEdit()
            self.line4 = QLineEdit()
            self.line5 = QLineEdit()
            opsButton = QPushButton("Просмотр операций")
            opsButton.setCheckable(True)
            opsButton.clicked.connect(self.opsButton)
            artsButton = QPushButton("Просмотр статей")
            artsButton.setCheckable(True)
            artsButton.clicked.connect(self.artsButton)
            modButton = QPushButton("Изменить")
            modButton.setCheckable(True)
            modButton.clicked.connect(self.modButton)
            exitButton = QPushButton("Назад, к операциям")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Введите id операции, которую хотите изменить (если какое-то поле изменять не надо, оставьте его пустым)"))
            layout.addWidget(self.line1)
            layout.addWidget(QLabel("Введите изменённое название статьи"))
            layout.addWidget(self.line2)
            layout.addWidget(QLabel("Введите изменённый доход от операции"))
            layout.addWidget(self.line3)
            layout.addWidget(QLabel("Введите изменённый расход от операции"))
            layout.addWidget(self.line4)
            layout.addWidget(QLabel("Введите изменённую дату операции в формате дд-мм-гггг"))
            layout.addWidget(self.line5)
            layout.addWidget(artsButton)
            layout.addWidget(opsButton)
            layout.addWidget(modButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)

            self.setCentralWidget(container)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def artsButton(self):
        openWindow(self, "arts", False)

    def opsButton(self):
        openWindow(self, "ops", False)

    def modButton(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute("SELECT name, debit, credit, create_date FROM operations o JOIN articles a ON o.article_id = a.id WHERE o.id = " +
                            self.line1.text())
                r = cur.fetchone()
                name = r[0] if self.line2.text() == "" else self.line2.text()
                debit = r[1] if self.line3.text() == "" else self.line3.text()
                credit = r[2] if self.line4.text() == "" else self.line4.text()
                create_date = r[3] if self.line5.text() == "" else self.line5.text()
                cur.execute("SELECT id FROM articles a WHERE a.name = '" + name + "'")
                r = cur.fetchone()
                cur.execute("UPDATE operations SET article_id = '" + str(r[0]) + "', debit = " + str(debit) + ", credit = " + str(credit) +
                            ", create_date = '" + str(create_date) + "' WHERE id = " + self.line1.text())
                Data.conn.commit()
            self.exitButton()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            Data.conn.rollback()

    def exitButton(self):
        openWindow(self, "ops")
        fetch("arts")



class DelOperationWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setWindowTitle("Удаление операции")
            self.line = QLineEdit()
            delButton = QPushButton("Удалить")
            delButton.setCheckable(True)
            delButton.clicked.connect(self.delButton)
            exitButton = QPushButton("Назад, к операциям")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Введите id операции, которую хотите удалить"))
            layout.addWidget(self.line)
            layout.addWidget(delButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)

            self.setCentralWidget(container)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def delButton(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute("DELETE FROM operations WHERE id = " + self.line.text())
                Data.conn.commit()
            self.exitButton()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            Data.conn.rollback()

    def exitButton(self):
        openWindow(self, "ops")
        fetch("arts")



class AddArticleWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setWindowTitle("Добавление статьи")
            self.line = QLineEdit()
            artsButton = QPushButton("Просмотр статей")
            artsButton.setCheckable(True)
            artsButton.clicked.connect(self.artsButton)
            addButton = QPushButton("Добавить")
            addButton.setCheckable(True)
            addButton.clicked.connect(self.addButton)
            exitButton = QPushButton("Назад, к статьям")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Введите название новой статьи"))
            layout.addWidget(self.line)
            layout.addWidget(artsButton)
            layout.addWidget(addButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)

            self.setCentralWidget(container)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def artsButton(self):
        openWindow(self, "arts", False)

    def addButton(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute("INSERT INTO articles (name) VALUES ('" + self.line.text() + "')")
                Data.conn.commit()
            self.exitButton()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            Data.conn.rollback()

    def exitButton(self):
        openWindow(self, "arts")
        fetch("ops")



class ModArticleWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setWindowTitle("Изменение статьи")
            self.line1 = QLineEdit()
            self.line2 = QLineEdit()
            artsButton = QPushButton("Просмотр статей")
            artsButton.setCheckable(True)
            artsButton.clicked.connect(self.artsButton)
            modButton = QPushButton("Изменить")
            modButton.setCheckable(True)
            modButton.clicked.connect(self.modButton)
            exitButton = QPushButton("Назад, к статьям")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Введите id статьи, которую хотите изменить"))
            layout.addWidget(self.line1)
            layout.addWidget(QLabel("Введите изменённое название статьи"))
            layout.addWidget(self.line2)
            layout.addWidget(artsButton)
            layout.addWidget(modButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)

            self.setCentralWidget(container)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def artsButton(self):
        openWindow(self, "arts", False)

    def modButton(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute("UPDATE articles SET name = '" + self.line2.text() + "' WHERE id = " + self.line1.text())
                Data.conn.commit()
            self.exitButton()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            Data.conn.rollback()

    def exitButton(self):
        openWindow(self, "arts")
        fetch("ops")



class DelArticleWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setWindowTitle("Удаление статьи")
            self.line = QLineEdit()
            delButton = QPushButton("Удалить")
            delButton.setCheckable(True)
            delButton.clicked.connect(self.delButton)
            exitButton = QPushButton("Назад, к статьям")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Введите id статьи, которую хотите удалить"))
            layout.addWidget(self.line)
            layout.addWidget(delButton)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)

            self.setCentralWidget(container)
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")

    def delButton(self):
        try:
            with Data.conn.cursor() as cur:
                cur.execute("DELETE FROM articles WHERE id = " + self.line.text())
                Data.conn.commit()
            self.exitButton()
        except Exception as e:
            openWindow(self, "ErrorWindow", False, f"{repr(e)}")
            Data.conn.rollback()

    def exitButton(self):
        openWindow(self, "arts")
        fetch("ops")



class ErrorWindow(QMainWindow):
    def __init__(self, s):
        super().__init__()

        try:
            self.setWindowTitle("Ошибка")
            self.label = QLabel(s)
            self.setMaximumSize(QSize(500, 500))
            exitButton = QPushButton("Закрыть")
            exitButton.setCheckable(True)
            exitButton.clicked.connect(self.exitButton)
            layout = QVBoxLayout()
            layout.addWidget(self.label)
            layout.addWidget(exitButton)

            container = QWidget()
            container.setLayout(layout)

            self.setCentralWidget(container)
        except Exception as e:
            print(f"{repr(e)}")

    def exitButton(self):
        try:
            self.hide()
        except Exception as e:
            print(f"{repr(e)}")


def main():
    app = QApplication([])
    window = SignInWindow()
    window.show()
    Data.windows["SignInWindow"] = window
    app.exec()


if __name__ == "__main__":
    main()
