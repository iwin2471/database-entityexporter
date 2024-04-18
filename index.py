import mysql.connector
import os

class TypeScriptEntityGenerator:
    def __init__(self, host, database, user, password, output_dir):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.output_dir = output_dir

    def connect_to_database(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.conn.cursor(dictionary=True)
        except mysql.connector.Error as error:
            print("Error connecting to the database:", error)

    def generate_typescript_entities(self):
        self.cursor.execute("SHOW TABLES")
        tables = self.cursor.fetchall()

        for table in tables:
            table_name = list(table.values())[0]
            typescript_entity = self.generate_typescript_entity(table_name)
            self.write_to_typescript_file(table_name, typescript_entity)

        self.conn.close()

    def generate_typescript_entity(self, table_name):
        self.cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = self.cursor.fetchall()
        classNmae = self.convertToLowerCamelCase(table_name)
        classNmae = classNmae[0].upper() + classNmae[1:]

        typescript_entity = f"export class {classNmae} {{\n"
        for column in columns:
            column_name = column["Field"]
            column_type = column["Type"]
            typescript_type = self.map_mysql_to_typescript(column_type)
            typescript_entity += f"  {self.convertToLowerCamelCase(column_name)}: {typescript_type};\n"
        typescript_entity += "}\n"

        return typescript_entity
    
    def convertToLowerCamelCase(self, text):
        parts = text.split("_")
        camelCaseText = parts[0].lower()
        for part in parts[1:]:
            camelCaseText += part.capitalize()
        return camelCaseText

    def map_mysql_to_typescript(self, mysql_type):
        type_map = {
            "int": "number",
            "bigint": "number",
            "smallint": "number",
            "tinyint": "number",
            "text": "string",
            "varchar": "string",
            "date": "Date",
            "datetime": "Date",
            "timestamp": "Date",
            "boolean": "boolean"
        }
        for key in type_map:
            if mysql_type.startswith(key):
                return type_map[key]
        return "any"

    def write_to_typescript_file(self, table_name, typescript_entity):
        classNmae = self.convertToLowerCamelCase(table_name)
        classNmae = classNmae[0].upper() + classNmae[1:]
        file_name = f"{classNmae}.ts"
        file_path = os.path.join(self.output_dir, file_name)

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            with open(file_path, "w") as file:
                file.write(typescript_entity)
            print(f"TypeScript entity for '{table_name}' written to '{file_path}'")
        except (OSError, IOError) as error:
            print(f"Error writing TypeScript entity for '{table_name}': {error}")

if __name__ == "__main__":
    # Database connection details
    HOST = ""
    DATABASE = ""
    USER = ""
    PASSWORD = ""

    # Output directory for TypeScript files
    OUTPUT_DIR = "./ts"

    generator = TypeScriptEntityGenerator(HOST, DATABASE, USER, PASSWORD, OUTPUT_DIR)
    generator.connect_to_database()
    generator.generate_typescript_entities()