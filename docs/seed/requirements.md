# Earthquake Claim Accelerator - Technical Implementation Guide

## Quick Start Development Setup

### Prerequisites
```bash
# Required tools
node >= 18.0.0
python >= 3.10
postgresql >= 14
redis >= 6.0

# API Keys needed (use synthetic for MVP)
OPENAI_API_KEY=sk-synthetic-key-for-testing
DATABASE_URL=postgresql://localhost/earthquake_claims
REDIS_URL=redis://localhost:6379
```

### Project Structure
```
earthquake-claim-accelerator/
├── frontend/                 # Next.js application
│   ├── app/                 # App router pages
│   ├── components/          # React components
│   ├── lib/                # Utilities and API clients
│   └── public/             # Static assets
├── backend/                 # Python FastAPI
│   ├── agents/             # AI agent implementations
│   ├── api/                # API routes
│   ├── models/             # Database models
│   ├── processors/         # Document processors
│   └── synthetic/          # Synthetic data generators
├── infrastructure/          # Docker and deployment
│   ├── docker-compose.yml
│   └── kubernetes/
└── tests/                  # Test suites
```

## 1. Database Setup

### PostgreSQL Schema with Vector Support

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Properties table
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address TEXT NOT NULL,
    city VARCHAR(50) DEFAULT 'Wellington',
    building_type VARCHAR(20) CHECK (building_type IN ('office', 'retail', 'mixed')),
    floors INTEGER CHECK (floors BETWEEN 1 AND 50),
    year_built INTEGER,
    nbs_rating DECIMAL(5,2) CHECK (nbs_rating BETWEEN 0 AND 100),
    valuation DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insurance policies table
CREATE TABLE insurance_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID REFERENCES properties(id),
    insurer VARCHAR(50),
    policy_number VARCHAR(100),
    sum_insured DECIMAL(12,2),
    excess DECIMAL(10,2),
    nhc_cover DECIMAL(10,2) DEFAULT 345000, -- $300k + GST
    business_interruption_cover DECIMAL(12,2),
    renewal_date DATE,
    active BOOLEAN DEFAULT true
);

-- Earthquake events table
CREATE TABLE earthquake_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    occurred_at TIMESTAMP NOT NULL,
    magnitude DECIMAL(3,1),
    depth_km INTEGER,
    epicenter_lat DECIMAL(10,7),
    epicenter_long DECIMAL(10,7),
    location_description TEXT
);

-- Claims table
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID REFERENCES properties(id),
    event_id UUID REFERENCES earthquake_events(id),
    policy_id UUID REFERENCES insurance_policies(id),
    status VARCHAR(20) DEFAULT 'draft',
    claimed_amount DECIMAL(12,2),
    nhc_portion DECIMAL(10,2),
    private_portion DECIMAL(12,2),
    settlement_amount DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    settled_at TIMESTAMP
);

-- Damage assessments table
CREATE TABLE damage_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID REFERENCES claims(id),
    structural_damage VARCHAR(20),
    facade_damage VARCHAR(20),
    services_damage VARCHAR(20),
    estimated_repair_cost DECIMAL(12,2),
    assessment_date DATE,
    engineer_name VARCHAR(100),
    report_url TEXT
);

-- Precedent cases table with vector embeddings
CREATE TABLE precedent_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_reference VARCHAR(50),
    building_type VARCHAR(20),
    floors INTEGER,
    damage_level VARCHAR(20),
    claim_amount DECIMAL(12,2),
    settlement_amount DECIMAL(12,2),
    settlement_ratio DECIMAL(5,4),
    key_arguments TEXT[],
    timeline_days INTEGER,
    insurer VARCHAR(50),
    case_summary TEXT,
    embedding vector(1536) -- OpenAI embedding dimension
);

-- Claim documents table
CREATE TABLE claim_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID REFERENCES claims(id),
    document_type VARCHAR(30),
    version INTEGER DEFAULT 1,
    file_name VARCHAR(255),
    file_url TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create indexes
CREATE INDEX idx_properties_nbs ON properties(nbs_rating);
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_property ON claims(property_id);
CREATE INDEX idx_precedent_embedding ON precedent_cases USING ivfflat (embedding vector_cosine_ops);
```

## 2. Synthetic Data Generator

### Python Script for Realistic Test Data

```python
# backend/synthetic/generator.py

import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
import numpy as np
from typing import List, Dict

fake = Faker('en_NZ')

class SyntheticDataGenerator:
    
    # Wellington CBD streets for realistic addresses
    WELLINGTON_STREETS = [
        'Lambton Quay', 'Willis Street', 'Featherston Street',
        'Cuba Street', 'Courtenay Place', 'Wakefield Street',
        'Victoria Street', 'Customhouse Quay', 'Thorndon Quay'
    ]
    
    INSURERS = ['Vero', 'IAG', 'Tower', 'QBE', 'Zurich']
    
    DAMAGE_LEVELS = ['none', 'minor', 'moderate', 'major', 'severe']
    
    def generate_property(self) -> Dict:
        """Generate a realistic Wellington commercial property"""
        street = random.choice(self.WELLINGTON_STREETS)
        
        return {
            'id': str(uuid.uuid4()),
            'address': f"{random.randint(1, 300)} {street}, Wellington",
            'building_type': random.choices(
                ['office', 'retail', 'mixed'],
                weights=[0.7, 0.2, 0.1]
            )[0],
            'floors': random.randint(4, 12),
            'year_built': random.randint(1960, 2010),
            'nbs_rating': round(random.uniform(15, 85), 2),
            'valuation': round(random.uniform(10_000_000, 50_000_000), -5)
        }
    
    def generate_earthquake_event(self) -> Dict:
        """Generate realistic earthquake event for Wellington region"""
        base_date = datetime(2010, 1, 1)
        days_offset = random.randint(0, 5000)
        
        return {
            'id': str(uuid.uuid4()),
            'occurred_at': base_date + timedelta(days=days_offset),
            'magnitude': round(random.uniform(5.5, 7.2), 1),
            'depth_km': random.randint(5, 40),
            'epicenter_lat': round(random.uniform(-41.5, -41.1), 7),
            'epicenter_long': round(random.uniform(174.6, 175.0), 7),
            'location_description': random.choice([
                'Cook Strait', 'Lower Hutt', 'Wellington Harbour',
                'Marlborough', 'Wairarapa'
            ])
        }
    
    def generate_claim_with_precedent(self, property_data: Dict, event_data: Dict) -> Dict:
        """Generate a complete claim with realistic patterns"""
        
        # Calculate damage based on magnitude and building age
        damage_factor = self._calculate_damage_factor(
            event_data['magnitude'],
            property_data['year_built'],
            property_data['nbs_rating']
        )
        
        # Determine damage levels
        structural = self._get_damage_level(damage_factor * 0.8)
        facade = self._get_damage_level(damage_factor * 1.2)
        services = self._get_damage_level(damage_factor * 1.0)
        
        # Calculate claim amounts
        repair_cost = property_data['valuation'] * damage_factor * random.uniform(0.15, 0.35)
        nhc_portion = min(repair_cost, 345000)  # $300k + GST
        private_portion = max(0, repair_cost - nhc_portion)
        
        # Settlement patterns based on insurer
        insurer = random.choice(self.INSURERS)
        settlement_ratio = self._get_settlement_ratio(insurer, structural)
        settlement_amount = repair_cost * settlement_ratio
        
        # Timeline based on complexity
        base_timeline = 180
        if repair_cost > 10_000_000:
            base_timeline = 360
        timeline_days = base_timeline + random.randint(-60, 180)
        
        return {
            'id': str(uuid.uuid4()),
            'property_id': property_data['id'],
            'event_id': event_data['id'],
            'structural_damage': structural,
            'facade_damage': facade,
            'services_damage': services,
            'claimed_amount': round(repair_cost, 2),
            'nhc_portion': round(nhc_portion, 2),
            'private_portion': round(private_portion, 2),
            'settlement_amount': round(settlement_amount, 2),
            'settlement_ratio': settlement_ratio,
            'timeline_days': timeline_days,
            'insurer': insurer,
            'key_arguments': self._generate_key_arguments(structural, facade, services)
        }
    
    def _calculate_damage_factor(self, magnitude: float, year_built: int, nbs_rating: float) -> float:
        """Calculate damage factor based on earthquake and building characteristics"""
        base_factor = (magnitude - 5.0) / 2.0
        age_factor = (2024 - year_built) / 100
        nbs_factor = (100 - nbs_rating) / 100
        return min(1.0, base_factor * (1 + age_factor) * (1 + nbs_factor))
    
    def _get_damage_level(self, factor: float) -> str:
        """Convert damage factor to categorical level"""
        if factor < 0.1:
            return 'none'
        elif factor < 0.3:
            return 'minor'
        elif factor < 0.5:
            return 'moderate'
        elif factor < 0.7:
            return 'major'
        else:
            return 'severe'
    
    def _get_settlement_ratio(self, insurer: str, damage_level: str) -> float:
        """Get settlement ratio based on insurer patterns"""
        base_ratios = {
            'Vero': 0.85,
            'IAG': 0.82,
            'Tower': 0.88,
            'QBE': 0.80,
            'Zurich': 0.83
        }
        
        damage_modifiers = {
            'minor': 1.05,
            'moderate': 1.0,
            'major': 0.95,
            'severe': 0.90
        }
        
        base = base_ratios.get(insurer, 0.85)
        modifier = damage_modifiers.get(damage_level, 1.0)
        
        return round(base * modifier * random.uniform(0.9, 1.1), 3)
    
    def _generate_key_arguments(self, structural: str, facade: str, services: str) -> List[str]:
        """Generate realistic key arguments for claims"""
        arguments = []
        
        if structural in ['major', 'severe']:
            arguments.append("Structural damage exceeded initial assessment")
            arguments.append("Foundation issues discovered during detailed investigation")
        
        if facade in ['major', 'severe']:
            arguments.append("Heritage facade requirements increased costs")
            arguments.append("Weather-tightness issues post-repair")
        
        if services in ['major', 'severe']:
            arguments.append("Complete services replacement required")
            arguments.append("Asbestos discovered in service areas")
        
        # Add random business arguments
        if random.random() > 0.5:
            arguments.append("Business interruption losses exceeded projections")
        
        if random.random() > 0.3:
            arguments.append("Tenant relocations and compensation required")
            
        return arguments[:4]  # Limit to 4 key arguments

    def generate_batch(self, count: int = 100) -> Dict:
        """Generate a batch of synthetic claims data"""
        properties = [self.generate_property() for _ in range(count // 5)]
        events = [self.generate_earthquake_event() for _ in range(10)]
        
        claims = []
        for _ in range(count):
            prop = random.choice(properties)
            event = random.choice(events)
            claim = self.generate_claim_with_precedent(prop, event)
            claims.append(claim)
        
        return {
            'properties': properties,
            'events': events,
            'claims': claims
        }

# Generate embeddings for precedent search
def generate_case_embedding(case_text: str) -> List[float]:
    """Generate a mock embedding vector for testing"""
    # In production, use: openai.Embedding.create(input=case_text)
    np.random.seed(hash(case_text) % 2**32)
    return np.random.randn(1536).tolist()
```

## 3. AI Agent Implementation

### Document Analysis Agent

```python
# backend/agents/document_analyzer.py

from typing import Dict, List, Optional
import re
from dataclasses import dataclass
from datetime import datetime
import PyPDF2
from PIL import Image
import pytesseract

@dataclass
class DamageExtraction:
    structural_elements: List[str]
    damage_descriptions: Dict[str, str]
    cost_estimates: Dict[str, float]
    compliance_issues: List[str]
    confidence_score: float

class DocumentAnalyzer:
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.extraction_prompt = """
        Extract the following from this engineering report:
        1. Structural damage assessment
        2. Non-structural damage
        3. Services damage
        4. Repair cost estimates
        5. Compliance/code issues
        
        Format as JSON with clear categories.
        Text: {text}
        """
    
    def analyze_engineering_report(self, pdf_path: str) -> DamageExtraction:
        """Extract structured data from engineering PDF"""
        
        # Extract text from PDF
        text = self._extract_pdf_text(pdf_path)
        
        # Use LLM to structure the extraction
        response = self.llm.complete(
            self.extraction_prompt.format(text=text[:8000])
        )
        
        # Parse response and structure data
        structured = self._parse_llm_response(response)
        
        # Extract cost estimates with regex patterns
        costs = self._extract_costs(text)
        
        # Identify compliance issues
        compliance = self._extract_compliance_issues(text)
        
        return DamageExtraction(
            structural_elements=structured.get('structural', []),
            damage_descriptions=structured.get('descriptions', {}),
            cost_estimates=costs,
            compliance_issues=compliance,
            confidence_score=self._calculate_confidence(structured)
        )
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text content from PDF"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            for page in pdf.pages:
                text += page.extract_text()
        return text
    
    def _extract_costs(self, text: str) -> Dict[str, float]:
        """Extract cost estimates using patterns"""
        costs = {}
        
        # Pattern for NZ dollar amounts
        pattern = r'\$[\d,]+(?:\.\d{2})?'
        
        # Look for cost categories
        categories = [
            'structural', 'facade', 'services', 
            'demolition', 'temporary', 'professional'
        ]
        
        for category in categories:
            # Find costs near category keywords
            regex = rf'{category}.*?(\$[\d,]+(?:\.\d{2})?)'
            match = re.search(regex, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace('$', '').replace(',', '')
                costs[category] = float(amount_str)
        
        return costs
    
    def _extract_compliance_issues(self, text: str) -> List[str]:
        """Extract building code compliance issues"""
        issues = []
        
        # Keywords indicating compliance problems
        compliance_keywords = [
            'non-compliant', 'does not meet', 'below standard',
            'requires upgrade', 'deficient', 'inadequate'
        ]
        
        sentences = text.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in compliance_keywords):
                issues.append(sentence.strip())
        
        return issues[:10]  # Limit to top 10 issues
    
    def _calculate_confidence(self, structured_data: Dict) -> float:
        """Calculate confidence score for extraction"""
        score = 0.5  # Base score
        
        if structured_data.get('structural'):
            score += 0.1
        if structured_data.get('descriptions'):
            score += 0.1
        if len(structured_data.get('descriptions', {})) > 5:
            score += 0.2
        
        return min(score, 1.0)

    def analyze_damage_photos(self, image_paths: List[str]) -> Dict:
        """Analyze damage from photos using vision model"""
        
        damage_classifications = []
        
        for path in image_paths:
            # In production: Use GPT-4V or similar
            # For MVP: Mock classification
            classification = self._mock_classify_image(path)
            damage_classifications.append(classification)
        
        return {
            'total_images': len(image_paths),
            'damage_detected': len([d for d in damage_classifications if d['has_damage']]),
            'classifications': damage_classifications,
            'summary': self._summarize_photo_damage(damage_classifications)
        }
    
    def _mock_classify_image(self, image_path: str) -> Dict:
        """Mock image classification for MVP"""
        return {
            'image': image_path,
            'has_damage': random.choice([True, True, False]),
            'damage_type': random.choice(['crack', 'spalling', 'displacement', 'water']),
            'severity': random.choice(['minor', 'moderate', 'severe']),
            'location': random.choice(['exterior', 'interior', 'structural', 'facade'])
        }
```

### Precedent Matching Agent

```python
# backend/agents/precedent_matcher.py

import numpy as np
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity

class PrecedentMatcher:
    
    def __init__(self, db_connection, embedding_model):
        self.db = db_connection
        self.embedder = embedding_model
    
    def find_similar_cases(
        self,
        claim_details: Dict,
        top_k: int = 5
    ) -> List[Dict]:
        """Find most similar precedent cases"""
        
        # Create embedding for current claim
        claim_text = self._create_claim_description(claim_details)
        claim_embedding = self.embedder.encode(claim_text)
        
        # Query similar cases using vector similarity
        similar_cases = self._vector_search(
            claim_embedding,
            filters={
                'building_type': claim_details['building_type'],
                'floors': (claim_details['floors'] - 2, claim_details['floors'] + 2)
            },
            limit=top_k * 2
        )
        
        # Re-rank based on multiple factors
        ranked_cases = self._rerank_cases(similar_cases, claim_details)
        
        return ranked_cases[:top_k]
    
    def _create_claim_description(self, claim_details: Dict) -> str:
        """Create searchable text description of claim"""
        return f"""
        Building Type: {claim_details['building_type']}
        Floors: {claim_details['floors']}
        Year Built: {claim_details['year_built']}
        NBS Rating: {claim_details['nbs_rating']}%
        Structural Damage: {claim_details['structural_damage']}
        Facade Damage: {claim_details['facade_damage']}
        Services Damage: {claim_details['services_damage']}
        Estimated Cost: ${claim_details['estimated_cost']:,.0f}
        Key Issues: {', '.join(claim_details.get('key_issues', []))}
        """
    
    def _vector_search(
        self,
        embedding: np.ndarray,
        filters: Dict,
        limit: int
    ) -> List[Dict]:
        """Search precedent database using vector similarity"""
        
        query = """
        SELECT 
            id, case_reference, building_type, floors,
            damage_level, claim_amount, settlement_amount,
            key_arguments, timeline_days, insurer,
            1 - (embedding <-> %s) as similarity
        FROM precedent_cases
        WHERE building_type = %s
            AND floors BETWEEN %s AND %s
        ORDER BY embedding <-> %s
        LIMIT %s
        """
        
        results = self.db.execute(
            query,
            [
                embedding,
                filters['building_type'],
                filters['floors'][0],
                filters['floors'][1],
                embedding,
                limit
            ]
        )
        
        return [dict(r) for r in results]
    
    def _rerank_cases(
        self,
        cases: List[Dict],
        claim_details: Dict
    ) -> List[Dict]:
        """Re-rank cases based on multiple relevance factors"""
        
        for case in cases:
            score = case['similarity'] * 0.5  # Base similarity score
            
            # Damage level similarity
            if case['damage_level'] == claim_details.get('structural_damage'):
                score += 0.2
            
            # Claim amount proximity (within 20%)
            if claim_details.get('estimated_cost'):
                ratio = case['claim_amount'] / claim_details['estimated_cost']
                if 0.8 <= ratio <= 1.2:
                    score += 0.15
            
            # Same insurer bonus
            if case['insurer'] == claim_details.get('insurer'):
                score += 0.1
            
            # Recent cases weighted higher
            if case.get('settlement_date'):
                # Implement recency weighting
                pass
            
            case['relevance_score'] = score
        
        return sorted(cases, key=lambda x: x['relevance_score'], reverse=True)

    def extract_strategy_insights(self, precedent_cases: List[Dict]) -> Dict:
        """Extract strategic insights from precedent cases"""
        
        insights = {
            'average_settlement_ratio': np.mean([c['settlement_amount'] / c['claim_amount'] 
                                                 for c in precedent_cases]),
            'average_timeline_days': np.mean([c['timeline_days'] for c in precedent_cases]),
            'common_arguments': self._extract_common_arguments(precedent_cases),
            'insurer_patterns': self._analyze_insurer_patterns(precedent_cases),
            'success_factors': self._identify_success_factors(precedent_cases)
        }
        
        return insights
    
    def _extract_common_arguments(self, cases: List[Dict]) -> List[str]:
        """Find most common successful arguments"""
        all_arguments = []
        for case in cases:
            if case['settlement_amount'] / case['claim_amount'] > 0.8:
                all_arguments.extend(case.get('key_arguments', []))
        
        # Count frequency
        from collections import Counter
        argument_counts = Counter(all_arguments)
        
        return [arg for arg, _ in argument_counts.most_common(5)]
```

## 4. API Implementation

### FastAPI Backend

```python
# backend/api/main.py

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio

app = FastAPI(title="Earthquake Claim Accelerator")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ClaimCreate(BaseModel):
    property_id: str
    event_date: str
    initial_assessment: Dict

class ClaimResponse(BaseModel):
    claim_id: str
    status: str
    nhc_portion: float
    private_portion: float
    next_steps: List[str]

@app.post("/api/claims/create", response_model=ClaimResponse)
async def create_claim(claim_data: ClaimCreate):
    """Create a new claim"""
    
    # Generate claim ID
    claim_id = str(uuid.uuid4())
    
    # Calculate NHC vs private portions
    nhc_portion = min(claim_data.initial_assessment.get('estimated_cost', 0), 345000)
    private_portion = max(0, claim_data.initial_assessment.get('estimated_cost', 0) - nhc_portion)
    
    # Save to database
    await save_claim(claim_id, claim_data)
    
    return ClaimResponse(
        claim_id=claim_id,
        status="draft",
        nhc_portion=nhc_portion,
        private_portion=private_portion,
        next_steps=[
            "Upload engineering report",
            "Upload damage photos",
            "Review extracted data",
            "Generate claim package"
        ]
    )

@app.post("/api/claims/{claim_id}/documents/upload")
async def upload_document(
    claim_id: str,
    file: UploadFile = File(...)
):
    """Upload and process claim documents"""
    
    # Validate file type
    if not file.filename.endswith(('.pdf', '.jpg', '.png')):
        raise HTTPException(400, "Invalid file type")
    
    # Save file
    file_path = await save_uploaded_file(file)
    
    # Process based on type
    if file.filename.endswith('.pdf'):
        # Start async processing
        asyncio.create_task(process_engineering_report(claim_id, file_path))
        return {"status": "processing", "document_id": str(uuid.uuid4())}
    else:
        # Image processing
        asyncio.create_task(process_damage_photo(claim_id, file_path))
        return {"status": "processing", "document_id": str(uuid.uuid4())}

@app.get("/api/claims/{claim_id}/precedents")
async def get_precedents(claim_id: str):
    """Find similar precedent cases"""
    
    # Get claim details
    claim = await get_claim(claim_id)
    
    # Find precedents
    matcher = PrecedentMatcher(db, embedder)
    precedents = matcher.find_similar_cases(claim, top_k=5)
    insights = matcher.extract_strategy_insights(precedents)
    
    return {
        "similar_claims": precedents,
        "insights": insights,
        "recommended_strategy": generate_strategy(precedents, insights)
    }

@app.post("/api/claims/{claim_id}/generate-package")
async def generate_claim_package(claim_id: str):
    """Generate complete claim package"""
    
    # Get all claim data
    claim = await get_claim_with_documents(claim_id)
    
    # Generate package
    generator = ClaimPackageGenerator()
    package_url = await generator.generate(claim)
    
    return {
        "package_url": package_url,
        "sections": [
            "Property Details",
            "Event Information",
            "Damage Assessment",
            "Cost Estimates",
            "Supporting Evidence",
            "Precedent Cases"
        ],
        "status": "ready"
    }

@app.get("/api/claims/{claim_id}/strategy")
async def get_settlement_strategy(claim_id: str):
    """Get recommended settlement strategy"""
    
    claim = await get_claim(claim_id)
    precedents = await get_precedents(claim_id)
    
    strategy = StrategyGenerator().generate(claim, precedents)
    
    return {
        "recommended_actions": strategy['actions'],
        "decision_points": strategy['decision_points'],
        "timeline": strategy['timeline'],
        "risk_assessment": strategy['risks']
    }
```

## 5. Frontend Implementation

### Next.js Components

```typescript
// frontend/app/claims/new/page.tsx

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { FileUpload } from '@/components/file-upload';
import { PropertySelector } from '@/components/property-selector';

export default function NewClaim() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [claimData, setClaimData] = useState({
    propertyId: '',
    eventDate: '',
    engineeringReport: null,
    photos: [],
    initialAssessment: {}
  });

  const handlePropertySelect = (propertyId: string) => {
    setClaimData(prev => ({ ...prev, propertyId }));
    setStep(2);
  };

  const handleFileUpload = async (files: File[]) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    const response = await fetch(`/api/claims/${claimData.id}/documents/upload`, {
      method: 'POST',
      body: formData
    });
    
    if (response.ok) {
      setStep(3);
    }
  };

  const generatePackage = async () => {
    const response = await fetch(`/api/claims/${claimData.id}/generate-package`, {
      method: 'POST'
    });
    
    const result = await response.json();
    router.push(`/claims/${claimData.id}/review`);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">New Earthquake Claim</h1>
      
      {step === 1 && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Select Property</h2>
          <PropertySelector onSelect={handlePropertySelect} />
        </Card>
      )}
      
      {step === 2 && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Upload Documents</h2>
          <FileUpload
            accept=".pdf,.jpg,.png"
            multiple
            onUpload={handleFileUpload}
            className="mb-4"
          />
          <p className="text-sm text-gray-600">
            Upload engineering reports and damage photos
          </p>
        </Card>
      )}
      
      {step === 3 && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Review Extraction</h2>
          <ExtractedDataReview claimId={claimData.id} />
          <Button onClick={generatePackage} className="mt-4">
            Generate Claim Package
          </Button>
        </Card>
      )}
    </div>
  );
}
```

```typescript
// frontend/components/precedent-viewer.tsx

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface Precedent {
  caseReference: string;
  buildingType: string;
  claimAmount: number;
  settlementAmount: number;
  settlementRatio: number;
  keyArguments: string[];
  timelineDays: number;
  relevanceScore: number;
}

export function PrecedentViewer({ claimId }: { claimId: string }) {
  const [precedents, setPrecedents] = useState<Precedent[]>([]);
  const [insights, setInsights] = useState(null);
  
  useEffect(() => {
    fetch(`/api/claims/${claimId}/precedents`)
      .then(res => res.json())
      .then(data => {
        setPrecedents(data.similar_claims);
        setInsights(data.insights);
      });
  }, [claimId]);
  
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Similar Precedent Cases</h3>
      
      {precedents.map((precedent, idx) => (
        <Card key={idx} className="p-4">
          <div className="flex justify-between items-start mb-2">
            <div>
              <p className="font-medium">{precedent.caseReference}</p>
              <p className="text-sm text-gray-600">
                {precedent.buildingType} - {precedent.timelineDays} days
              </p>
            </div>
            <Badge variant="outline">
              {(precedent.relevanceScore * 100).toFixed(0)}% match
            </Badge>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mt-3">
            <div>
              <p className="text-sm text-gray-600">Claimed</p>
              <p className="font-semibold">
                ${precedent.claimAmount.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Settled</p>
              <p className="font-semibold text-green-600">
                ${precedent.settlementAmount.toLocaleString()}
                <span className="text-sm ml-1">
                  ({(precedent.settlementRatio * 100).toFixed(1)}%)
                </span>
              </p>
            </div>
          </div>
          
          <div className="mt-3">
            <p className="text-sm text-gray-600 mb-1">Key Arguments:</p>
            <div className="flex flex-wrap gap-1">
              {precedent.keyArguments.map((arg, i) => (
                <Badge key={i} variant="secondary" className="text-xs">
                  {arg}
                </Badge>
              ))}
            </div>
          </div>
        </Card>
      ))}
      
      {insights && (
        <Card className="p-4 bg-blue-50">
          <h4 className="font-semibold mb-2">Strategy Insights</h4>
          <ul className="space-y-1 text-sm">
            <li>Average settlement: {(insights.average_settlement_ratio * 100).toFixed(1)}%</li>
            <li>Average timeline: {insights.average_timeline_days} days</li>
            <li>Success rate with similar damage: {insights.success_rate}%</li>
          </ul>
        </Card>
      )}
    </div>
  );
}
```

## 6. Docker Compose for Local Development

```yaml
# infrastructure/docker-compose.yml

version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg14
    environment:
      POSTGRES_DB: earthquake_claims
      POSTGRES_USER: claims_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://claims_user:secure_password@postgres/earthquake_claims
      REDIS_URL: redis://redis:6379
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
      - uploads:/app/uploads

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  redis_data:
  minio_data:
  uploads:
```

## 7. Testing Strategy

```python
# tests/test_claim_processing.py

import pytest
from datetime import datetime
from backend.synthetic.generator import SyntheticDataGenerator
from backend.agents.document_analyzer import DocumentAnalyzer

class TestClaimProcessing:
    
    @pytest.fixture
    def synthetic_data(self):
        generator = SyntheticDataGenerator()
        return generator.generate_batch(10)
    
    @pytest.fixture
    def sample_claim(self, synthetic_data):
        return synthetic_data['claims'][0]
    
    def test_nhc_portion_calculation(self, sample_claim):
        """Test NHC portion is correctly capped"""
        assert sample_claim['nhc_portion'] <= 345000
        
        if sample_claim['claimed_amount'] < 345000:
            assert sample_claim['nhc_portion'] == sample_claim['claimed_amount']
    
    def test_settlement_ratio_bounds(self, synthetic_data):
        """Test settlement ratios are realistic"""
        for claim in synthetic_data['claims']:
            ratio = claim['settlement_amount'] / claim['claimed_amount']
            assert 0.5 <= ratio <= 1.2
    
    def test_damage_assessment_extraction(self):
        """Test extraction from mock engineering report"""
        analyzer = DocumentAnalyzer(mock_llm_client)
        
        mock_report = "tests/fixtures/mock_engineering_report.pdf"
        result = analyzer.analyze_engineering_report(mock_report)
        
        assert result.confidence_score > 0.7
        assert len(result.structural_elements) > 0
        assert result.cost_estimates
    
    def test_precedent_matching(self, sample_claim):
        """Test precedent matching returns relevant cases"""
        matcher = PrecedentMatcher(mock_db, mock_embedder)
        
        precedents = matcher.find_similar_cases(sample_claim, top_k=5)
        
        assert len(precedents) <= 5
        assert all(p['relevance_score'] > 0.5 for p in precedents)
        
        # Check building type matches
        assert all(
            p['building_type'] == sample_claim['building_type'] 
            for p in precedents
        )
    
    @pytest.mark.integration
    def test_end_to_end_claim_flow(self):
        """Test complete claim processing flow"""
        
        # 1. Create claim
        response = client.post("/api/claims/create", json={
            "property_id": "test-property",
            "event_date": "2024-07-21",
            "initial_assessment": {
                "estimated_cost": 5000000
            }
        })
        assert response.status_code == 200
        claim_id = response.json()['claim_id']
        
        # 2. Upload document
        with open("tests/fixtures/test_report.pdf", "rb") as f:
            response = client.post(
                f"/api/claims/{claim_id}/documents/upload",
                files={"file": f}
            )
        assert response.status_code == 200
        
        # 3. Get precedents
        response = client.get(f"/api/claims/{claim_id}/precedents")
        assert response.status_code == 200
        assert 'similar_claims' in response.json()
        
        # 4. Generate package
        response = client.post(f"/api/claims/{claim_id}/generate-package")
        assert response.status_code == 200
        assert 'package_url' in response.json()
```

## 8. Deployment & Monitoring

```yaml
# infrastructure/kubernetes/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: claim-accelerator-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: earthquake-claims/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

This complete MVP implementation provides everything needed to build and deploy the earthquake insurance claim accelerator with synthetic data, ready for demonstration and testing.