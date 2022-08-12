```
{
    "title": "JourneyTime JSON Credentials Store",
	"FLASK_HOST": "<server ip address - typically 127.0.0.1>",
    "FLASK_PORT": "<server port - typically 80>",
    "CORS_PROTECTION": "DISABLED <'DISABLED' disables Flask CORS protection - useful for testing>",
    "DB_USER": "<your MySQL db username>",
    "DB_PASS": "<your MySQL db password>",
    "DB_SRVR": "<your MySQL db server ip address>",
    "DB_PORT": "<your MySQL db server port>",
    "DB_NAME": "<your MySQL db name>",
    "SELENIUM_TESTING": {  <addresses used when running selenium tests>
        "JTAPI_SRVR": "http://127.0.0.1",
        "JTAPI_PORT": "",
        "JTUI_SRVR": "http://127.0.0.1",
        "JTUI_PORT": "8080"
    },
    "DUBLIN_CC": {  <lat/lon of Dublin City Center - used for distance from CC calculations>
        "lat": 53.347269,
        "lon": -6.259107
    },
    "MAPS_API_KEY": "<your Google Maps API key (used by the lightweight Journey Planning app)>",
    "DOWNLOAD_CHUNK_SIZE": "32768",
    "DOWNLOAD_ROW_LIMIT_JSON": "5000",
    "DOWNLOAD_ROW_LIMIT_JSON_ATTACHMENT": "100000",
    "SECRET_KEY": "<random key used for additional security between API and Journey Planning app>",
    "open-weather": {
        "url": "https://pro.openweathermap.org/data/2.5/forecast/hourly",
        "api-key": "<your open-weather API key>"
    },
	"cronitor": {
        "TelemetryURL": "<your cronitor telemetry URL used for process monitoring>"
    },
    "nta-gtfs": {
        "gtfs-schedule-data-url": "https://www.transportforireland.ie/transitData/google_transit_combined.zip",
        "gtfsr-api-url": "https://gtfsr.transportforireland.ie/v1",
        "gtfsr-api-key-primary": "<your NTA gtfsr api primary key>",
        "gtfsr-api-key-secondary": "<your NTA gtfsr api secondary key>"
    },
    "GTFS_LOADER": {
        "JTAPI_SRVR": "http://localhost"  <address of server used to trigger model update, post GTFS load>
    }
}
```