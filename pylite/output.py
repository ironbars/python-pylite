from tabulate import tabulate

def print_result(cursor):
    rows = cursor.fetchall()

    if len(rows) > 0:
        headers = tuple(col[0] for col in cursor.description)

        print(tabulate(rows, headers=headers, tablefmt="grid"))
