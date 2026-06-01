from typing import Dict, List, Any


RENTAL_DATA: List[Dict[str, Any]] = [
    {"name": "Vinhomes Ocean Park Studio", "destination": "VinUni", "distance_km": 1.2, "price_million": 2.8},
    {"name": "Trau Quy Minihouse", "destination": "VinUni", "distance_km": 2.9, "price_million": 3.2},
    {"name": "Ecohome Dang Xa", "destination": "VinUni", "distance_km": 2.5, "price_million": 2.4},
    {"name": "Bach Khoa Dorm", "destination": "HUST", "distance_km": 0.8, "price_million": 1.8},
    {"name": "Le Thanh Nghi Homestay", "destination": "HUST", "distance_km": 2.1, "price_million": 2.3},
    {"name": "Minh Khai Apartment", "destination": "HUST", "distance_km": 4.6, "price_million": 1.9},
    {"name": "Nhon Co-living", "destination": "HAUI", "distance_km": 1.5, "price_million": 1.4},
    {"name": "Dien Student House", "destination": "HAUI", "distance_km": 6.2, "price_million": 1.2},
    {"name": "Cau Dien Studio", "destination": "HAUI", "distance_km": 7.8, "price_million": 1.7},
    {"name": "Trieu Khuc Room", "destination": "PTIT", "distance_km": 2.9, "price_million": 2.7},
    {"name": "Van Quan Flat", "destination": "PTIT", "distance_km": 3.7, "price_million": 3.0},
    {"name": "Mo Lao Mini", "destination": "PTIT", "distance_km": 4.4, "price_million": 2.4},
    {"name": "Xuan Thuy Studio", "destination": "UET", "distance_km": 1.1, "price_million": 2.4},
    {"name": "Nghia Tan House", "destination": "UET", "distance_km": 3.6, "price_million": 2.6},
    {"name": "Mai Dich Room", "destination": "UET", "distance_km": 4.8, "price_million": 2.2},
]


class RentalSearchTools:
    def __init__(self):
        self._last_find_flat_results: List[Dict[str, Any]] = []
        self.call_history: List[str] = []

    def find_flat(self, destination: str, distance: float) -> List[Dict[str, Any]]:
        """Return all rentals with distance_km <= distance from destination."""
        self.call_history.append("find_flat")
        normalized_destination = str(destination).strip().lower()
        distance_limit = float(distance)

        filtered = [
            item
            for item in RENTAL_DATA
            if item["destination"].lower() == normalized_destination and item["distance_km"] <= distance_limit
        ]
        self._last_find_flat_results = filtered
        return filtered

    def find_max_price(self, price: float) -> List[Dict[str, Any]]:
        """Return rentals with price_million < price, sorted ascending by price."""
        self.call_history.append("find_max_price")
        if not self._last_find_flat_results:
            return [
                {
                    "error": "find_flat must be called first",
                    "hint": "Call find_flat(destination, distance) before find_max_price(price)",
                }
            ]

        max_price = float(price)
        filtered = [
            item
            for item in self._last_find_flat_results
            if item["price_million"] < max_price
        ]
        return sorted(filtered, key=lambda item: item["price_million"])

    def build_tool_specs(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "find_flat",
                "description": "Find rentals near a destination. Input: destination (string), distance (km as number).",
                "function": self.find_flat,
            },
            {
                "name": "find_max_price",
                "description": "Filter previous find_flat results by strict max monthly price (< price) in million VND and sort ascending.",
                "function": self.find_max_price,
            },
        ]
