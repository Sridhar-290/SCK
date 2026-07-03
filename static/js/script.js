document.addEventListener('DOMContentLoaded', () => {
    // 1. Navigation & Layout Logic
    const container = document.querySelector('.container');
    if (!container) return; // Exit if not on dashboard/analyer page

    // 2. Global DOM Elements
    const jobRoleSelect = document.getElementById('jobRole');
    const evaluateBtn = document.getElementById('evaluateBtn');
    const agentAnalyzeBtn = document.getElementById('agentAnalyzeBtn');

    // 3. Init
    fetchRoles();
    fetchHistory();

    // 4. Mode Switching
    window.switchMode = function (mode) {
        const btns = document.querySelectorAll('.mode-btn');
        const stdForm = document.getElementById('standard-form');
        const agentForm = document.getElementById('agent-form');

        if (mode === 'standard') {
            btns[0].classList.add('active');
            btns[1].classList.remove('active');
            stdForm.classList.remove('hidden');
            agentForm.classList.add('hidden');
        } else {
            btns[0].classList.remove('active');
            btns[1].classList.add('active');
            stdForm.classList.add('hidden');
            agentForm.classList.remove('hidden');
        }
    }

    // 5. Standard Evaluation
    evaluateBtn.addEventListener('click', async () => {
        const roleId = document.getElementById('jobRole').value;
        const text = document.getElementById('resumeText').value;
        const fileInput = document.getElementById('resumeFile');
        const file = fileInput ? fileInput.files[0] : null;

        if (!roleId || roleId === 'Loading...') {
            alert('Please select a job role.');
            return;
        }

        if (!text && !file) {
            alert('Please paste a resume or upload a PDF.');
            return;
        }

        // UI Loading
        evaluateBtn.disabled = true;
        evaluateBtn.textContent = 'Analyzing...';

        const formData = new FormData();
        formData.append('job_role_id', roleId);
        if (file) {
            formData.append('resume_file', file);
            if (text) formData.append('resume_text', text);
        } else {
            formData.append('resume_text', text);
        }

        try {
            const response = await fetch('/evaluate', { method: 'POST', body: formData });
            const data = await response.json();

            if (data.error) {
                alert(data.error);
            } else {
                displayResults(data);
                fetchHistory();
            }
        } catch (error) {
            console.error(error);
            alert('Analysis failed. Please try again.');
        } finally {
            evaluateBtn.disabled = false;
            evaluateBtn.textContent = 'Analyze Resume';
        }
    });

    // 6. AI Agent Evaluation
    if (agentAnalyzeBtn) {
        agentAnalyzeBtn.addEventListener('click', async () => {
            const jdText = document.getElementById('jdText').value.trim();
            const resumeText = document.getElementById('agentResumeText').value.trim();
            const file = document.getElementById('agentResumeFile').files[0];

            if (!jdText || (!resumeText && !file)) {
                alert("Please provide the Job Description and your Resume.");
                return;
            }

            agentAnalyzeBtn.disabled = true;
            agentAnalyzeBtn.textContent = "Analyzing...";

            try {
                let body;
                let headers = {};

                if (file) {
                    const formData = new FormData();
                    formData.append('resume_file', file);
                    formData.append('jd_text', jdText);
                    if (resumeText) formData.append('resume_text', resumeText);
                    body = formData;
                } else {
                    headers['Content-Type'] = 'application/json';
                    body = JSON.stringify({ jd_text: jdText, resume_text: resumeText });
                }

                const response = await fetch('/analyze_jd', { method: 'POST', headers: headers, body: body });
                const data = await response.json();

                if (data.error) {
                    alert(data.error);
                } else {
                    showAgentResults(data);
                }
            } catch (error) {
                console.error(error);
                alert("Analysis failed.");
            } finally {
                agentAnalyzeBtn.disabled = false;
                agentAnalyzeBtn.textContent = "Run AI Analysis";
            }
        });
    }

    // 7. Helpers: Display Logic
    function displayResults(data) {
        document.getElementById('resultCard').classList.remove('hidden');
        document.getElementById('agentResultCard').classList.add('hidden');

        document.getElementById('matchScoreDisplay').textContent = data.score + "%";

        // Dynamic Score Color
        const color = data.score > 75 ? '#4ade80' : data.score > 50 ? '#facc15' : '#f87171';
        document.getElementById('matchScoreDisplay').style.color = color;

        document.getElementById('suggestionBox').textContent = data.suggestions;

        renderTags(document.getElementById('matchedKeywords'), data.matched_keywords, 'tag-matched');
        renderTags(document.getElementById('missingKeywords'), data.missing_keywords, 'tag-missing');

        // Scroll on mobile
        if (window.innerWidth < 900) {
            document.getElementById('resultCard').scrollIntoView({ behavior: 'smooth' });
        }
    }

    function showAgentResults(data) {
        document.getElementById('agentResultCard').classList.remove('hidden');
        document.getElementById('resultCard').classList.add('hidden');

        document.getElementById('agentInsight').textContent = data.insight;
        document.getElementById('agentLagging').textContent = data.lagging;

        renderTags(document.getElementById('agentMatched'), data.matched, 'tag-matched');
        renderTags(document.getElementById('agentMissing'), data.missing, 'tag-missing');

        if (window.innerWidth < 900) {
            document.getElementById('agentResultCard').scrollIntoView({ behavior: 'smooth' });
        }
    }

    function renderTags(container, list, className) {
        container.innerHTML = '';
        list.forEach(kw => {
            const span = document.createElement('span');
            span.className = `keyword-tag ${className}`;
            span.textContent = kw;
            container.appendChild(span);
        });
    }

    // 8. Data Fetching
    async function fetchRoles() {
        try {
            const response = await fetch('/roles');
            const roles = await response.json();
            jobRoleSelect.innerHTML = '<option value="" disabled selected>Select a job role</option>';
            roles.forEach(role => {
                const opt = document.createElement('option');
                opt.value = role.id;
                opt.textContent = role.name;
                jobRoleSelect.appendChild(opt);
            });
        } catch (e) { console.error(e); }
    }

    async function fetchHistory() {
        try {
            const response = await fetch('/history');
            const history = await response.json();
            const list = document.getElementById('historyList');
            list.innerHTML = '';

            history.forEach(item => {
                const div = document.createElement('div');
                div.className = 'history-item';
                // Color code score in history
                const scoreClass = item.score > 75 ? 'text-high' : item.score > 50 ? 'text-mid' : 'text-low';

                div.innerHTML = `
                    <div class="h-header">
                        <span class="h-role">${item.role_name}</span>
                        <span class="h-score ${scoreClass}">${item.score}%</span>
                    </div>
                    <div class="h-date">${new Date(item.timestamp).toLocaleDateString()}</div>
                `;
                // Click to view (optional: could repopulate results)
                list.appendChild(div);
            });
        } catch (e) {
            document.getElementById('historyList').innerHTML = '<p class="text-low">Failed to load history</p>';
        }
    }
});
