#!/usr/bin/env python3
"""
Reads the agent output files and assembles the OS manual content JSON.
This is a helper - the actual Notion fetching is done by the agents.
The content JSON is then fed into generate_os_manual.py.
"""

import json
import os
import re
import sys


def clean_notion_content(raw_text):
    """Extract clean content from Notion page fetch result."""
    # Extract content between <content> tags
    match = re.search(r'<content>\n?(.*?)\n?</content>', raw_text, re.DOTALL)
    if match:
        content = match.group(1)
    else:
        content = raw_text

    # Remove child page links (we handle them separately)
    content = re.sub(r'<page url="[^"]*">([^<]*)</page>', '', content)

    # Clean up Notion callout syntax
    content = content.replace('\\[!tip\\]', '[TIP]')
    content = content.replace('\\[!important\\]', '[IMPORTANT]')
    content = content.replace('\\[!warning\\]', '[WARNING]')
    content = content.replace('\\[!info\\]', '[INFO]')

    # Remove excessive blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()


# Structure definition: sections with their sub-page IDs and titles
SECTIONS = [
    {
        "number": 1,
        "title": "North Star & Vision",
        "icon": "🌟",
        "description": "Why we exist and where we're going. Rarely referenced daily, but foundational to every decision.",
        "sub_pages": [
            {"id": "32886897-dca2-81e4-9d72-e50a0e475c38", "title": "Life Vision Statement"},
            {"id": "32886897-dca2-81c1-82fe-d78935e4b45c", "title": "3-Year Business Vision"},
            {"id": "32886897-dca2-8174-b467-f8311daa7dc9", "title": "1-Year Business Vision (2026)"},
            {"id": "32886897-dca2-8156-83e6-e1ef08692158", "title": "Strategic Priorities (12-Month Focus)"},
            {"id": "32886897-dca2-818f-bbb3-c52d6c22edc9", "title": "Founder Intent"},
        ]
    },
    {
        "number": 2,
        "title": "How This OS Works",
        "icon": "📘",
        "description": "How the Agency OS is structured, how to use it daily, and the core rules that govern everything.",
        "sub_pages": [
            {"id": "32886897-dca2-8163-b335-c77814790bca", "title": "Start Here"},
            {"id": "32886897-dca2-81dd-9460-c6dc3c2e2475", "title": "How To Use This OS"},
            {"id": "32886897-dca2-81ca-bef9-f86ab5f973f5", "title": "Operating Spine Quick Read"},
        ]
    },
    {
        "number": 3,
        "title": "Offers & Economics",
        "icon": "💰",
        "description": "What we sell, how we price, and why margins matter. No exceptions without founder approval.",
        "sub_pages": [
            {"id": "32886897-dca2-812b-99d6-c9d5862272d2", "title": "Core Offers"},
            {"id": "32886897-dca2-811d-b988-d99b2dfb59ad", "title": "Retainer-Based Documentation"},
            {"id": "32886897-dca2-81c0-b473-ebec382f47ff", "title": "Signature Project Shoots"},
            {"id": "32886897-dca2-8178-a386-eedb9594608c", "title": "Progression + Completion Packages"},
            {"id": "32886897-dca2-818a-8881-c55cf56a475a", "title": "Retainer Pricing Framework"},
            {"id": "32886897-dca2-81ce-bb6e-ecb88d93dd1d", "title": "One-Off Project Pricing"},
            {"id": "32886897-dca2-8136-b665-dd7cacc1e0f5", "title": "Margin Philosophy"},
        ]
    },
    {
        "number": 4,
        "title": "Sales & Client Acquisition",
        "icon": "🤝",
        "description": "The complete sales playbook. From first contact to signed contract.",
        "sub_pages": [
            {"id": "32886897-dca2-8185-af36-dad4f6884989", "title": "Sales Process Overview"},
            {"id": "32886897-dca2-8189-a156-e85a305e40e0", "title": "Pricing Disclosure Rules"},
            {"id": "32886897-dca2-81c6-be7c-da1a77529c2d", "title": "Discovery Call Script"},
            {"id": "32886897-dca2-81e2-a77f-e3eafa2340ae", "title": "Pricing Pushback Script"},
            {"id": "32886897-dca2-8199-993f-d3251a12c291", "title": "Scope Creep Response Script"},
            {"id": "32886897-dca2-81cb-8dd3-c9979ffe8231", "title": "Follow-Up Sequences"},
        ]
    },
    {
        "number": 5,
        "title": "Daily Ops",
        "icon": "⚙️",
        "description": "Every Daily Ops document solves one type of problem. Find your situation, follow the document exactly.",
        "sub_pages": [
            {"id": "32886897-dca2-81b8-8bc5-ef50a554cc8e", "title": "Client Intake & Qualification"},
            {"id": "32886897-dca2-8171-83e9-f73dc7c6a8ea", "title": "Pricing, Scope & Change Orders"},
            {"id": "32886897-dca2-8160-8da8-c6d87f4f46fb", "title": "Sales to Onboarding Handoff"},
            {"id": "32886897-dca2-816d-a19a-d31cfa32c7aa", "title": "Project Execution Pipeline"},
            {"id": "32886897-dca2-816b-b049-c886c0c92fec", "title": "Quality Control"},
            {"id": "32886897-dca2-812a-ae19-d70c4f163acd", "title": "Delivery"},
            {"id": "32886897-dca2-811f-8059-cf58918e0848", "title": "Client Feedback & Revisions"},
            {"id": "32886897-dca2-81d8-b1e2-c9a694b4b530", "title": "Communication & Escalation"},
            {"id": "32886897-dca2-81e6-a735-f913ccdd64a8", "title": "Roles & Authority"},
            {"id": "32886897-dca2-8119-8971-dfd65f7269d7", "title": "Weekly Operating Review"},
        ]
    },
    {
        "number": 6,
        "title": "People",
        "icon": "👥",
        "description": "Role definitions, hiring criteria, and performance standards. Authority comes from role, not confidence or tenure.",
        "sub_pages": [
            {"id": "32886897-dca2-8192-b198-f9a4fb71dcb4", "title": "Role Definitions"},
            {"id": "32886897-dca2-81da-be2e-cab7cc8e37ff", "title": "Hiring & Onboarding"},
            {"id": "32886897-dca2-8109-b92e-efc213671f93", "title": "Performance & Offboarding"},
        ]
    },
    {
        "number": 7,
        "title": "Client Documents",
        "icon": "📄",
        "description": "Contracts, onboarding templates, and client standards. No work starts without contract and payment terms met.",
        "sub_pages": [
            {"id": "32886897-dca2-8171-9f25-ea902c9708c6", "title": "Master Working Agreement"},
            {"id": "32886897-dca2-8113-ad05-fd17634edec3", "title": "Retainer Agreement"},
            {"id": "32886897-dca2-8103-925b-ed8bbe7fac12", "title": "One-Off Project Agreement"},
            {"id": "32886897-dca2-81e1-bf41-ebdba5ee4924", "title": "Licensing & Usage Terms"},
            {"id": "32886897-dca2-8131-b570-e110d2cce1e7", "title": "Payment Terms & Enforcement"},
            {"id": "32886897-dca2-81fe-9665-f8fdd00dfcc6", "title": "Onboarding Templates"},
            {"id": "32886897-dca2-81d0-b6f8-ffd5eefccf33", "title": "Client Standards"},
        ]
    },
    {
        "number": 8,
        "title": "Governance",
        "icon": "🏛️",
        "description": "Risk management, capacity rules, and founder decision authority. Exceptions are rare, approved, documented, and do not create precedent.",
        "sub_pages": [
            {"id": "32886897-dca2-81f7-a092-f6d93fdfc2bd", "title": "Capacity Ceiling"},
            {"id": "32886897-dca2-8169-8db0-e45d696a8d8c", "title": "Risk Scenarios & Early Signals"},
            {"id": "32886897-dca2-8192-8952-d4e67389a9bb", "title": "Strategic Priorities (Governance)"},
            {"id": "32886897-dca2-81a2-af5b-c95ea96d2fd6", "title": "Founder Decision Log"},
        ]
    },
    {
        "number": 9,
        "title": "Reference Library",
        "icon": "📚",
        "description": "Brand guidelines, visual standards, file naming, tools, and system health. The reference shelf.",
        "sub_pages": [
            {"id": "32886897-dca2-81a7-a098-ea1feba22194", "title": "Brand Guidelines"},
            {"id": "32886897-dca2-8188-827d-d1ecec9a3a2c", "title": "Visual Standards"},
            {"id": "32886897-dca2-812a-a6bd-c97c068a9b94", "title": "File Naming & Delivery Standards"},
            {"id": "32886897-dca2-8107-ab43-e76032e08325", "title": "Tools & Software Notes"},
            {"id": "32886897-dca2-8171-96e3-c9f424420ae5", "title": "System Health"},
        ]
    },
    {
        "number": 10,
        "title": "Financial Health",
        "icon": "💰",
        "description": "Profit-per-X, margin targets, COGS, and cash flow rules. The numbers that keep the business alive.",
        "sub_pages": [
            {"id": "32886897-dca2-819c-b2a2-e3c7a2645ec0", "title": "Profit-per-X Definition"},
            {"id": "32886897-dca2-8141-9104-e92f559d0108", "title": "Margin Targets"},
            {"id": "32886897-dca2-81a5-b83a-ed34d27609cd", "title": "Cost of Delivery (COGS)"},
            {"id": "32886897-dca2-81e5-b64e-fd5dead88bf5", "title": "Financial Red Flags"},
            {"id": "32886897-dca2-8198-92b8-d028db40a58c", "title": "Deposits & Milestones"},
            {"id": "32886897-dca2-8134-9416-df157f45c8a7", "title": "Net Terms & Enforcement"},
            {"id": "32886897-dca2-81c4-8438-df7a8b01a40c", "title": "Non-Payment Protocol"},
        ]
    },
    {
        "number": 11,
        "title": "Growth, Scale & Risk",
        "icon": "🚀",
        "description": "How we grow without breaking. Capacity planning, delegation, bottlenecks, and strategic tradeoffs.",
        "sub_pages": [
            {"id": "32886897-dca2-8101-bb1c-c0b1f09e5480", "title": "Capacity Planning"},
            {"id": "32886897-dca2-813a-a03e-d2f0bd1a04fe", "title": "Delegation Strategy"},
            {"id": "32886897-dca2-817f-8622-f8fb6e9810d6", "title": "Bottleneck Identification"},
            {"id": "32886897-dca2-8121-ae3a-fd096ac6ac44", "title": "What Cannot Be Scaled"},
            {"id": "32886897-dca2-81d7-96ee-c3789e2a0145", "title": "Risk Scenarios"},
            {"id": "32886897-dca2-81eb-9ddd-f31e7e7750ba", "title": "Strategic Tradeoffs"},
        ]
    },
]

OS_INDEX = """
> **Sales & Intake**
> - **A new lead comes in** → Client Intake & Qualification SOP
> - **Unsure if a lead is a good fit** → Client Intake & Qualification SOP
> - **Client is price shopping** → Client Intake & Qualification SOP

---

> **Pricing, Scope & Money**
> - **Client asks for extra work** → Pricing, Scope & Change Orders SOP
> - **Client says "it should be quick / small / easy"** → Pricing, Scope & Change Orders SOP
> - **Unsure if something is in scope** → Pricing, Scope & Change Orders SOP
> - **Client resists a change order** → Pricing, Scope & Change Orders SOP → Escalate if resistance continues

---

> **Deal Closed / Starting Work**
> - **A deal just closed** → Sales to Onboarding Handoff SOP
> - **Client wants work to start immediately** → Sales to Onboarding Handoff SOP
> - **Unsure if we can start work yet** → Project Execution Stage Gates

---

> **Project Execution**
> - **Unsure what stage a project is in** → Project Execution Stage Gates
> - **Trying to move forward but something is missing** → Project Execution Stage Gates
> - **Someone suggests skipping a step** → Project Execution Stage Gates → Escalate immediately

---

> **Editing & Quality**
> - **Editing direction feels unclear** → Quality Control Review SOP
> - **Unsure if work is good enough to send** → Quality Control Review SOP
> - **Deadline pressure risking quality** → Quality Control Review SOP → Escalate before delivery

---

> **Client Feedback & Revisions**
> - **Feedback is vague or emotional** → Client Feedback & Revisions SOP
> - **Feedback coming in pieces** → Client Feedback & Revisions SOP
> - **Client introduces new ideas during revisions** → Client Feedback & Revisions SOP → Likely new scope

---

> **Communication & Decisions**
> - **Not sure who decides something** → Roles & Authority Matrix
> - **Feeling unsure, stuck, or uncomfortable** → Communication & Escalation Protocol
> - **Something feels risky but not "broken" yet** → Communication & Escalation Protocol

---

> **Payments & Client Behavior**
> - **Payment is late** → Payment Terms Enforcement → Escalate if unresolved
> - **Client pushing boundaries repeatedly** → Operating Spine → Escalate for review

---

> **Weekly / System Use**
> - **Weekly check on how things are running** → Weekly Operating Review Ritual
> - **Noticing repeated friction or exceptions** → System Health → Active Tensions

---

> **If You Are Still Unsure**
> If you have read the listed document, followed it exactly, and still feel unsure: **Escalate immediately.** Silence, guessing, or improvising is not acceptable.
"""


if __name__ == "__main__":
    print(json.dumps({
        "sections": SECTIONS,
        "os_index": OS_INDEX,
    }, indent=2))
