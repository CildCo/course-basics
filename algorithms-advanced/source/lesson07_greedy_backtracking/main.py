def greedy_coins(coins, amount):
    result = []
    remaining = amount
    for coin in sorted(coins, reverse=True):
        while remaining >= coin:
            remaining -= coin
            result.append(coin)
    return result

coins = [1, 3, 4]
amount = 6
greedy_result = greedy_coins(coins, amount)
print("贪心结果:", greedy_result, "共", len(greedy_result), "枚")


def coin_change(coins, amount):
    dp = [float("inf")] * (amount + 1)
    choice = [-1] * (amount + 1)
    dp[0] = 0

    for value in range(1, amount + 1):
        for coin in coins:
            if coin <= value and dp[value - coin] + 1 < dp[value]:
                dp[value] = dp[value - coin] + 1
                choice[value] = coin

    if dp[amount] == float("inf"):
        return None, dp
    picked = []
    value = amount
    while value > 0:
        picked.append(choice[value])
        value -= choice[value]
    return picked, dp

optimal, dp_table = coin_change(coins, amount)
print("DP 最优结果:", optimal, "共", len(optimal), "枚")
print("前 7 个金额的最少硬币数:", dp_table[:7])


def solve_n_queens(size):
    solutions = []

    def backtrack(row, columns, diagonals, anti_diagonals, board):
        if row == size:
            solutions.append(board[:])
            return
        for column in range(size):
            if column in columns or row - column in diagonals or row + column in anti_diagonals:
                continue
            columns.add(column)
            diagonals.add(row - column)
            anti_diagonals.add(row + column)
            board.append(column)
            backtrack(row + 1, columns, diagonals, anti_diagonals, board)
            board.pop()
            columns.remove(column)
            diagonals.remove(row - column)
            anti_diagonals.remove(row + column)

    backtrack(0, set(), set(), set(), [])
    return solutions

solutions = solve_n_queens(6)
print("6 皇后解的数量:", len(solutions))
for column in solutions[0]:
    print("." * column + "Q" + "." * (6 - column - 1))


for size in range(4, 9):
    count = len(solve_n_queens(size))
    print(f"{size} 皇后解的数量: {count}")
