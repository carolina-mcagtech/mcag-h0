# app/modules/observations/catalog.py

SECTION_CATALOG: dict = {
    "STRUCTURAL": {
        "label": "Structural Component Observations",
        "metadata_fields": {
            "approximate_age_of_building": {"type": "text", "label": "Approximate Age of Building"},
            "requires": {"type": "multiselect", "label": "Requires", "options": ["Repairs", "Replacement"]},
            "crawl_space_entered": {"type": "select", "label": "Crawl Space Entered", "options": ["Yes", "No"]},
            "attic_entered": {"type": "select", "label": "Attic Entered", "options": ["Yes", "No"]},
            "condensation": {"type": "select", "label": "Condensation", "options": ["Yes", "No"]},
            "water_penetration": {"type": "select", "label": "Water Penetration", "options": ["Yes", "No"]},
            "wall_material": {"type": "multiselect", "label": "Wall Material", "options": ["Concrete", "Plaster", "Wood", "Plaster & Wood", "Other"]},
            "floor_material": {"type": "multiselect", "label": "Floor Material", "options": ["Concrete", "Wood", "Plywood", "T & G Decking", "Other"]},
            "beam_material": {"type": "multiselect", "label": "Beam Material", "options": ["Wood", "Timbers", "Steel", "Concrete", "Other"]},
            "column_material": {"type": "multiselect", "label": "Column Material", "options": ["Steel", "Wood", "C.M.U.", "Other"]},
            "roof_type": {"type": "multiselect", "label": "Roof Type", "options": ["Gable", "Hip", "Shed", "Flat", "Other"]},
        },
        "items": [
            {"key": "floors", "label": "Floors", "sort_order": 1},
            {"key": "walls", "label": "Walls", "sort_order": 2},
            {"key": "columns", "label": "Columns", "sort_order": 3},
            {"key": "beams", "label": "Beams", "sort_order": 4},
            {"key": "joists", "label": "Joists", "sort_order": 5},
            {"key": "ceilings", "label": "Ceilings", "sort_order": 6},
            {"key": "trusses", "label": "Trusses", "sort_order": 7},
        ],
    },
    "EXTERIOR": {
        "label": "Exterior Component Observations",
        "metadata_fields": {
            "wood_deterioration_at": {"type": "text", "label": "Wood Deterioration At"},
            "vegetation_limits_view": {"type": "select", "label": "Vegetation Limits View", "options": ["Yes", "No"]},
            "adequate_drainage": {"type": "select", "label": "Adequate Drainage", "options": ["Yes", "No"]},
            "garage_door_opener": {"type": "select", "label": "Garage Door Opener", "options": ["Yes", "No"]},
            "safety_reverse_stop": {"type": "select", "label": "Safety Reverse Stop", "options": ["Yes", "No"]},
            "wall_material": {"type": "multiselect", "label": "Wall Material", "options": ["Metal", "Vinyl", "Wood", "Masonry", "Other"]},
            "trim_fascia_soffit": {"type": "multiselect", "label": "Trim / Fascia / Soffit", "options": ["Metal", "Vinyl", "Wood", "Other"]},
            "entry_doors": {"type": "multiselect", "label": "Entry Doors", "options": ["Metal", "Wood", "Steel", "Aluminum & Glass"]},
            "prime_windows": {"type": "multiselect", "label": "Prime Windows", "options": ["Metal", "Vinyl", "Wood", "Single Glass", "Double Glass"]},
            "sliding_doors": {"type": "multiselect", "label": "Sliding Doors", "options": ["Metal", "Vinyl", "Wood", "Single Glass", "Double Glass"]},
            "garage_doors": {"type": "multiselect", "label": "Garage Doors", "options": ["Metal", "Wood", "Fiberglass", "Fiberboard"]},
        },
        "items": [
            {"key": "wall_cladding", "label": "Wall Cladding", "sort_order": 1},
            {"key": "trim_fascia_soffit", "label": "Trim / Fascia / Soffit", "sort_order": 2},
            {"key": "entry_doors", "label": "Entry Doors", "sort_order": 3},
            {"key": "prime_windows", "label": "Prime Windows", "sort_order": 4},
            {"key": "sliding_doors", "label": "Sliding Doors", "sort_order": 5},
            {"key": "garage_doors", "label": "Garage Doors", "sort_order": 6},
            {"key": "shutters", "label": "Shutters", "sort_order": 7},
            {"key": "driveway_walks", "label": "Driveway / Walks", "sort_order": 8},
            {"key": "steps_railings", "label": "Steps / Railings", "sort_order": 9},
            {"key": "porch_balcony", "label": "Porch / Balcony", "sort_order": 10},
            {"key": "deck_patio", "label": "Deck / Patio", "sort_order": 11},
        ],
    },
    "ROOF": {
        "label": "Roof Component Observations",
        "metadata_fields": {
            "inspection_method": {"type": "multiselect", "label": "Inspection Method", "options": ["On Roof", "At Eaves", "Ground", "Other"]},
            "visible_coverings": {"type": "multiselect", "label": "Visible Coverings", "options": ["Tile", "Shingle", "Gravel", "Roll Roofing"]},
            "gutters": {"type": "multiselect", "label": "Gutters", "options": ["Aluminum", "Copper", "Plastic", "None"]},
            "flashing": {"type": "multiselect", "label": "Flashing", "options": ["Metal", "Asphalt", "Rolled", "Concealed"]},
            "approx_age_of_roof": {"type": "text", "label": "Approx Age of Roof"},
            "any_sign_of_leak": {"type": "select", "label": "Any Sign of Leak", "options": ["Yes", "No"]},
            "recommendation": {"type": "select", "label": "Recommendation", "options": ["Repair", "Replacement"]},
        },
        "items": [
            {"key": "valleys", "label": "Valleys", "sort_order": 1},
            {"key": "gutters", "label": "Gutters", "sort_order": 2},
            {"key": "downspouts", "label": "Downspouts", "sort_order": 3},
            {"key": "splash_blocks", "label": "Splash Blocks", "sort_order": 4},
            {"key": "flashing", "label": "Flashing", "sort_order": 5},
            {"key": "skylights", "label": "Skylights", "sort_order": 6},
            {"key": "chimney", "label": "Chimney", "sort_order": 7},
            {"key": "plumbing_vents", "label": "Plumbing Vents", "sort_order": 8},
            {"key": "ventilation", "label": "Ventilation", "sort_order": 9},
        ],
    },
    "ELECTRICAL": {
        "label": "Electrical Component Observations",
        "metadata_fields": {
            "service_entrance": {"type": "select", "label": "Service Entrance", "options": ["Overhead", "Underground"]},
            "over_current_device": {"type": "select", "label": "Over Current Device", "options": ["Fuse", "Breaker"]},
            "branch_protection": {"type": "select", "label": "Branch Protection", "options": ["Fuse", "Breaker"]},
            "wire_type": {"type": "multiselect", "label": "Wire Type", "options": ["Copper", "Aluminum"]},
            "main_panel_location": {"type": "text", "label": "Main Panel Location"},
        },
        "items": [
            {"key": "service_entry", "label": "Service Entry", "sort_order": 1},
            {"key": "meter", "label": "Meter", "sort_order": 2},
            {"key": "main_panel", "label": "Main Panel", "sort_order": 3},
            {"key": "main_disconnect", "label": "Main Disconnect", "sort_order": 4},
            {"key": "grounding", "label": "Grounding", "sort_order": 5},
        ],
    },
    "PLUMBING": {
        "label": "Plumbing Component Observations",
        "metadata_fields": {
            "visible_supply_lines": {"type": "multiselect", "label": "Visible Supply Lines", "options": ["Copper", "Plastic", "Iron", "Galvanized"]},
            "visible_waste_lines": {"type": "multiselect", "label": "Visible Waste Lines", "options": ["Copper", "Plastic", "Lead", "Galvanized"]},
            "water_heater_type": {"type": "select", "label": "Water Heater Type", "options": ["Electric", "Gas", "Oil", "Other"]},
            "waste_disposal": {"type": "select", "label": "Waste Disposal", "options": ["Sewer", "Septic"]},
            "water_heater_brand": {"type": "text", "label": "Water Heater Brand"},
            "water_heater_approx_age": {"type": "text", "label": "Water Heater Approx Age"},
            "water_heater_approx_capacity": {"type": "text", "label": "Water Heater Approx Capacity"},
            "pressure_relief_valve": {"type": "select", "label": "Pressure Relief Valve", "options": ["Yes", "No"]},
            "any_leaks_noted": {"type": "select", "label": "Any Leaks Noted", "options": ["Yes", "No"]},
            "unusual_conditions": {"type": "select", "label": "Unusual Conditions", "options": ["Yes", "No"]},
        },
        "items": [
            {"key": "supply_lines", "label": "Supply Lines", "sort_order": 1},
            {"key": "pan", "label": "Pan", "sort_order": 2},
            {"key": "pressure", "label": "Pressure", "sort_order": 3},
            {"key": "drainage", "label": "Drainage", "sort_order": 4},
            {"key": "exterior_faucets", "label": "Exterior Faucets", "sort_order": 5},
            {"key": "sump_pump", "label": "Sump Pump", "sort_order": 6},
            {"key": "fuel_lines", "label": "Fuel Lines", "sort_order": 7},
            {"key": "chained_to_wall", "label": "Chained to Wall", "sort_order": 8},
            {"key": "casing", "label": "Casing", "sort_order": 9},
            {"key": "tank_bottom", "label": "Tank Bottom", "sort_order": 10},
            {"key": "temp_control", "label": "Temp Control", "sort_order": 11},
        ],
    },
    "AIR_CONDITIONING": {
        "label": "Air Conditioning Component Observations",
        "metadata_fields": {
            "type_of_cooling": {"type": "multiselect", "label": "Type of Cooling", "options": ["Electrical Split System", "Hydro-Tech", "Wall Unit"]},
            "type_of_fuel": {"type": "multiselect", "label": "Type of Fuel", "options": ["Electric", "Ground Water", "Natural Gas", "Other"]},
            "distribution": {"type": "multiselect", "label": "Distribution", "options": ["Ductwork", "Metal", "Fiberglass", "Flexible"]},
            "make_of_unit": {"type": "text", "label": "Make of Unit"},
            "approximate_age": {"type": "text", "label": "Approximate Age"},
            "functioning": {"type": "select", "label": "Functioning", "options": ["Yes", "No"]},
            "adequate_cooling": {"type": "select", "label": "Adequate Cooling", "options": ["Yes", "No"]},
            "unusual_conditions": {"type": "select", "label": "Unusual Conditions", "options": ["Yes", "No"]},
            "temp_at_diffuser": {"type": "number", "label": "Temp at Diffuser (°F)"},
            "temp_at_return": {"type": "number", "label": "Temp at Return (°F)"},
            "delta_temperature": {"type": "number", "label": "Delta Temperature (°F)"},
        },
        "items": [
            {"key": "exterior_casing", "label": "Exterior Casing", "sort_order": 1},
            {"key": "exterior_lines", "label": "Exterior Lines", "sort_order": 2},
            {"key": "refrigerant_lines", "label": "Refrigerant Lines", "sort_order": 3},
            {"key": "insulation", "label": "Insulation", "sort_order": 4},
            {"key": "interior_ducts", "label": "Interior Ducts", "sort_order": 5},
            {"key": "condensate_drain", "label": "Condensate Drain", "sort_order": 6},
            {"key": "thermostat", "label": "Thermostat", "sort_order": 7},
            {"key": "elect_disconnect", "label": "Elect. Disconnect", "sort_order": 8},
        ],
    },
    "INSULATION_VENTILATION": {
        "label": "Insulation & Ventilation Component Observations",
        "metadata_fields": {
            "visible_insulation": {"type": "multiselect", "label": "Visible Insulation", "options": ["Cellulose", "Fiberglass", "Foam"]},
            "amount_in_inches": {"type": "text", "label": "Amount in Inches"},
            "how_applied": {"type": "multiselect", "label": "How Applied", "options": ["Roll / Batt", "Blown-In", "Rigid", "Other"]},
            "visible_vapor_barrier": {"type": "multiselect", "label": "Visible Vapor Barrier", "options": ["Paper", "Plastic", "Aluminum", "Other"]},
            "inadequate_ventilation_suspected": {"type": "select", "label": "Inadequate Ventilation Suspected", "options": ["Yes", "No"]},
            "vapor_barriers_missing": {"type": "select", "label": "Vapor Barriers Missing or Improper", "options": ["Yes", "No"]},
        },
        "items": [
            {"key": "insulation", "label": "Insulation", "sort_order": 1},
            {"key": "attic_vents", "label": "Attic Vents", "sort_order": 2},
            {"key": "foundation_vents", "label": "Foundation Vents", "sort_order": 3},
            {"key": "kitchen_fans", "label": "Kitchen Fans", "sort_order": 4},
            {"key": "bath_fans", "label": "Bath Fans", "sort_order": 5},
            {"key": "dryer_vent", "label": "Dryer Vent", "sort_order": 6},
        ],
    },
    "INTERIOR_KITCHEN_DINING": {
        "label": "Interior Components — Kitchen / Dining",
        "metadata_fields": {},
        "items": [
            {"key": "walls_ceilings", "label": "Walls / Ceilings", "sort_order": 1},
            {"key": "floor", "label": "Floor", "sort_order": 2},
            {"key": "cabinets", "label": "Cabinets", "sort_order": 3},
            {"key": "counters", "label": "Counters", "sort_order": 4},
            {"key": "sink", "label": "Sink", "sort_order": 5},
            {"key": "plumbing", "label": "Plumbing", "sort_order": 6},
            {"key": "electrical", "label": "Electrical", "sort_order": 7},
            {"key": "door_window", "label": "Door / Window", "sort_order": 8},
        ],
    },
    "INTERIOR_APPLIANCES": {
        "label": "Interior Components — Appliances",
        "metadata_fields": {},
        "items": [
            {"key": "refrigerator", "label": "Refrigerator", "sort_order": 1},
            {"key": "freezer", "label": "Freezer", "sort_order": 2},
            {"key": "dishwasher", "label": "Dishwasher", "sort_order": 3},
            {"key": "disposal", "label": "Disposal", "sort_order": 4},
            {"key": "washing_machine", "label": "Washing Machine", "sort_order": 5},
            {"key": "dryer", "label": "Dryer", "sort_order": 6},
            {"key": "microwave", "label": "Microwave", "sort_order": 7},
            {"key": "oven_range", "label": "Oven / Range", "sort_order": 8},
        ],
    },
    "INTERIOR_LAUNDRY_MISC": {
        "label": "Interior — Laundry / Miscellaneous",
        "metadata_fields": {
            "fire_alarms_installed": {"type": "select", "label": "Fire Alarms Installed", "options": ["Yes", "No"]},
            "proper_laundry_hookup": {"type": "select", "label": "Proper Laundry Hook-up", "options": ["Yes", "No"]},
            "dryer_type": {"type": "select", "label": "Dryer Type", "options": ["Gas", "Electric"]},
            "signs_of_leaks": {"type": "select", "label": "Signs of Leaks or Abnormal Condensation", "options": ["Yes", "No"]},
            "garage_separation": {"type": "select", "label": "House/Garage/Party Separation Surfaces Complete", "options": ["Yes", "No"]},
        },
        "items": [],
    },
    "BEDROOMS": {
        "label": "Bedrooms — Condition of Components",
        "metadata_fields": {},
        "is_room_based": True,
        "room_type": "BEDROOM",
        "items": [
            {"key": "walls_ceilings", "label": "Walls / Ceilings", "sort_order": 1},
            {"key": "floor", "label": "Floor", "sort_order": 2},
            {"key": "electrical", "label": "Electrical", "sort_order": 3},
            {"key": "door", "label": "Door", "sort_order": 4},
            {"key": "window", "label": "Window", "sort_order": 5},
            {"key": "closets", "label": "Closets", "sort_order": 6},
        ],
    },
    "BATHROOMS": {
        "label": "Bathrooms — Condition of Components",
        "metadata_fields": {},
        "is_room_based": True,
        "room_type": "BATHROOM",
        "items": [
            {"key": "walls_ceilings", "label": "Walls / Ceilings", "sort_order": 1},
            {"key": "vanity_basin", "label": "Vanity Basin", "sort_order": 2},
            {"key": "tub_shower", "label": "Tub / Shower", "sort_order": 3},
            {"key": "toilet", "label": "Toilet", "sort_order": 4},
            {"key": "plumbing", "label": "Plumbing", "sort_order": 5},
            {"key": "electrical", "label": "Electrical", "sort_order": 6},
            {"key": "door_window", "label": "Door / Window", "sort_order": 7},
            {"key": "fan", "label": "Fan", "sort_order": 8},
            {"key": "floor", "label": "Floor", "sort_order": 9},
        ],
    },
}


def get_section_catalog(section: str) -> dict | None:
    return SECTION_CATALOG.get(section)


def get_section_items(section: str) -> list[dict]:
    entry = SECTION_CATALOG.get(section)
    if entry is None:
        return []
    return entry["items"]


def get_room_label(room_type: str, room_index: int) -> str:
    if room_type == "BEDROOM":
        return "Master Bedroom" if room_index == 1 else f"Bedroom {room_index}"
    if room_type == "BATHROOM":
        return "Master Bathroom" if room_index == 1 else f"Bathroom {room_index}"
    return f"Room {room_index}"
