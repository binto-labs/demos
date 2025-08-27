# Earthquake Claim Accelerator - Core Algorithm Pseudocode

## 1. Document Analysis Algorithm (PDF Extraction and AI Processing)

### Algorithm: AnalyzeEngineeringReport
```
ALGORITHM: AnalyzeEngineeringReport
INPUT: pdf_path (string), llm_client (LLM interface)
OUTPUT: DamageExtraction (structured damage data)

DATA STRUCTURES:
    DamageExtraction:
        - structural_elements: List<string>
        - damage_descriptions: Map<string, string>
        - cost_estimates: Map<string, float>
        - compliance_issues: List<string>
        - confidence_score: float

CONSTANTS:
    MAX_TEXT_EXTRACTION = 8000 characters
    MIN_CONFIDENCE_THRESHOLD = 0.7
    COST_PATTERN_REGEX = "\$[\d,]+(?:\.\d{2})?"

BEGIN
    // Phase 1: Text Extraction
    raw_text ← ExtractPDFText(pdf_path)
    
    IF raw_text.length = 0 THEN
        RETURN error("Failed to extract text from PDF")
    END IF
    
    // Phase 2: Structured Extraction using LLM
    extraction_prompt ← BuildExtractionPrompt()
    truncated_text ← raw_text.substring(0, MAX_TEXT_EXTRACTION)
    
    llm_response ← llm_client.complete(
        prompt: extraction_prompt,
        text: truncated_text,
        max_tokens: 2000,
        temperature: 0.1  // Low temperature for consistent extraction
    )
    
    // Phase 3: Parse and Structure Data
    structured_data ← ParseLLMResponse(llm_response)
    
    // Phase 4: Extract Cost Estimates with Pattern Matching
    cost_estimates ← ExtractCostEstimates(raw_text)
    
    // Phase 5: Identify Compliance Issues
    compliance_issues ← ExtractComplianceIssues(raw_text)
    
    // Phase 6: Calculate Confidence Score
    confidence ← CalculateConfidenceScore(structured_data, cost_estimates, compliance_issues)
    
    // Phase 7: Validate and Return
    IF confidence < MIN_CONFIDENCE_THRESHOLD THEN
        LogWarning("Low confidence extraction", confidence)
    END IF
    
    RETURN DamageExtraction(
        structural_elements: structured_data.structural,
        damage_descriptions: structured_data.descriptions,
        cost_estimates: cost_estimates,
        compliance_issues: compliance_issues,
        confidence_score: confidence
    )
END

SUBROUTINE: ExtractCostEstimates
INPUT: text (string)
OUTPUT: cost_map (Map<string, float>)

CONSTANTS:
    COST_CATEGORIES = ["structural", "facade", "services", "demolition", "temporary", "professional"]

BEGIN
    cost_map ← EmptyMap()
    
    FOR EACH category IN COST_CATEGORIES DO
        // Look for costs within 200 characters of category keyword
        pattern ← category + ".*?" + COST_PATTERN_REGEX
        matches ← RegexFindAll(pattern, text, CASE_INSENSITIVE, MAX_DISTANCE: 200)
        
        IF matches.length > 0 THEN
            // Take the largest amount if multiple found
            amounts ← []
            FOR EACH match IN matches DO
                clean_amount ← CleanCurrencyString(match.amount)
                amounts.append(ParseFloat(clean_amount))
            END FOR
            cost_map[category] ← Max(amounts)
        END IF
    END FOR
    
    RETURN cost_map
END

SUBROUTINE: CalculateConfidenceScore
INPUT: structured_data, cost_estimates, compliance_issues
OUTPUT: score (float between 0 and 1)

BEGIN
    base_score ← 0.5
    
    // Structural elements found
    IF structured_data.structural.length > 0 THEN
        base_score += 0.1
    END IF
    
    // Rich damage descriptions
    IF structured_data.descriptions.size > 3 THEN
        base_score += 0.15
    END IF
    
    // Cost estimates extracted
    IF cost_estimates.size > 2 THEN
        base_score += 0.15
    END IF
    
    // Compliance issues identified
    IF compliance_issues.length > 0 THEN
        base_score += 0.1
    END IF
    
    RETURN Min(base_score, 1.0)
END
```

**Time Complexity**: O(n) where n = document length
**Space Complexity**: O(m) where m = extracted data size
**Optimization**: Parallel processing for multiple documents, caching LLM responses

---

## 2. Precedent Matching Algorithm (Vector Similarity Search)

### Algorithm: FindSimilarCases
```
ALGORITHM: FindSimilarCases
INPUT: claim_details (ClaimData), top_k (integer)
OUTPUT: ranked_precedents (List<PrecedentCase>)

DATA STRUCTURES:
    ClaimData:
        - building_type: string
        - floors: integer
        - year_built: integer
        - nbs_rating: float
        - structural_damage: string
        - facade_damage: string
        - services_damage: string
        - estimated_cost: float
        - key_issues: List<string>
    
    PrecedentCase:
        - case_reference: string
        - building_type: string
        - floors: integer
        - damage_level: string
        - claim_amount: float
        - settlement_amount: float
        - settlement_ratio: float
        - key_arguments: List<string>
        - timeline_days: integer
        - insurer: string
        - similarity_score: float
        - relevance_score: float

CONSTANTS:
    EMBEDDING_DIMENSION = 1536  // OpenAI embedding size
    SIMILARITY_THRESHOLD = 0.6
    RERANK_WEIGHTS = {
        similarity: 0.5,
        damage_match: 0.2,
        amount_proximity: 0.15,
        insurer_match: 0.1,
        recency_boost: 0.05
    }

BEGIN
    // Phase 1: Create Query Embedding
    claim_description ← CreateClaimDescription(claim_details)
    query_embedding ← embedding_model.encode(claim_description)
    
    // Phase 2: Vector Similarity Search with Filters
    filters ← BuildSearchFilters(claim_details)
    
    candidate_cases ← VectorSearch(
        embedding: query_embedding,
        filters: filters,
        limit: top_k * 3  // Oversample for reranking
    )
    
    // Phase 3: Multi-factor Reranking
    FOR EACH case IN candidate_cases DO
        case.relevance_score ← CalculateRelevanceScore(case, claim_details, query_embedding)
    END FOR
    
    // Phase 4: Sort and Return Top K
    ranked_cases ← SortByDescending(candidate_cases, "relevance_score")
    
    RETURN ranked_cases[0:top_k]
END

SUBROUTINE: VectorSearch
INPUT: embedding, filters, limit
OUTPUT: similar_cases (List<PrecedentCase>)

BEGIN
    // PostgreSQL with pgvector extension
    query ← """
    SELECT 
        id, case_reference, building_type, floors,
        damage_level, claim_amount, settlement_amount,
        key_arguments, timeline_days, insurer,
        1 - (embedding <-> $1) as similarity_score
    FROM precedent_cases
    WHERE building_type = $2
        AND floors BETWEEN $3 AND $4
        AND 1 - (embedding <-> $1) > $5
    ORDER BY embedding <-> $1
    LIMIT $6
    """
    
    results ← database.execute(
        query,
        [embedding, filters.building_type, 
         filters.floor_min, filters.floor_max,
         SIMILARITY_THRESHOLD, limit]
    )
    
    RETURN results
END

SUBROUTINE: CalculateRelevanceScore
INPUT: precedent_case, claim_details, query_embedding
OUTPUT: relevance_score (float)

BEGIN
    base_similarity ← precedent_case.similarity_score * RERANK_WEIGHTS.similarity
    
    // Damage level matching
    damage_bonus ← 0
    IF precedent_case.damage_level = claim_details.structural_damage THEN
        damage_bonus ← RERANK_WEIGHTS.damage_match
    END IF
    
    // Claim amount proximity (within 20% gets full bonus)
    amount_bonus ← 0
    IF claim_details.estimated_cost > 0 THEN
        ratio ← precedent_case.claim_amount / claim_details.estimated_cost
        IF 0.8 <= ratio <= 1.2 THEN
            amount_bonus ← RERANK_WEIGHTS.amount_proximity
        ELSE IF 0.6 <= ratio <= 1.4 THEN
            amount_bonus ← RERANK_WEIGHTS.amount_proximity * 0.5
        END IF
    END IF
    
    // Same insurer bonus
    insurer_bonus ← 0
    IF precedent_case.insurer = claim_details.insurer THEN
        insurer_bonus ← RERANK_WEIGHTS.insurer_match
    END IF
    
    // Recency boost (newer cases weighted higher)
    recency_boost ← CalculateRecencyBoost(precedent_case.settlement_date)
    
    total_score ← base_similarity + damage_bonus + amount_bonus + insurer_bonus + recency_boost
    
    RETURN Min(total_score, 1.0)
END

SUBROUTINE: ExtractStrategyInsights
INPUT: precedent_cases (List<PrecedentCase>)
OUTPUT: insights (StrategyInsights)

BEGIN
    // Calculate aggregate statistics
    settlement_ratios ← [case.settlement_ratio FOR case IN precedent_cases]
    timeline_days ← [case.timeline_days FOR case IN precedent_cases]
    
    avg_settlement_ratio ← Mean(settlement_ratios)
    avg_timeline ← Mean(timeline_days)
    
    // Extract common arguments from successful cases
    successful_cases ← Filter(precedent_cases, lambda case: case.settlement_ratio > 0.8)
    all_arguments ← FlattenList([case.key_arguments FOR case IN successful_cases])
    argument_frequency ← CountFrequency(all_arguments)
    common_arguments ← TopN(argument_frequency, 5)
    
    // Analyze insurer patterns
    insurer_performance ← GroupBy(precedent_cases, "insurer")
    insurer_patterns ← {}
    FOR EACH insurer, cases IN insurer_performance DO
        insurer_patterns[insurer] ← {
            avg_ratio: Mean([case.settlement_ratio FOR case IN cases]),
            avg_timeline: Mean([case.timeline_days FOR case IN cases]),
            case_count: cases.length
        }
    END FOR
    
    RETURN StrategyInsights(
        average_settlement_ratio: avg_settlement_ratio,
        average_timeline_days: avg_timeline,
        common_arguments: common_arguments,
        insurer_patterns: insurer_patterns,
        confidence: CalculateInsightConfidence(precedent_cases)
    )
END
```

**Time Complexity**: O(log n + k) for vector search, O(k log k) for reranking
**Space Complexity**: O(k + d) where k = candidates, d = embedding dimension
**Optimization**: Index maintenance, embedding caching, batch processing

---

## 3. Damage Assessment Algorithm (From Engineering Reports)

### Algorithm: AssessDamageFromReport
```
ALGORITHM: AssessDamageFromReport
INPUT: extraction_data (DamageExtraction), property_data (PropertyInfo)
OUTPUT: damage_assessment (DamageAssessment)

DATA STRUCTURES:
    DamageAssessment:
        - structural_level: DamageLevel (none, minor, moderate, major, severe)
        - facade_level: DamageLevel
        - services_level: DamageLevel
        - overall_severity_score: float (0-1)
        - repair_cost_estimate: float
        - repair_timeline_estimate: integer (days)
        - risk_factors: List<string>
        - compliance_requirements: List<string>

CONSTANTS:
    DAMAGE_KEYWORDS = {
        "severe": ["collapsed", "failed", "destroyed", "unsafe", "condemned"],
        "major": ["significant", "extensive", "structural", "bearing", "foundation"],
        "moderate": ["cracked", "damaged", "displaced", "compromised"],
        "minor": ["hairline", "superficial", "cosmetic", "surface"],
        "none": ["no damage", "intact", "undamaged", "sound"]
    }
    
    BASE_REPAIR_COSTS = {
        "severe": 0.6,     // 60% of property value
        "major": 0.4,      // 40% of property value
        "moderate": 0.2,   // 20% of property value
        "minor": 0.05,     // 5% of property value
        "none": 0.0
    }

BEGIN
    // Phase 1: Analyze Structural Damage
    structural_level ← ClassifyDamageLevel(
        extraction_data.structural_elements,
        extraction_data.damage_descriptions,
        "structural"
    )
    
    // Phase 2: Analyze Facade Damage
    facade_level ← ClassifyDamageLevel(
        extraction_data.structural_elements,
        extraction_data.damage_descriptions,
        "facade"
    )
    
    // Phase 3: Analyze Services Damage
    services_level ← ClassifyDamageLevel(
        extraction_data.structural_elements,
        extraction_data.damage_descriptions,
        "services"
    )
    
    // Phase 4: Calculate Overall Severity
    severity_score ← CalculateOverallSeverity(structural_level, facade_level, services_level)
    
    // Phase 5: Estimate Repair Costs
    base_cost ← EstimateBaseCost(structural_level, facade_level, services_level, property_data)
    adjusted_cost ← ApplyCostAdjustments(base_cost, extraction_data, property_data)
    
    // Phase 6: Estimate Timeline
    timeline ← EstimateRepairTimeline(structural_level, facade_level, services_level, adjusted_cost)
    
    // Phase 7: Identify Risk Factors
    risk_factors ← IdentifyRiskFactors(extraction_data, property_data, severity_score)
    
    // Phase 8: Extract Compliance Requirements
    compliance_requirements ← ExtractComplianceRequirements(extraction_data.compliance_issues)
    
    RETURN DamageAssessment(
        structural_level: structural_level,
        facade_level: facade_level,
        services_level: services_level,
        overall_severity_score: severity_score,
        repair_cost_estimate: adjusted_cost,
        repair_timeline_estimate: timeline,
        risk_factors: risk_factors,
        compliance_requirements: compliance_requirements
    )
END

SUBROUTINE: ClassifyDamageLevel
INPUT: structural_elements, damage_descriptions, category
OUTPUT: damage_level (DamageLevel)

BEGIN
    category_text ← ExtractCategoryText(structural_elements, damage_descriptions, category)
    
    IF category_text.length = 0 THEN
        RETURN "none"
    END IF
    
    // Score each damage level based on keyword presence
    level_scores ← {}
    FOR EACH level, keywords IN DAMAGE_KEYWORDS DO
        score ← 0
        FOR EACH keyword IN keywords DO
            occurrences ← CountOccurrences(keyword, category_text, CASE_INSENSITIVE)
            score += occurrences * GetKeywordWeight(keyword)
        END FOR
        level_scores[level] ← score
    END FOR
    
    // Return level with highest score
    max_level ← MaxKey(level_scores)
    
    // Validate with cost indicators if available
    IF HasCostIndicators(category_text) THEN
        cost_level ← InferLevelFromCosts(category_text)
        IF cost_level > max_level THEN
            max_level ← cost_level  // Upgrade if costs suggest higher damage
        END IF
    END IF
    
    RETURN max_level
END

SUBROUTINE: CalculateOverallSeverity
INPUT: structural_level, facade_level, services_level
OUTPUT: severity_score (float 0-1)

CONSTANTS:
    LEVEL_WEIGHTS = {
        structural: 0.5,   // Highest weight for structural
        facade: 0.3,       // Medium weight for facade
        services: 0.2      // Lower weight for services
    }
    
    LEVEL_VALUES = {
        "none": 0.0,
        "minor": 0.2,
        "moderate": 0.4,
        "major": 0.7,
        "severe": 1.0
    }

BEGIN
    structural_value ← LEVEL_VALUES[structural_level] * LEVEL_WEIGHTS.structural
    facade_value ← LEVEL_VALUES[facade_level] * LEVEL_WEIGHTS.facade
    services_value ← LEVEL_VALUES[services_level] * LEVEL_WEIGHTS.services
    
    severity_score ← structural_value + facade_value + services_value
    
    RETURN Min(severity_score, 1.0)
END

SUBROUTINE: EstimateBaseCost
INPUT: structural_level, facade_level, services_level, property_data
OUTPUT: estimated_cost (float)

BEGIN
    property_value ← property_data.valuation
    
    // Calculate component costs
    structural_cost ← property_value * BASE_REPAIR_COSTS[structural_level] * 0.6
    facade_cost ← property_value * BASE_REPAIR_COSTS[facade_level] * 0.25
    services_cost ← property_value * BASE_REPAIR_COSTS[services_level] * 0.15
    
    base_cost ← structural_cost + facade_cost + services_cost
    
    // Apply building-specific multipliers
    IF property_data.building_type = "heritage" THEN
        base_cost *= 1.3  // Heritage premium
    END IF
    
    IF property_data.year_built < 1980 THEN
        base_cost *= 1.15  // Older building premium
    END IF
    
    IF property_data.floors > 10 THEN
        base_cost *= 1.1  // High-rise complexity
    END IF
    
    RETURN base_cost
END
```

**Time Complexity**: O(n + k) where n = text length, k = number of categories
**Space Complexity**: O(k + m) where k = categories, m = extracted features
**Optimization**: Parallel processing of categories, cached keyword matching

---

## 4. NHC vs Private Portion Calculation Algorithm

### Algorithm: CalculateNHCPrivateSplit
```
ALGORITHM: CalculateNHCPrivateSplit
INPUT: damage_assessment (DamageAssessment), policy_data (InsurancePolicy), property_data (PropertyInfo)
OUTPUT: cost_breakdown (CostBreakdown)

DATA STRUCTURES:
    CostBreakdown:
        - total_repair_cost: float
        - nhc_eligible_amount: float
        - nhc_portion: float (capped at $345,000)
        - private_portion: float
        - excess_applicable: float
        - business_interruption: float
        - breakdown_details: Map<string, float>

CONSTANTS:
    NHC_CAP = 345000.0  // $300,000 + GST
    NHC_COVERAGE_CATEGORIES = [
        "structural_damage",
        "building_services", 
        "temporary_accommodation",
        "demolition_debris_removal"
    ]
    
    PRIVATE_ONLY_CATEGORIES = [
        "betterment",
        "code_upgrades", 
        "cosmetic_improvements",
        "business_enhancement"
    ]

BEGIN
    total_cost ← damage_assessment.repair_cost_estimate
    
    // Phase 1: Categorize Costs
    cost_categories ← CategorizeCosts(damage_assessment, property_data)
    
    // Phase 2: Calculate NHC Eligible Amount
    nhc_eligible ← 0.0
    FOR EACH category, amount IN cost_categories DO
        IF category IN NHC_COVERAGE_CATEGORIES THEN
            nhc_eligible += amount
        END IF
    END FOR
    
    // Phase 3: Apply NHC Cap
    nhc_portion ← Min(nhc_eligible, NHC_CAP)
    
    // Phase 4: Calculate Private Portion
    private_portion ← total_cost - nhc_portion
    
    // Phase 5: Apply Policy Excess
    excess_applicable ← Min(policy_data.excess, nhc_portion)
    adjusted_nhc ← nhc_portion - excess_applicable
    adjusted_private ← private_portion + excess_applicable
    
    // Phase 6: Business Interruption Calculation
    bi_amount ← CalculateBusinessInterruption(
        damage_assessment.repair_timeline_estimate,
        property_data,
        policy_data
    )
    
    // Phase 7: Create Detailed Breakdown
    breakdown_details ← {
        "structural_repairs": cost_categories.get("structural_damage", 0),
        "facade_repairs": cost_categories.get("facade_damage", 0),
        "services_repairs": cost_categories.get("building_services", 0),
        "temporary_works": cost_categories.get("temporary_accommodation", 0),
        "demolition": cost_categories.get("demolition_debris_removal", 0),
        "code_upgrades": cost_categories.get("code_upgrades", 0),
        "betterment": cost_categories.get("betterment", 0),
        "professional_fees": cost_categories.get("professional_fees", 0),
        "contingency": total_cost * 0.1
    }
    
    RETURN CostBreakdown(
        total_repair_cost: total_cost,
        nhc_eligible_amount: nhc_eligible,
        nhc_portion: adjusted_nhc,
        private_portion: adjusted_private,
        excess_applicable: excess_applicable,
        business_interruption: bi_amount,
        breakdown_details: breakdown_details
    )
END

SUBROUTINE: CategorizeCosts
INPUT: damage_assessment, property_data
OUTPUT: cost_categories (Map<string, float>)

BEGIN
    categories ← EmptyMap()
    total_cost ← damage_assessment.repair_cost_estimate
    
    // Allocate costs based on damage levels and building characteristics
    structural_ratio ← GetDamageRatio(damage_assessment.structural_level)
    facade_ratio ← GetDamageRatio(damage_assessment.facade_level)
    services_ratio ← GetDamageRatio(damage_assessment.services_level)
    
    // Base allocations
    categories["structural_damage"] ← total_cost * structural_ratio * 0.5
    categories["facade_damage"] ← total_cost * facade_ratio * 0.2
    categories["building_services"] ← total_cost * services_ratio * 0.15
    
    // Fixed percentages for other categories
    categories["professional_fees"] ← total_cost * 0.08
    categories["temporary_accommodation"] ← total_cost * 0.05
    categories["demolition_debris_removal"] ← total_cost * 0.02
    
    // Code upgrade requirements
    IF property_data.year_built < 1980 OR property_data.nbs_rating < 67 THEN
        categories["code_upgrades"] ← total_cost * 0.15
    ELSE
        categories["code_upgrades"] ← 0.0
    END IF
    
    // Betterment (improvement beyond original condition)
    IF damage_assessment.overall_severity_score > 0.6 THEN
        categories["betterment"] ← total_cost * 0.1
    ELSE
        categories["betterment"] ← 0.0
    END IF
    
    // Normalize to ensure total matches
    current_total ← Sum(categories.values())
    scaling_factor ← total_cost / current_total
    
    FOR EACH category, amount IN categories DO
        categories[category] ← amount * scaling_factor
    END FOR
    
    RETURN categories
END

SUBROUTINE: CalculateBusinessInterruption
INPUT: repair_timeline_days, property_data, policy_data
OUTPUT: bi_amount (float)

BEGIN
    IF policy_data.business_interruption_cover = 0 THEN
        RETURN 0.0
    END IF
    
    // Estimate monthly rental/business income
    annual_rental ← property_data.valuation * 0.08  // 8% yield assumption
    monthly_income ← annual_rental / 12
    
    // Calculate business interruption period
    // Assume 50% income loss during repair period
    bi_months ← Ceiling(repair_timeline_days / 30.0)
    income_loss ← monthly_income * 0.5 * bi_months
    
    // Add additional costs (temporary premises, increased costs)
    additional_costs ← monthly_income * 0.2 * bi_months
    
    total_bi ← income_loss + additional_costs
    
    // Apply policy limit
    max_bi ← policy_data.business_interruption_cover
    
    RETURN Min(total_bi, max_bi)
END
```

**Time Complexity**: O(k) where k = number of cost categories
**Space Complexity**: O(k) for cost breakdown storage
**Optimization**: Cached calculation templates, parallel category processing

---

## 5. Settlement Strategy Generation Algorithm

### Algorithm: GenerateSettlementStrategy
```
ALGORITHM: GenerateSettlementStrategy
INPUT: claim_data (ClaimData), precedent_insights (StrategyInsights), cost_breakdown (CostBreakdown)
OUTPUT: settlement_strategy (SettlementStrategy)

DATA STRUCTURES:
    SettlementStrategy:
        - target_amount: float
        - negotiation_points: List<NegotiationPoint>
        - timeline_strategy: TimelineStrategy
        - risk_assessment: RiskAssessment
        - decision_tree: DecisionNode
        - fallback_positions: List<FallbackPosition>
    
    NegotiationPoint:
        - topic: string
        - position: string
        - supporting_evidence: List<string>
        - precedent_cases: List<string>
        - strength_score: float (0-1)
    
    DecisionNode:
        - condition: string
        - action_if_true: string
        - action_if_false: string
        - children: List<DecisionNode>

CONSTANTS:
    NEGOTIATION_TOPICS = [
        "structural_assessment_accuracy",
        "repair_methodology", 
        "code_upgrade_necessity",
        "temporary_accommodation",
        "business_interruption",
        "professional_fees",
        "betterment_arguments"
    ]
    
    INSURER_STRATEGIES = {
        "aggressive": {settlement_target: 0.75, timeline_preference: "fast"},
        "balanced": {settlement_target: 0.85, timeline_preference: "standard"},
        "conservative": {settlement_target: 0.95, timeline_preference: "thorough"}
    }

BEGIN
    // Phase 1: Determine Strategy Approach
    approach ← DetermineApproach(claim_data, precedent_insights)
    
    // Phase 2: Calculate Target Settlement Amount
    target_amount ← CalculateTargetAmount(cost_breakdown, precedent_insights, approach)
    
    // Phase 3: Build Negotiation Points
    negotiation_points ← BuildNegotiationPoints(claim_data, cost_breakdown, precedent_insights)
    
    // Phase 4: Create Timeline Strategy
    timeline_strategy ← CreateTimelineStrategy(claim_data, precedent_insights, approach)
    
    // Phase 5: Assess Risks
    risk_assessment ← AssessNegotiationRisks(claim_data, precedent_insights)
    
    // Phase 6: Build Decision Tree
    decision_tree ← BuildDecisionTree(negotiation_points, risk_assessment)
    
    // Phase 7: Define Fallback Positions
    fallback_positions ← CreateFallbackPositions(target_amount, risk_assessment)
    
    RETURN SettlementStrategy(
        target_amount: target_amount,
        negotiation_points: negotiation_points,
        timeline_strategy: timeline_strategy,
        risk_assessment: risk_assessment,
        decision_tree: decision_tree,
        fallback_positions: fallback_positions
    )
END

SUBROUTINE: CalculateTargetAmount
INPUT: cost_breakdown, precedent_insights, approach
OUTPUT: target_amount (float)

BEGIN
    base_claim ← cost_breakdown.total_repair_cost
    
    // Adjust based on precedent success rates
    precedent_adjustment ← precedent_insights.average_settlement_ratio
    
    // Adjust based on approach
    approach_multiplier ← INSURER_STRATEGIES[approach].settlement_target
    
    // Calculate initial target
    initial_target ← base_claim * precedent_adjustment * approach_multiplier
    
    // Apply confidence adjustments
    confidence_factor ← precedent_insights.confidence
    adjusted_target ← initial_target * (0.9 + 0.1 * confidence_factor)
    
    // Ensure minimum viable settlement
    minimum_acceptable ← cost_breakdown.nhc_portion + cost_breakdown.private_portion * 0.8
    
    RETURN Max(adjusted_target, minimum_acceptable)
END

SUBROUTINE: BuildNegotiationPoints
INPUT: claim_data, cost_breakdown, precedent_insights
OUTPUT: negotiation_points (List<NegotiationPoint>)

BEGIN
    points ← []
    
    FOR EACH topic IN NEGOTIATION_TOPICS DO
        point ← CreateNegotiationPoint(topic, claim_data, cost_breakdown, precedent_insights)
        IF point.strength_score > 0.3 THEN  // Only include strong points
            points.append(point)
        END IF
    END FOR
    
    // Sort by strength score (strongest first)
    points.sortByDescending("strength_score")
    
    RETURN points
END

SUBROUTINE: CreateNegotiationPoint
INPUT: topic, claim_data, cost_breakdown, precedent_insights
OUTPUT: negotiation_point (NegotiationPoint)

BEGIN
    SWITCH topic:
        CASE "structural_assessment_accuracy":
            position ← "Engineering assessment confirms structural damage requires complete remediation"
            evidence ← [
                "Independent structural engineer report",
                "Code compliance requirements",
                "Safety considerations"
            ]
            strength ← CalculateStrengthFromDamageLevel(claim_data.structural_damage)
            
        CASE "repair_methodology":
            position ← "Modern repair methods and materials required for resilience"
            evidence ← [
                "Building code updates since original construction",
                "Insurance industry best practices",
                "Long-term performance requirements"
            ]
            strength ← CalculateStrengthFromAge(claim_data.property_age)
            
        CASE "code_upgrade_necessity":
            position ← "Code upgrades are consequential damage, not betterment"
            evidence ← [
                "Council consent requirements",
                "Structural safety mandates",
                "Legal compliance obligations"
            ]
            strength ← CalculateStrengthFromNBS(claim_data.nbs_rating)
            
        CASE "business_interruption":
            position ← "Extended repair timeline creates significant income loss"
            evidence ← [
                "Market rental analysis",
                "Tenant displacement costs", 
                "Alternative accommodation expenses"
            ]
            strength ← CalculateStrengthFromTimeline(precedent_insights.average_timeline_days)
    END SWITCH
    
    // Find supporting precedents
    supporting_precedents ← FindSupportingPrecedents(topic, precedent_insights)
    
    RETURN NegotiationPoint(
        topic: topic,
        position: position,
        supporting_evidence: evidence,
        precedent_cases: supporting_precedents,
        strength_score: strength
    )
END

SUBROUTINE: BuildDecisionTree
INPUT: negotiation_points, risk_assessment
OUTPUT: decision_tree (DecisionNode)

BEGIN
    root ← DecisionNode(
        condition: "Initial offer >= 80% of target",
        action_if_true: "Accept and close",
        action_if_false: "Proceed with negotiation"
    )
    
    // Build negotiation flow
    current_node ← root
    
    FOR EACH point IN negotiation_points.topN(3) DO  // Focus on top 3 points
        negotiate_node ← DecisionNode(
            condition: "Insurer accepts " + point.topic,
            action_if_true: "Move to next point",
            action_if_false: "Present supporting evidence"
        )
        
        evidence_node ← DecisionNode(
            condition: "Evidence compelling",
            action_if_true: "Insurer concedes point",
            action_if_false: "Escalate or compromise"
        )
        
        negotiate_node.children.append(evidence_node)
        current_node.children.append(negotiate_node)
        current_node ← evidence_node
    END FOR
    
    // Add final decision nodes
    final_offer_node ← DecisionNode(
        condition: "Final offer >= minimum acceptable",
        action_if_true: "Accept settlement",
        action_if_false: "Consider dispute resolution"
    )
    
    current_node.children.append(final_offer_node)
    
    RETURN root
END

SUBROUTINE: AssessNegotiationRisks
INPUT: claim_data, precedent_insights
OUTPUT: risk_assessment (RiskAssessment)

BEGIN
    risks ← []
    
    // Timeline risk
    IF precedent_insights.average_timeline_days > 365 THEN
        risks.append({
            type: "extended_timeline",
            probability: 0.7,
            impact: "high",
            mitigation: "Set clear milestones and escalation triggers"
        })
    END IF
    
    // Settlement ratio risk
    IF precedent_insights.average_settlement_ratio < 0.8 THEN
        risks.append({
            type: "low_settlement_ratio", 
            probability: 0.6,
            impact: "medium",
            mitigation: "Strengthen evidence package"
        })
    END IF
    
    // Complexity risk
    IF claim_data.total_cost > 10000000 THEN
        risks.append({
            type: "high_value_complexity",
            probability: 0.8,
            impact: "high", 
            mitigation: "Engage specialist legal counsel early"
        })
    END IF
    
    // Insurer-specific risk
    insurer_pattern ← precedent_insights.insurer_patterns.get(claim_data.insurer)
    IF insurer_pattern AND insurer_pattern.avg_ratio < 0.75 THEN
        risks.append({
            type: "difficult_insurer",
            probability: 0.9,
            impact: "medium",
            mitigation: "Prepare for formal dispute process"
        })
    END IF
    
    RETURN RiskAssessment(
        identified_risks: risks,
        overall_risk_level: CalculateOverallRiskLevel(risks),
        recommended_approach: DetermineRiskBasedApproach(risks)
    )
END
```

**Time Complexity**: O(n*m) where n = negotiation points, m = precedent cases
**Space Complexity**: O(n + d) where n = negotiation points, d = decision tree depth
**Optimization**: Template-based strategies, cached precedent analysis

---

## 6. Claim Package Assembly Algorithm

### Algorithm: AssembleClaimPackage
```
ALGORITHM: AssembleClaimPackage
INPUT: claim_data (CompleteClaimData)
OUTPUT: claim_package (ClaimPackage)

DATA STRUCTURES:
    ClaimPackage:
        - cover_letter: DocumentSection
        - executive_summary: DocumentSection  
        - property_details: DocumentSection
        - event_details: DocumentSection
        - damage_assessment: DocumentSection
        - cost_breakdown: DocumentSection
        - supporting_evidence: DocumentSection
        - precedent_analysis: DocumentSection
        - appendices: List<DocumentSection>
        - package_metadata: PackageMetadata

    DocumentSection:
        - title: string
        - content: string
        - attachments: List<Attachment>
        - page_count: integer
        - section_id: string

CONSTANTS:
    TEMPLATE_SECTIONS = [
        "cover_letter",
        "executive_summary", 
        "property_details",
        "event_details",
        "damage_assessment", 
        "cost_breakdown",
        "supporting_evidence",
        "precedent_analysis"
    ]
    
    REQUIRED_ATTACHMENTS = [
        "engineering_report",
        "damage_photos", 
        "insurance_policy",
        "property_valuation"
    ]

BEGIN
    package ← InitializeClaimPackage()
    
    // Phase 1: Generate Cover Letter
    package.cover_letter ← GenerateCoverLetter(claim_data)
    
    // Phase 2: Create Executive Summary
    package.executive_summary ← GenerateExecutiveSummary(claim_data)
    
    // Phase 3: Compile Property Details
    package.property_details ← CompilePropertyDetails(claim_data.property_info)
    
    // Phase 4: Document Event Details
    package.event_details ← DocumentEventDetails(claim_data.earthquake_event)
    
    // Phase 5: Present Damage Assessment
    package.damage_assessment ← PresentDamageAssessment(claim_data.damage_data)
    
    // Phase 6: Detail Cost Breakdown
    package.cost_breakdown ← DetailCostBreakdown(claim_data.cost_analysis)
    
    // Phase 7: Organize Supporting Evidence
    package.supporting_evidence ← OrganizeSupportingEvidence(claim_data.documents)
    
    // Phase 8: Include Precedent Analysis
    package.precedent_analysis ← IncludePrecedentAnalysis(claim_data.precedents)
    
    // Phase 9: Attach Supporting Documents
    package.appendices ← AttachSupportingDocuments(claim_data.attachments)
    
    // Phase 10: Generate Package Metadata
    package.package_metadata ← GeneratePackageMetadata(package)
    
    // Phase 11: Validate Completeness
    validation_result ← ValidatePackageCompleteness(package)
    IF NOT validation_result.is_complete THEN
        LogWarning("Incomplete package", validation_result.missing_items)
    END IF
    
    // Phase 12: Generate Final Document
    final_pdf ← CompileToPDF(package)
    package.final_document_url ← SaveDocument(final_pdf)
    
    RETURN package
END

SUBROUTINE: GenerateExecutiveSummary
INPUT: claim_data
OUTPUT: executive_summary (DocumentSection)

BEGIN
    summary_content ← """
    EXECUTIVE SUMMARY
    
    Claim Reference: {claim_id}
    Property: {property_address}
    Event Date: {event_date}
    Total Claim Amount: ${total_amount:,.2f}
    
    DAMAGE OVERVIEW
    This claim arises from earthquake damage sustained on {event_date}. 
    Our structural engineering assessment has identified:
    
    • Structural Damage: {structural_level}
    • Facade Damage: {facade_level}  
    • Services Damage: {services_level}
    
    COST SUMMARY
    Total Repair Cost: ${total_cost:,.2f}
    NHC Portion: ${nhc_portion:,.2f}
    Private Portion: ${private_portion:,.2f}
    
    PRECEDENT ANALYSIS
    Based on {precedent_count} similar cases, the average settlement 
    ratio is {avg_settlement:.1%} with a typical timeline of 
    {avg_timeline} days.
    
    RECOMMENDATION
    We recommend settlement of ${recommended_amount:,.2f} based on:
    {key_arguments}
    """
    
    formatted_content ← FormatTemplate(summary_content, {
        claim_id: claim_data.claim_id,
        property_address: claim_data.property_info.address,
        event_date: claim_data.earthquake_event.date,
        total_amount: claim_data.cost_analysis.total_repair_cost,
        structural_level: claim_data.damage_data.structural_level,
        facade_level: claim_data.damage_data.facade_level,
        services_level: claim_data.damage_data.services_level,
        total_cost: claim_data.cost_analysis.total_repair_cost,
        nhc_portion: claim_data.cost_analysis.nhc_portion,
        private_portion: claim_data.cost_analysis.private_portion,
        precedent_count: claim_data.precedents.length,
        avg_settlement: claim_data.strategy_insights.average_settlement_ratio,
        avg_timeline: claim_data.strategy_insights.average_timeline_days,
        recommended_amount: claim_data.settlement_strategy.target_amount,
        key_arguments: JoinList(claim_data.settlement_strategy.negotiation_points.topN(3).map("position"))
    })
    
    RETURN DocumentSection(
        title: "Executive Summary",
        content: formatted_content,
        attachments: [],
        page_count: 2,
        section_id: "exec_summary"
    )
END

SUBROUTINE: DetailCostBreakdown
INPUT: cost_analysis
OUTPUT: cost_section (DocumentSection)

BEGIN
    // Create detailed cost table
    cost_table ← CreateCostTable(cost_analysis.breakdown_details)
    
    // Add NHC vs Private analysis
    nhc_analysis ← GenerateNHCAnalysis(cost_analysis)
    
    // Include methodology explanation
    methodology ← ExplainCostMethodology(cost_analysis)
    
    content ← CombineContent([
        "DETAILED COST BREAKDOWN\n",
        cost_table,
        "\nNHC VS PRIVATE INSURANCE ANALYSIS\n",
        nhc_analysis,
        "\nCOST ESTIMATION METHODOLOGY\n", 
        methodology
    ])
    
    RETURN DocumentSection(
        title: "Cost Breakdown and Analysis",
        content: content,
        attachments: [],
        page_count: 4,
        section_id: "cost_breakdown"
    )
END

SUBROUTINE: CreateCostTable
INPUT: breakdown_details
OUTPUT: cost_table (string)

BEGIN
    table_header ← "| Category | Amount ($) | Percentage | NHC Eligible |\n"
    table_separator ← "|----------|------------|------------|---------------|\n"
    
    table_rows ← []
    total_amount ← Sum(breakdown_details.values())
    
    FOR EACH category, amount IN breakdown_details DO
        percentage ← (amount / total_amount) * 100
        nhc_eligible ← IsCategoryNHCEligible(category) ? "Yes" : "No"
        
        row ← FormatTableRow(category, amount, percentage, nhc_eligible)
        table_rows.append(row)
    END FOR
    
    total_row ← FormatTotalRow(total_amount)
    
    RETURN table_header + table_separator + JoinList(table_rows) + total_row
END

SUBROUTINE: ValidatePackageCompleteness
INPUT: package
OUTPUT: validation_result (ValidationResult)

BEGIN
    missing_items ← []
    warnings ← []
    
    // Check required sections
    FOR EACH section IN TEMPLATE_SECTIONS DO
        IF NOT package.hasSection(section) THEN
            missing_items.append("Missing section: " + section)
        END IF
    END FOR
    
    // Check required attachments  
    FOR EACH attachment IN REQUIRED_ATTACHMENTS DO
        IF NOT package.hasAttachment(attachment) THEN
            missing_items.append("Missing attachment: " + attachment)
        END IF
    END FOR
    
    // Check content quality
    IF package.executive_summary.content.length < 500 THEN
        warnings.append("Executive summary may be too brief")
    END IF
    
    IF package.precedent_analysis.attachments.length < 3 THEN
        warnings.append("Limited precedent case support")
    END IF
    
    RETURN ValidationResult(
        is_complete: missing_items.length = 0,
        missing_items: missing_items,
        warnings: warnings,
        completeness_score: CalculateCompletenessScore(package)
    )
END
```

**Time Complexity**: O(n + m + k) where n = sections, m = attachments, k = content length
**Space Complexity**: O(s) where s = total package size
**Optimization**: Template caching, parallel section generation, incremental compilation

---

## 7. Data Validation and Error Handling Algorithms

### Algorithm: ValidateClaimData
```
ALGORITHM: ValidateClaimData
INPUT: claim_data (RawClaimData)
OUTPUT: validation_result (ValidationResult)

DATA STRUCTURES:
    ValidationResult:
        - is_valid: boolean
        - errors: List<ValidationError>
        - warnings: List<ValidationWarning>
        - data_quality_score: float (0-1)
        - correctable_issues: List<CorrectableIssue>
    
    ValidationError:
        - field: string
        - error_type: string
        - message: string
        - severity: string (critical, major, minor)
    
    ValidationRule:
        - field: string
        - rule_type: string
        - condition: function
        - error_message: string

CONSTANTS:
    VALIDATION_RULES = [
        {field: "property.address", rule_type: "required", message: "Property address is required"},
        {field: "property.valuation", rule_type: "range", min: 100000, max: 100000000, message: "Property valuation must be between $100k and $100m"},
        {field: "property.nbs_rating", rule_type: "range", min: 0, max: 100, message: "NBS rating must be between 0 and 100"},
        {field: "earthquake.magnitude", rule_type: "range", min: 4.0, max: 9.0, message: "Earthquake magnitude must be between 4.0 and 9.0"},
        {field: "damage.estimated_cost", rule_type: "positive", message: "Estimated cost must be positive"},
        {field: "policy.sum_insured", rule_type: "minimum", min: 1000000, message: "Sum insured should be at least $1m for commercial property"}
    ]

BEGIN
    validation_result ← InitializeValidationResult()
    
    // Phase 1: Schema Validation
    schema_errors ← ValidateSchema(claim_data)
    validation_result.errors.extend(schema_errors)
    
    // Phase 2: Business Rule Validation
    FOR EACH rule IN VALIDATION_RULES DO
        rule_result ← ApplyValidationRule(claim_data, rule)
        IF NOT rule_result.passed THEN
            validation_result.errors.append(rule_result.error)
        END IF
    END FOR
    
    // Phase 3: Cross-field Validation
    cross_field_errors ← ValidateCrossFieldRules(claim_data)
    validation_result.errors.extend(cross_field_errors)
    
    // Phase 4: Data Quality Assessment
    quality_warnings ← AssessDataQuality(claim_data)
    validation_result.warnings.extend(quality_warnings)
    
    // Phase 5: Consistency Checks
    consistency_issues ← CheckDataConsistency(claim_data)
    validation_result.warnings.extend(consistency_issues)
    
    // Phase 6: Calculate Overall Scores
    validation_result.data_quality_score ← CalculateQualityScore(validation_result)
    validation_result.is_valid ← (validation_result.errors.filter("severity", "critical").length = 0)
    
    // Phase 7: Identify Auto-correctable Issues
    validation_result.correctable_issues ← IdentifyCorrectableIssues(validation_result.errors)
    
    RETURN validation_result
END

SUBROUTINE: ValidateCrossFieldRules
INPUT: claim_data
OUTPUT: cross_field_errors (List<ValidationError>)

BEGIN
    errors ← []
    
    // Rule: Sum insured should cover estimated repair cost
    IF claim_data.policy.sum_insured < claim_data.damage.estimated_cost THEN
        errors.append(ValidationError(
            field: "policy.sum_insured",
            error_type: "insufficient_coverage",
            message: "Sum insured ($" + claim_data.policy.sum_insured + ") is less than estimated repair cost ($" + claim_data.damage.estimated_cost + ")",
            severity: "major"
        ))
    END IF
    
    // Rule: NHC cover consistency
    IF claim_data.policy.nhc_cover > 345000 THEN
        errors.append(ValidationError(
            field: "policy.nhc_cover", 
            error_type: "invalid_nhc_amount",
            message: "NHC cover cannot exceed $345,000 (current: $" + claim_data.policy.nhc_cover + ")",
            severity: "critical"
        ))
    END IF
    
    // Rule: Property age vs construction standards
    IF claim_data.property.year_built < 1980 AND claim_data.property.nbs_rating > 80 THEN
        errors.append(ValidationError(
            field: "property.nbs_rating",
            error_type: "inconsistent_data",
            message: "High NBS rating unlikely for pre-1980 building without significant strengthening",
            severity: "minor"
        ))
    END IF
    
    // Rule: Damage level vs estimated cost consistency
    damage_cost_ratio ← claim_data.damage.estimated_cost / claim_data.property.valuation
    
    IF claim_data.damage.structural_level = "severe" AND damage_cost_ratio < 0.3 THEN
        errors.append(ValidationError(
            field: "damage.estimated_cost",
            error_type: "inconsistent_damage_cost",
            message: "Severe structural damage cost seems low relative to property value",
            severity: "minor"
        ))
    END IF
    
    IF claim_data.damage.structural_level = "minor" AND damage_cost_ratio > 0.4 THEN
        errors.append(ValidationError(
            field: "damage.estimated_cost", 
            error_type: "inconsistent_damage_cost",
            message: "Minor damage cost seems high relative to property value",
            severity: "minor"
        ))
    END IF
    
    RETURN errors
END

SUBROUTINE: AssessDataQuality
INPUT: claim_data
OUTPUT: quality_warnings (List<ValidationWarning>)

BEGIN
    warnings ← []
    
    // Check for missing optional but important data
    IF NOT claim_data.property.has("construction_type") THEN
        warnings.append(ValidationWarning(
            field: "property.construction_type",
            message: "Construction type not specified - may affect damage assessment accuracy"
        ))
    END IF
    
    IF NOT claim_data.earthquake.has("distance_from_epicenter") THEN
        warnings.append(ValidationWarning(
            field: "earthquake.distance_from_epicenter", 
            message: "Distance from epicenter not provided - may affect expected damage correlation"
        ))
    END IF
    
    // Check data freshness
    IF claim_data.property.valuation_date < TwoYearsAgo() THEN
        warnings.append(ValidationWarning(
            field: "property.valuation_date",
            message: "Property valuation is over 2 years old - consider updating"
        ))
    END IF
    
    // Check document completeness
    IF claim_data.documents.engineering_reports.length = 0 THEN
        warnings.append(ValidationWarning(
            field: "documents.engineering_reports",
            message: "No engineering reports attached - may weaken claim strength"
        ))
    END IF
    
    IF claim_data.documents.damage_photos.length < 5 THEN
        warnings.append(ValidationWarning(
            field: "documents.damage_photos",
            message: "Limited damage photographic evidence - recommend additional documentation"
        ))
    END IF
    
    RETURN warnings
END

SUBROUTINE: HandleValidationErrors
INPUT: validation_result (ValidationResult), claim_data (RawClaimData)
OUTPUT: error_handling_result (ErrorHandlingResult)

CONSTANTS:
    AUTO_CORRECT_RULES = {
        "format_currency": lambda value: FormatCurrency(value),
        "normalize_address": lambda address: NormalizeAddress(address),
        "validate_dates": lambda date: ParseAndValidateDate(date),
        "cap_nhs_amount": lambda amount: Min(amount, 345000)
    }

BEGIN
    handling_result ← InitializeErrorHandlingResult()
    
    // Phase 1: Attempt Auto-correction
    corrected_data ← DeepCopy(claim_data)
    correction_log ← []
    
    FOR EACH issue IN validation_result.correctable_issues DO
        IF CanAutoCorrect(issue) THEN
            correction_applied ← ApplyAutoCorrection(corrected_data, issue)
            IF correction_applied.success THEN
                correction_log.append(correction_applied)
                handling_result.auto_corrections.append(issue)
            END IF
        END IF
    END FOR
    
    // Phase 2: Re-validate after corrections
    IF correction_log.length > 0 THEN
        revalidation_result ← ValidateClaimData(corrected_data)
        handling_result.improved_validation ← revalidation_result
    END IF
    
    // Phase 3: Generate Error Report
    FOR EACH error IN validation_result.errors DO
        IF error.severity = "critical" THEN
            handling_result.blocking_errors.append(error)
        ELSE IF error.severity = "major" THEN
            handling_result.review_required.append(error)
        ELSE
            handling_result.minor_issues.append(error)
        END IF
    END FOR
    
    // Phase 4: Create Action Plan
    action_plan ← CreateErrorResolutionPlan(validation_result.errors)
    handling_result.resolution_plan ← action_plan
    
    // Phase 5: Data Quality Recommendations
    recommendations ← GenerateDataQualityRecommendations(validation_result)
    handling_result.recommendations ← recommendations
    
    RETURN handling_result
END

SUBROUTINE: CreateErrorResolutionPlan
INPUT: errors (List<ValidationError>)
OUTPUT: action_plan (List<ActionItem>)

BEGIN
    plan ← []
    
    // Group errors by type and priority
    error_groups ← GroupBy(errors, "error_type")
    
    FOR EACH error_type, error_list IN error_groups DO
        SWITCH error_type:
            CASE "missing_required_field":
                plan.append(ActionItem(
                    priority: "high",
                    action: "Collect missing required data",
                    fields: error_list.map("field"),
                    estimated_effort: "1-2 hours"
                ))
            
            CASE "invalid_range":
                plan.append(ActionItem(
                    priority: "medium", 
                    action: "Verify and correct out-of-range values",
                    fields: error_list.map("field"),
                    estimated_effort: "30 minutes"
                ))
            
            CASE "inconsistent_data":
                plan.append(ActionItem(
                    priority: "medium",
                    action: "Review data consistency and resolve conflicts",
                    fields: error_list.map("field"),
                    estimated_effort: "1 hour"
                ))
            
            CASE "insufficient_coverage":
                plan.append(ActionItem(
                    priority: "high",
                    action: "Review insurance policy limits and coverage gaps",
                    fields: ["policy"],
                    estimated_effort: "2-3 hours"
                ))
        END SWITCH
    END FOR
    
    // Sort by priority
    plan.sortBy(["priority", "estimated_effort"])
    
    RETURN plan
END

ALGORITHM: MonitorDataQuality
INPUT: processed_claims (List<ProcessedClaim>)
OUTPUT: quality_metrics (QualityMetrics)

BEGIN
    metrics ← InitializeQualityMetrics()
    
    // Track validation success rates
    total_claims ← processed_claims.length
    valid_claims ← processed_claims.filter(lambda claim: claim.validation_result.is_valid).length
    
    metrics.validation_success_rate ← valid_claims / total_claims
    
    // Track common error patterns
    all_errors ← FlattenList([claim.validation_result.errors FOR claim IN processed_claims])
    error_frequency ← CountFrequency(all_errors.map("error_type"))
    metrics.common_error_types ← error_frequency.topN(10)
    
    // Track data quality trends over time
    quality_scores ← [claim.validation_result.data_quality_score FOR claim IN processed_claims]
    metrics.average_quality_score ← Mean(quality_scores)
    metrics.quality_trend ← CalculateTrend(quality_scores, processed_claims.map("created_at"))
    
    // Track auto-correction effectiveness
    auto_corrections ← [claim.error_handling_result.auto_corrections FOR claim IN processed_claims]
    metrics.auto_correction_rate ← Mean([corrections.length FOR corrections IN auto_corrections])
    
    // Generate quality improvement recommendations
    metrics.improvement_recommendations ← GenerateQualityImprovements(metrics)
    
    RETURN metrics
END
```

**Time Complexity**: O(n*r) where n = data fields, r = validation rules
**Space Complexity**: O(n + e) where n = data size, e = number of errors
**Optimization**: Parallel validation, rule caching, incremental validation

---

## Performance and Optimization Considerations

### Algorithm Performance Summary

| Algorithm | Time Complexity | Space Complexity | Bottlenecks | Optimization Strategy |
|-----------|----------------|------------------|-------------|----------------------|
| Document Analysis | O(n) | O(m) | LLM API calls | Parallel processing, caching |
| Precedent Matching | O(log n + k log k) | O(k + d) | Vector similarity | Index optimization, batch queries |
| Damage Assessment | O(n + k) | O(k + m) | Text processing | Parallel categorization |
| NHC Calculation | O(k) | O(k) | Cost categorization | Template caching |
| Strategy Generation | O(n*m) | O(n + d) | Decision tree building | Template strategies |
| Package Assembly | O(n + m + k) | O(s) | PDF generation | Parallel section creation |
| Data Validation | O(n*r) | O(n + e) | Rule evaluation | Parallel validation |

### Optimization Strategies

1. **Parallel Processing**: All algorithms designed for concurrent execution
2. **Caching**: LLM responses, embeddings, templates, and validation results
3. **Incremental Processing**: Update only changed components
4. **Batch Operations**: Process multiple claims simultaneously
5. **Memory Management**: Streaming for large documents, garbage collection
6. **Database Optimization**: Proper indexing, query optimization, connection pooling
7. **API Optimization**: Request batching, response compression, retry mechanisms

### Error Recovery Patterns

1. **Graceful Degradation**: Continue processing with reduced functionality
2. **Retry Logic**: Exponential backoff for transient failures
3. **Fallback Mechanisms**: Alternative processing paths when primary fails
4. **Data Quality Scoring**: Confidence metrics for all extractions
5. **Human-in-the-loop**: Escalation paths for complex cases
6. **Audit Trails**: Complete logging for debugging and compliance

This comprehensive pseudocode provides the algorithmic foundation for implementing the Earthquake Claim Accelerator with clear logic flows, optimization strategies, and robust error handling.