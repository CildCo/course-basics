name = "小居"
age = 3
price = 9.9
is_learning = True

print(name, age, price, is_learning)


print(type(age))
print(type(price))
print(type(name))
print(type(is_learning))


age = age + 1
print(f"{name} 今年 {age} 岁")
print("明年", age + 1, "岁")


age_text = "18"
age_number = int(age_text)
print(age_number + 1)
