import weewx
import weewx.engine
import weewx.manager
import sqlite3
import mysql.connector
from datetime import datetime
import syslog

class RainTotals(weewx.engine.StdService):
    """
    Service to calculate and store rain totals by week, month, and year
    Supports both MySQL and SQLite databases
    """
    
    def __init__(self, engine, config_dict):
        super(RainTotals, self).__init__(engine, config_dict)

        self.conn = None
        self.cursor = None
        self.db_type = None

        try:
            # Detect database type and get configuration
            db_config = self._get_db_config(config_dict)
            self.db_type = db_config['type']
            
            # Connect to appropriate database
            if self.db_type == 'mysql':
                self._connect_mysql(db_config)
            else:  # sqlite
                self._connect_sqlite(db_config)
            
            self._log(f"Connected to {self.db_type.upper()} database.")

            # Create tables and process data
            self._create_tables()
            self._process_weekly_totals()
            self._process_monthly_totals()
            self._process_yearly_totals()

        except Exception as e:
            self._log(f"Error in RainTotals service: {e}", error=True)

    def _get_db_config(self, config_dict):
        """Detect database type and extract configuration"""
        # Get the database binding information
        wx_binding = config_dict['Station'].get('binding', 'wx_binding')
        archive_db = config_dict['DataBindings'][wx_binding]['database']
        db_section = config_dict['Databases'][archive_db]
        
        # Determine database type
        db_type = db_section.get('database_type', '').lower()
        
        if db_type == 'mysql':
            mysql_config = config_dict['DatabaseTypes']['MySQL']
            return {
                'type': 'mysql',
                'host': mysql_config.get('host', 'localhost'),
                'port': mysql_config.get('port', 3306),
                'user': mysql_config['user'],
                'password': mysql_config['password'],
                'database': db_section['database_name']
            }
        else:  # Default to SQLite
            return {
                'type': 'sqlite',
                'database_name': db_section['database_name']
            }

    def _connect_mysql(self, db_config):
        """Connect to MySQL database"""
        self.conn = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        self.cursor = self.conn.cursor()

    def _connect_sqlite(self, db_config):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(db_config['database_name'])
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        """Create tables with database-specific SQL"""
        if self.db_type == 'mysql':
            self._create_mysql_tables()
        else:
            self._create_sqlite_tables()

    def _create_mysql_tables(self):
        """Create tables for MySQL - preserving original structure"""
        # Weekly rain totals table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS archive_week_raintotal (
                id INT AUTO_INCREMENT PRIMARY KEY,
                year INT,
                week INT,
                week_start_date DATE UNIQUE,
                rain_total FLOAT
            )
        """)

        # Monthly rain totals table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS archive_month_raintotal (
                id INT AUTO_INCREMENT PRIMARY KEY,
                year INT,
                month INT,
                rain_total FLOAT,
                UNIQUE (year, month)
            )
        """)

        # Yearly rain totals table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS archive_year_raintotal (
                id INT AUTO_INCREMENT PRIMARY KEY,
                year INT UNIQUE,
                rain_total FLOAT
            )
        """)
        self.conn.commit()

    def _create_sqlite_tables(self):
        """Create tables for SQLite - preserving original structure"""
        # Weekly rain totals table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS archive_week_raintotal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                week INTEGER,
                week_start_date TEXT UNIQUE,
                rain_total REAL
            )
        """)

        # Monthly rain totals table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS archive_month_raintotal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                month INTEGER,
                rain_total REAL,
                UNIQUE (year, month)
            )
        """)

        # Yearly rain totals table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS archive_year_raintotal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER UNIQUE,
                rain_total REAL
            )
        """)
        self.conn.commit()

    def _process_weekly_totals(self):
        """Calculate weekly rain totals"""
        self._log("Calculating weekly rain totals...")
        
        # Get last processed week
        self.cursor.execute("SELECT MAX(week_start_date) FROM archive_week_raintotal")
        last = self.cursor.fetchone()[0]
        
        if not last:
            if self.db_type == 'mysql':
                self.cursor.execute("SELECT MIN(FROM_UNIXTIME(dateTime)) FROM archive")
            else:
                self.cursor.execute("SELECT MIN(datetime(dateTime, 'unixepoch')) FROM archive")
            last = self.cursor.fetchone()[0]
        
        if not last:
            self._log("No data found in archive table for weekly totals.", error=True)
            return

        # Database-specific queries
        if self.db_type == 'mysql':
            query = """
                SELECT
                    YEAR(FROM_UNIXTIME(dateTime)) AS year,
                    WEEK(FROM_UNIXTIME(dateTime), 1) AS week,
                    MIN(FROM_UNIXTIME(dateTime)) AS week_start,
                    SUM(rain) AS rain_total
                FROM archive
                WHERE FROM_UNIXTIME(dateTime) > %s
                GROUP BY year, week
            """
            params = (last,)
        else:
            query = """
                SELECT
                    CAST(strftime('%Y', datetime(dateTime, 'unixepoch')) AS INTEGER) AS year,
                    CAST(strftime('%W', datetime(dateTime, 'unixepoch')) AS INTEGER) AS week,
                    MIN(datetime(dateTime, 'unixepoch')) AS week_start,
                    SUM(rain) AS rain_total
                FROM archive
                WHERE datetime(dateTime, 'unixepoch') > ?
                GROUP BY year, week
            """
            params = (last,)

        self.cursor.execute(query, params)
        
        for year, week, start, rain_total in self.cursor.fetchall():
            if self.db_type == 'mysql':
                start_date = start.date()
                insert_query = """
                    INSERT INTO archive_week_raintotal (year, week, week_start_date, rain_total)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE rain_total = VALUES(rain_total)
                """
                params = (year, week, start_date, rain_total)
            else:
                insert_query = """
                    INSERT OR REPLACE INTO archive_week_raintotal (year, week, week_start_date, rain_total)
                    VALUES (?, ?, ?, ?)
                """
                params = (year, week, start, rain_total)
            
            self.cursor.execute(insert_query, params)
        
        self.conn.commit()
        self._log("Weekly rain totals updated.")

    def _process_monthly_totals(self):
        """Calculate monthly rain totals"""
        self._log("Calculating monthly rain totals...")

        self.cursor.execute("SELECT MAX(year), MAX(month) FROM archive_month_raintotal")
        last_processed_year, last_processed_month = self.cursor.fetchone()

        where_clause = ""
        params = []

        if last_processed_year is not None and last_processed_month is not None:
            if self.db_type == 'mysql':
                where_clause = """
                    WHERE (YEAR(FROM_UNIXTIME(dateTime)) > %s) OR
                          (YEAR(FROM_UNIXTIME(dateTime)) = %s AND MONTH(FROM_UNIXTIME(dateTime)) > %s)
                """
                params = [last_processed_year, last_processed_year, last_processed_month]
            else:
                where_clause = """
                    WHERE (CAST(strftime('%Y', datetime(dateTime, 'unixepoch')) AS INTEGER) > ?) OR
                          (CAST(strftime('%Y', datetime(dateTime, 'unixepoch')) AS INTEGER) = ? AND 
                           CAST(strftime('%m', datetime(dateTime, 'unixepoch')) AS INTEGER) > ?)
                """
                params = [last_processed_year, last_processed_year, last_processed_month]
            
            self._log(f"Monthly: Processing data after year {last_processed_year}, month {last_processed_month:02d}")
        else:
            self.cursor.execute("SELECT MIN(dateTime) FROM archive")
            min_archive_epoch = self.cursor.fetchone()[0]
            if min_archive_epoch is None:
                self._log("No data found in archive table to calculate monthly totals. Skipping.", error=True)
                return
            self._log("Monthly: archive_month_raintotal is empty. Processing all historical data from archive.")

        if self.db_type == 'mysql':
            sql_query = f"""
                SELECT
                    YEAR(FROM_UNIXTIME(dateTime)) AS year,
                    MONTH(FROM_UNIXTIME(dateTime)) AS month,
                    SUM(rain) AS rain_total
                FROM archive
                {where_clause}
                GROUP BY year, month
                ORDER BY year, month
            """
        else:
            sql_query = f"""
                SELECT
                    CAST(strftime('%Y', datetime(dateTime, 'unixepoch')) AS INTEGER) AS year,
                    CAST(strftime('%m', datetime(dateTime, 'unixepoch')) AS INTEGER) AS month,
                    SUM(rain) AS rain_total
                FROM archive
                {where_clause}
                GROUP BY year, month
                ORDER BY year, month
            """

        self._log(f"DEBUG SQL (Monthly): {sql_query.strip()} with params: {params}")

        self.cursor.execute(sql_query, tuple(params))
        fetched_rows = self.cursor.fetchall()
        self._log(f"Monthly: Fetched {len(fetched_rows)} rows from archive for processing.")

        for year, month, rain_total in fetched_rows:
            if self.db_type == 'mysql':
                insert_query = """
                    INSERT INTO archive_month_raintotal (year, month, rain_total)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE rain_total = VALUES(rain_total)
                """
            else:
                insert_query = """
                    INSERT OR REPLACE INTO archive_month_raintotal (year, month, rain_total)
                    VALUES (?, ?, ?)
                """
            
            self.cursor.execute(insert_query, (year, month, rain_total))
        
        self.conn.commit()
        self._log("Monthly rain totals updated.")

    def _process_yearly_totals(self):
        """Calculate yearly rain totals"""
        self._log("Calculating yearly rain totals...")
        self.cursor.execute("SELECT MAX(year) FROM archive_year_raintotal")
        last = self.cursor.fetchone()[0] or 0

        if self.db_type == 'mysql':
            query = """
                SELECT
                    YEAR(FROM_UNIXTIME(dateTime)) AS year,
                    SUM(rain) AS rain_total
                FROM archive
                WHERE YEAR(FROM_UNIXTIME(dateTime)) > %s
                GROUP BY year
                ORDER BY year
            """
            params = (last,)
        else:
            query = """
                SELECT
                    CAST(strftime('%Y', datetime(dateTime, 'unixepoch')) AS INTEGER) AS year,
                    SUM(rain) AS rain_total
                FROM archive
                WHERE CAST(strftime('%Y', datetime(dateTime, 'unixepoch')) AS INTEGER) > ?
                GROUP BY year
                ORDER BY year
            """
            params = (last,)

        self.cursor.execute(query, params)
        
        for year, rain_total in self.cursor.fetchall():
            if self.db_type == 'mysql':
                insert_query = """
                    INSERT INTO archive_year_raintotal (year, rain_total)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE rain_total = VALUES(rain_total)
                """
            else:
                insert_query = """
                    INSERT OR REPLACE INTO archive_year_raintotal (year, rain_total)
                    VALUES (?, ?)
                """
            
            self.cursor.execute(insert_query, (year, rain_total))
        
        self.conn.commit()
        self._log("Yearly rain totals updated.")

    def _log(self, message, error=False):
        """Log messages to syslog"""
        level = syslog.LOG_ERR if error else syslog.LOG_INFO
        syslog.syslog(level, f"rain_totals: {message}")

    def shutDown(self):
        """Clean up database connections"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            self._log("Database connection closed.")
        except Exception as e:
            self._log(f"Error during shutdown: {e}", error=True)