

---
name: bug_hunter
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers: bug_hunt, resource_check
---

# Bug Hunter Microagent

## Description
This microagent is designed to perform read-only tasks such as hunting for possible bugs and excessive resource usage in the codebase.

## Usage
- **Trigger Words**: `bug_hunt`, `resource_check`
- **Functionality**: The microagent will analyze the codebase to identify potential bugs and areas of excessive resource usage.

## Instructions
1. **Bug Hunting**: The microagent will scan the codebase for common coding errors, such as null pointer exceptions, infinite loops, and memory leaks.
2. **Resource Usage**: The microagent will evaluate the code for inefficient resource usage, such as excessive memory allocation, CPU-intensive operations, and unnecessary database queries.

## Limitations
- This microagent is read-only and will not make any changes to the codebase.
- It is designed to identify potential issues but does not automatically fix them.

## Examples
- **Bug Hunting**: "Please bug_hunt the codebase for any potential issues."
- **Resource Usage**: "Please resource_check the codebase for excessive resource usage."

