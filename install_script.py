#!/usr/bin/env python3
"""
Installer for Rain Totals Extension
Installs the service and configures weewx.conf automatically
"""

import configobj
import os
import shutil
import sys
from distutils.version import StrictVersion

# Extension information
EXTENSION_NAME = "rain-totals"
EXTENSION_VERSION = "1.0.0"
REQUIRED_WEEWX_VERSION = "4.0.0"
DESCRIPTION = "Service to calculate and store rain totals by week, month, and year"

# File mappings: source -> destination (relative to weewx root)
file_list = [
    ('bin/user/rain_totals.py', 'bin/user/rain_totals.py'),
]

def loader():
    return RainTotalsInstaller()

class RainTotalsInstaller(object):
    def __init__(self):
        pass

    def install(self, engine):
        """Install the Rain Totals extension"""
        print(f"Installing {EXTENSION_NAME} extension v{EXTENSION_VERSION}")
        
        # Check weewx version
        try:
            import weewx
            if StrictVersion(weewx.__version__) < StrictVersion(REQUIRED_WEEWX_VERSION):
                print(f"ERROR: Rain Totals requires weewx {REQUIRED_WEEWX_VERSION} or later. "
                      f"Found weewx {weewx.__version__}")
                return False
        except ImportError:
            print("WARNING: Cannot determine weewx version")

        config_dict = engine.config_dict
        install_dir = os.path.dirname(__file__)
        weewx_root = config_dict['WEEWX_ROOT']
        
        # Install files
        print("Installing files...")
        for src, dst in file_list:
            src_path = os.path.join(install_dir, src)
            dst_path = os.path.join(weewx_root, dst)
            
            # Create destination directory if it doesn't exist
            dst_dir = os.path.dirname(dst_path)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            
            # Copy file
            if os.path.exists(src_path):
                print(f"  Copying {src} to {dst}")
                shutil.copy2(src_path, dst_path)
            else:
                print(f"WARNING: Source file {src_path} not found")

        # Configure weewx.conf
        print("Configuring weewx.conf...")
        self._configure_weewx(config_dict)
        
        print(f"{EXTENSION_NAME} extension installed successfully!")
        print("\nThe Rain Totals service will:")
        print("- Calculate weekly, monthly, and yearly rain totals")
        print("- Store results in archive_week_raintotal, archive_month_raintotal, and archive_year_raintotal tables")
        print("- Work with both MySQL and SQLite databases")
        print("- Run automatically when weewx starts")
        print("\nRestart weewx to activate the extension.")
        
        return True

    def _configure_weewx(self, config_dict):
        """Add Rain Totals service to weewx configuration"""
        
        # Ensure Engine section exists
        if 'Engine' not in config_dict:
            config_dict['Engine'] = configobj.ConfigObj()
        
        # Ensure Services section exists under Engine
        if 'Services' not in config_dict['Engine']:
            config_dict['Engine']['Services'] = configobj.ConfigObj()
        
        # Add to data_services (runs after archive records are processed)
        service_name = 'user.rain_totals.RainTotals'
        
        if 'data_services' not in config_dict['Engine']['Services']:
            config_dict['Engine']['Services']['data_services'] = []
        
        data_services = config_dict['Engine']['Services']['data_services']
        
        # Convert to list if it's a string
        if isinstance(data_services, str):
            data_services = [data_services]
        elif not isinstance(data_services, list):
            data_services = list(data_services)
        
        # Add our service if it's not already there
        if service_name not in data_services:
            data_services.append(service_name)
            config_dict['Engine']['Services']['data_services'] = data_services
            print(f"  Added {service_name} to data_services")
        else:
            print(f"  {service_name} already in data_services")

        # Add configuration section for the extension
        if 'RainTotals' not in config_dict:
            config_dict['RainTotals'] = configobj.ConfigObj()
            config_dict['RainTotals']['# Rain Totals Service Configuration'] = None
            config_dict['RainTotals']['# This service calculates weekly, monthly, and yearly rain totals'] = None
            config_dict['RainTotals']['# No configuration options are currently available'] = None
            print("  Added [RainTotals] configuration section")

    def uninstall(self, engine):
        """Uninstall the Rain Totals extension"""
        print(f"Uninstalling {EXTENSION_NAME} extension...")
        
        config_dict = engine.config_dict
        weewx_root = config_dict['WEEWX_ROOT']
        
        # Remove files
        print("Removing files...")
        for src, dst in file_list:
            dst_path = os.path.join(weewx_root, dst)
            if os.path.exists(dst_path):
                print(f"  Removing {dst}")
                os.remove(dst_path)
        
        # Remove from weewx.conf
        print("Removing from weewx.conf...")
        self._unconfigure_weewx(config_dict)
        
        print(f"{EXTENSION_NAME} extension uninstalled successfully!")
        print("Note: Database tables are left intact. Remove manually if desired:")
        print("  - archive_week_raintotal")
        print("  - archive_month_raintotal") 
        print("  - archive_year_raintotal")
        print("\nRestart weewx to complete removal.")
        
        return True

    def _unconfigure_weewx(self, config_dict):
        """Remove Rain Totals service from weewx configuration"""
        
        service_name = 'user.rain_totals.RainTotals'
        
        # Remove from data_services
        try:
            data_services = config_dict['Engine']['Services']['data_services']
            if isinstance(data_services, str):
                data_services = [data_services]
            elif not isinstance(data_services, list):
                data_services = list(data_services)
            
            if service_name in data_services:
                data_services.remove(service_name)
                config_dict['Engine']['Services']['data_services'] = data_services
                print(f"  Removed {service_name} from data_services")
        except KeyError:
            pass
        
        # Remove configuration section
        if 'RainTotals' in config_dict:
            del config_dict['RainTotals']
            print("  Removed [RainTotals] configuration section")

if __name__ == "__main__":
    print("This is an extension installer. Use 'weectl extension install' instead.")
    sys.exit(1)