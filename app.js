document.addEventListener('DOMContentLoaded', () => {
  let allData = null;

  // Theme Toggle Logic
  const themeToggle = document.getElementById('themeToggle');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && prefersDark)) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }

  themeToggle.addEventListener('click', () => {
    let currentTheme = document.documentElement.getAttribute('data-theme');
    let newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  });

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

  // Aggregate Institution Trend
  function aggregateInstitutionTrend(facultyList) {
    const aggregated = {};
    
    facultyList.forEach(f => {
      (f.trend || []).forEach(t => {
        if (!aggregated[t.year]) {
          aggregated[t.year] = 0;
        }
        aggregated[t.year] += t.count;
      });
    });

    return Object.keys(aggregated).map(year => ({
      year: parseInt(year),
      count: aggregated[year]
    })).sort((a, b) => a.year - b.year);
  }

  // Draw Sparkline
  function drawSparkline(containerElement, trendData) {
    d3.select(containerElement).selectAll('*').remove();

    if (!trendData || trendData.length < 2) return; // need at least 2 points for a line

    const width = 100;
    const height = 30;
    const margin = { top: 2, right: 2, bottom: 2, left: 2 };

    const svg = d3.select(containerElement)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const x = d3.scaleLinear()
      .domain(d3.extent(trendData, d => d.year))
      .range([margin.left, width - margin.right]);

    const y = d3.scaleLinear()
      .domain([0, d3.max(trendData, d => d.count)])
      .range([height - margin.bottom, margin.top]);

    const line = d3.line()
      .x(d => x(d.year))
      .y(d => y(d.count))
      .curve(d3.curveMonotoneX);

    const area = d3.area()
      .x(d => x(d.year))
      .y0(height - margin.bottom)
      .y1(d => y(d.count))
      .curve(d3.curveMonotoneX);

    const defs = svg.append('defs');
    const gradient = defs.append('linearGradient')
      .attr('id', 'sparkline-gradient')
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%');
    
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', 'var(--primary-color)')
      .attr('stop-opacity', 0.4);
      
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', 'var(--primary-color)')
      .attr('stop-opacity', 0);

    svg.append('path')
      .datum(trendData)
      .attr('fill', 'url(#sparkline-gradient)')
      .attr('d', area);

    svg.append('path')
      .datum(trendData)
      .attr('fill', 'none')
      .attr('stroke', 'var(--primary-color)')
      .attr('stroke-width', 2)
      .attr('d', line);
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
      const instTrend = aggregateInstitutionTrend(inst.faculty);
      
      // Institution Row
      const tr = document.createElement('tr');
      tr.className = 'inst-row';
      tr.innerHTML = `
        <td>${index + 1}</td>
        <td><strong>${escapeHTML(inst.name)}</strong> <span>▶</span></td>
        <td><div class="sparkline-container" id="sparkline-inst-${index}"></div></td>
        <td>${(inst.score - 1).toFixed(2)}</td>
      `;
      
      // Faculty Drill-down Row
      const drillDownTr = document.createElement('tr');
      drillDownTr.className = 'faculty-row';
      
      const td = document.createElement('td');
      td.colSpan = 3;
      
      let facultyHtml = '';
      const validFaculty = [];
      inst.faculty.forEach((f, fIdx) => {
        // Calculate faculty's individual score for sorting within institution
        let fScore = calculateScore([f], activeAreas);
        if (fScore > 1) {
          validFaculty.push({ f, fScore, fIdx });
        }
      });

      // Sort faculty by score within institution
      validFaculty.sort((a, b) => b.fScore - a.fScore);

      validFaculty.forEach(({ f, fScore, fIdx }) => {
        facultyHtml += `
          <div class="faculty-card">
            <h4>${escapeHTML(f.name)}</h4>
            <div class="sparkline-container" id="sparkline-fac-${index}-${fIdx}"></div>
            <p>Score: ${(fScore - 1).toFixed(2)}</p>
            <a href="${escapeHTML(f.links.homepage)}" target="_blank">Homepage</a>
          </div>
        `;
      });
      
      td.innerHTML = facultyHtml ? `<div>${facultyHtml}</div>` : '<p>No matching faculty.</p>';
      drillDownTr.appendChild(td);
      
      // Toggle expansion
      tr.addEventListener('click', () => {
        drillDownTr.classList.toggle('expanded');
        const arrow = tr.querySelector('span');
        arrow.textContent = drillDownTr.classList.contains('expanded') ? '▼' : '▶';
        
        // Draw faculty sparklines only when expanded to save initial rendering time
        if (drillDownTr.classList.contains('expanded')) {
          validFaculty.forEach(({ f, fIdx }) => {
            const container = document.getElementById(`sparkline-fac-${index}-${fIdx}`);
            if (container) drawSparkline(container, f.trend);
          });
        }
      });

      tbody.appendChild(tr);
      tbody.appendChild(drillDownTr);

      // Draw institution sparkline
      const instContainer = document.getElementById(`sparkline-inst-${index}`);
      if (instContainer) drawSparkline(instContainer, instTrend);
    });
  }

  // Initial Load
  fetch('data.json')
    .then(response => response.json())
    .then(data => {
      allData = data;
      renderTable(allData);
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
  });
});
