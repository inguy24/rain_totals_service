#!/usr/bin/env python3
"""
Installer for Rain Totals Extension
Author: Shane Burkhardt
Email: shane@shaneburkhardt.com  
GitHub: https://github.com/inguy24/rain_totals_service/
"""

from weecfg.extension import ExtensionInstaller

def loader():
    return RainTotalsInstaller()

class RainTotalsInstaller(ExtensionInstaller):
    def __init__(self):
        super(RainTotalsInstaller, self).__init__(
            version="0.5.0",
            name='rain_totals_service',
            description='Service to calculate and store rain totals by week, month, and year',
            author="Shane Burkhardt",
            author_email="shane@shaneburkhardt.com",
            data_services='user.rain_totals_service.RainTotals',
            config={
                'RainTotals': {
                    '# Rain Totals Service Configuration': None,
                    '# This service calculates weekly, monthly, and yearly rain totals': None,
                    '# No configuration options are currently available': None
                }
            },
            files=[('bin/user', [
                'bin/user/rain_totals_service.py'
            ])]
        )