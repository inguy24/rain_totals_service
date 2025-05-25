# Rain Totals Extension for WeeWX

A WeeWX service that automatically calculates and stores rain totals aggregated by week, month, and year.

## Why This Extension?

WeeWX has limitations when it comes to calculating rain totals across longer time periods, particularly when using `group_by` aggregation in templates and reports. The built-in aggregation functions can produce incorrect results when averaging rain data across weeks, months, and years because rain is a cumulative measurement, not an average.

**Common Problems This Solves:**
- Incorrect monthly/yearly rain totals in charts and reports
- Inability to easily create multi-year climatological comparisons  
- Performance issues when calculating long-term rain statistics on-the-fly
- Complex template logic required for proper rain aggregation

**What This Extension Provides:**
- Pre-calculated, accurate rain totals stored in dedicated tables
- Fast access to historical rain data for reports and charts
- Foundation for building multi-year climatological charts
- Consistent rain total calculations across your entire archive

This extension is particularly valuable for creating rainfall climatology charts, comparing current year rainfall to historical averages, and generating professional weather reports with accurate long-term precipitation data.

## Features

- **Database Support**: Works with both MySQL and SQLite databases
- **Automatic Detection**: Automatically detects your database type from weewx.conf
- **Incremental Processing**: Only processes new data for efficiency
- **Three Time Periods**: Calculates totals for weekly, monthly, and yearly periods
- **Clean Table Names**: Uses descriptive table names that follow WeeWX conventions

## Requirements

- **WeeWX**: Version 4.0 or later
- **Python**: Version 3.6 or later (required for f-string support)
- **Database**: MySQL or SQLite (automatically detected)

## Installation

### Using weectl (Recommended)

```bash
# Download the extension
wget https://github.com/yourusername/weewx-rain-totals/archive/main.zip

# Install using weectl
sudo weectl extension install main.zip

# Restart WeeWX
sudo systemctl restart weewx
```

### Manual Installation

1. Copy `rain_totals.py` to your WeeWX `bin/user/` directory
2. Add the service to your `weewx.conf` file:

```ini
[Engine]
    [[Services]]
        data_services = ..., user.rain_totals.RainTotals
```

3. Restart WeeWX

## Database Tables Created

The extension creates three tables in your WeeWX database:

### archive_week_raintotal
- `id`: Auto-incrementing integer primary key
- `year`: Year 
- `week`: Week number (1-53)
- `week_start_date`: Date when the week started
- `rain_total`: Total rainfall for the week

### archive_month_raintotal  
- `id`: Auto-incrementing integer primary key
- `year`: Year
- `month`: Month (1-12)
- `rain_total`: Total rainfall for the month

### archive_year_raintotal
- `id`: Auto-incrementing integer primary key  
- `year`: Year
- `rain_total`: Total rainfall for the year

## How the Service Works

The Rain Totals service uses an **incremental processing approach** to efficiently handle large amounts of historical data:

### Processing Logic
The service tracks which archive records have been processed by using a "high water mark" approach:

- **Weekly**: Finds the latest `week_start_date` in `archive_week_raintotal` and only processes archive records after that date
- **Monthly**: Finds the latest `year/month` combination in `archive_month_raintotal` and only processes archive records from subsequent months  
- **Yearly**: Finds the latest `year` in `archive_year_raintotal` and only processes archive records from subsequent years

### Benefits
- **Efficient**: Only calculates totals for new time periods, not all historical data
- **Fast startup**: Service runs quickly even with years of archive data
- **Automatic**: No manual intervention required for normal operation

### Rebuilding Tables
If you need to recalculate all historical rain totals (e.g., after fixing archive data), you can trigger a complete rebuild:

#### For MySQL:
```sql
DROP TABLE archive_week_raintotal;
DROP TABLE archive_month_raintotal; 
DROP TABLE archive_year_raintotal;
```

#### For SQLite:
```sql
DROP TABLE archive_week_raintotal;
DROP TABLE archive_month_raintotal;
DROP TABLE archive_year_raintotal;
```

After dropping the tables, restart WeeWX. The service will:
1. Recreate all three tables
2. Process your entire archive history from the beginning
3. Calculate rain totals for all historical time periods

**Note**: The initial rebuild after dropping tables may take some time if you have many years of archive data.

## Usage

Once installed, the service runs automatically whenever WeeWX processes archive records. No additional configuration is required.

The service will:
1. Check for new archive records since the last run
2. Calculate rain totals for any new time periods
3. Update the appropriate tables with the calculated totals

## Database Compatibility

### MySQL
- Uses MySQL-specific SQL syntax and functions
- Supports `ON DUPLICATE KEY UPDATE` for efficient upserts
- Uses `FROM_UNIXTIME()` for timestamp conversion
- Uses `AUTO_INCREMENT` for primary keys

### SQLite  
- Uses SQLite-specific SQL syntax and functions
- Uses `INSERT OR REPLACE` for upserts
- Uses `datetime()` for timestamp conversion
- Uses `AUTOINCREMENT` for primary keys

## Configuration

The extension automatically detects your database configuration from `weewx.conf`. No additional configuration is required.

The service reads:
- Database type from `[Databases]` section
- Connection parameters from `[DatabaseTypes]` section  
- Database binding from `[Station]` section

## Logging

The extension logs its activities to the system log with the prefix `rain_totals:`. You can monitor its operation with:

```bash
sudo tail -f /var/log/syslog | grep rain_totals
```

## Troubleshooting

### Service Not Running
- Check that the service is listed in your `weewx.conf` under `data_services`
- Verify the file is in the correct location (`bin/user/rain_totals.py`)
- Check the WeeWX log for error messages

### Database Connection Issues
- Verify your database configuration in `weewx.conf`
- Check database permissions for the WeeWX user
- Ensure the database server is running (MySQL only)

### Missing Data
- The service only processes new data after installation
- For historical data, you may need to manually populate or recreate tables
- Check that your archive table contains rain data

## Development

### File Structure
```
rain-totals/
├── bin/
│   └── user/
│       └── rain_totals.py     # Main service code
├── install.py                 # Extension installer
├── setup.cfg                  # Extension metadata
└── README.md                 # This file
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with both MySQL and SQLite
5. Submit a pull request

## License

This project is licensed under the GPL-3.0 License - see the LICENSE file for details.

## Support

- Create an issue on GitHub for bugs or feature requests
- Check the WeeWX user forum for general WeeWX questions
- Review the WeeWX documentation for service development

## Changelog

### Version 1.0.0
- Initial release
- Support for MySQL and SQLite databases  
- Automatic database type detection
- Weekly, monthly, and yearly rain total calculations
- WeeWX 4.0+ compatibility