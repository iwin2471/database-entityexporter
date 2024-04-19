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
        

    def fetch_foreign_keys(self, table_name):
        query = f"""
            SELECT DISTINCT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = '{self.database}' AND REFERENCED_TABLE_NAME IS NOT NULL;
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def generate_typescript_entity(self, table_name):
        self.cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = self.cursor.fetchall()
        foreign_keys = self.fetch_foreign_keys(table_name)
        
        className = self.convertToLowerCamelCase(table_name)
        className = className[0].upper() + className[1:]
        typescript_entity = ';\n'.join(
                f'import {{ {self.convertToUpperCamelCase(fk["REFERENCED_TABLE_NAME"])} }} from \"./{self.convertToUpperCamelCase(fk["REFERENCED_TABLE_NAME"])}\"'
                for fk in foreign_keys)
        typescript_entity += ';\n'

        
        typescript_entity += f"export class {className} {{\n"
        for column in columns:
            column_name = column["Field"]
            column_type = column["Type"]
            typescript_type = self.map_mysql_to_typescript(column_type)
            typescript_entity += f"  {self.convertToLowerCamelCase(column_name)}: {typescript_type};\n"

        # getRelation method
        if foreign_keys:
            relation_body = ', '.join(
                f'"{self.convertToLowerCamelCase(fk["COLUMN_NAME"])}": {self.convertToUpperCamelCase(fk["REFERENCED_TABLE_NAME"])}'
                for fk in foreign_keys
            )
            typescript_entity += f"  static getRelation() {{\n    return {{{relation_body}}};\n  }}\n"

        typescript_entity += "}\n"
        return typescript_entity
    
    def convertToLowerCamelCase(self, text):
        parts = text.split("_")
        camelCaseText = parts[0].lower()
        for part in parts[1:]:
            camelCaseText += part.capitalize()
        return camelCaseText
    
    def convertToUpperCamelCase(self, text):
        parts = text.split("_")
        camelCaseText = parts[0][0].upper() + parts[0][1:]
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
        classNmae = self.convertToUpperCamelCase(table_name)
        file_name = f"{classNmae}.ts"
        file_path = os.path.join(self.output_dir, file_name)

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            with open(file_path, "w") as file:
                file.write(typescript_entity)
            print(f"TypeScript entity for '{table_name}' written to '{file_path}'")
        except (OSError, IOError) as error:
            print(f"Error writing TypeScript entity for '{table_name}': {error}")
    
    def write_index_fille(self):
        index_file_path = os.path.join(self.output_dir, "index.ts")
        try:
            with open(index_file_path, "w") as file:
                file.write("export * from './types';\n")
            print(f"Index file written to '{index_file_path}'")
        except (OSError, IOError) as error:
            print(f"Error writing index file: {error}")

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
