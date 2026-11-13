import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="YOUR_PASSWORD",
        database="Qalam"
    )


if __name__ == "__main__":
    connection = get_connection()
    print("Connected to Qalam successfully!")
    connection.close()