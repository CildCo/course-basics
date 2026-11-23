class Employee:
    def __init__(self, name, base_salary):
        self.name = name
        self.base_salary = base_salary

    def monthly_pay(self):
        return self.base_salary

    def describe(self):
        return f"{self.name}：月薪 {self.monthly_pay()} 元"


class Engineer(Employee):
    def __init__(self, name, base_salary, project_bonus):
        super().__init__(name, base_salary)
        self.project_bonus = project_bonus

    def monthly_pay(self):
        return self.base_salary + self.project_bonus


class Manager(Employee):
    def __init__(self, name, base_salary, team_size):
        super().__init__(name, base_salary)
        self.team_size = team_size

    def monthly_pay(self):
        return self.base_salary + self.team_size * 500


people = [
    Employee("小陈", 8000),
    Engineer("小林", 9000, 1500),
    Manager("小周", 12000, 6),
]
for person in people:
    print(person.describe())


class MarkdownFormatter:
    def render(self, rows):
        head = "| 月份 | 销售额 |\n| --- | --- |"
        body = "\n".join(f"| {month} | {amount} |" for month, amount in rows)
        return head + "\n" + body


class CsvFormatter:
    def render(self, rows):
        lines = ["month,amount"]
        lines += [f"{month},{amount}" for month, amount in rows]
        return "\n".join(lines)


class Report:
    def __init__(self, title, formatter):
        self.title = title
        self.formatter = formatter

    def render(self, rows):
        return f"# {self.title}\n\n" + self.formatter.render(rows)


rows = [("1月", 12000), ("2月", 15000), ("3月", 13800)]
report = Report("一季度销售", MarkdownFormatter())
print(report.render(rows))

report.formatter = CsvFormatter()
print()
print(report.render(rows))


# 加一种 JSON 输出，只需要新写一个格式化器，Report 不用动
class JsonFormatter:
    def render(self, rows):
        import json

        return json.dumps(
            [{"month": month, "amount": amount} for month, amount in rows],
            ensure_ascii=False,
        )


report.formatter = JsonFormatter()
print(report.render(rows))
