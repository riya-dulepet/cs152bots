# Human-AI Pipeline for Detecting Misogynistic Hate Speech via LLMs

**Group 19: Ramya Iyer, Riya Dulepet, Haley Lepe, Nubia Correa**  
**Department of Engineering**

## Overview

We implement an automated system to detect misogynistic hate speech in online platforms using LLMs. It aims to balance **user safety**, **freedom of expression**, and **global compliance** by accurately identifying hateful messages targeted at women.

## Problem Description

Online misogynistic hate speech is pervasive and harmful:

- **66%** of respondents report encountering hate speech frequently online.
- **73%** of Gen Z social media users have witnessed misogynistic content.
- **50%** encounter misogynistic content weekly.

The core challenge is to detect such content automatically and act promptly **without excessive censorship**.

## Policy Description

### Violation Criteria

Violations include, but are not limited to:

- Violent or criminal threats toward women
- Dehumanization or denial of rights
- Gendered slurs and severe harassment
- Negative stereotypes or dismissals
- Sexual objectification or humiliation
- Intersectional hate targeting multiple protected traits

### Moderation Actions

Based on severity, the system takes automated actions such as:

- Removing or graying-out content
- Warning or suspending users (Severity 1-2)
- Blacklisting malicious links or wallets (scam/fraud)
- Escalating Severity 3 cases to legal authorities
- Permanent bans after 3 rule violations (with human review)

## Dataset

We use the dataset **“An expert annotated dataset for the detection of online misogyny”** from the EACL 2021 conference, focusing on misogynistic speech types from **Reddit**.

## Technology Stack & Models

- **LLM Models:**
  - GPT-4o Mini (OpenAI)
  - Gemini 1.5 Flash (Google)
- **Prompt Engineering:**
  - _Long Prompt:_ Detailed policy + exhaustive rules + labeled data
  - _Short Prompt:_ Concise policy + flexible logic + no labeled data (LLM more openly decides labels)

## LLM Output Schema

- **label:** `MISOGYNISTIC` or `NON-MISOGYNISTIC`
- **category:** One of `VIOLENT`, `DEHUMANIZATION`, `HARASSMENT`, `STEREOTYPING`, `SEXUAL`, or `N/A`
- **confidence:** Model’s certainty score (0.50 - 1.00)
- **severity:** Harm level from 0 (none) to 4 (severe)

## Evaluation & Findings

- Short prompting achieves higher precision and consistent results.
- GPT-4o Mini demonstrated better precision (86%) than Gemini (70%) with 83% accuracy overall.
- Long prompts increase recall but risk over-censorship.
- Challenges include sarcasm detection, stylized Unicode, ASCII masking, and dogwhistles.
- The system balances false positives (over-flagging) and false negatives (missed content).

## Future Work

- User-facing transparency tools explaining moderation decisions
- Context-aware models incorporating thread history and user metadata
- Multimodal hate speech detection (images, audio, video) using multimodal LLMs

## References

- [1] Fleck, A. (2024). _2 in 3 people often encounter hate speech online_ [Statista].
- [2] Amnesty International UK. (2025). _Toxic tech: New polling exposes widespread online misogyny._

# Posters & Flows

## User Flow Diagram

![User Flow Diagram](assets/User%20Reporting%20Flow.png)

## Moderator Review Flow Diagram

![Moderator Review Flow Diagram](assets/Moderator%20Reporting%20Flow.png)

## CS 152 Final Poster

![CS 152 Final Poster](assets/CS%20152%20Final%20Poster.png)



## Final Demo Video

Our demo video walks through the functionality of our misogynistic hate speech detection pipeline and showcases the LLM evaluation setup.

[Click here to watch our demo video] (https://drive.google.com/file/d/1pipn2UOSM6vWb23GUn3rBcUKH0DxYFOw/view?usp=sharing)

