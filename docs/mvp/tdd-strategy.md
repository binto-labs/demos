# London School TDD Strategy - Earthquake Claim Accelerator

## Overview

The London School of Test-Driven Development emphasizes **outside-in** development using mocks and test doubles to drive design and maintain fast, isolated test suites. This strategy ensures the Earthquake Claim Accelerator maintains high quality through comprehensive testing practices.

## 1. London School TDD Principles

### Core Philosophy
- **Outside-In Development**: Start with acceptance tests, work inward
- **Mock-Driven Design**: Use mocks to define interfaces and interactions
- **Fast Feedback Loops**: Tests must run quickly (<5s for unit suite)
- **Isolated Tests**: No shared state or dependencies between tests
- **Behavior-Driven**: Focus on behavior, not implementation

### Red-Green-Refactor Cycle
```
1. RED: Write a failing test that describes desired behavior
2. GREEN: Write minimal code to make the test pass
3. REFACTOR: Improve design while keeping tests green
```

### Mock-First Approach
```typescript
// Example: Start with mocked dependencies
describe('ClaimProcessor', () => {
  let processor: ClaimProcessor;
  let mockValidator: jest.Mocked<ClaimValidator>;
  let mockRepository: jest.Mocked<ClaimRepository>;

  beforeEach(() => {
    mockValidator = createMockValidator();
    mockRepository = createMockRepository();
    processor = new ClaimProcessor(mockValidator, mockRepository);
  });

  it('should process valid earthquake claim', async () => {
    mockValidator.validate.mockResolvedValue({ isValid: true });
    mockRepository.save.mockResolvedValue({ id: 'claim-123' });

    const result = await processor.process(validClaimData);

    expect(mockValidator.validate).toHaveBeenCalledWith(validClaimData);
    expect(result.status).toBe('processed');
  });
});
```

## 2. Test Pyramid Structure

### Unit Tests (70% of total tests)
- **Purpose**: Test individual components in isolation
- **Tools**: Jest (JavaScript/TypeScript), Pytest (Python)
- **Speed**: <100ms per test
- **Coverage**: 95% minimum

### Integration Tests (20% of total tests)
- **Purpose**: Test component interactions
- **Tools**: Jest with test containers, Pytest with fixtures
- **Speed**: <5s per test
- **Coverage**: Critical workflows and data flow

### End-to-End Tests (10% of total tests)
- **Purpose**: Test complete user journeys
- **Tools**: Cypress, Playwright
- **Speed**: <30s per test
- **Coverage**: Key business scenarios

```
         /\
        /E2E\      <- Cypress (Slow, Comprehensive)
       /------\     
      /Integr. \   <- Jest + TestContainers (Medium)
     /----------\   
    /   Unit     \ <- Jest/Pytest + Mocks (Fast)
   /--------------\
```

## 3. Testing Frameworks Configuration

### JavaScript/TypeScript - Jest
```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/types/**/*'
  ],
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    }
  },
  testMatch: ['**/__tests__/**/*.(test|spec).ts'],
  setupFilesAfterEnv: ['<rootDir>/src/test-setup.ts']
};
```

### Python - Pytest
```python
# pytest.ini
[tool:pytest]
minversion = 6.0
addopts = 
    --strict-markers
    --strict-config
    --cov=src
    --cov-report=term-missing
    --cov-fail-under=90
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### E2E - Cypress
```javascript
// cypress.config.js
export default {
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'cypress/support/e2e.ts',
    video: true,
    screenshotOnRunFailure: true,
    retries: {
      runMode: 2,
      openMode: 0
    }
  }
};
```

## 4. Mock Strategies and Test Doubles

### Mock Hierarchy
1. **Stubs**: Return predetermined responses
2. **Mocks**: Verify interactions and behavior
3. **Spies**: Monitor real object behavior
4. **Fakes**: Working implementations for testing

### Mock Categories

#### External Services
```typescript
// Mock external APIs
const mockGeolocationService = {
  validateAddress: jest.fn(),
  getCoordinates: jest.fn(),
  getRegionRisk: jest.fn()
};

// Mock database operations
const mockClaimRepository = {
  findById: jest.fn(),
  save: jest.fn(),
  findByUserId: jest.fn()
};
```

#### Infrastructure Mocks
```typescript
// Mock file system operations
jest.mock('fs/promises', () => ({
  readFile: jest.fn(),
  writeFile: jest.fn(),
  unlink: jest.fn()
}));

// Mock HTTP clients
jest.mock('axios', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn()
}));
```

#### Time and Random Mocks
```typescript
// Mock Date for consistent tests
const mockDate = new Date('2024-01-01T00:00:00Z');
jest.spyOn(global, 'Date').mockImplementation(() => mockDate);

// Mock random for predictable tests
jest.spyOn(Math, 'random').mockReturnValue(0.5);
```

## 5. Coverage Requirements

### Minimum Thresholds
- **Statements**: 90%
- **Branches**: 90%
- **Functions**: 90%
- **Lines**: 90%

### Coverage Exclusions
```javascript
// Exclude from coverage
/* istanbul ignore next */
const developmentOnlyCode = () => {
  // Development utilities
};
```

### Coverage Reports
```bash
# Generate HTML coverage report
npm run test:coverage

# Coverage badges in README
# Statements: 94% | Branches: 92% | Functions: 96% | Lines: 94%
```

## 6. CI/CD Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm run test:unit
      - run: npm run test:coverage
      
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v3
      - run: npm run test:integration
      
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm run build
      - run: npm run test:e2e
```

### Pre-commit Hooks
```json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged && npm run test:unit",
      "pre-push": "npm run test:integration"
    }
  }
}
```

## 7. Quality Gates

### Automated Checks
- **Code Coverage**: Must maintain 90% minimum
- **Test Performance**: Unit tests <5s, Integration <30s
- **No Flaky Tests**: Tests must pass consistently
- **Security Scans**: SAST/DAST integration
- **Performance Regression**: Response time thresholds

### Review Gates
```yaml
# Branch protection rules
protection:
  required_status_checks:
    - unit-tests
    - integration-tests
    - coverage-check
    - security-scan
  required_reviews: 2
  dismiss_stale_reviews: true
```

### Deployment Gates
- All tests pass
- Coverage thresholds met
- Security vulnerabilities resolved
- Performance benchmarks pass

## 8. Key Test Scenarios

### Critical User Journeys

#### 1. Claim Submission Flow
```typescript
describe('Claim Submission Journey', () => {
  it('should complete earthquake claim from start to finish', async () => {
    // Arrange
    const claimData = createEarthquakeClaimData();
    
    // Act & Assert
    await submitClaim(claimData);
    await verifyClaimReceived();
    await processInitialValidation();
    await assignToAdjuster();
    await generateClaimNumber();
  });
});
```

#### 2. Document Upload & Processing
```typescript
describe('Document Processing', () => {
  it('should accept and process property damage photos', async () => {
    const photos = createMockPhotoUploads();
    
    const result = await documentProcessor.process(photos);
    
    expect(result.status).toBe('processed');
    expect(result.extractedData).toContain('structural_damage');
  });
});
```

#### 3. Risk Assessment
```typescript
describe('Risk Assessment Engine', () => {
  it('should calculate risk score based on location and claim history', async () => {
    const location = { lat: 37.7749, lng: -122.4194 }; // San Francisco
    const claimHistory = createClaimHistory(3);
    
    const riskScore = await riskEngine.assess(location, claimHistory);
    
    expect(riskScore).toBeGreaterThan(0.7); // High risk area
  });
});
```

#### 4. Payment Processing
```typescript
describe('Payment Workflow', () => {
  it('should process approved claim payment', async () => {
    const approvedClaim = createApprovedClaim();
    
    const payment = await paymentProcessor.process(approvedClaim);
    
    expect(payment.status).toBe('completed');
    expect(mockBankingService.transfer).toHaveBeenCalled();
  });
});
```

### Edge Cases & Error Scenarios
- Network failures and retries
- Malformed data handling
- Concurrent claim submissions
- System overload scenarios
- Fraud detection triggers

### Performance Test Scenarios
```typescript
describe('Performance Requirements', () => {
  it('should handle 1000 concurrent claim submissions', async () => {
    const claims = Array(1000).fill(null).map(createRandomClaim);
    
    const start = performance.now();
    await Promise.all(claims.map(submitClaim));
    const duration = performance.now() - start;
    
    expect(duration).toBeLessThan(5000); // 5 second threshold
  });
});
```

## Implementation Checklist

- [ ] Set up Jest/Pytest with coverage reporting
- [ ] Configure Cypress for E2E testing
- [ ] Implement mock factories for test data
- [ ] Create shared test utilities
- [ ] Set up CI/CD pipeline with quality gates
- [ ] Configure branch protection rules
- [ ] Implement performance monitoring
- [ ] Create test data generators
- [ ] Set up test environment isolation
- [ ] Document testing best practices

## Metrics and Monitoring

### Test Metrics
- Test execution time trends
- Coverage percentage over time
- Flaky test identification
- Test failure patterns

### Quality Metrics
- Bug detection rate
- Production incident correlation
- Code review findings
- Performance regression detection

---

This London School TDD strategy ensures the Earthquake Claim Accelerator maintains the highest quality standards through comprehensive, fast, and reliable testing practices that drive excellent design decisions.