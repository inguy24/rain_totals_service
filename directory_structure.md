# Rain Totals Extension - Directory Structure

Create this directory structure for your extension:

```
rain-totals/
├── bin/
│   └── user/
│       └── rain_totals.py          # Main service (from artifact #1)
├── install.py                      # Installer script (from artifact #2)  
├── setup.cfg                       # Extension metadata (from artifact #3)
├── README.md                       # Documentation (from artifact #4)
└── LICENSE                         # GPL-3.0 license file (create separately)
```

## Installation Steps

1. **Create the directory structure** as shown above
2. **Copy the code** from each artifact into the corresponding file
3. **Update metadata** in `setup.cfg`:
   - Change author name and email
   - Update GitHub URL  
   - Adjust version if needed
4. **Create a LICENSE file** with GPL-3.0 text
5. **Test the extension**:
   ```bash
   # Create a zip file
   zip -r rain-totals.zip rain-totals/
   
   # Install using weectl
   sudo weectl extension install rain-totals.zip
   ```

## Key Changes Made

### 1. Table Names Updated
- `rain_weekly_averages` → `archive_week_raintotal`
- `rain_monthly_averages` → `archive_month_raintotal` 
- `rain_yearly_averages` → `archive_year_raintotal`

### 2. Database Abstraction Added
- Automatic detection of MySQL vs SQLite
- Database-specific SQL queries and syntax
- Proper connection handling for both database types

### 3. Extension Structure Created  
- Complete `install.py` with automatic configuration
- Metadata in `setup.cfg` for