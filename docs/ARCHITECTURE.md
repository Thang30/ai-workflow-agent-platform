# AI Workflow Agent Platform

## Overview

A multi-agent system that executes structured workflows using LLMs.

## Agents

### Planner
- Breaks user input into steps
- Output: list of steps (JSON)

### Executor
- Executes each step using tools
- Returns result

### Reviewer
- Validates and improves final output

## Flow

User Input → Planner → Executor (per step) → Reviewer → Final Output

## Tech Stack

- Backend: Python, FastAPI, LangChain
- Frontend: React, TypeScript
- Infra: Docker (later)