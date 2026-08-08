document.addEventListener('DOMContentLoaded', () => {
  let allData = null;

  // Utility for escaping HTML
  function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
  
  // Tab Switching Logic
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      
      e.target.classList.add('active');
      document.getElementById(`${e.target.dataset.tab}-tab`).classList.add('active');
    });
  });

  // Calculate Geometric Mean
  function calculateScore(facultyList, activeAreas) {
    if (activeAreas.length === 0) return 0;
    
    let totalAdjusted = activeAreas.reduce((acc, area) => {
      acc[area] = 0;
      return acc;
    }, {});

    facultyList.forEach(f => {
      activeAreas.forEach(area => {
        if (f.subareas[area]) {
          totalAdjusted[area] += f.subareas[area];
        }
      });
    });

    let product = 1.0;
    activeAreas.forEach(area => {
      product *= (totalAdjusted[area] + 1);
    });

    return Math.pow(product, 1 / activeAreas.length);
  }

  // Render Table
  function renderTable(data) {
    const activeAreas = Array.from(document.querySelectorAll('.area-filter:checked')).map(cb => cb.value);
    const searchQuery = document.getElementById('searchInput').value.toLowerCase();
    
    const tbody = document.getElementById('rankingBody');
    tbody.innerHTML = '';

    const scoredInstitutions = data.institutions.map(inst => {
      const score = calculateScore(inst.faculty, activeAreas);
      return { ...inst, score };
    }).filter(inst => {
      if (inst.score <= 1 && activeAreas.length > 0) return false; // Filter out zero-pubs
      if (searchQuery && !inst.name.toLowerCase().includes(searchQuery)) return false;
      return true;
    }).sort((a, b) => b.score - a.score);

    scoredInstitutions.forEach((inst, index) => {
      // Institution Row
      const tr = document.createElement('tr');
      tr.className = 'inst-row';
      tr.innerHTML = `
        <td>${index + 1}</td>
        <td><strong>${escapeHTML(inst.name)}</strong> <span>▶</span></td>
        <td>${(inst.score - 1).toFixed(2)}</td>
      `;
      
      // Faculty Drill-down Row
      const drillDownTr = document.createElement('tr');
      drillDownTr.className = 'faculty-row';
      
      const td = document.createElement('td');
      td.colSpan = 3;
      
      let facultyHtml = '';
      inst.faculty.forEach(f => {
        // Calculate faculty's individual score for sorting within institution
        let fScore = calculateScore([f], activeAreas);
        if (fScore > 1) {
          facultyHtml += `
            <div class="faculty-card">
              <h4>${escapeHTML(f.name)}</h4>
              <p>Score: ${(fScore - 1).toFixed(2)}</p>
              <a href="${escapeHTML(f.links.homepage)}" target="_blank">Homepage</a>
            </div>
          `;
        }
      });
      
      td.innerHTML = facultyHtml || '<p>No matching faculty.</p>';
      drillDownTr.appendChild(td);
      
      // Toggle expansion
      tr.addEventListener('click', () => {
        drillDownTr.classList.toggle('expanded');
        const arrow = tr.querySelector('span');
        arrow.textContent = drillDownTr.classList.contains('expanded') ? '▼' : '▶';
      });

      tbody.appendChild(tr);
      tbody.appendChild(drillDownTr);
    });
  }

  // Render Programs
  function renderPrograms(programs) {
    const searchQuery = document.getElementById('searchInput').value.toLowerCase();
    const container = document.getElementById('programsContainer');
    container.innerHTML = '';
    
    Object.values(programs).filter(prog => {
      if (searchQuery && !prog.institution.toLowerCase().includes(searchQuery)) return false;
      return true;
    }).forEach(prog => {
      const card = document.createElement('div');
      card.className = 'program-card';
      card.innerHTML = `
        <h3>${escapeHTML(prog.institution)}</h3>
        <p><strong>Degree:</strong> ${escapeHTML(prog.degree_type || 'N/A')}</p>
        <p><strong>Funding:</strong> ${escapeHTML(prog.funding_model || 'N/A')}</p>
        <a href="${escapeHTML(prog.program_homepage)}" target="_blank" class="program-link">Program Website <span>&rarr;</span></a>
      `;
      container.appendChild(card);
    });
  }

  // Initial Load
  fetch('data.json')
    .then(response => response.json())
    .then(data => {
      allData = data;
      renderTable(allData);
      renderPrograms(allData.programs);
    })
    .catch(error => {
      console.error('Error loading data:', error);
      document.querySelector('.content').innerHTML = '<p style="text-align:center; padding: 2rem;">Error loading ranking data. Please check data.json exists and is valid.</p>';
    });

  // Setup Event Listeners for Filters
  document.querySelectorAll('.area-filter').forEach(cb => {
    cb.addEventListener('change', () => renderTable(allData));
  });
  document.getElementById('searchInput').addEventListener('input', () => {
    renderTable(allData);
    renderPrograms(allData.programs);
  });
});
