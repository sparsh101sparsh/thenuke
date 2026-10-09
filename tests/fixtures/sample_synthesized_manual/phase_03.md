# Phase 3: The Event Loop & Task Scheduling Hierarchy

Technically bolo toh jab runtime execute hota hai, sabse pehle memory heap aur execution stack initialize hota hai.
Dhayan se samjho: execution context lifecycle consists of Creation Phase and Execution Phase.

[MENTAL MODEL]
Think of the Call Stack as a strict LIFO container where each frame encapsulates local variables, this binding, and lexical environment record.

[INVARIANT]
JavaScript engine guarantees single-threaded synchronous execution inside the main execution thread.

[ENGINEERING GOTCHA]
Never block the Call Stack with synchronous CPU-intensive loops or synchronous file reads in production event loops.

[INTERVIEW TIP]
FAANG interviewers often evaluate if you can distinguish between VariableEnvironment and LexicalEnvironment in ES2024 spec.

<!-- DIAGRAM: call_stack {"diagram_type": "Event Loop", "frames": ["globalContext", "evaluatePipeline"]} -->

## Production Implementation Snippet
```javascript
const transactionRecords = [
  { transactionId: 'TX-101', status: 'settled', amount: 540.00 },
  { transactionId: 'TX-102', status: 'pending', amount: 120.50 },
  { transactionId: 'TX-103', status: 'settled', amount: 980.25 }
];

const groupedTransactions = Object.groupBy(transactionRecords, tx => tx.status);
// Output: { settled: [...], pending: [...] }

const { promise, resolve } = Promise.withResolvers();
resolve(groupedTransactions);
// Output: Promise { <fulfilled>: Object }
```

## Phase Challenges

### Challenge 1: Output Prediction
Predict the exact console output of the microtask ordering below:
```javascript
console.log('Checkpoint A'); // Output: Checkpoint A
queueMicrotask(() => console.log('Checkpoint B')); // Output: Checkpoint B
Promise.resolve().then(() => console.log('Checkpoint C')); // Output: Checkpoint C
console.log('Checkpoint D'); // Output: Checkpoint D
// Output: Checkpoint A
// Output: Checkpoint D
// Output: Checkpoint B
// Output: Checkpoint C
```

### Challenge 2: Algorithm Utility
Implement a zero-dependency LRU cache utility with O(1) time complexity constraints for get and put operations.

### Challenge 3: Industrial Mini-Project
Build an in-memory Rate Limiter token bucket component supporting burst capacity and concurrent request sliding windows.
