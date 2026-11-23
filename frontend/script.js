// ======================================
// GREENROUTE AI - DASHBOARD JAVASCRIPT
// ======================================

const API_BASE = "http://127.0.0.1:8000";

// Get HTML elements
const promptInput = document.getElementById("userPrompt");
const submitButton = document.getElementById("submitButton");
const statusElement = document.getElementById("status");
const responseElement = document.getElementById("response");

const selectedModelElement = document.getElementById("selectedModel");
const taskTypeElement = document.getElementById("taskType");
const confidenceElement = document.getElementById("confidence");
const decisionTraceElement = document.getElementById("decisionTrace");

const totalRequestsElement = document.getElementById("totalRequests");
const successRateElement = document.getElementById("successRate");
const activeProvidersElement = document.getElementById("activeProviders");
const fallbackCountElement = document.getElementById("fallbackCount");

const fallbackStatusElement = document.getElementById("fallbackStatus");

const historyBody = document.getElementById("historyBody");
const performanceContainer = document.getElementById("performanceContainer");


// ======================================
// HELPER FUNCTIONS
// ======================================

function formatConfidence(value) {
    if (value === undefined || value === null) {
        return "N/A";
    }

    const number = Number(value);

    if (isNaN(number)) {
        return String(value);
    }

    if (number <= 1) {
        return (number * 100).toFixed(1) + "%";
    }

    return number.toFixed(1) + "%";
}


function formatTime(value) {
    if (value === undefined || value === null) {
        return "N/A";
    }

    return Number(value).toFixed(2) + " sec";
}


function createCell(value) {
    const cell = document.createElement("td");
    cell.textContent = value === undefined || value === null ?
        "N/A" :
        String(value);

    return cell;
}


// ======================================
// SUBMIT PROMPT
// ======================================

async function submitPrompt() {

    const prompt = promptInput.value.trim();

    if (prompt === "") {
        statusElement.textContent = "Please enter a prompt.";
        return;
    }

    submitButton.disabled = true;
    submitButton.textContent = "Processing...";

    statusElement.textContent = "GreenRoute AI is analyzing your prompt...";
    responseElement.textContent = "Generating response...";

    try {

        const result = await fetch(API_BASE + "/api/route", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                prompt: prompt
            })
        });

        const data = await result.json();

        if (!result.ok) {
            throw new Error(data.detail || "Request failed.");
        }

        // Display AI response
        responseElement.textContent = data.response || "No response received.";

        // Display routing information
        selectedModelElement.textContent =
            data.selected_model || "Unknown";

        taskTypeElement.textContent =
            data.task_type || "Unknown";

        confidenceElement.textContent =
            formatConfidence(data.confidence);

        // Display fallback status
        const fallbackUsed = data.fallback_used === true;

        fallbackStatusElement.textContent =
            fallbackUsed ? "Yes" : "No";

        // Display decision trace
        if (data.decision_trace !== undefined &&
            data.decision_trace !== null) {

            if (typeof data.decision_trace === "string") {
                decisionTraceElement.textContent = data.decision_trace;
            } else {
                decisionTraceElement.textContent =
                    JSON.stringify(data.decision_trace, null, 2);
            }

        } else {
            decisionTraceElement.textContent =
                "Routing decision completed.";
        }

        statusElement.textContent =
            "Response generated successfully!";

        // Refresh dashboard data
        await loadDashboardData();

    } catch (error) {

        statusElement.textContent = "Error: " + error.message;

        responseElement.textContent =
            "Unable to generate a response. Please check the backend server.";

        console.error("Routing error:", error);

    } finally {

        submitButton.disabled = false;
        submitButton.textContent = "Submit Prompt →";

    }
}


// ======================================
// LOAD REQUEST HISTORY
// ======================================

async function loadHistory() {

    try {

        const result = await fetch(API_BASE + "/api/history");

        if (!result.ok) {
            throw new Error("Unable to load history.");
        }

        const data = await result.json();

        const history = data.history || [];

        historyBody.innerHTML = "";

        if (history.length === 0) {

            const row = document.createElement("tr");
            const cell = document.createElement("td");

            cell.colSpan = 6;
            cell.textContent = "No request history available.";

            row.appendChild(cell);
            historyBody.appendChild(row);

            return history;
        }

        history.forEach(function(item) {

            const row = document.createElement("tr");

            row.appendChild(createCell(item.id));

            const promptCell = createCell(item.prompt);
            promptCell.style.maxWidth = "250px";
            row.appendChild(promptCell);

            row.appendChild(createCell(item.task_type));
            row.appendChild(createCell(item.selected_model));
            row.appendChild(createCell(item.status));
            row.appendChild(createCell(formatTime(item.execution_time)));

            historyBody.appendChild(row);

        });

        return history;

    } catch (error) {

        console.error("History error:", error);

        historyBody.innerHTML = "";

        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 6;
        cell.textContent = "Unable to load request history.";

        row.appendChild(cell);
        historyBody.appendChild(row);

        return [];

    }
}


// ======================================
// LOAD PROVIDER PERFORMANCE
// ======================================

async function loadPerformance() {

    try {

        const result = await fetch(API_BASE + "/api/performance");

        if (!result.ok) {
            throw new Error("Unable to load performance.");
        }

        const data = await result.json();

        const performance = data.provider_performance || {};

        performanceContainer.innerHTML = "";

        const providers = {};

        // Combine provider results across task types
        Object.keys(performance).forEach(function(task) {

            const taskData = performance[task];

            Object.keys(taskData).forEach(function(provider) {

                if (!providers[provider]) {
                    providers[provider] = {
                        total: 0,
                        successful: 0
                    };
                }

                providers[provider].total +=
                    Number(taskData[provider].total_attempts || 0);

                providers[provider].successful +=
                    Number(taskData[provider].successful_attempts || 0);

            });

        });

        const providerNames = Object.keys(providers);

        if (providerNames.length === 0) {

            performanceContainer.textContent =
                "No provider performance data available yet.";

            return providerNames.length;
        }

        providerNames.forEach(function(provider) {

            const total = providers[provider].total;
            const successful = providers[provider].successful;

            const rate = total > 0 ?
                (successful / total) * 100 :
                0;

            const wrapper = document.createElement("div");
            wrapper.style.marginBottom = "25px";

            const heading = document.createElement("div");
            heading.style.display = "flex";
            heading.style.justifyContent = "space-between";
            heading.style.marginBottom = "10px";

            const name = document.createElement("strong");
            name.textContent = provider;

            const percentage = document.createElement("strong");
            percentage.textContent = rate.toFixed(1) + "%";
            percentage.style.color = "#55d6a2";

            heading.appendChild(name);
            heading.appendChild(percentage);

            const barBackground = document.createElement("div");
            barBackground.style.height = "10px";
            barBackground.style.background = "#263448";
            barBackground.style.borderRadius = "10px";
            barBackground.style.overflow = "hidden";

            const bar = document.createElement("div");
            bar.style.width = rate + "%";
            bar.style.height = "100%";
            bar.style.background = "#37c98b";
            bar.style.borderRadius = "10px";

            barBackground.appendChild(bar);

            const details = document.createElement("p");
            details.style.color = "#91a3b8";
            details.style.fontSize = "12px";
            details.style.marginTop = "8px";

            details.textContent =
                successful + " successful out of " + total + " attempts";

            wrapper.appendChild(heading);
            wrapper.appendChild(barBackground);
            wrapper.appendChild(details);

            performanceContainer.appendChild(wrapper);

        });

        return providerNames.length;

    } catch (error) {

        console.error("Performance error:", error);

        performanceContainer.textContent =
            "Unable to load provider performance.";

        return 0;

    }
}


// ======================================
// LOAD DASHBOARD STATISTICS
// ======================================

async function loadDashboardStats() {

    try {

        const result = await fetch(API_BASE + "/api/stats");

        if (!result.ok) {
            throw new Error("Unable to load dashboard statistics.");
        }

        const stats = await result.json();

        const totalRequests = Number(stats.total_requests || 0);
        const successRate = Number(stats.success_rate || 0);
        const fallbackCount = Number(stats.fallback_count || 0);

        totalRequestsElement.textContent = totalRequests;
        successRateElement.textContent = successRate.toFixed(1) + "%";
        fallbackCountElement.textContent = fallbackCount;

    } catch (error) {

        console.error("Stats error:", error);

        totalRequestsElement.textContent = "0";
        successRateElement.textContent = "0.0%";
        fallbackCountElement.textContent = "0";

    }
}


// ======================================
// LOAD COMPLETE DASHBOARD
// ======================================

async function loadDashboardData() {

    await loadHistory();

    await loadDashboardStats();

    const providerCount = await loadPerformance();

    activeProvidersElement.textContent = providerCount;

}


// ======================================
// SIDEBAR NAVIGATION
// ======================================

const navigationLinks = document.querySelectorAll(".nav-link");

navigationLinks.forEach(function(link) {

    link.addEventListener("click", function() {

        navigationLinks.forEach(function(item) {
            item.classList.remove("active");
        });

        link.classList.add("active");

    });

});


// ======================================
// EVENT LISTENERS
// ======================================

submitButton.addEventListener("click", submitPrompt);


// ======================================
// INITIAL DASHBOARD LOAD
// ======================================

loadDashboardData();