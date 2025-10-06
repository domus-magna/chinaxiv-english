# Manual Test Plan: ChinaXiv Translation Pipeline

## Overview
This test plan validates the updated translation pipeline with 10 papers to ensure high-quality results, proper math preservation, and robust error handling.

## Prerequisites
- Python 3.11+ environment activated
- OpenRouter API key set (`OPENROUTER_API_KEY`)
- Internet connection for API calls
- Test papers available in `data/selected.json` or harvested IA records

## Test Setup

### 1. Environment Preparation
```bash
cd /Users/alexanderhuth/chinaxiv-english
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Verify Configuration
```bash
# Check config is properly set
python -c "from src.config import get_config; print('Config loaded:', bool(get_config()))"

# Verify API key
python -c "import os; print('API key set:', bool(os.getenv('OPENROUTER_API_KEY')))"
```

### 3. Prepare Test Papers
```bash
# Harvest a small batch of papers for testing
python -m src.harvest_ia --limit 10 --min-year 2020

# Check available papers
ls data/records/ia_*.json | head -1 | xargs python -c "
import json, sys
with open(sys.argv[1]) as f: data = json.load(f)
print(f'Available papers: {len(data)}')
for i, paper in enumerate(data[:5]):
    print(f'{i+1}. {paper[\"id\"]}: {paper[\"title\"][:60]}...')
"
```

## Test Cases

### Test Case 1: Basic Translation (Paper 1)
**Objective**: Verify basic translation functionality

**Steps**:
1. Select first paper from harvested records
2. Run translation with dry-run first
3. Run actual translation
4. Verify output structure

**Commands**:
```bash
# Get first paper ID
PAPER_ID=$(python -c "
import json, glob
files = sorted(glob.glob('data/records/ia_*.json'), reverse=True)
with open(files[0]) as f: data = json.load(f)
print(data[0]['id'])
")

# Dry run test
python -m src.translate $PAPER_ID --dry-run

# Actual translation
python -m src.translate $PAPER_ID
```

**Expected Results**:
- [ ] Dry run completes without API calls
- [ ] Actual translation completes successfully
- [ ] Output file created in `data/translated/`
- [ ] JSON structure contains `title_en`, `abstract_en`, `body_en`

### Test Case 2: Math-Heavy Paper (Paper 2)
**Objective**: Validate mathematical content preservation

**Steps**:
1. Select paper with mathematical content
2. Translate and verify math preservation
3. Check citation preservation

**Commands**:
```bash
# Find paper with math content (look for papers with equations)
PAPER_ID=$(python -c "
import json, glob
files = sorted(glob.glob('data/records/ia_*.json'), reverse=True)
for file in files:
    with open(file) as f: data = json.load(f)
    for paper in data:
        if 'equation' in paper.get('abstract', '').lower() or 'math' in paper.get('abstract', '').lower():
            print(paper['id'])
            break
    else:
        continue
    break
")

# Translate math-heavy paper
python -m src.translate $PAPER_ID
```

**Expected Results**:
- [ ] Translation completes without math preservation errors
- [ ] Mathematical expressions preserved exactly
- [ ] Citation commands (`\cite{}`, `\ref{}`) preserved
- [ ] No `⟪MATH_*⟫` placeholders in final output

### Test Case 3: Long Paper (Paper 3)
**Objective**: Test chunking and large document handling

**Steps**:
1. Select longest available paper
2. Monitor translation progress
3. Verify complete translation

**Commands**:
```bash
# Find longest paper
PAPER_ID=$(python -c "
import json, glob
files = sorted(glob.glob('data/records/ia_*.json'), reverse=True)
longest_paper = None
max_length = 0
for file in files:
    with open(file) as f: data = json.load(f)
    for paper in data:
        length = len(paper.get('abstract', ''))
        if length > max_length:
            max_length = length
            longest_paper = paper['id']
print(longest_paper)
")

# Translate long paper
python -m src.translate $PAPER_ID
```

**Expected Results**:
- [ ] Translation completes without timeout
- [ ] All paragraphs translated
- [ ] Cost tracking works correctly
- [ ] No memory issues

### Test Case 4: Error Handling (Paper 4)
**Objective**: Test fallback mechanisms and error recovery

**Steps**:
1. Simulate API failure (temporarily modify API key)
2. Verify fallback behavior
3. Restore API key and retry

**Commands**:
```bash
# Backup API key
cp .env .env.backup

# Temporarily break API key
echo "OPENROUTER_API_KEY=invalid_key" > .env

# Try translation (should fail gracefully)
PAPER_ID=$(python -c "
import json, glob
files = sorted(glob.glob('data/records/ia_*.json'), reverse=True)
with open(files[0]) as f: data = json.load(f)
print(data[3]['id'])
")

python -m src.translate $PAPER_ID || echo "Expected failure"

# Restore API key
mv .env.backup .env

# Retry with valid key
python -m src.translate $PAPER_ID
```

**Expected Results**:
- [ ] Invalid API key handled gracefully
- [ ] Clear error message provided
- [ ] Translation succeeds after API key restoration
- [ ] No partial/corrupted output files

### Test Case 5: Quality Validation (Paper 5)
**Objective**: Verify quality checks and validation

**Steps**:
1. Translate paper and check validation logs
2. Verify quality metrics
3. Check for warnings

**Commands**:
```bash
PAPER_ID=$(python -c "
import json, glob
files = sorted(glob.glob('data/records/ia_*.json'), reverse=True)
with open(files[0]) as f: data = json.load(f)
print(data[4]['id'])
")

# Translate with verbose logging
python -m src.translate $PAPER_ID 2>&1 | tee translation.log

# Check for quality warnings
grep -i "warning\|error" translation.log || echo "No warnings found"
```

**Expected Results**:
- [ ] No validation errors
- [ ] Reasonable translation length ratios
- [ ] No math placeholder leakage
- [ ] Citation counts preserved

### Test Case 6: Batch Processing (Papers 6-8)
**Objective**: Test multiple papers in sequence

**Steps**:
1. Translate 3 papers sequentially
2. Monitor system performance
3. Verify all outputs

**Commands**:
```bash
# Get 3 paper IDs
PAPER_IDS=$(python -c "
import json, glob
files = sorted(glob.glob('data/records/ia_*.json'), reverse=True)
with open(files[0]) as f: data = json.load(f)
for i in range(5, 8):
    if i < len(data):
        print(data[i]['id'])
")

# Translate each paper
for paper_id in $PAPER_IDS; do
    echo "Translating $paper_id..."
    python -m src.translate $paper_id
    echo "Completed $paper_id"
done
```

**Expected Results**:
- [ ] All 3 papers translate successfully
- [ ] No memory leaks or performance degradation
- [ ] Consistent output quality
- [ ] Cost tracking accurate across batch

### Test Case 7: Academic Tone Validation (Paper 9)
**Objective**: Verify academic writing style and terminology

**Steps**:
1. Select paper with technical content
2. Translate and review academic tone
3. Check terminology consistency

**Commands**:
```bash
PAPER_ID=$(python -c "
import json, glob
files = sorted(glob.glob('data/records/ia_*.json'), reverse=True)
with open(files[0]) as f: data = json.load(f)
print(data[8]['id'])
")

# Translate and review
python -m src.translate $PAPER_ID

# Review translation quality
python -c "
import json
with open(f'data/translated/{PAPER_ID}.json') as f:
    data = json.load(f)
print('Title:', data.get('title_en', 'N/A'))
print('Abstract preview:', data.get('abstract_en', 'N/A')[:200] + '...')
print('Body paragraphs:', len(data.get('body_en', [])))
"
```

**Expected Results**:
- [ ] Academic tone maintained
- [ ] Technical terminology appropriate
- [ ] Formal scientific writing style
- [ ] Professional language throughout

### Test Case 8: Edge Cases (Paper 10)
**Objective**: Test edge cases and boundary conditions

**Steps**:
1. Select paper with special characters or formatting
2. Test various edge cases
3. Verify robust handling

**Commands**:
```bash
PAPER_ID=$(python -c "
import json, glob
files = sorted(glob.glob('data/records/ia_*.json'), reverse=True)
with open(files[0]) as f: data = json.load(f)
print(data[9]['id'])
")

# Test edge cases
python -m src.translate $PAPER_ID

# Check for special character handling
python -c "
import json
with open(f'data/translated/{PAPER_ID}.json') as f:
    data = json.load(f)
    
# Check for various edge cases
abstract = data.get('abstract_en', '')
print('Special characters found:', any(c in abstract for c in 'αβγδεζηθικλμνξοπρστυφχψω'))
print('Unicode handling:', len(abstract.encode('utf-8')) == len(abstract))
print('Math symbols preserved:', any(c in abstract for c in '∑∏∫∂∇±×÷≤≥≠≈∞'))
"
```

**Expected Results**:
- [ ] Special characters handled correctly
- [ ] Unicode encoding preserved
- [ ] Mathematical symbols intact
- [ ] No encoding errors

## Quality Assessment

### Manual Review Checklist
For each translated paper, verify:

**Content Quality**:
- [ ] Translation reads naturally in English
- [ ] Academic tone maintained
- [ ] Technical terminology appropriate
- [ ] No obvious translation errors
- [ ] Complete information preservation

**Mathematical Content**:
- [ ] All equations preserved exactly
- [ ] Math symbols intact (∑, ∏, ∫, ∂, ∇, etc.)
- [ ] LaTeX commands preserved (`\cite{}`, `\ref{}`, etc.)
- [ ] No math placeholder leakage
- [ ] Equation numbering preserved

**Formatting**:
- [ ] Proper paragraph structure
- [ ] Section headings preserved
- [ ] Citation formatting intact
- [ ] No formatting artifacts
- [ ] Clean, readable output

**Technical Validation**:
- [ ] JSON structure valid
- [ ] All required fields present
- [ ] No encoding issues
- [ ] File size reasonable
- [ ] Processing time acceptable

## Performance Metrics

### Expected Performance
- **Translation Speed**: 30-90 seconds per paper (P50)
- **Success Rate**: ≥95% (19/20 papers)
- **Math Preservation**: 100% (no placeholder leakage)
- **Cost Efficiency**: ≤$0.01 per paper average
- **Memory Usage**: Stable (no leaks)

### Monitoring Commands
```bash
# Monitor system resources
top -pid $(pgrep -f "python.*translate") -l 1

# Check translation costs
python -c "
import json, glob
total_cost = 0
for file in glob.glob('data/costs/*.json'):
    with open(file) as f: data = json.load(f)
    total_cost += sum(item.get('cost', 0) for item in data)
print(f'Total cost: ${total_cost:.4f}')
"

# Verify output quality
python -c "
import json, glob
translations = glob.glob('data/translated/*.json')
print(f'Total translations: {len(translations)}')
for file in translations:
    with open(file) as f: data = json.load(f)
    if not data.get('title_en') or not data.get('abstract_en'):
        print(f'Incomplete: {file}')
"
```

## Success Criteria

### Test Passes If:
- [ ] All 10 papers translate successfully
- [ ] No math preservation errors
- [ ] Academic tone maintained throughout
- [ ] Citation commands preserved exactly
- [ ] Quality validation passes
- [ ] Error handling works correctly
- [ ] Performance within expected ranges
- [ ] Cost tracking accurate

### Test Fails If:
- [ ] Any paper fails to translate
- [ ] Math content corrupted or lost
- [ ] Translation quality poor
- [ ] System errors or crashes
- [ ] Performance significantly degraded
- [ ] Cost tracking inaccurate

## Reporting

### Test Report Template
```
Test Date: [DATE]
Tester: [AGENT_NAME]
Environment: [PYTHON_VERSION, OS]

Papers Tested: 10/10
Success Rate: [X]%

Quality Assessment:
- Math Preservation: [PASS/FAIL]
- Academic Tone: [PASS/FAIL]
- Citation Preservation: [PASS/FAIL]
- Error Handling: [PASS/FAIL]

Performance Metrics:
- Average Translation Time: [X] seconds
- Total Cost: $[X.XX]
- Memory Usage: [STABLE/ISSUES]

Issues Found:
- [List any issues]

Recommendations:
- [List recommendations]
```

## Troubleshooting

### Common Issues
1. **API Key Issues**: Verify `OPENROUTER_API_KEY` is set correctly
2. **Network Timeouts**: Check internet connection and API status
3. **Memory Issues**: Monitor system resources during batch processing
4. **Quality Issues**: Review validation logs and adjust prompts if needed
5. **Cost Issues**: Check pricing configuration and token usage

### Recovery Steps
```bash
# Reset environment
source .venv/bin/activate
pip install -r requirements.txt

# Clear cache if needed
rm -rf data/translated/*.json
rm -rf data/costs/*.json

# Restart test
python -m src.translate [PAPER_ID]
```

## Conclusion

This test plan validates the updated translation pipeline's ability to deliver high-quality scientific translations with proper math preservation, academic tone, and robust error handling. The 10-paper test provides comprehensive coverage of various scenarios and edge cases.
