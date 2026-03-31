from app.models.alert import GeoLocation
import random

class GeoIPResolver:
    """
    Resolves IP addresses to Geographic coordinates.
    Uses a High-Fidelity Synthetic Resolver for the StealthVault Demo.
    """

    # 🌍 GLOBAL HOTSPOTS: Synthetic IP mapping for demo impact
    HOTSPOTS = {
        "185.": {"city": "Moscow", "country": "Russia", "code": "RU", "lat": 55.75, "lng": 37.61},
        "103.": {"city": "Mumbai", "country": "India", "code": "IN", "lat": 19.07, "lng": 72.87},
        "45.":  {"city": "Beijing", "country": "China", "code": "CN", "lat": 39.90, "lng": 116.40},
        "172.": {"city": "San Francisco", "country": "USA", "code": "US", "lat": 37.77, "lng": -122.41},
        "80.":  {"city": "Berlin", "country": "Germany", "code": "DE", "lat": 52.52, "lng": 13.40},
        "92.":  {"city": "Kyiv", "country": "Ukraine", "code": "UA", "lat": 50.45, "lng": 30.52},
        "31.":  {"city": "Amsterdam", "country": "Netherlands", "code": "NL", "lat": 52.36, "lng": 4.89},
    }

    def resolve(self, ip_address: str) -> GeoLocation:
        """
        Resolve an IP to a GeoLocation.
        """
        ip_str = str(ip_address)
        
        # Check hotspots
        for prefix, data in self.HOTSPOTS.items():
            if ip_str.startswith(prefix):
                # Add a tiny random jitter to avoid perfect overlapping dots
                jitter_lat = random.uniform(-0.5, 0.5)
                jitter_lng = random.uniform(-0.5, 0.5)
                
                return GeoLocation(
                    city=data["city"],
                    country=data["country"],
                    country_code=data["code"],
                    latitude=data["lat"] + jitter_lat,
                    longitude=data["lng"] + jitter_lng
                )
        
        # Default fallback: London (Global Hub)
        return GeoLocation(
            city="London",
            country="United Kingdom",
            country_code="GB",
            latitude=51.50 + random.uniform(-0.3, 0.3),
            longitude=-0.12 + random.uniform(-0.3, 0.3)
        )

# Singleton
geoip_resolver = GeoIPResolver()
