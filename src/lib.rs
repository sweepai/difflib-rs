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
}

impl SequenceMatcher {
    fn new(a: Vec<String>, b: Vec<String>) -> Self {
        Self { a, b }
    }

    fn get_grouped_opcodes(&self, n: usize) -> Vec<Vec<OpCode>> {
        let opcodes = self.get_opcodes();
        if opcodes.is_empty() {
            return Vec::new();
        }
        
        // Filter out pure equal opcodes if they're the only ones
        let has_changes = opcodes.iter().any(|op| op.tag != "equal");
        if !has_changes {
            return Vec::new();
        }
        
        let mut groups = Vec::new();
        let mut group = Vec::new();
        
        for opcode in opcodes {
            if opcode.tag == "equal" && opcode.i2 - opcode.i1 > 2 * n {
                // Large equal block, split it
                if !group.is_empty() {
                    // Add context to end of current group
                    if opcode.i2 - opcode.i1 > n {
                        group.push(OpCode {
                            tag: "equal".to_string(),
                            i1: opcode.i1,
                            i2: opcode.i1 + n,
                            j1: opcode.j1,
                            j2: opcode.j1 + n,
                        });
                    } else {
                        group.push(opcode.clone());
                    }
                    groups.push(group);
                    group = Vec::new();
                }
                
                // Start new group with context
                if opcode.i2 - opcode.i1 > n {
                    group.push(OpCode {
                        tag: "equal".to_string(),
                        i1: opcode.i2 - n,
                        i2: opcode.i2,
                        j1: opcode.j2 - n,
                        j2: opcode.j2,
                    });
                }
            } else {
                group.push(opcode);
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
        
        let mut i = 0;
        let mut j = 0;
        
        for (ai, bj, size) in matches {
            // Handle deletions and insertions before this match
            if i < ai && j < bj {
                // Replace
                opcodes.push(OpCode {
                    tag: "replace".to_string(),
                    i1: i,
                    i2: ai,
                    j1: j,
                    j2: bj,
                });
            } else if i < ai {
                // Delete
                opcodes.push(OpCode {
                    tag: "delete".to_string(),
                    i1: i,
                    i2: ai,
                    j1: j,
                    j2: j,
                });
            } else if j < bj {
                // Insert
                opcodes.push(OpCode {
                    tag: "insert".to_string(),
                    i1: i,
                    i2: i,
                    j1: j,
                    j2: bj,
                });
            }
            
            // Handle the matching block
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
        // If sequences are identical, return one big match
        if self.a == self.b {
            if self.a.is_empty() {
                return vec![(0, 0, 0)];
            } else {
                return vec![(0, 0, self.a.len()), (self.a.len(), self.b.len(), 0)];
            }
        }
        
        let mut matches = Vec::new();
        let mut queue = vec![(0, self.a.len(), 0, self.b.len())];
        
        while let Some((alo, ahi, blo, bhi)) = queue.pop() {
            let (i, j, k) = self.find_longest_match(alo, ahi, blo, bhi);
            if k > 0 {
                matches.push((i, j, k));
                if alo < i && blo < j {
                    queue.push((alo, i, blo, j));
                }
                if i + k < ahi && j + k < bhi {
                    queue.push((i + k, ahi, j + k, bhi));
                }
            }
        }
        
        matches.sort();
        
        // Add sentinel
        matches.push((self.a.len(), self.b.len(), 0));
        
        matches
    }

    fn find_longest_match(&self, alo: usize, ahi: usize, blo: usize, bhi: usize) -> (usize, usize, usize) {
        let mut best_i = alo;
        let mut best_j = blo;
        let mut best_size = 0;
        
        let mut j2len: HashMap<usize, usize> = HashMap::new();
        
        for i in alo..ahi {
            let mut newj2len: HashMap<usize, usize> = HashMap::new();
            for j in blo..bhi {
                if self.a[i] == self.b[j] {
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
        
        (best_i, best_j, best_size)
    }
}

fn format_range_unified(start: usize, length: usize) -> String {
    if length == 1 {
        format!("{}", start + 1)
    } else if length == 0 {
        format!("{}", start)
    } else {
        format!("{},{}", start + 1, length)
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

        let file1_range = format_range_unified(first.i1, last.i2 - first.i1);
        let file2_range = format_range_unified(first.j1, last.j2 - first.j1);

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