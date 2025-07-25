document.addEventListener('DOMContentLoaded', function() {
    fetch('result.json')
        .then(response => response.json())
        .then(data => processData(data))
        .catch(error => {
            console.error('Error loading data:', error);
            document.getElementById('loadingContainer').innerHTML = 
                '<div class="alert alert-danger small">Error loading evaluation results.</div>';
        });

    function processData(data) {
        const results = data.results.results;
        const modelMap = new Map();
        const testCaseMap = new Map();
        const testCaseDescriptions = new Map();
        
        results.forEach(result => {
            const modelId = result.provider.id;
            const modelLabel = result.provider.label || modelId;
            if (!modelMap.has(modelId)) modelMap.set(modelId, modelLabel);
            
            let testCaseName = '';
            if (result.gradingResult?.componentResults?.[0]?.assertion?.value) {
                const assertValue = result.gradingResult.componentResults[0].assertion.value;
                if (assertValue.includes('://')) {
                    const parts = assertValue.split('://');
                    if (parts.length > 1) {
                        const subParts = parts[1].split('.py:');
                        if (subParts.length > 0) testCaseName = subParts[0];
                    }
                }
            }
            
            if (testCaseName && !testCaseMap.has(testCaseName)) {
                testCaseMap.set(testCaseName, new Map());
                if (result.testCase?.description) {
                    testCaseDescriptions.set(testCaseName, result.testCase.description);
                }
            }
            
            if (testCaseName) {
                const testCaseResults = testCaseMap.get(testCaseName);
                if (!testCaseResults.has(modelId)) {
                    testCaseResults.set(modelId, { passes: 0, total: 0, reasons: [] });
                }
                
                const resultData = testCaseResults.get(modelId);
                resultData.total++;
                
                if (result.gradingResult?.componentResults?.[0]?.pass) {
                    resultData.passes++;
                }
                
                if (result.gradingResult?.componentResults?.[0]?.reason) {
                    resultData.reasons.push(result.gradingResult.componentResults[0].reason);
                }
            }
        });

        const testCases = Array.from(testCaseMap.keys());
        const testCaseOverallResults = new Map();
        const modelOverallResults = new Map();
        
        testCases.forEach(testCase => {
            let totalPasses = 0, totalRuns = 0;
            modelMap.forEach((_, modelId) => {
                const modelResults = testCaseMap.get(testCase).get(modelId);
                if (modelResults) {
                    totalPasses += modelResults.passes;
                    totalRuns += modelResults.total;
                }
            });
            testCaseOverallResults.set(testCase, {
                winPercentage: totalRuns > 0 ? (totalPasses / totalRuns) * 100 : 0,
                passes: totalPasses,
                total: totalRuns
            });
        });

        modelMap.forEach((_, modelId) => {
            let passes = 0, total = 0;
            testCases.forEach(testCase => {
                const modelResults = testCaseMap.get(testCase)?.get(modelId);
                if (modelResults) {
                    passes += modelResults.passes;
                    total += modelResults.total;
                }
            });
            modelOverallResults.set(modelId, {
                successRate: total > 0 ? (passes / total) * 100 : 0,
                passes, total
            });
        });

        const sortedTestCases = testCases.sort((a, b) => 
            testCaseOverallResults.get(b).winPercentage - testCaseOverallResults.get(a).winPercentage);
        const sortedModels = Array.from(modelMap.entries()).sort((a, b) => 
            modelOverallResults.get(b[0]).successRate - modelOverallResults.get(a[0]).successRate);

        const headerRow = document.getElementById('headerRow');
        const tableBody = document.getElementById('tableBody');
        
        sortedModels.forEach(([_, modelLabel]) => {
            const th = document.createElement('th');
            th.className = 'text-center align-middle border border-dark small py-2';
            th.style.width = '96px';
            th.textContent = modelLabel;
            headerRow.appendChild(th);
        });

        sortedTestCases.forEach(testCase => {
            const row = document.createElement('tr');
            row.className = 'border border-dark';
            
            const testCaseCell = document.createElement('td');
            testCaseCell.className = 'small fw-medium border border-dark py-2';
            testCaseCell.textContent = testCase;
            if (testCaseDescriptions.has(testCase)) {
                testCaseCell.setAttribute('data-bs-toggle', 'tooltip');
                testCaseCell.setAttribute('data-bs-placement', 'right');
                testCaseCell.setAttribute('title', testCaseDescriptions.get(testCase));
            }
            row.appendChild(testCaseCell);
            
            const winPercentage = testCaseOverallResults.get(testCase).winPercentage;
            const winCell = document.createElement('td');
            winCell.className = 'text-center border border-dark small py-2';
            winCell.textContent = `${winPercentage.toFixed(1)}%`;
            addPerformanceClass(winCell, winPercentage);
            row.appendChild(winCell);
            
            sortedModels.forEach(([modelId]) => {
                const cell = document.createElement('td');
                cell.className = 'text-center border border-dark small py-2';
                
                const modelResults = testCaseMap.get(testCase)?.get(modelId);
                if (modelResults) {
                    const passRate = (modelResults.passes / modelResults.total) * 100;
                    cell.textContent = `${modelResults.passes}/${modelResults.total}`;
                    addPerformanceClass(cell, passRate);
                    
                    if (modelResults.reasons.length > 0) {
                        cell.setAttribute('data-bs-toggle', 'tooltip');
                        cell.setAttribute('data-bs-placement', 'top');
                        cell.setAttribute('data-bs-html', 'true');
                        cell.setAttribute('title', modelResults.reasons.map((reason, i) => 
                            `Test ${i + 1}: ${reason}`).join('<br>'));
                    }
                } else {
                    cell.textContent = '0/0';
                    cell.classList.add('text-muted');
                }
                row.appendChild(cell);
            });
            tableBody.appendChild(row);
        });

        const footerRow = document.getElementById('footerRow');
        footerRow.children[1].textContent = '';
        
        sortedModels.forEach(([modelId]) => {
            const cell = document.createElement('td');
            cell.className = 'text-center fw-bold border border-dark small py-2';
            const successRate = modelOverallResults.get(modelId).successRate;
            cell.textContent = `${successRate.toFixed(1)}%`;
            addPerformanceClass(cell, successRate);
            footerRow.appendChild(cell);
        });

        new bootstrap.Tooltip(document.body, {
            selector: '[data-bs-toggle="tooltip"]'
        });

        document.getElementById('loadingContainer').style.display = 'none';
        document.getElementById('tableContainer').style.display = 'block';
    }
    
    function addPerformanceClass(element, percentage) {
        if (percentage >= 80) element.classList.add('table-success');
        else if (percentage >= 60) element.classList.add('table-primary');
        else if (percentage >= 40) element.classList.add('table-warning');
        else element.classList.add('table-danger');
    }
});