import mysql.connector
import sys

DB_HOST = str(sys.argv[5])
DB_USER = str(sys.argv[6])
DB_PASSWORD = str(sys.argv[7])
DB_PORT = str(sys.argv[8])
DB_DATABASE = str(sys.argv[9])


class DataBase:
    """A class for working with a MySQL database, when initialized, it creates from data from env."""

    def __init__(self):
        """Connects to a database using data from env.
        Return:
            None
        """
        self.connector = mysql.connector.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            database=DB_DATABASE,
            port=DB_PORT,
        )

        self.cursor = self.connector.cursor()

    def send_command(self, command: str):
        """Sends SQL code in the database.
        Args:
            command (str): SQL command.
        Returns:
            set : Reply to the command.
        """
        res = self.cursor.execute(command, multi=True)
        try:
            for self.cursor in res:
                print(self.cursor)
                if self.cursor.with_rows:
                    return self.cursor.fetchall()
        except RuntimeError:  # If there is no result
            pass
        self.connector.commit()

    def disconnect(self):
        """Closes the database connection.
        Return:
            None
        """
        self.connector.close()

    def insert_restaurant(
        self,
        restaurant_name,
        telephone="",
        website="",
        tags=None,
        address="",
        city="",
        zip_code=None,
        latitude=None,
        longitude=None,
        yelp_rating=None,
        google_rating=None,
    ):
        """Creates new entries in the "restaurant", "tag" and "tag_restaurant" tables.
        Args:
            restaurant_name (str): Restaurant name.
            telephone (str): Restaurant phone.
            website (str): Restaurant website.
            tags (list): List of restaurant tags.
            address (str): Restaurant address.
            city (str): Restaurant city.
            zip_code (int): ZIP code of the restaurant.
            latitude (float): latitude.
            longitude (float): longitude.
            yelp_rating (float): Yelp rating.
            google_rating (float): Google rating.
        Return:
            None
        """
        try:
            #  New restaurant
            self.send_command(
                f"INSERT INTO restaurant (restaurant_name, telephone, website, address, city, zip_code, latitude, longitude, yelp_rating, google_rating) VALUES('{restaurant_name}', '{telephone}', '{website}', '{address}', '{city}', {zip_code}, {latitude}, {longitude}, {yelp_rating}, {google_rating});"
            )
        except mysql.connector.errors.IntegrityError:
            print("Restaurant already exist")
            return

        last_restaurant_id = self.send_command("SELECT LAST_INSERT_ID();")[0][0]

        if type(tags) is list:
            for tag in tags:
                res = self.send_command(f"SELECT id FROM tag WHERE title='{tag}'")
                if len(res) == 0:
                    #  If the tag doesn't exist
                    #  New tag
                    self.send_command(f"INSERT INTO tag (title) VALUES('{tag}')")
                    last_tag_id = self.send_command("SELECT LAST_INSERT_ID();")[0][0]
                else:
                    last_tag_id = res[0][0]

                #  New tag_restaurant
                self.send_command(
                    f"INSERT INTO tag_restaurant (tag_id, restaurant_id) VALUES({last_tag_id}, {last_restaurant_id})"
                )

    def crete_table(self):
        """Creates tables "restaurant", "tag" and "tag_restaurant" in the database if there are none..
        Return:
            None
        """
        create_restaurant_table = "CREATE TABLE IF NOT EXISTS restaurant (id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, restaurant_name VARCHAR(50) NOT NULL UNIQUE, telephone VARCHAR(20), website VARCHAR(100), address VARCHAR(100), city VARCHAR(20), zip_code INT(10), latitude float4, longitude float4, yelp_rating float4, google_rating float4);"
        create_tag_table = "CREATE TABLE IF NOT EXISTS tag (id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, title VARCHAR(30) NOT NULL UNIQUE );"
        create_tag_restaurant_table = "CREATE TABLE IF NOT EXISTS tag_restaurant( id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, tag_id INT(6) UNSIGNED NOT NULL, restaurant_id INT(6) UNSIGNED NOT NULL, FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE, FOREIGN KEY (restaurant_id) REFERENCES restaurant(id) ON DELETE CASCADE);"

        self.send_command(create_restaurant_table)
        self.send_command(create_tag_table)
        self.send_command(create_tag_restaurant_table)

    def __delete__(self, instance):
        self.connector.close()
