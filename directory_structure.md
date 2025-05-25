# Rain Totals Extension - Directory Structure

Create this directory structure for your extension:

```
rain-totals/
├── bin/
│   └── user/
│       └── rain_totals.py          # Main service (from artifact #1)
├── install.py                      # Installer script (from artifact #2)  
├── README.md                       # Documentation (from artifact #4)
└── LICENSE                         # GPL-3.0 license file (create separately)
```

## Installation Steps

1. **Create the directory structure** as shown above
2. **Copy the code** from each artifact into the corresponding file:
   - `rain_totals.py` - Main service code 
   - `install.py` - Installer with your contact information
   - `README.md` - Complete documentation
3. **Create a LICENSE file** with GPL-3.0 text (optional for testing)
4. **Test the extension**:
   ```bash
   # Create a zip file
   zip -r rain-totals.zip rain-totals/
   
   # Install using weectl
   sudo weectl extension install rain-totals.zip
   
   # Check installation
   sudo weectl extension list | grep rain
   
   # Restart WeeWX
   sudo systemctl restart weewx
   ```

## Key Changes Made

### 1. Table Names Updated
- `rain_weekly_averages` → `archive_week_raintotal`
- `rain_monthly_averages` → `archive_month_raintotal` 
- `rain_yearly_averages` → `archive_year_raintotal`

### 2. Column Names Updated
- `avg_rain` → `rain_total` (more descriptive)

### 3. Database Abstraction Added
- Automatic detection of MySQL vs SQLite
- Database-specific SQL queries and syntax
- Proper connection handling for both database types

### 4. Extension Structure Created  
- Complete `install.py` with automatic configuration
- Professional installer with contact information and version checking
- Requirements validation (WeeWX 4.0+, Python 3.6+)

## Testing Tips

1. **Check logs** during installation:
   ```bash
   sudo tail -f /var/log/syslog | grep weectl
   ```

2. **Monitor service startup**:
   ```bash
   sudo tail -f /var/log/syslog | grep rain_totals
   ```

3. **Verify tables were created**:
   ```sql
   -- For MySQL
   SHOW TABLES LIKE 'archive_%_raintotal';
   
   -- For SQLite  
   .tables archive_*_raintotal
   ```

4. **Check service is listed in config**:
   ```bash
   grep -A5 "data_services" /etc/weewx/weewx.conf
   ```