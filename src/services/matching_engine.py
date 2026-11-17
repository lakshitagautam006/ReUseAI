"""Resource Matching Service for ReUseAI (Phase 4).
Matches analyzed waste materials with suitable reuse opportunities and potential users
using material compatibility, physical integrity, cleanliness, condition, and reuse application synergy.
Computes dynamic, non-identical match scores and generates detailed four-point match rationales.
"""

import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field

from src.models.schemas import MatchedOpportunity, WasteAnalysisResult


@dataclass
class OpportunityCatalogItem:
    """Represents a verified reuse opportunity in the circular economy catalog."""
    opportunity_id: str
    name: str
    category: str
    target_user: str
    compatible_materials: List[str]
    compatible_waste_types: List[str]
    acceptable_conditions: List[str]
    requires_recyclable: bool
    key_applications: List[str]
    keywords: List[str]
    description: str
    requires_intact_structure: bool = False
    preferred_form: str = "any"  # "container", "crushed_bulk", "sheet", "fiber", "any"
    material_properties: str = ""


# Comprehensive sample opportunity catalog across major circular waste streams
SAMPLE_OPPORTUNITY_CATALOG: List[OpportunityCatalogItem] = [
    # ---------------- Plastics ----------------
    OpportunityCatalogItem(
        opportunity_id="OPP-PLAST-01",
        name="Makerspace 3D Printing Filament Recycler",
        category="Additive Manufacturing & Makerspaces",
        target_user="FabLabs, Makerspaces & 3D Printing Collectives",
        compatible_materials=["PET", "Polyethylene Terephthalate", "HDPE", "PP", "Plastic", "Polypropylene", "PET Bottle"],
        compatible_waste_types=["Plastics", "Plastic"],
        acceptable_conditions=["Intact", "Clean", "Lightly Soiled", "Crushed"],
        requires_recyclable=True,
        key_applications=[
            "Extrude shredded plastic flakes into 1.75mm recycled 3D printer filament.",
            "Benchtop injection molding into modular mechanical components."
        ],
        keywords=["filament", "3d print", "shred", "bottle", "pellet", "print", "extrude", "spool", "plastic"],
        description="Local makerspaces equipped with open-source plastic shredders and filament extruders.",
        requires_intact_structure=False,
        preferred_form="crushed_bulk",
        material_properties="High thermoplastic melt-reversibility, uniform melt flow index (MFI), and high tensile strength enable consistent 1.75mm diameter filament extrusion."
    ),
    OpportunityCatalogItem(
        opportunity_id="OPP-PLAST-02",
        name="rPET Textile Fiber & Yarn Spinner",
        category="Secondary Industrial Manufacturing",
        target_user="Circular Apparel & Technical Textile Mills",
        compatible_materials=["PET", "Polyethylene Terephthalate", "Polyester", "Plastic Bottle"],
        compatible_waste_types=["Plastics", "Plastic"],
        acceptable_conditions=["Intact", "Clean", "Crushed", "Lightly Soiled"],
        requires_recyclable=True,
        key_applications=[
            "Melt-spin washed polymer flake into recycled polyester staple fiber.",
            "Manufacture non-woven acoustic insulation and recycled geotextiles."
        ],
        keywords=["yarn", "fiber", "textile", "fabric", "fleece", "spinning", "bottle", "clothing", "polyester"],
        description="Regional textile recycling plants that transform post-consumer PET bottles into fiber.",
        requires_intact_structure=False,
        preferred_form="crushed_bulk",
        material_properties="High molecular weight intrinsic viscosity (IV) and elongation yield resistance allow mechanical fiber drawing into continuous staple yarn."
    ),
    OpportunityCatalogItem(
        opportunity_id="OPP-PLAST-03",
        name="Community Garden Sub-Irrigation Planter Drive",
        category="Urban Agriculture & Community DIY",
        target_user="School Allotments, Community Gardens & Urban Farmers",
        compatible_materials=["PET", "Plastic Bottle", "HDPE", "Plastic Container", "Plastic Tub", "Plastic"],
        compatible_waste_types=["Plastics", "Plastic"],
        acceptable_conditions=["Intact", "Clean"],
        requires_recyclable=False,
        key_applications=[
            "Fabricate zero-electricity passive wicking planters for herbs and seedlings.",
            "Assemble gravity-fed drip irrigation reservoirs for raised community garden beds."
        ],
        keywords=["planter", "herb", "seedling", "garden", "water", "irrigation", "soil", "wick", "pot", "bottle"],
        description="Community urban agriculture networks repurposing clean rigid containers into planters.",
        requires_intact_structure=True,
        preferred_form="container",
        material_properties="Watertight moisture barrier, UV-stability, chemical non-leaching properties, and lightweight structural rigidity form an ideal hydroponic wicking envelope."
    ),
    OpportunityCatalogItem(
        opportunity_id="OPP-PLAST-04",
        name="Eco-Brick & Structural Enclosure Initiative",
        category="Alternative Building & Civil Repurposing",
        target_user="Permaculture Collectives & Green Building Initiatives",
        compatible_materials=["Plastic", "Soft Plastic", "Film", "LDPE", "Multi-layer Plastic", "PET", "Plastic Bottle"],
        compatible_waste_types=["Plastics", "Plastic"],
        acceptable_conditions=["Intact", "Clean", "Crushed", "Lightly Soiled", "Fragmented"],
        requires_recyclable=False,
        key_applications=[
            "Pack high-density eco-bricks for thermal mass garden walls and community benches.",
            "Use as non-structural lightweight void-fill in sustainable raised beds."
        ],
        keywords=["brick", "bench", "wall", "building", "compact", "insulation", "stuff", "eco-brick"],
        description="Volunteer community building drives using non-recyclable plastic as thermal mass.",
        requires_intact_structure=False,
        preferred_form="any",
        material_properties="High durability against biological rot and long-term compressive stability provide effective inert thermal mass for earthen cob construction."
    ),

    # ---------------- Cardboard & Paper ----------------
    OpportunityCatalogItem(
        opportunity_id="OPP-CARD-01",
        name="Molded Pulp Packaging & Cushioning Converter",
        category="Industrial Secondary Packaging",
        target_user="Eco-Packaging Converters & Industrial Shippers",
        compatible_materials=["Corrugated Cardboard", "Cardboard", "Kraft Paper", "Cardboard Box", "Paperboard"],
        compatible_waste_types=["Cardboard & Paper", "Cardboard", "Paper"],
        acceptable_conditions=["Intact", "Slightly Damaged", "Crushed", "Clean"],
        requires_recyclable=True,
        key_applications=[
            "Repulp clean corrugated fiber into molded pulp electronics trays and protective corner caps.",
            "Convert into biodegradable egg cartons and produce trays."
        ],
        keywords=["box", "packaging", "pulp", "shipping", "carton", "molded", "corrugated", "cushioning", "tray"],
        description="Secondary packaging facilities hydropulping unsoiled cardboard into molded cushions.",
        requires_intact_structure=False,
        preferred_form="crushed_bulk",
        material_properties="Long unbleached virgin and secondary softwood kraft fibers provide strong interlocking hydrogen bonding and high impact absorption when hydropulped."
    ),
    OpportunityCatalogItem(
        opportunity_id="OPP-CARD-02",
        name="Urban Permaculture Sheet Mulch & Weed Barrier",
        category="Urban Agriculture & Soil Regeneration",
        target_user="Organic Community Farms, Landscapers & Community Forests",
        compatible_materials=["Corrugated Cardboard", "Cardboard", "Brown Kraft Paper", "Cardboard Box"],
        compatible_waste_types=["Cardboard & Paper", "Cardboard"],
        acceptable_conditions=["Intact", "Slightly Damaged", "Clean", "Unwaxed"],
        requires_recyclable=False,
        key_applications=[
            "Lay as weed-suppressing sheet mulch under woodchips for soil regeneration.",
            "Form biodegradable trench lining and worm composting bed carbon layers."
        ],
        keywords=["mulch", "weed", "garden", "soil", "compost", "sheet", "bed", "earthworm", "brown", "cardboard"],
        description="Local organic farms and agroforestry initiatives utilizing plain cardboard as sheet mulch.",
        requires_intact_structure=False,
        preferred_form="sheet",
        material_properties="High cellulosic carbon-to-nitrogen ratio, light-blocking opacity, and natural biodegradability decompose into rich humus while feeding beneficial fungi and earthworms."
    ),
    OpportunityCatalogItem(
        opportunity_id="OPP-CARD-03",
        name="Makerspace Flatpack Storage & Partition Lab",
        category="Makerspace & Creative DIY",
        target_user="Makerspaces, STEM Schools & Micro-Studios",
        compatible_materials=["Cardboard", "Corrugated Cardboard", "Heavy Paperboard", "Cardboard Box", "Box"],
        compatible_waste_types=["Cardboard & Paper", "Cardboard"],
        acceptable_conditions=["Intact", "Clean", "Slightly Damaged"],
        requires_recyclable=False,
        key_applications=[
            "Laser-cut or score interlocking drawer dividers and desktop craft organizers.",
            "Construct modular acoustic desk privacy shields for educational makerspaces."
        ],
        keywords=["organizer", "drawer", "divider", "storage", "box", "craft", "partition", "flatpack"],
        description="Educational workshops and makerspaces transforming cardboard boxes into organizers.",
        requires_intact_structure=True,
        preferred_form="sheet",
        material_properties="Fluted structural sandwich corrugation offers remarkable planar stiffness, lightweight rigidity, and easy scoring along flute axes for slotted joinery."
    ),
    OpportunityCatalogItem(
        opportunity_id="OPP-CARD-04",
        name="Cellulose Thermal Insulation Manufacturer",
        category="Green Building Materials",
        target_user="Eco-Insulation Contractors & Fiber Processors",
        compatible_materials=["Cardboard", "Newsprint", "Office Paper", "Paper", "Paperboard"],
        compatible_waste_types=["Cardboard & Paper", "Paper", "Cardboard"],
        acceptable_conditions=["Dry", "Clean", "Lightly Soiled", "Crushed"],
        requires_recyclable=True,
        key_applications=[
            "Fiberize dry waste paper into flame-retardant blow-in attic and wall insulation.",
            "Manufacture acoustic wall baffle batts for soundproofing commercial spaces."
        ],
        keywords=["insulation", "cellulose", "fiber", "thermal", "acoustic", "shredded", "blow-in"],
        description="Green construction contractors processing clean secondary paper into thermal insulation.",
        requires_intact_structure=False,
        preferred_form="crushed_bulk",
        material_properties="Low thermal conductivity (k-value ~0.038 W/mK) and cellular acoustic damping properties trap dead air when hammer-milled into loose-fill fibers."
    ),

    # ---------------- Metals ----------------
    OpportunityCatalogItem(
        opportunity_id="OPP-METL-01",
        name="Secondary Aluminum Foundry & Ingot Casting",
        category="Secondary Metallurgy & Foundry",
        target_user="Local Foundries & Metal Recycling Smelters",
        compatible_materials=["Aluminum", "Aluminum Can", "Tin", "Steel", "Metal", "Alloy", "Soda Can"],
        compatible_waste_types=["Metals", "Metal"],
        acceptable_conditions=["Intact", "Crushed", "Clean", "Lightly Soiled"],
        requires_recyclable=True,
        key_applications=[
            "Remelt aluminum scrap with 95% energy savings over bauxite smelting into casting ingots.",
            "Cast secondary structural hardware and engine component alloys."
        ],
        keywords=["can", "aluminum", "metal", "melt", "smelt", "ingot", "casting", "foundry", "crushed"],
        description="Regional secondary foundries remelting aluminum containers into high-purity billets.",
        requires_intact_structure=False,
        preferred_form="crushed_bulk",
        material_properties="Low metallurgical melting point (~660°C), non-degrading atomic recyclability, and high thermal efficiency yield prime secondary alloys at fraction of virgin smelting energy."
    ),
    OpportunityCatalogItem(
        opportunity_id="OPP-METL-02",
        name="Robotics Lab Hardware & Bracket Reclamation",
        category="STEM Education & Robotics Labs",
        target_user="Student Robotics Teams, Makers & Hardware Tinkers",
        compatible_materials=["Aluminum", "Steel", "Metal Scrap", "Hardware", "Brackets", "Sheet Metal", "Aluminum Can"],
        compatible_waste_types=["Metals", "Metal"],
        acceptable_conditions=["Intact", "Clean", "Slightly Damaged"],
        requires_recyclable=False,
        key_applications=[
            "Cut and drill into lightweight custom robot chassis brackets and servo mounts.",
            "Form protective heat shields and sensor enclosures for prototype electronics."
        ],
        keywords=["robotics", "bracket", "hardware", "proto", "chassis", "mount", "sheet", "drill", "metal"],
        description="Makerspace robotics teams salvaging sheet and extruded metal for custom prototyping.",
        requires_intact_structure=False,
        preferred_form="sheet",
        material_properties="Excellent strength-to-weight ratio, ductility for clean 90-degree bending, and workability with hand shears and drill bits allow rapid chassis fabrication."
    ),
    OpportunityCatalogItem(
        opportunity_id="OPP-METL-03",
        name="Artisan Tin-Punched Lantern & Planter Studio",
        category="Artisanal Decor & Household Craft",
        target_user="Craft Artisans, Etsy Makers & Decor Designers",
        compatible_materials=["Aluminum Can", "Tin Can", "Copper", "Brass", "Metal", "Can"],
        compatible_waste_types=["Metals", "Metal"],
        acceptable_conditions=["Intact", "Clean"],
        requires_recyclable=False,
        key_applications=[
            "Punch decorative filigree patterns to create candle lanterns and ambient lamps.",
            "Fabricate rust-resistant hanging succulent planters and desk caddies."
        ],
        keywords=["lantern", "candle", "holder", "planter", "lamp", "desk", "craft", "punched", "artisan", "can"],
        description="Upcycling craft collectives converting intact beverage and food cans into decorative pieces.",
        requires_intact_structure=True,
        preferred_form="container",
        material_properties="Thin-gauge aluminum or tin plate provides structural containment while remaining malleable enough for precision hole punching and light diffusion."
    ),

    # ---------------- Glass ----------------
    OpportunityCatalogItem(
        opportunity_id="OPP-GLAS-01",
        name="Cullet Terrazzo Tile & Engineered Stone Mill",
        category="Architectural Surfaces & Construction",
        target_user="Terrazzo Tile Fabricators & Green Builders",
        compatible_materials=["Glass", "Glass Bottle", "Jar", "Cullet", "Silica Glass", "Glass Jar"],
        compatible_waste_types=["Glass"],
        acceptable_conditions=["Intact", "Clean", "Fragmented", "Crushed"],
        requires_recyclable=True,
        key_applications=[
            "Crush and tumble into polished glass cullet aggregate for terrazzo countertops.",
            "Cast high-durability decorative architectural floor tiles and precast pavers."
        ],
        keywords=["glass", "cullet", "terrazzo", "crushed", "aggregate", "bottle", "tile", "countertop", "fragment"],
        description="Surface fabricators embedding crushed colored and clear container glass into terrazzo.",
        requires_intact_structure=False,
        preferred_form="crushed_bulk",
        material_properties="High compressive strength, Mohs hardness 6, and brilliant optical reflectivity create decorative, wear-resistant, polished architectural aggregates."
    ),
    OpportunityCatalogItem(
        opportunity_id="OPP-GLAS-02",
        name="Horticultural Drainage & Terrarium Substrate",
        category="Horticulture & Greenhouse Supplies",
        target_user="Urban Hydroponic Nurseries & Terrarium Crafters",
        compatible_materials=["Glass", "Glass Bottle", "Jar", "Foamed Glass", "Glass Jar"],
        compatible_waste_types=["Glass"],
        acceptable_conditions=["Clean", "Crushed", "Intact"],
        requires_recyclable=False,
        key_applications=[
            "Tumble fragments into smooth decorative pebbles for indoor plant drainage reservoirs.",
            "Repurpose intact jars into sealed miniature rainforest terrariums and vivariums."
        ],
        keywords=["drainage", "terrarium", "gravel", "plant", "hydroponic", "pebble", "jar", "succulent", "glass"],
        description="Horticulturalists and houseplant studios utilizing glass containers and tumbled cullet.",
        requires_intact_structure=False,
        preferred_form="any",
        material_properties="Chemically inert, non-porous silica glass provides zero pH distortion, excellent moisture retention boundaries, and pristine optical light transmission."
    ),
    OpportunityCatalogItem(
        opportunity_id="OPP-GLAS-03",
        name="Zero-Waste Pantry Bulk Refill & Storage Station",
        category="Zero-Waste Retail & Community Pantries",
        target_user="Bulk Grocery Refill Stores, Food Pantries & Sustainable Kitchens",
        compatible_materials=["Glass Jar", "Glass Container", "Jar", "Glass Bottle", "Silica Glass", "Glass"],
        compatible_waste_types=["Glass"],
        acceptable_conditions=["Intact", "Clean"],
        requires_recyclable=False,
        key_applications=[
            "Sanitize and deploy for circular packaging-free bulk pantry dry goods dispensing.",
            "Serve as reusable, airtight food preservation and fermentation crocks."
        ],
        keywords=["pantry", "jar", "bulk", "refill", "storage", "dry goods", "food", "airtight", "kitchen", "glass"],
        description="Packaging-free grocery stores and zero-waste pantries sanitizing clean glass containers.",
        requires_intact_structure=True,
        preferred_form="container",
        material_properties="Complete chemical inertness, non-porous non-leaching silicate matrix, zero flavor/odor retention, and high heat sanitization resistance enable infinite food-safe reuse."
    ),
    OpportunityCatalogItem(
        opportunity_id="OPP-GLAS-04",
        name="Artisan Hand-Poured Soy Candle & Luminary Studio",
        category="Artisanal Decor & Candlemaking",
        target_user="Artisan Candle Studios, Craft Collectives & Gift Boutiques",
        compatible_materials=["Glass Jar", "Jar", "Glass Container", "Glass Bottle", "Glass"],
        compatible_waste_types=["Glass"],
        acceptable_conditions=["Intact", "Clean"],
        requires_recyclable=False,
        key_applications=[
            "Pour custom natural soy and beeswax botanical candles in repurposed glass jars.",
            "Craft ambient illuminated lanterns and rustic event centerpiece luminaries."
        ],
        keywords=["candle", "wax", "luminary", "light", "lantern", "flame", "wick", "decor", "jar", "glass"],
        description="Local artisan candlemakers and eco-studios repurposing clean intact glass jars into scented candles.",
        requires_intact_structure=True,
        preferred_form="container",
        material_properties="High thermal shock resistance, thick-walled flame containment, and optical clarity disperse warm candlelight safely without toxic off-gassing."
    ),

    # ---------------- Textiles ----------------
    OpportunityCatalogItem(
        opportunity_id="OPP-TEXT-01",
        name="Mechanical Shoddy Fiber & Acoustic Batt Producer",
        category="Acoustic & Thermal Building Products",
        target_user="Soundproofing Manufacturers & Automotive Underlay Recyclers",
        compatible_materials=["Cotton", "Polyester", "Textiles", "Denim", "Fabric", "Wool", "Clothes"],
        compatible_waste_types=["Textiles"],
        acceptable_conditions=["Dry", "Clean", "Lightly Soiled", "Torn"],
        requires_recyclable=True,
        key_applications=[
            "Garnet and tear clean post-consumer textiles into high-performance acoustic wall baffles.",
            "Compress into automotive carpet underlay and vibration dampening pads."
        ],
        keywords=["shredded", "fiber", "acoustic", "insulation", "fabric", "cloth", "padding", "denim"],
        description="Industrial fiber processors reclaiming post-consumer textiles into acoustic padding.",
        requires_intact_structure=False,
        preferred_form="fiber",
        material_properties="Interlaced fibrous matrix absorbs acoustic vibrations and provides thermal resistance when mechanically shredded into dense non-woven batts."
    ),

    # ---------------- Electronics ----------------
    OpportunityCatalogItem(
        opportunity_id="OPP-ELEC-01",
        name="Community Hardware Repair Cafe & Component Bank",
        category="Community Repair & Electronics Reuse",
        target_user="Repair Cafes, Electronics Tinkers & Volunteer Fixers",
        compatible_materials=["Circuit Board", "Wiring", "Cables", "Electronics", "PCB", "Electronic"],
        compatible_waste_types=["Electronics"],
        acceptable_conditions=["Intact", "Slightly Damaged", "Clean"],
        requires_recyclable=False,
        key_applications=[
            "Desolder and test salvageable passives, connectors, and power regulator modules.",
            "Strip and splice intact copper wiring and power cords for household appliance repairs."
        ],
        keywords=["cable", "circuit", "pcb", "component", "repair", "wire", "switch", "electronics", "solder"],
        description="Community repair networks harvesting components to keep consumer appliances alive.",
        requires_intact_structure=False,
        preferred_form="any",
        material_properties="High-purity electrolytic copper conductor traces and modular solid-state silicon components maintain functional viability long after outer housing disposal."
    ),

    # ---------------- Wood & Timber ----------------
    OpportunityCatalogItem(
        opportunity_id="OPP-WOOD-01",
        name="Architectural Salvage & Rustic Furniture Studio",
        category="Custom Woodworking & Carpentry",
        target_user="Carpenters, Woodworkers & Makerspace Craftsmen",
        compatible_materials=["Lumber", "Pallet Wood", "Timber", "Untreated Wood", "Plywood", "Wood"],
        compatible_waste_types=["Wood & Timber", "Wood"],
        acceptable_conditions=["Intact", "Clean", "Dry", "Slightly Damaged"],
        requires_recyclable=False,
        key_applications=[
            "Plane and join reclaimed lumber into rustic shelving, dining tables, and accent walls.",
            "Construct sturdy raised planter boxes for local community allotments."
        ],
        keywords=["wood", "pallet", "shelf", "timber", "furniture", "lumber", "planing", "carpentry", "box"],
        description="Artisanal woodworking shops turning salvaged crates, pallets, and lumber into furniture.",
        requires_intact_structure=False,
        preferred_form="sheet",
        material_properties="Cellular lignocellulosic grain provides high bending strength, natural warm aesthetics, and excellent fastener holding when dressed with hand planes."
    ),

    # ---------------- Organics ----------------
    OpportunityCatalogItem(
        opportunity_id="OPP-ORGN-01",
        name="Community In-Vessel Compost & Soil Regeneration",
        category="Soil Biology & Urban Composting",
        target_user="Urban Community Gardens & Municipal Composting Hubs",
        compatible_materials=["Food Waste", "Clean Biomass", "Organic", "Compostable", "Green Waste"],
        compatible_waste_types=["Organics", "Organic"],
        acceptable_conditions=["Clean", "Fresh", "Soiled"],
        requires_recyclable=False,
        key_applications=[
            "Blend high-nitrogen food scraps with high-carbon mulch in thermophilic compost reactors.",
            "Produce living, microbe-rich compost topdressing for municipal parks and garden beds."
        ],
        keywords=["compost", "soil", "organic", "rot", "fertilizer", "garden", "mulch", "microbe"],
        description="Neighborhood composting hubs diverting biodegradable kitchen and market waste.",
        requires_intact_structure=False,
        preferred_form="any",
        material_properties="High bioavailable nitrogen and organic moisture content accelerate thermophilic microbial proliferation, heating piles above 55°C to pasteurize weed seeds."
    ),

    # ---------------- General / Mixed Creative Reuse ----------------
    OpportunityCatalogItem(
        opportunity_id="OPP-COMM-01",
        name="Community Creative Reuse & STEM Scrap Depot",
        category="Public Arts & Educational STEM",
        target_user="Art Teachers, Early Childhood Educators & Crafters",
        compatible_materials=["Plastic", "Cardboard", "Metal", "Glass", "Fabric", "Wood", "Paper"],
        compatible_waste_types=["Plastics", "Cardboard & Paper", "Metals", "Glass", "Textiles", "Wood & Timber", "Other"],
        acceptable_conditions=["Clean", "Intact", "Slightly Damaged"],
        requires_recyclable=False,
        key_applications=[
            "Distribute clean industrial clean-cuts and packaging scrap to local schools for STEM challenges.",
            "Supply community art centers and makerspaces with low-cost mixed-media materials."
        ],
        keywords=["craft", "school", "art", "creative", "reuse", "kid", "stem", "diy", "project"],
        description="Community scrap stores providing free or low-cost clean discard materials to educators.",
        requires_intact_structure=False,
        preferred_form="any",
        material_properties="Safe, clean, non-toxic household and industrial offcuts stimulate tactile exploratory problem-solving and open-ended artistic composition."
    ),
]


class ResourceMatchingEngine:
    """Resource Matching Service for ReUseAI (Phase 4).
    Evaluates analyzed waste material against an opportunity catalog using:
    - Material compatibility (max 35 pts)
    - Waste type compatibility (max 20 pts)
    - Physical condition, cleanliness & integrity readiness (max 25 pts)
    - Reuse idea & application synergy (max 20 pts)
    Calculates dynamic, non-identical match scores and delivers detailed, comprehensive rationales.
    """

    MIN_MATCH_THRESHOLD: float = 50.0

    def __init__(self, catalog: Optional[List[OpportunityCatalogItem]] = None):
        self.catalog = catalog if catalog is not None else SAMPLE_OPPORTUNITY_CATALOG

    def match(
        self,
        material: str,
        waste_type: str,
        condition: str,
        recyclable: Union[bool, int, str] = True,
        reuse_ideas: Optional[List[str]] = None,
        confidence: float = 0.95,
        top_k: int = 3,
    ) -> List[MatchedOpportunity]:
        """Perform intelligent multi-factor matching against the opportunity catalog.

        Args:
            material: Detected material name (e.g., 'Polyethylene Terephthalate / PET Plastic').
            waste_type: Waste category (e.g., 'Plastics', 'Cardboard & Paper').
            condition: Physical state and cleanliness (e.g., 'Intact, Clean', 'Crushed').
            recyclable: Whether item is recyclable (bool/int).
            reuse_ideas: List of practical reuse/upcycling suggestions from AI analysis.
            confidence: Vision model confidence rating (0.0 to 1.0).
            top_k: Maximum number of top matching opportunities to return (default 3).

        Returns:
            List of up to top_k MatchedOpportunity instances meeting the match threshold.
        """
        if not material or not str(material).strip():
            return []

        clean_material = str(material).strip()
        clean_waste_type = str(waste_type).strip() if waste_type else "Other"
        clean_condition = str(condition).strip() if condition else "Intact"
        ideas_list = reuse_ideas if isinstance(reuse_ideas, list) else []

        # Coerce recyclable flag
        if isinstance(recyclable, bool):
            is_rec = recyclable
        elif isinstance(recyclable, (int, float)):
            is_rec = recyclable >= 50
        elif isinstance(recyclable, str):
            is_rec = recyclable.lower() in ("true", "yes", "1", "recyclable")
        else:
            is_rec = True

        scored_candidates: List[MatchedOpportunity] = []

        for opp in self.catalog:
            score, reason, suggested_app = self._evaluate_opportunity(
                opp=opp,
                material=clean_material,
                waste_type=clean_waste_type,
                condition=clean_condition,
                recyclable=is_rec,
                reuse_ideas=ideas_list,
                confidence=confidence,
            )

            if score >= self.MIN_MATCH_THRESHOLD:
                scored_candidates.append(
                    MatchedOpportunity(
                        opportunity_name=opp.name,
                        opportunity_category=opp.category,
                        match_score=score,
                        reason=reason,
                        suggested_application=suggested_app,
                        target_user=opp.target_user,
                    )
                )

        # Sort descending by match score
        scored_candidates.sort(key=lambda x: x.match_score, reverse=True)

        return scored_candidates[:top_k]

    def match_from_result(
        self,
        analysis_result: WasteAnalysisResult,
        top_k: int = 3,
    ) -> List[MatchedOpportunity]:
        """Convenience method to execute resource matching directly from a WasteAnalysisResult."""
        if not analysis_result or not analysis_result.material:
            return []

        mat = analysis_result.material
        raw_ideas = [s.title for s in analysis_result.reuse_suggestions] if analysis_result.reuse_suggestions else []
        return self.match(
            material=mat.material_type,
            waste_type=mat.primary_category,
            condition=mat.physical_condition,
            recyclable=mat.recyclable,
            reuse_ideas=raw_ideas,
            confidence=mat.confidence_score,
            top_k=top_k,
        )

    def _evaluate_opportunity(
        self,
        opp: OpportunityCatalogItem,
        material: str,
        waste_type: str,
        condition: str,
        recyclable: bool,
        reuse_ideas: List[str],
        confidence: float,
    ) -> tuple[float, str, str]:
        """Compute multi-factor score and generate specific 4-point matching reasoning."""
        mat_lower = material.lower()
        waste_lower = waste_type.lower()
        cond_lower = condition.lower()
        ideas_combined = " ".join([str(i) for i in reuse_ideas]).lower()

        # ---------------- 1. Material Compatibility (0 to 35 pts) ----------------
        mat_score = 0.0
        mat_match_name = ""
        is_exact_grade = False

        # Check for specific polymer / grade matches first
        for comp in opp.compatible_materials:
            comp_lower = comp.lower()
            if comp_lower in mat_lower:
                if len(comp) >= 3 and comp_lower not in ["plastic", "metal", "glass", "wood", "paper", "box"]:
                    # Continuous granular score based on match specificity
                    mat_score = min(35.0, 32.5 + len(comp) * 0.1)
                    mat_match_name = comp
                    is_exact_grade = True
                    break
                else:
                    mat_score = 29.5
                    mat_match_name = comp

        if not is_exact_grade:
            for comp in opp.compatible_materials:
                comp_lower = comp.lower()
                if mat_lower in comp_lower or comp_lower in mat_lower:
                    mat_score = max(mat_score, min(29.0, 26.0 + len(comp) * 0.1))
                    if not mat_match_name:
                        mat_match_name = comp
                    break

        if mat_score == 0.0:
            # Token overlap check
            mat_tokens = set(re.findall(r"\w+", mat_lower))
            for comp in opp.compatible_materials:
                comp_tokens = set(re.findall(r"\w+", comp.lower()))
                if mat_tokens & comp_tokens:
                    mat_score = 16.0
                    mat_match_name = comp
                    break

        # ---------------- 2. Waste Type Compatibility (0 to 20 pts) ----------------
        waste_score = 0.0
        for cwt in opp.compatible_waste_types:
            cwt_lower = cwt.lower()
            if cwt_lower == waste_lower:
                waste_score = 20.0
                break
            elif cwt_lower in waste_lower or waste_lower in cwt_lower:
                waste_score = 16.5
                break
            elif "other" in cwt_lower or "mixed" in cwt_lower:
                waste_score = 10.0

        # Hard disqualification if neither material nor category has relevance
        if mat_score == 0.0 and waste_score == 0.0:
            return 0.0, "Incompatible material and waste category.", ""

        # ---------------- 3. Condition & Physical Integrity (0 to 25 pts) ----------------
        cond_score = 14.0
        cond_eval_reason = ""

        is_crushed_or_fragmented = any(k in cond_lower for k in ["crushed", "fragment", "broken", "shattered", "shredded", "torn"])
        is_clean = any(k in cond_lower for k in ["clean", "sanitized", "unsoiled", "sterile", "dry"])
        is_soiled = any(k in cond_lower for k in ["soiled", "dirty", "residue", "stain", "oily"])
        is_hazardous = any(k in cond_lower for k in ["heavy", "contaminat", "toxic", "hazard", "biohazard", "radioactive", "sludge"])

        if is_hazardous:
            cond_score = 2.0
            cond_eval_reason = f"Condition '{condition}' presents severe contamination or toxicity, preventing reuse without specialized hazardous treatment."
        elif opp.requires_intact_structure and is_crushed_or_fragmented:
            # Planter, Jar storage, Lantern, or Box organizer CANNOT use crushed/broken vessels
            cond_score = 4.0
            cond_eval_reason = f"Application requires an intact physical vessel; the current {condition.lower()} state compromises structural containment."
        elif opp.preferred_form == "crushed_bulk" and is_crushed_or_fragmented:
            # Foundry, Terrazzo, Pelletizer, Shoddy fiber actually PREFERS crushed/fragmented compaction
            cond_score = 24.5 if not is_soiled else 18.5
            cond_eval_reason = f"Compacted or fragmented state '{condition}' is optimal for bulk transit density and rapid secondary shredding/remelting."
        elif opp.requires_intact_structure and not is_crushed_or_fragmented:
            if is_clean:
                cond_score = 24.2
                if opp.preferred_form == "container":
                    cond_eval_reason = f"Intact and clean physical condition '{condition}' preserves watertight structural integrity for immediate container reuse."
                elif opp.preferred_form == "sheet":
                    cond_eval_reason = f"Intact and clean physical condition '{condition}' preserves planar stiffness and surface integrity for structural partitioning."
                else:
                    cond_eval_reason = f"Intact and clean physical condition '{condition}' preserves structural integrity and dimensional stability for immediate secondary reuse."
            else:
                cond_score = 17.8
                cond_eval_reason = f"Intact structure '{condition}' provides suitable physical form, though standard surface cleaning is advised before deployment."
        else:
            # General / other forms
            if is_clean or "intact" in cond_lower:
                cond_score = 21.0
                cond_eval_reason = f"Physical condition '{condition}' satisfies processing standards without significant material degradation."
            elif is_soiled:
                cond_score = 14.0
                cond_eval_reason = f"Material exhibits light surface soiling ({condition}), which requires washing but does not compromise bulk reprocessing."
            else:
                cond_score = 16.0
                cond_eval_reason = f"Physical state '{condition}' is acceptable for secondary conversion."

        # Bonus for optimal physical form match (e.g. rigid container vs flat sheet)
        if opp.preferred_form == "container" and any(k in mat_lower for k in ["bottle", "jar", "can", "tub", "pot", "vessel"]):
            cond_score = min(25.0, cond_score + 0.6)
        elif opp.preferred_form == "sheet" and any(k in mat_lower for k in ["box", "board", "cardboard", "sheet", "corrugat"]):
            cond_score = min(25.0, cond_score + 0.6)

        # ---------------- 4. Reuse Application Synergy (0 to 20 pts) ----------------
        matched_keywords = []
        for kw in opp.keywords:
            if kw in ideas_combined or kw in mat_lower:
                matched_keywords.append(kw)

        # Differentiate alignment with primary (first) suggestion vs secondary ideas
        primary_idea = str(reuse_ideas[0]).lower() if reuse_ideas else ""
        primary_matches = set([kw for kw in opp.keywords if kw in primary_idea])
        all_unique_matches = set(matched_keywords)

        # Continuous, dynamic score based on depth of alignment
        synergy_base = 5.0
        primary_bonus = len(primary_matches) * 2.5
        secondary_bonus = len(all_unique_matches - primary_matches) * 1.4
        idea_score = min(20.0, synergy_base + primary_bonus + secondary_bonus)

        # ---------------- Composite Score Calculation ----------------
        base_total = mat_score + waste_score + cond_score + idea_score

        # Recyclability constraint enforcement
        if opp.requires_recyclable and not recyclable:
            base_total = min(base_total, 38.0)

        # Structural integrity constraint enforcement
        if opp.requires_intact_structure and is_crushed_or_fragmented:
            base_total = min(base_total, 34.0)

        # Confidence weighting: dynamic scaling without locking scores together
        conf_clamped = max(0.6, min(1.0, float(confidence)))
        scaled_total = base_total * (0.88 + 0.12 * conf_clamped)

        # Clamp and round to 1 decimal place
        final_score = round(max(0.0, min(99.0, scaled_total)), 1)

        # ---------------- Generate 4-Point Match Rationale ----------------
        suggested_app = opp.key_applications[0] if opp.key_applications else opp.description
        full_reason = self._generate_four_point_rationale(
            material=material,
            opp=opp,
            mat_match_name=mat_match_name or material,
            mat_score=mat_score,
            condition=condition,
            cond_eval_reason=cond_eval_reason,
            matched_keywords=matched_keywords,
            suggested_app=suggested_app,
        )

        return final_score, full_reason, suggested_app

    def _generate_four_point_rationale(
        self,
        material: str,
        opp: OpportunityCatalogItem,
        mat_match_name: str,
        mat_score: float,
        condition: str,
        cond_eval_reason: str,
        matched_keywords: List[str],
        suggested_app: str,
    ) -> str:
        """Compose a rigorous match rationale explicitly covering all four required criteria:
        1. Why this resource matches the material.
        2. Which physical properties make it suitable.
        3. Whether the material condition supports the proposed application.
        4. What the resource can practically be used for.
        """
        # Point 1: Material Match Basis
        pt1 = f"{material} directly supplies compatible {mat_match_name} feedstock for {opp.name}."

        # Point 2: Specific Physical Properties
        if opp.material_properties:
            pt2 = f"Key properties: {opp.material_properties}"
        else:
            pt2 = "Key properties: High material durability and inherent structural viability make it suitable for secondary circular processing."

        # Point 3: Condition Suitability
        pt3 = f"Condition suitability: {cond_eval_reason}"

        # Point 4: Practical Reuse Application
        pt4 = f"Practical application: Can be immediately utilized by {opp.target_user} to {suggested_app.rstrip('.')}."

        return f"{pt1} {pt2} {pt3} {pt4}"

    def get_unmatched_explanation(
        self,
        material: str,
        waste_type: str,
        condition: str,
    ) -> str:
        """Provide a clear, human-friendly explanation when no matching opportunities are found."""
        return (
            f"No verified reuse opportunities met the minimum 50% compatibility threshold for '{material}' "
            f"under condition '{condition}'. This typically occurs with heavily degraded, hazardous, or composite materials. "
            "We recommend municipal hazardous sorting, verified waste-to-energy recovery, or contacting a specialized recycler."
        )


# Backward-compatible and convenient alias
ResourceMatcher = ResourceMatchingEngine
