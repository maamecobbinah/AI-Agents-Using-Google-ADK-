# Inspiration Agents with Google ADK

This repository gives an overview of how to build **simple agents** using the **Google Agent Development Kit (ADK)**.

For ADK samples, see: [Google ADK Samples](https://github.com/google/adk-samples/tree/main)

---

## Prerequisites
- Python 3.9+
- Google Cloud API Key (free tier supported)

---

## What is Google ADK?

**Google Agent Development Kit (ADK)** is a framework that simplifies the creation and deployment of AI agents.  
It allows agents to interact with tools, process data (text, audio, files, video), and use advanced AI models from Google and third parties.

---

## Types of Agents in ADK

- **Single Agent:** Handles all tasks in one model. Ideal for simple queries or reporting tasks.  
- **Sequential Agent:** Breaks tasks into steps (e.g., extract → transform → visualize).  
- **Parallel Agent:** Executes multiple tasks concurrently (e.g., fetch from multiple sources).  
- **Hierarchical Agent:** Routes tasks based on intent to specialized sub-agents.  
- **Loop Agent:** Repeats tasks for iterative refinement or validation.  
- **Cooperative Multi-Agent:** Multiple agents collaborate (e.g., one prepares data, another analyzes).  
- **Competitive Multi-Agent:** Agents propose solutions and the best is selected.

---

## Agent Callbacks in ADK

Callbacks allow you to **manage agent state, modify variables, and control behavior** at key points:

- **Managing State:** Read or update session state before the agent runs.  
- **Before Model Callback:** Preprocessing, caching, or tool preparation.  
- **After Model Callback:** Guardrails and output validation.

---

## MCP (Model Component Platform) Overview

**MCP** is a middleware platform that manages and connects AI agents to tools and prompts efficiently.  
It acts as a central server, allowing agents to share tools and prompts, reducing duplication and making scaling easier.

---

## Prototype: Socratic Science Storyteller Agent

This repository also contains a **prototype educational agent**: the **Socratic Science Storyteller**.

The agent helps **children and young learners** explore topics in **science, technology, and medicine** through:
- Interactive storytelling
- Socratic questioning
- Curiosity-driven explanations

Rather than giving direct answers, the agent **guides learning through questions, narratives, and age-appropriate explanations**, encouraging critical thinking and discovery.

---

### What the Agent Does

Given:
- A topic (e.g., *space*, *the human heart*, *robots*)  
- An optional age range

The agent will:

1. Retrieve trusted educational information (e.g., NASA, public science sources)  
2. Frame the topic as a short story or scenario  
3. Ask guiding Socratic questions  
4. Adapt explanations based on user responses  
5. Keep content age-appropriate  
6. Block or redirect non-educational or explicit topics

---


### Example Interaction

> **Agent:**  
> “Imagine you are a tiny astronaut traveling inside a rocket…  
> What do you think keeps the rocket from falling back to Earth?”

> **Child:**  
> “Fire?”

> **Agent:**  
> “Great thought! What do you think the fire pushes against to lift the rocket up?”

---

### Agent Type

**Single Agent** – All reasoning, storytelling, questioning, and safety checks are handled by a single ADK agent, making the system simple and extensible.

---

### Guardrails & Safety Design

The agent ensures:
- Only responds to **educational topics**  
- Avoids explicit, harmful, or age-inappropriate content  
- Redirects unsafe prompts to safe alternatives  
- Uses trusted public educational sources

The agent does **not**:
- Provide medical advice  
- Generate explicit or violent content  
- Collect personal data  

---

### Project Structure

```text
.
├── agent.py            # Core Socratic storytelling agent
├── tools/              # Educational data source tools
├── prompts/            # System + safety + storytelling prompts
├── callbacks.py        # Guardrails and validation callbacks
├── README.md           # This documentation


