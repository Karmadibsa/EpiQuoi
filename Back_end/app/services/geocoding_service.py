"""Service for geocoding and campus location finding."""

import logging
from typing import Optional, Tuple, Dict, List
import httpx

from app.config import settings
from app.exceptions import GeocodingError
from app.utils.campus_data import CAMPUSES
from app.utils.geo_utils import haversine_distance

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for finding nearest Epitech campus based on location."""

    @staticmethod
    async def get_nearest_campus(
        query: str
    ) -> Optional[Tuple[Dict, Optional[Dict], str]]:
        """
        Find the nearest Epitech campus based on a location query.
        
        Args:
            query: Location query (zip code, city name, etc.)
        
        Returns:
            Tuple of (nearest_overall, nearest_in_country, user_detected_info)
            or None if geocoding fails
        """
        try:
            user_coords = None
            user_label = "Localisation inconnue"
            user_country_detected = "Inconnu"

            async with httpx.AsyncClient(timeout=settings.geocoding_timeout) as client:
                # 1. Try French API (api-adresse.data.gouv.fr)
                valid_french_result = False
                try:
                    resp = await client.get(
                        f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=1"
                    )
                    data = resp.json()

                    if data.get('features'):
                        props = data['features'][0]['properties']
                        result_type = props.get('type')
                        user_city_name = props.get('city', '')
                        normalized_query = query.lower().strip()

                        # Anti false-positive validation
                        if not (
                            result_type == 'street'
                            and normalized_query not in user_city_name.lower()
                        ):
                            valid_french_result = True
                            user_coords = data['features'][0]['geometry']['coordinates']
                            user_label = props.get('label')
                            user_country_detected = "France"
                        else:
                            # If rejected as false positive, check if it's a zip code
                            if query.isdigit():
                                valid_french_result = True
                                user_coords = data['features'][0]['geometry']['coordinates']
                                user_label = props.get('label')
                                user_country_detected = "France"
                except Exception as e:
                    logger.debug(f"French geocoding API failed: {e}")

                # 2. If French API failed, try OpenStreetMap (Worldwide)
                if not valid_french_result:
                    logger.info(f"Switching to Nominatim for: {query}")
                    try:
                        headers = {'User-Agent': 'EpiChat/1.0'}
                        resp_osm = await client.get(
                            f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1",
                            headers=headers
                        )
                        data_osm = resp_osm.json()

                        if data_osm:
                            user_coords = [
                                float(data_osm[0]['lon']),
                                float(data_osm[0]['lat'])
                            ]
                            user_label = data_osm[0]['display_name']
                            # Simple country detection from display name
                            if "Germany" in user_label or "Deutschland" in user_label:
                                user_country_detected = "Allemagne"
                            elif "Spain" in user_label or "España" in user_label:
                                user_country_detected = "Espagne"
                            elif "Belgium" in user_label or "Belgique" in user_label:
                                user_country_detected = "Belgique"
                            else:
                                user_country_detected = "Autre"
                    except Exception as e:
                        logger.debug(f"OpenStreetMap geocoding failed: {e}")

            if not user_coords:
                logger.warning(f"Could not geocode location: {query}")
                return None

            user_lon, user_lat = user_coords[0], user_coords[1]
            user_detected_info = f"{user_label} (Pays: {user_country_detected})"

            # 3. Calculate distances to ALL campuses
            results: List[Dict] = []
            for city, info in CAMPUSES.items():
                camp_lat, camp_lon = info['coords']
                dist = haversine_distance(user_lat, user_lon, camp_lat, camp_lon)
                results.append({
                    'city': city,
                    'dist': int(dist),
                    'data': info
                })

            # Sort by distance
            results.sort(key=lambda x: x['dist'])

            nearest_overall = results[0]

            # Find nearest campus IN USER'S COUNTRY (if known)
            nearest_in_country = None
            if user_country_detected and user_country_detected != "Autre":
                nearest_in_country = next(
                    (r for r in results if r['data']['country'] == user_country_detected),
                    None
                )

            return (nearest_overall, nearest_in_country, user_detected_info)

        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            raise GeocodingError(f"Failed to geocode location: {str(e)}")
