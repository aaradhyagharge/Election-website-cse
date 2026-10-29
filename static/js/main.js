// Election Candidate Smart Declaration Portal JavaScript

document.addEventListener('DOMContentLoaded', function () {
    initSmartCalculator();
    initProposersLogic();
    initDobAgeCalculator();
    initElectionConstituencyFilter();
});

/**
 * 1. Smart Asset & Liability Live Calculator
 * Calculates totals for Movable, Immovable, Liabilities and Net Worth in real-time.
 */
function initSmartCalculator() {
    const movableInputs = [
        'movable_cash', 'movable_bank_deposits', 'movable_bonds_shares',
        'movable_vehicles', 'movable_jewellery', 'movable_other'
    ];

    const immovableInputs = [
        'immovable_agricultural', 'immovable_non_agricultural',
        'immovable_commercial', 'immovable_residential', 'immovable_other'
    ];

    const liabilityInputs = [
        'liabilities_bank_loans', 'liabilities_govt_dues', 'liabilities_other'
    ];

    function formatCurrency(num) {
        return '₹ ' + Number(num || 0).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function calculateSection(inputs, totalDisplayId) {
        let sum = 0;
        inputs.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                const val = parseFloat(el.value) || 0;
                sum += val;
            }
        });
        const displayEl = document.getElementById(totalDisplayId);
        if (displayEl) {
            displayEl.textContent = formatCurrency(sum);
        }
        return sum;
    }

    function updateAllTotals() {
        const totalMovable = calculateSection(movableInputs, 'total_movable_display');
        const totalImmovable = calculateSection(immovableInputs, 'total_immovable_display');
        const totalLiabilities = calculateSection(liabilityInputs, 'total_liabilities_display');

        const netWorth = (totalMovable + totalImmovable) - totalLiabilities;
        const netWorthEl = document.getElementById('net_worth_display');
        if (netWorthEl) {
            netWorthEl.textContent = formatCurrency(netWorth);
            if (netWorth < 0) {
                netWorthEl.style.color = '#dc2626';
            } else {
                netWorthEl.style.color = '#15803d';
            }
        }
    }

    // Attach listener to all asset & liability inputs
    const allInputIds = [...movableInputs, ...immovableInputs, ...liabilityInputs];
    allInputIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', updateAllTotals);
        }
    });

    // Initial calculation on load
    updateAllTotals();
}

/**
 * 2. Dynamic Proposers Table Logic
 * Toggles between 1 proposer (for recognized political parties)
 * and 10 proposers (for independent candidates) under Representation of the People Act, 1951.
 */
function initProposersLogic() {
    const partyTypeSelect = document.getElementById('party_type');
    const proposersContainer = document.getElementById('proposers_rows_container');
    const proposersNotice = document.getElementById('proposers_notice');

    if (!partyTypeSelect || !proposersContainer) return;

    function adjustProposerRows() {
        const partyType = partyTypeSelect.value;
        const isRecognized = (partyType === 'recognized_national' || partyType === 'recognized_state');
        const requiredCount = isRecognized ? 1 : 10;

        if (proposersNotice) {
            if (isRecognized) {
                proposersNotice.innerHTML = `<strong>Statutory Rule:</strong> As a candidate set up by a recognized party, <strong>1 elector proposer</strong> is required under Sec 33 of RPA 1951.`;
                proposersNotice.className = 'alert alert-info';
            } else {
                proposersNotice.innerHTML = `<strong>Statutory Rule:</strong> As an Independent / Unrecognized candidate, <strong>10 elector proposers</strong> subscribed from the constituency are required under Sec 33 of RPA 1951.`;
                proposersNotice.className = 'alert alert-warning';
            }
        }

        const existingRows = proposersContainer.querySelectorAll('.proposer-row');
        const currentCount = existingRows.length;

        if (requiredCount > currentCount) {
            for (let i = currentCount + 1; i <= requiredCount; i++) {
                const tr = document.createElement('tr');
                tr.className = 'proposer-row';
                tr.innerHTML = `
                    <td style="text-align:center; font-weight:bold;">${i}</td>
                    <td><input type="text" name="prop_name[]" class="form-control" placeholder="Proposer Full Name" required></td>
                    <td><input type="text" name="prop_epic[]" class="form-control" placeholder="EPIC / Voter ID No" required></td>
                    <td><input type="text" name="prop_part[]" class="form-control" placeholder="Electoral Part No" required></td>
                    <td><input type="text" name="prop_serial[]" class="form-control" placeholder="Serial No" required></td>
                `;
                proposersContainer.appendChild(tr);
            }
        } else if (requiredCount < currentCount) {
            // Keep rows up to requiredCount
            for (let i = currentCount - 1; i >= requiredCount; i--) {
                existingRows[i].remove();
            }
        }
    }

    partyTypeSelect.addEventListener('change', adjustProposerRows);
}

/**
 * 3. Date of Birth -> Age Calculator & Validation
 */
function initDobAgeCalculator() {
    const dobInput = document.getElementById('date_of_birth');
    const ageInput = document.getElementById('calculated_age');
    const ageWarning = document.getElementById('age_warning');

    if (!dobInput || !ageInput) return;

    function calcAge() {
        if (!dobInput.value) return;
        const dob = new Date(dobInput.value);
        const today = new Date();
        let age = today.getFullYear() - dob.getFullYear();
        const m = today.getMonth() - dob.getMonth();
        if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
            age--;
        }
        ageInput.value = age + ' years';

        const minAge = parseInt(ageInput.getAttribute('data-min-age')) || 25;
        if (age < minAge) {
            if (ageWarning) {
                ageWarning.style.display = 'block';
                ageWarning.textContent = `Warning: Calculated age is ${age} years. The minimum required age for this election category is ${minAge} years.`;
            }
        } else {
            if (ageWarning) ageWarning.style.display = 'none';
        }
    }

    dobInput.addEventListener('change', calcAge);
    calcAge();
}

/**
 * 4. Dynamic Constituency Dropdown on Election Selection
 */
function initElectionConstituencyFilter() {
    const electionSelect = document.getElementById('election_select');
    const constituencySelect = document.getElementById('constituency_select');

    if (!electionSelect || !constituencySelect) return;

    electionSelect.addEventListener('change', function () {
        const electionId = this.value;
        if (!electionId) {
            constituencySelect.innerHTML = '<option value="">-- First Select an Election --</option>';
            return;
        }

        constituencySelect.innerHTML = '<option value="">Loading constituencies...</option>';

        fetch(`/api/constituencies/${electionId}`)
            .then(res => res.json())
            .then(data => {
                let options = '<option value="">-- Select Assigned Constituency --</option>';
                data.forEach(c => {
                    options += `<option value="${c.id}">${c.name} (${c.state}) - ${c.type}</option>`;
                });
                constituencySelect.innerHTML = options;
            })
            .catch(err => {
                console.error("Error fetching constituencies:", err);
                constituencySelect.innerHTML = '<option value="">Failed to load constituencies</option>';
            });
    });
}

