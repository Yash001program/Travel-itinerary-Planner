import json
import re
from typing import Any, Dict, List


def _extract_json(raw_text: str) -> Dict[str, Any]:
    """Safely extracts and parses JSON from LLM markdown or raw responses."""
    cleaned = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _call_llm(provider: str, api_key: str, prompt: str) -> Dict[str, Any]:
    """Dispatches structured JSON prompts to Google Gemini or Groq."""
    if provider == "Google Gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.5,
            ),
        )
        return _extract_json(response.text)

    elif provider == "Groq":
        from groq import Groq

        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior travel logistics architect. Always output valid JSON strictly adhering to the requested schema.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
        )
        return _extract_json(completion.choices[0].message.content)

    raise ValueError(f"Unsupported LLM provider: {provider}")


# ---------------------------------------------------------------------------
# EPIC 3: SMART DESTINATION RECOMMENDER
# ---------------------------------------------------------------------------

def recommend_destinations(
    prefs: Dict[str, Any], provider: str, api_key: str, demo_mode: bool
) -> List[Dict[str, Any]]:
    """Returns top 3 matching destinations based on vibe, season, party, and budget."""
    if demo_mode or not api_key:
        vibe = prefs.get("vibe", "Cultural")
        budget = prefs.get("budget", "Moderate")
        catalog = {
            "Beach": [
                {
                    "city": "Phuket & Krabi",
                    "country": "Thailand",
                    "currency": "THB",
                    "match_score": 97,
                    "weather_note": "29°C Sunny & Dry Breeze — Ideal island-hopping window",
                    "est_daily_usd": 85 if budget == "Budget" else (160 if budget == "Moderate" else 380),
                    "tags": ["Limestone Cliffs", "Night Markets", "Island Hopping", "Thai Street Food"],
                    "why_it_fits": f"Tailored for a {prefs.get('party', 'Couple')} trip balancing coastal relaxation with vibrant night bazaars.",
                },
                {
                    "city": "Gokarna & South Goa",
                    "country": "India",
                    "currency": "INR",
                    "match_score": 94,
                    "weather_note": "28°C Clear Coastal Skies — Low humidity & calm Arabian Sea",
                    "est_daily_usd": 55 if budget == "Budget" else (120 if budget == "Moderate" else 290),
                    "tags": ["Cliffside Cafes", "Heritage Latin Quarter", "Sunset Beaches", "Seafood"],
                    "why_it_fits": "Zero-rush coastal trail pairing peaceful coves in Gokarna with Fontainhas heritage walks.",
                },
                {
                    "city": "Da Nang & Hoi An",
                    "country": "Vietnam",
                    "currency": "VND",
                    "match_score": 91,
                    "weather_note": "26°C Pleasant Coastal Mildness — Great for cycling & beach lounging",
                    "est_daily_usd": 60 if budget == "Budget" else (130 if budget == "Moderate" else 310),
                    "tags": ["Lantern Old Town", "My Khe Beach", "Marble Mountains", "Banh Mi Trail"],
                    "why_it_fits": "Combines golden sand beaches with UNESCO lantern-lit streets just 30 minutes apart.",
                },
            ],
            "Mountains": [
                {
                    "city": "Manali & Kasol",
                    "country": "India",
                    "currency": "INR",
                    "match_score": 96,
                    "weather_note": "12°C Crisp Alpine Air — Clear Himalayan ridge views",
                    "est_daily_usd": 50 if budget == "Budget" else (110 if budget == "Moderate" else 260),
                    "tags": ["Pine Forests", "Riverside Cafes", "Solang Valley", "Old Manali"],
                    "why_it_fits": "High-altitude serenity with walkable village clusters and cozy mountain bakeries.",
                },
                {
                    "city": "Interlaken & Lauterbrunnen",
                    "country": "Switzerland",
                    "currency": "EUR",
                    "match_score": 93,
                    "weather_note": "10°C Crisp Mountain Sun — Seamless Swiss rail connectivity",
                    "est_daily_usd": 180 if budget == "Budget" else (320 if budget == "Moderate" else 650),
                    "tags": ["72 Waterfalls", "Alpine Railways", "Paragliding", "Lake Brienz"],
                    "why_it_fits": "Unmatched alpine drama with zero transit friction via synchronized mountain cogwheel trains.",
                },
                {
                    "city": "Pokhara",
                    "country": "Nepal",
                    "currency": "USD",
                    "match_score": 90,
                    "weather_note": "19°C Crystal Annapurna Panorama — Peak visibility season",
                    "est_daily_usd": 45 if budget == "Budget" else (95 if budget == "Moderate" else 220),
                    "tags": ["Phewa Lake", "Sarangkot Sunrise", "Himalayan Views", "Lakeside Dining"],
                    "why_it_fits": "Laid-back lakeside base offering effortless sunrise viewpoints without extreme trekking.",
                },
            ],
            "Cultural": [
                {
                    "city": "Kyoto",
                    "country": "Japan",
                    "currency": "JPY",
                    "match_score": 98,
                    "weather_note": "17°C Crisp & Clear — Ideal walking weather across historic wards",
                    "est_daily_usd": 110 if budget == "Budget" else (210 if budget == "Moderate" else 480),
                    "tags": ["Fushimi Inari", "Gion Geisha District", "Tea Ceremonies", "Nishiki Market"],
                    "why_it_fits": "Neighborhood-clustered temples, bamboo groves, and centuries-old culinary alleys.",
                },
                {
                    "city": "Udaipur & Jaipur",
                    "country": "India",
                    "currency": "INR",
                    "match_score": 95,
                    "weather_note": "24°C Golden Royal Winter — Comfortable daytime fort exploration",
                    "est_daily_usd": 55 if budget == "Budget" else (135 if budget == "Moderate" else 350),
                    "tags": ["Lake Pichola", "Amber Fort", "Rooftop Havelis", "Artisan Bazaars"],
                    "why_it_fits": "Regal architecture paired with curated spice markets and sunset boat rides.",
                },
                {
                    "city": "Istanbul",
                    "country": "Turkey",
                    "currency": "EUR",
                    "match_score": 92,
                    "weather_note": "18°C Breezy Bosphorus Weather — Ideal for ferry hops & bazaars",
                    "est_daily_usd": 80 if budget == "Budget" else (155 if budget == "Moderate" else 360),
                    "tags": ["Sultanahmet", "Grand Bazaar", "Bosphorus Cruise", "Karakoy Food"],
                    "why_it_fits": "Two continents in one trip with tightly grouped historic monuments and vibrant street dining.",
                },
            ],
            "Urban": [
                {
                    "city": "Tokyo",
                    "country": "Japan",
                    "currency": "JPY",
                    "match_score": 98,
                    "weather_note": "18°C Dry & Sunny — Effortless Yamanote Line neighborhood hops",
                    "est_daily_usd": 120 if budget == "Budget" else (230 if budget == "Moderate" else 520),
                    "tags": ["Shibuya & Shinjuku", "Asakusa", "Izakaya Alleys", "Digital Art Museums"],
                    "why_it_fits": "Hyper-efficient metro loops connecting neon skyscrapers with quiet Edo-era temples.",
                },
                {
                    "city": "Singapore",
                    "country": "Singapore",
                    "currency": "USD",
                    "match_score": 95,
                    "weather_note": "30°C Tropical Warmth — Lush covered walkways & evening bay breezes",
                    "est_daily_usd": 115 if budget == "Budget" else (225 if budget == "Moderate" else 500),
                    "tags": ["Marina Bay", "Hawker Michelin Food", "Gardens by the Bay", "Kampong Glam"],
                    "why_it_fits": "Compact city-state where every cultural enclave and futuristic garden is 15 minutes apart.",
                },
                {
                    "city": "Dubai",
                    "country": "UAE",
                    "currency": "AED",
                    "match_score": 92,
                    "weather_note": "26°C Peak Outdoor Season — Perfect for desert safaris & marina walks",
                    "est_daily_usd": 130 if budget == "Budget" else (260 if budget == "Moderate" else 600),
                    "tags": ["Downtown Skyline", "Al Fahidi Old Town", "Desert Safari", "Dubai Marina"],
                    "why_it_fits": "Seamless blend of ultra-modern architecture, heritage creek souks, and desert adventures.",
                },
            ],
        }
        return catalog.get(vibe, catalog["Cultural"])

    prompt = f"""
    Recommend the top 3 travel destinations matching these user preferences:
    - Preferred Vibe: {prefs.get('vibe')}
    - Travel Dates: {prefs.get('start_date')} for {prefs.get('duration')} days
    - Budget Tier: {prefs.get('budget')}
    - Travel Party: {prefs.get('party')}
    - Pace: {prefs.get('pace')}
    - Interests: {', '.join(prefs.get('interests', []))}

    Return strict JSON with key "recommendations" containing a list of 3 objects, each with:
    - "city" (string)
    - "country" (string)
    - "currency" (3-letter ISO currency code like USD, INR, EUR, JPY, THB, AED)
    - "match_score" (integer 85-99)
    - "weather_note" (string describing seasonal weather for the dates)
    - "est_daily_usd" (number)
    - "tags" (list of 4 short strings)
    - "why_it_fits" (1-2 sentence tailored explanation)
    """
    result = _call_llm(provider, api_key, prompt)
    return result.get("recommendations", [])[:3]


# ---------------------------------------------------------------------------
# EPIC 4: DAY-BY-DAY GEOGRAPHICALLY CLUSTERED ITINERARY GENERATOR
# ---------------------------------------------------------------------------

def generate_itinerary(
    prefs: Dict[str, Any], provider: str, api_key: str, demo_mode: bool
) -> Dict[str, Any]:
    """Generates a day-wise geographically clustered itinerary with itemized local/USD costs."""
    destination = prefs.get("destination", "").strip() or "Kyoto, Japan"
    duration = int(prefs.get("duration", 3))

    if demo_mode or not api_key:
        return _build_demo_itinerary(destination, duration, prefs)

    prompt = f"""
    Design a {duration}-day geographically optimized travel itinerary for {destination}.
    User Profile:
    - Travel Dates: starting {prefs.get('start_date')}
    - Budget Level: {prefs.get('budget')}
    - Travel Party: {prefs.get('party')}
    - Pace: {prefs.get('pace')}
    - Interests: {', '.join(prefs.get('interests', []))}

    CRITICAL LOGISTICS RULE (Geographic Clustering):
    Assign each day to ONE specific district/neighborhood cluster (e.g., "Day 1: Higashiyama & Gion District", "Day 2: Arashiyama & Western Hills") so all 4 slots on that day are within 5-15 minutes of each other with zero cross-city backtracking.

    Return strict JSON with this exact schema:
    {{
      "destination": "{destination}",
      "local_currency": "3-letter ISO code (e.g., JPY, INR, EUR, USD, THB, AED)",
      "emergency_info": {{
        "police": "local number",
        "ambulance": "local number",
        "tourist_helpline": "local tourist police/helpline",
        "local_tips": ["tip 1", "tip 2", "tip 3"]
      }},
      "days": [
        {{
          "day_number": 1,
          "cluster_zone": "Neighborhood / District Cluster Name",
          "transit_note": "Short note on walking/transit radius within this cluster",
          "slots": [
            {{
              "slot_name": "Morning Sightseeing",
              "time_window": "09:00 AM - 12:00 PM",
              "title": "Specific Venue / Activity Name",
              "neighborhood": "Exact micro-area",
              "description": "Concise actionable guide & why it fits user interests.",
              "transit_from_prev": "Starting point in cluster",
              "cost_local": 1500
            }},
            {{
              "slot_name": "Lunch Recommendation",
              "time_window": "12:15 PM - 01:45 PM",
              "title": "Specific Restaurant / Food Hall",
              "neighborhood": "Exact micro-area",
              "description": "Must-order local dishes matching budget tier.",
              "transit_from_prev": "6 min walk (450m)",
              "cost_local": 1800
            }},
            {{
              "slot_name": "Afternoon Leisure",
              "time_window": "02:00 PM - 05:30 PM",
              "title": "Specific Cultural/Adventure/Scenic Spot",
              "neighborhood": "Exact micro-area",
              "description": "Tailored afternoon experience.",
              "transit_from_prev": "10 min walk",
              "cost_local": 1200
            }},
            {{
              "slot_name": "Evening Dining & Entertainment",
              "time_window": "06:30 PM - 09:30 PM",
              "title": "Specific Dinner & Nightlife/Stroll Spot",
              "neighborhood": "Exact micro-area",
              "description": "Evening atmosphere, dining, and entertainment.",
              "transit_from_prev": "8 min walk",
              "cost_local": 3500
            }}
          ]
        }}
      ]
    }}
    """
    return _call_llm(provider, api_key, prompt)


# ---------------------------------------------------------------------------
# EPIC 4: SURGICAL SINGLE-DAY / SINGLE-SLOT DYNAMIC SWAP
# ---------------------------------------------------------------------------

def regenerate_day_or_slot(
    itinerary: Dict[str, Any],
    day_number: int,
    target_slot: str,
    modification_prompt: str,
    prefs: Dict[str, Any],
    provider: str,
    api_key: str,
    demo_mode: bool,
) -> Dict[str, Any]:
    """Modifies a single slot or single day in-place without disturbing the rest of the itinerary."""
    target_day = next(
        (d for d in itinerary.get("days", []) if d["day_number"] == day_number), None
    )
    if not target_day:
        return itinerary

    if demo_mode or not api_key:
        for slot in target_day["slots"]:
            if target_slot == "Entire Day" or slot["slot_name"] == target_slot:
                slot["title"] = f"[Updated] {modification_prompt.title()[:42]}"
                slot["description"] = (
                    f"Customized per your request ('{modification_prompt}') right inside "
                    f"{target_day['cluster_zone']} to preserve zero-backtracking transit flow."
                )
                slot["transit_from_prev"] = "5 min walk within same zone"
                slot["cost_local"] = round(slot["cost_local"] * 0.9, 0)
        return itinerary

    prompt = f"""
    Modify ONLY Day {day_number} ({target_day['cluster_zone']}) of this {itinerary['destination']} itinerary.
    - Target to modify: {target_slot}
    - User Change Request: "{modification_prompt}"
    - Keep the venue strictly inside or immediately adjacent to "{target_day['cluster_zone']}" so geographic clustering remains intact.
    - Currency: {itinerary['local_currency']} | Budget Tier: {prefs.get('budget')}

    Current Day {day_number} JSON:
    {json.dumps(target_day, indent=2)}

    Return strict JSON for ONLY the updated day object matching the exact schema:
    {{
      "day_number": {day_number},
      "cluster_zone": "{target_day['cluster_zone']}",
      "transit_note": "...",
      "slots": [ ... 4 slot objects ... ]
    }}
    """
    updated_day = _call_llm(provider, api_key, prompt)
    for idx, d in enumerate(itinerary["days"]):
        if d["day_number"] == day_number:
            itinerary["days"][idx] = updated_day
            break
    return itinerary


def _build_demo_itinerary(
    destination: str, duration: int, prefs: Dict[str, Any]
) -> Dict[str, Any]:
    """Provides rich, geographically clustered demo itineraries with realistic local costs."""
    budget = prefs.get("budget", "Moderate")
    mult = 0.6 if budget == "Budget" else (1.0 if budget == "Moderate" else 2.2)

    dest_lower = destination.lower()
    if "udaipur" in dest_lower or "jaipur" in dest_lower or "india" in dest_lower or "goa" in dest_lower or "manali" in dest_lower:
        currency = "INR"
        base_unit = 1000
    elif "tokyo" in dest_lower or "kyoto" in dest_lower or "japan" in dest_lower:
        currency = "JPY"
        base_unit = 2200
    elif "phuket" in dest_lower or "thailand" in dest_lower or "bangkok" in dest_lower:
        currency = "THB"
        base_unit = 650
    elif "dubai" in dest_lower or "uae" in dest_lower:
        currency = "AED"
        base_unit = 120
    else:
        currency = "USD"
        base_unit = 35

    day_templates = [
        {
            "cluster_zone": "Old Quarter & Heritage Core",
            "transit_note": "100% pedestrian-friendly historic core; all stops within a 1.2 km radius.",
            "slots": [
                {
                    "slot_name": "Morning Sightseeing",
                    "time_window": "09:00 AM - 12:00 PM",
                    "title": f"{destination.split(',')[0]} Grand Heritage Citadel & Sunrise Promenade",
                    "neighborhood": "Old Quarter North",
                    "description": "Arrive early to beat tour groups, explore centuries-old architecture, and capture panoramic morning views.",
                    "transit_from_prev": "Cluster starting point",
                    "cost_local": round(base_unit * 0.8 * mult),
                },
                {
                    "slot_name": "Lunch Recommendation",
                    "time_window": "12:15 PM - 01:45 PM",
                    "title": "Artisan Courtyard Kitchen & Regional Tasting Table",
                    "neighborhood": "Old Quarter Spice Lane",
                    "description": "Authentic regional thali/tasting menu sourced from local growers, featuring vegetarian & house-special platters.",
                    "transit_from_prev": "6 min walk (450m)",
                    "cost_local": round(base_unit * 1.1 * mult),
                },
                {
                    "slot_name": "Afternoon Leisure",
                    "time_window": "02:00 PM - 05:30 PM",
                    "title": "Guild Craft Workshops & Botanical Cloister Walk",
                    "neighborhood": "Old Quarter South",
                    "description": "Hands-on local craft demonstration followed by a shaded stroll through historic courtyard gardens.",
                    "transit_from_prev": "8 min walk (600m)",
                    "cost_local": round(base_unit * 0.7 * mult),
                },
                {
                    "slot_name": "Evening Dining & Entertainment",
                    "time_window": "06:30 PM - 09:30 PM",
                    "title": "Lantern Bazaar Night Walk & Rooftop Acoustic Supper",
                    "neighborhood": "Central Heritage Square",
                    "description": "Browse evening artisan stalls before settling into a candlelit rooftop dinner with live regional music.",
                    "transit_from_prev": "5 min walk (350m)",
                    "cost_local": round(base_unit * 1.8 * mult),
                },
            ],
        },
        {
            "cluster_zone": "Waterfront & Scenic Hills District",
            "transit_note": "Single 15-min scenic transit ride in the morning; lakeside boardwalk connects all afternoon/evening stops.",
            "slots": [
                {
                    "slot_name": "Morning Sightseeing",
                    "time_window": "08:30 AM - 11:45 AM",
                    "title": "Panoramic Ridge Trail & Cliffside Observatory",
                    "neighborhood": "West Hilltop Reserve",
                    "description": "Gentle morning ridge walk overlooking the bay/valley with crisp photo viewpoints.",
                    "transit_from_prev": "15 min local cab/shuttle",
                    "cost_local": round(base_unit * 0.6 * mult),
                },
                {
                    "slot_name": "Lunch Recommendation",
                    "time_window": "12:00 PM - 01:30 PM",
                    "title": "Harborfront Grill & Fresh Catch Bistro",
                    "neighborhood": "Marina Promenade",
                    "description": "Breezy waterfront seating serving wood-fired specialties, fresh salads, and cold-pressed local juices.",
                    "transit_from_prev": "10 min downhill funicular/walk",
                    "cost_local": round(base_unit * 1.3 * mult),
                },
                {
                    "slot_name": "Afternoon Leisure",
                    "time_window": "02:00 PM - 05:30 PM",
                    "title": "Private Sunset Boat Cruise & Cove Kayak",
                    "neighborhood": "South Pier",
                    "description": "Glide along calm waters with golden-hour skyline views and optional paddleboarding.",
                    "transit_from_prev": "4 min boardwalk stroll",
                    "cost_local": round(base_unit * 1.5 * mult),
                },
                {
                    "slot_name": "Evening Dining & Entertainment",
                    "time_window": "07:00 PM - 10:00 PM",
                    "title": "Night Pier Street Food Alley & Jazz Lounge",
                    "neighborhood": "Harbor East",
                    "description": "Sample iconic local street bites followed by craft mocktails/cocktails overlooking illuminated waters.",
                    "transit_from_prev": "7 min promenade walk",
                    "cost_local": round(base_unit * 1.6 * mult),
                },
            ],
        },
        {
            "cluster_zone": "Modern Arts, Markets & Culinary Quarter",
            "transit_note": "Compact creative district; zero cab rides needed between morning coffee and night market.",
            "slots": [
                {
                    "slot_name": "Morning Sightseeing",
                    "time_window": "09:30 AM - 12:00 PM",
                    "title": "Contemporary Design Museum & Street Mural District",
                    "neighborhood": "Arts Foundry Block",
                    "description": "Curated modern exhibitions and vibrant open-air street art alleys with specialty third-wave coffee.",
                    "transit_from_prev": "Cluster starting point",
                    "cost_local": round(base_unit * 0.9 * mult),
                },
                {
                    "slot_name": "Lunch Recommendation",
                    "time_window": "12:15 PM - 01:45 PM",
                    "title": "Central Covered Gastronomy Hall",
                    "neighborhood": "Market Square",
                    "description": "Vibrant culinary hall featuring 20+ family-run stalls serving authentic noodles, grills, and desserts.",
                    "transit_from_prev": "5 min walk (400m)",
                    "cost_local": round(base_unit * 1.0 * mult),
                },
                {
                    "slot_name": "Afternoon Leisure",
                    "time_window": "02:15 PM - 05:30 PM",
                    "title": "Botanical Glasshouse & Boutique Souvenir Quarter",
                    "neighborhood": "Greenway Avenue",
                    "description": "Relaxing afternoon amid exotic flora followed by curated local concept stores for meaningful keepsakes.",
                    "transit_from_prev": "8 min tree-lined walk",
                    "cost_local": round(base_unit * 0.8 * mult),
                },
                {
                    "slot_name": "Evening Dining & Entertainment",
                    "time_window": "06:45 PM - 09:45 PM",
                    "title": "Chef's Izakaya / Tapas Social & Cultural Showcase",
                    "neighborhood": "Lantern Alley",
                    "description": "Celebratory farewell dinner featuring shared small plates and lively evening ambiance.",
                    "transit_from_prev": "6 min walk",
                    "cost_local": round(base_unit * 2.0 * mult),
                },
            ],
        },
    ]

    days = []
    for i in range(duration):
        tpl = day_templates[i % len(day_templates)]
        days.append(
            {
                "day_number": i + 1,
                "cluster_zone": tpl["cluster_zone"],
                "transit_note": tpl["transit_note"],
                "slots": [dict(s) for s in tpl["slots"]],
            }
        )

    return {
        "destination": destination,
        "local_currency": currency,
        "emergency_info": {
            "police": "112 / 911 (Local Emergency Dispatch)",
            "ambulance": "108 / 112 (Medical Emergency)",
            "tourist_helpline": "+1-800-TOURIST-AID (24/7 Multilingual Desk)",
            "local_tips": [
                "Keep digital & offline PDF copies of passport/ID and hotel address.",
                "Use official metered taxis or verified ride-hailing apps after 10 PM.",
                "Carry small local currency notes for street markets and temple entries.",
            ],
        },
        "days": days,
    }
