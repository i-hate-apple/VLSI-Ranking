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

// Test
const facultyData = [
  { trend: [{ year: 2021, count: 1.5 }, { year: 2022, count: 2.0 }] },
  { trend: [{ year: 2022, count: 1.0 }, { year: 2023, count: 3.5 }] },
  { trend: [] }
];

const result = aggregateInstitutionTrend(facultyData);
console.assert(result.length === 3, "Expected 3 years");
console.assert(result[0].year === 2021 && result[0].count === 1.5, "2021 failed");
console.assert(result[1].year === 2022 && result[1].count === 3.0, "2022 failed");
console.assert(result[2].year === 2023 && result[2].count === 3.5, "2023 failed");

console.log("Institution aggregation tests passed!");
