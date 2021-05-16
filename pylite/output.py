from tabulate import tabulate

def print_result(cursor):
    headers = tuple(col[0] for col in cursor.description)

    print(tabulate(cursor, headers=headers, tablefmt="grid"))
