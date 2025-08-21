use pyo3::prelude::*;
use std::collections::HashMap;

#[derive(Debug, Clone)]
struct OpCode {
    tag: String,
    i1: usize,
    i2: usize,
    j1: usize,
    j2: usize,
}

struct SequenceMatcher {
    a: Vec<String>,
    b: Vec<String>,
    b2j: HashMap<String, Vec<usize>>,
    matching_blocks: Option<Vec<(usize, usize, usize)>>,
    opcodes: Option<Vec<OpCode>>,
}

impl SequenceMatcher {
    fn new(a: Vec<String>, b: Vec<String>) -> Self {
        let mut matcher = Self {
            a,
            b: Vec::new(),
            b2j: HashMap::new(),
            matching_blocks: None,
            opcodes: None,
        };
        matcher.set_seq2(b);
        matcher
    }
    
    fn set_seq2(&mut self, b: Vec<String>) {
        if self.b == b {
            return;
        }
        self.b = b;
        self.matching_blocks = None;
        self.opcodes = None;
        self.chain_b();
    }
    
    fn chain_b(&mut self) {
        let b = &self.b;
        self.b2j.clear();
        
        // Build b2j mapping like Python's difflib
        for (i, elt) in b.iter().enumerate() {
            self.b2j.entry(elt.clone()).or_insert_with(Vec::new).push(i);
        }
        
        // Apply popularity heuristic like Python's difflib
        // Remove elements that appear too frequently (> 1% of total)
        let n = b.len();
        if n >= 200 {
            let ntest = n / 100 + 1;
            let mut popular_elements = Vec::new();
            
            for (elt, indices) in &self.b2j {
                if indices.len() > ntest {
                    popular_elements.push(elt.clone());
                }
            }
            
            for elt in popular_elements {
                self.b2j.remove(&elt);
            }
        }
    }

    fn get_grouped_opcodes(&self, n: usize) -> Vec<Vec<OpCode>> {
        let mut codes = self.get_opcodes();
        if codes.is_empty() {
            return Vec::new();
        }
        if codes.len() == 1 && codes[0].tag == "equal" {
            return Vec::new();
        }
        let mut groups: Vec<Vec<OpCode>> = Vec::new();
        let mut group: Vec<OpCode> = Vec::new();

        if n == 0 {
            for code in codes.drain(..) {
                if code.tag == "equal" && code.i2 > code.i1 {
                    if !group.is_empty() {
                        groups.push(std::mem::take(&mut group));
                    }
                    continue;
                }
                group.push(code);
            }
            if !group.is_empty() {
                groups.push(group);
            }
            return groups;
        }

        for code in codes.drain(..) {
            if code.tag == "equal" && code.i2 - code.i1 > 2 * n {
                if !group.is_empty() {
                    group.push(OpCode {
                        tag: "equal".to_string(),
                        i1: code.i1,
                        i2: code.i1 + n,
                        j1: code.j1,
                        j2: code.j1 + n,
                    });
                    groups.push(std::mem::take(&mut group));
                }
                group.push(OpCode {
                    tag: "equal".to_string(),
                    i1: code.i2 - n,
                    i2: code.i2,
                    j1: code.j2 - n,
                    j2: code.j2,
                });
            } else {
                group.push(code);
            }
        }
        if !group.is_empty() {
            groups.push(group);
        }
        groups
    }

    fn get_opcodes(&self) -> Vec<OpCode> {
        let mut opcodes = Vec::new();
        let matches = self.get_matching_blocks();

        let mut i = 0usize;
        let mut j = 0usize;

        for (ai, bj, size) in matches {
            if i < ai && j < bj {
                opcodes.push(OpCode {
                    tag: "replace".to_string(),
                    i1: i,
                    i2: ai,
                    j1: j,
                    j2: bj,
                });
            } else if i < ai {
                opcodes.push(OpCode {
                    tag: "delete".to_string(),
                    i1: i,
                    i2: ai,
                    j1: j,
                    j2: j,
                });
            } else if j < bj {
                opcodes.push(OpCode {
                    tag: "insert".to_string(),
                    i1: i,
                    i2: i,
                    j1: j,
                    j2: bj,
                });
            }

            if size > 0 {
                opcodes.push(OpCode {
                    tag: "equal".to_string(),
                    i1: ai,
                    i2: ai + size,
                    j1: bj,
                    j2: bj + size,
                });
            }

            i = ai + size;
            j = bj + size;
        }

        opcodes
    }

    fn get_matching_blocks(&self) -> Vec<(usize, usize, usize)> {
        // Iterative implementation following Python's difflib algorithm
        let mut matches: Vec<(usize, usize, usize)> = Vec::new();
        let mut stack: Vec<(usize, usize, usize, usize)> = vec![(0, self.a.len(), 0, self.b.len())];

        while let Some((alo, ahi, blo, bhi)) = stack.pop() {
            let (i, j, k) = self.find_longest_match(alo, ahi, blo, bhi);
            if k > 0 {
                matches.push((i, j, k));
                if alo < i && blo < j {
                    stack.push((alo, i, blo, j));
                }
                if i + k < ahi && j + k < bhi {
                    stack.push((i + k, ahi, j + k, bhi));
                }
            }
        }

        // Sort by positions (i, j)
        matches.sort_unstable_by(|a, b| (a.0, a.1).cmp(&(b.0, b.1)));

        // Collapse adjacent matches
        let mut collapsed: Vec<(usize, usize, usize)> = Vec::new();
        for (i, j, k) in matches.into_iter() {
            if let Some(last) = collapsed.last_mut() {
                if last.0 + last.2 == i && last.1 + last.2 == j {
                    last.2 += k;
                    continue;
                }
            }
            collapsed.push((i, j, k));
        }

        // Add sentinel
        collapsed.push((self.a.len(), self.b.len(), 0));
        collapsed
    }

    fn find_longest_match(&self, alo: usize, ahi: usize, blo: usize, bhi: usize) -> (usize, usize, usize) {
        let mut best_i = alo;
        let mut best_j = blo;
        let mut best_size = 0;

        // Use the precomputed index for faster lookups
        let mut j2len: HashMap<usize, usize> = HashMap::new();

        for i in alo..ahi {
            let mut newj2len: HashMap<usize, usize> = HashMap::new();

            // Only check positions where this line actually appears in b
            if let Some(positions) = self.b2j.get(&self.a[i]) {
                for &j in positions {
                    if j < blo || j >= bhi {
                        continue;
                    }

                    let k = if j == 0 { 0 } else { *j2len.get(&(j - 1)).unwrap_or(&0) };
                    newj2len.insert(j, k + 1);
                    if k + 1 > best_size {
                        best_i = i - k;
                        best_j = j - k;
                        best_size = k + 1;
                    }
                }
            }
            j2len = newj2len;
        }

        // Extend the best match to include equal elements on both sides
        // (mirrors Python difflib behavior without isjunk)
        while best_i > alo && best_j > blo && self.a[best_i - 1] == self.b[best_j - 1] {
            best_i -= 1;
            best_j -= 1;
            best_size += 1;
        }
        while best_i + best_size < ahi
            && best_j + best_size < bhi
            && self.a[best_i + best_size] == self.b[best_j + best_size]
        {
            best_size += 1;
        }

        (best_i, best_j, best_size)
    }
    
    // Alternative implementation using a more efficient approach for small changes
    fn get_opcodes_efficient(&self) -> Vec<OpCode> {
        if self.a == self.b {
            if self.a.is_empty() {
                return Vec::new();
            }
            return vec![OpCode {
                tag: "equal".to_string(),
                i1: 0,
                i2: self.a.len(),
                j1: 0,
                j2: self.b.len(),
            }];
        }
        
        // For small changes in large files, use a more direct approach
        let mut opcodes = Vec::new();
        let mut i = 0;
        let mut j = 0;
        
        while i < self.a.len() && j < self.b.len() {
            if self.a[i] == self.b[j] {
                // Found a match, extend it
                let start_i = i;
                let start_j = j;
                while i < self.a.len() && j < self.b.len() && self.a[i] == self.b[j] {
                    i += 1;
                    j += 1;
                }
                opcodes.push(OpCode {
                    tag: "equal".to_string(),
                    i1: start_i,
                    i2: i,
                    j1: start_j,
                    j2: j,
                });
            } else {
                // Look ahead to find the next match
                let mut found_match = false;
                let mut next_i = i;
                let mut next_j = j;
                
                // Look for the next matching line within a reasonable window
                let window_size = 100.min(self.a.len() - i).min(self.b.len() - j);
                
                for di in 0..=window_size {
                    for dj in 0..=window_size {
                        if i + di < self.a.len() && j + dj < self.b.len() && self.a[i + di] == self.b[j + dj] {
                            next_i = i + di;
                            next_j = j + dj;
                            found_match = true;
                            break;
                        }
                    }
                    if found_match {
                        break;
                    }
                }
                
                if found_match {
                    // Determine the type of change
                    if next_i > i && next_j > j {
                        // Replace
                        opcodes.push(OpCode {
                            tag: "replace".to_string(),
                            i1: i,
                            i2: next_i,
                            j1: j,
                            j2: next_j,
                        });
                    } else if next_i > i {
                        // Delete
                        opcodes.push(OpCode {
                            tag: "delete".to_string(),
                            i1: i,
                            i2: next_i,
                            j1: j,
                            j2: j,
                        });
                    } else if next_j > j {
                        // Insert
                        opcodes.push(OpCode {
                            tag: "insert".to_string(),
                            i1: i,
                            i2: i,
                            j1: j,
                            j2: next_j,
                        });
                    }
                    i = next_i;
                    j = next_j;
                } else {
                    // No more matches, handle the rest
                    if i < self.a.len() && j < self.b.len() {
                        opcodes.push(OpCode {
                            tag: "replace".to_string(),
                            i1: i,
                            i2: self.a.len(),
                            j1: j,
                            j2: self.b.len(),
                        });
                    } else if i < self.a.len() {
                        opcodes.push(OpCode {
                            tag: "delete".to_string(),
                            i1: i,
                            i2: self.a.len(),
                            j1: j,
                            j2: j,
                        });
                    } else if j < self.b.len() {
                        opcodes.push(OpCode {
                            tag: "insert".to_string(),
                            i1: i,
                            i2: i,
                            j1: j,
                            j2: self.b.len(),
                        });
                    }
                    break;
                }
            }
        }
        
        // Handle remaining elements
        if i < self.a.len() {
            opcodes.push(OpCode {
                tag: "delete".to_string(),
                i1: i,
                i2: self.a.len(),
                j1: j,
                j2: j,
            });
        } else if j < self.b.len() {
            opcodes.push(OpCode {
                tag: "insert".to_string(),
                i1: i,
                i2: i,
                j1: j,
                j2: self.b.len(),
            });
        }
        
        opcodes
    }
}

fn format_range_unified(start: usize, stop: usize) -> String {
    let beginning = start + 1;
    let length = stop.saturating_sub(start);
    if length == 1 {
        format!("{}", beginning)
    } else if length == 0 {
        format!("{},0", start)
    } else {
        format!("{},{}", beginning, length)
    }
}

#[pyfunction]
#[pyo3(signature = (a, b, fromfile="", tofile="", fromfiledate="", tofiledate="", n=3, lineterm="\n"))]
fn unified_diff(
    a: Vec<String>,
    b: Vec<String>,
    fromfile: &str,
    tofile: &str,
    fromfiledate: &str,
    tofiledate: &str,
    n: usize,
    lineterm: &str,
) -> PyResult<Vec<String>> {
    // If sequences are identical, return empty result like Python's difflib
    if a == b {
        return Ok(Vec::new());
    }
    
    let mut result = Vec::new();
    let matcher = SequenceMatcher::new(a.clone(), b.clone());
    let groups = matcher.get_grouped_opcodes(n);

    // If no groups (no differences), return empty
    if groups.is_empty() {
        return Ok(Vec::new());
    }

    let mut started = false;

    for group in groups {
        if !started {
            started = true;
            let fromdate = if fromfiledate.is_empty() {
                String::new()
            } else {
                format!("\t{}", fromfiledate)
            };
            let todate = if tofiledate.is_empty() {
                String::new()
            } else {
                format!("\t{}", tofiledate)
            };

            result.push(format!("--- {}{}{}", fromfile, fromdate, lineterm));
            result.push(format!("+++ {}{}{}", tofile, todate, lineterm));
        }

        let first = &group[0];
        let last = &group[group.len() - 1];

        let file1_range = format_range_unified(first.i1, last.i2);
        let file2_range = format_range_unified(first.j1, last.j2);

        result.push(format!("@@ -{} +{} @@{}", file1_range, file2_range, lineterm));

        for opcode in group {
            match opcode.tag.as_str() {
                "equal" => {
                    for i in opcode.i1..opcode.i2 {
                        result.push(format!(" {}", a[i]));
                    }
                }
                "delete" | "replace" => {
                    for i in opcode.i1..opcode.i2 {
                        result.push(format!("-{}", a[i]));
                    }
                    if opcode.tag == "replace" {
                        for j in opcode.j1..opcode.j2 {
                            result.push(format!("+{}", b[j]));
                        }
                    }
                }
                "insert" => {
                    for j in opcode.j1..opcode.j2 {
                        result.push(format!("+{}", b[j]));
                    }
                }
                _ => {}
            }
        }
    }

    Ok(result)
}

#[pymodule]
fn difflib_rst(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(unified_diff, m)?)?;
    Ok(())
}