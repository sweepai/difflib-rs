use pyo3::prelude::*;
use std::collections::{HashMap, VecDeque};

#[derive(Debug, Clone)]
struct OpCode {
    tag: String,
    i1: usize,
    i2: usize,
    j1: usize,
    j2: usize,
}

struct SequenceMatcher<'a> {
    a: &'a [String],
    b: &'a [String],
    b2j: HashMap<&'a str, Vec<usize>>,
    matching_blocks: Option<Vec<(usize, usize, usize)>>,
    opcodes: Option<Vec<OpCode>>,
}

impl<'a> SequenceMatcher<'a> {
    fn new(a: &'a [String], b: &'a [String]) -> Self {
        let mut matcher = Self {
            a,
            b: &[],
            b2j: HashMap::new(),
            matching_blocks: None,
            opcodes: None,
        };
        matcher.set_seq2(b);
        matcher
    }
    
    fn set_seq2(&mut self, b: &'a [String]) {
        if self.b.as_ptr() == b.as_ptr() && self.b.len() == b.len() {
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
            self.b2j.entry(elt.as_str()).or_insert_with(Vec::new).push(i);
        }
        
        // Apply popularity heuristic like Python's difflib
        // Remove elements that appear too frequently (> 1% of total)
        let n = b.len();
        if n >= 200 {
            let ntest = n / 100 + 1;
            let mut popular_elements = Vec::new();
            
            for (&elt, indices) in &self.b2j {
                if indices.len() > ntest {
                    popular_elements.push(elt);
                }
            }
            
            for elt in popular_elements {
                self.b2j.remove(elt);
            }
        }
    }

    fn get_grouped_opcodes(&self, n: usize) -> Vec<Vec<OpCode>> {
        let mut codes = self.get_opcodes();
        if codes.is_empty() {
            return Vec::new();
        }
        
        // Special case: only equal operations (no changes)
        if codes.len() == 1 && codes[0].tag == "equal" {
            return Vec::new();
        }
        
        // Fixup leading and trailing groups if they show no changes
        // This matches Python's behavior to limit context lines
        if !codes.is_empty() && codes[0].tag == "equal" {
            let first = &mut codes[0];
            first.i1 = first.i2.saturating_sub(n);
            first.j1 = first.j2.saturating_sub(n);
        }
        
        if !codes.is_empty() && codes[codes.len() - 1].tag == "equal" {
            let last_idx = codes.len() - 1;
            let last = &mut codes[last_idx];
            last.i2 = (last.i1 + n).min(last.i2);
            last.j2 = (last.j1 + n).min(last.j2);
        }
        
        let mut groups: Vec<Vec<OpCode>> = Vec::new();
        let mut group: Vec<OpCode> = Vec::new();
        let nn = 2 * n;

        for code in codes.drain(..) {
            // Handle n == 0 case: split on any equal operations
            if n == 0 {
                if code.tag == "equal" && code.i2 > code.i1 {
                    if !group.is_empty() {
                        groups.push(std::mem::take(&mut group));
                    }
                    continue;
                }
                group.push(code);
            }
            // Handle n > 0 case: split on large equal operations
            else if code.tag == "equal" && code.i2 - code.i1 > nn {
                // End current group with trailing context
                if !group.is_empty() {
                    group.push(OpCode {
                        tag: "equal".to_string(),
                        i1: code.i1,
                        i2: (code.i1 + n).min(code.i2),
                        j1: code.j1,
                        j2: (code.j1 + n).min(code.j2),
                    });
                    groups.push(std::mem::take(&mut group));
                }
                // Start new group with leading context
                group.push(OpCode {
                    tag: "equal".to_string(),
                    i1: code.i2.saturating_sub(n).max(code.i1),
                    i2: code.i2,
                    j1: code.j2.saturating_sub(n).max(code.j1),
                    j2: code.j2,
                });
            } else {
                group.push(code);
            }
        }
        
        // Add final group if it exists and isn't just an equal operation
        if !group.is_empty() && !(group.len() == 1 && group[0].tag == "equal") {
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
        // Use queue-based approach like Python for better performance
        
        // Fast path for identical sequences
        if self.a.len() == self.b.len() {
            let mut all_equal = true;
            for i in 0..self.a.len() {
                if self.a[i] != self.b[i] {
                    all_equal = false;
                    break;
                }
            }
            if all_equal {
                return vec![(0, 0, self.a.len()), (self.a.len(), self.b.len(), 0)];
            }
        }
        
        let mut matches: Vec<(usize, usize, usize)> = Vec::new();
        // Use queue instead of stack like Python's implementation
        let mut queue: VecDeque<(usize, usize, usize, usize)> = VecDeque::new();
        queue.push_back((0, self.a.len(), 0, self.b.len()));

        while let Some((alo, ahi, blo, bhi)) = queue.pop_front() {
            let (i, j, k) = self.find_longest_match(alo, ahi, blo, bhi);
            
            // If we found a match, add it and queue the surrounding regions
            if k > 0 {
                matches.push((i, j, k));
                if alo < i && blo < j {
                    queue.push_back((alo, i, blo, j));
                }
                if i + k < ahi && j + k < bhi {
                    queue.push_back((i + k, ahi, j + k, bhi));
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
        // Use HashMap for sparse representation like Python - CRITICAL for performance with small changes
        
        let mut besti = alo;
        let mut bestj = blo;
        let mut bestsize = 0;
        
        // Use HashMap like Python for sparse representation - only stores non-zero values
        let mut j2len: HashMap<usize, usize> = HashMap::new();
        
        for i in alo..ahi {
            let mut newj2len: HashMap<usize, usize> = HashMap::new();
            
            // Get all positions where a[i] appears in b (like Python's b2j.get())
            if let Some(indices) = self.b2j.get(self.a[i].as_str()) {
                for &j in indices {
                    // Bounds check - exactly like Python
                    if j < blo {
                        continue;
                    }
                    if j >= bhi {
                        break;
                    }
                    
                    // k = length of longest match ending at (i-1, j-1)
                    // Use sparse lookup - only non-zero values are stored
                    let k = if j > 0 { 
                        j2len.get(&(j - 1)).copied().unwrap_or(0) 
                    } else { 
                        0 
                    };
                    
                    // Extend match by 1
                    let newk = k + 1;
                    newj2len.insert(j, newk);
                    
                    // Track best match found so far
                    if newk > bestsize {
                        besti = i + 1 - newk;
                        bestj = j + 1 - newk;
                        bestsize = newk;
                    }
                }
            }
            
            // Move instead of swap - more efficient for HashMap
            j2len = newj2len;
        }
        
        // Extend the best match as far as possible in both directions
        // This handles the case where the match can be extended beyond
        // the initial finding (important for correctness)
        
        // Extend backwards
        while besti > alo && bestj > blo && self.a[besti - 1] == self.b[bestj - 1] {
            besti -= 1;
            bestj -= 1;
            bestsize += 1;
        }
        
        // Extend forwards
        while besti + bestsize < ahi && bestj + bestsize < bhi && self.a[besti + bestsize] == self.b[bestj + bestsize] {
            bestsize += 1;
        }
        
        (besti, bestj, bestsize)
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
    
    let matcher = SequenceMatcher::new(&a, &b);
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