# AI Workflow Agent Platform

## Overview

A multi-agent system that executes structured workflows using LLMs.

## Agents

### Planner

- Breaks user input into steps
- Output: list of steps (JSON)

### Executor

- Chooses whether to answer directly or use a tool for each step
- Available tools: web search, calculator, and current date/time
- Returns step output plus structured tool metadata for traces and analytics

### Reviewer

- Validates and improves final output

## Flow

User Input → Planner → Executor (per step, with tool selection) → Reviewer → Final Output

## Tech Stack

- Backend: Python, FastAPI, LangChain
- Frontend: React, TypeScript
- Infra: Docker (later)
