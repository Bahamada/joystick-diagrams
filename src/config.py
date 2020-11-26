from configparser import ConfigParser

config = ConfigParser()
config.read('./config.cfg')

# Write logs
debug = config.getboolean('DEFAULT', 'EnableLogging', fallback=True)
debugLevel = config.getint('DEFAULT', 'LogLevel', fallback=1)

# Export out SVG files - for development only (leave as = 1)
export = 1

## Program can automatically open in browser as it creates, specify below if you want this. Only supports Chrome right now.
open_in_browser = config.getboolean('BROWSER', 'OpenTemplatesInBrowser', fallback=False)
chrome_path = config.get('BROWSER', 'ChromePath', fallback='chrome.exe')
