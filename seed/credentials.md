# Northstar Software — Demo Login Credentials

> Seed accounts created by `seed/seed.sh`. **For local/demo use only — do not deploy these to a public server.**
> Every account shares the same password to make testing easy.

**Password (all accounts):** `Northstar@2026`

| # | Name | Email | Role in workspace | Job title | Department |
|---|------|-------|-------------------|-----------|------------|
| 1 | Maya Hassan | `maya.hassan@northstar.io` | **Owner** | Chief Executive Officer | Leadership |
| 2 | Omar Nabil | `omar.nabil@northstar.io` | Admin | Chief Technology Officer | Engineering |
| 3 | Lina Farouk | `lina.farouk@northstar.io` | Admin | Product Manager | Product |
| 4 | Karim Adel | `karim.adel@northstar.io` | Member | Senior Backend Engineer | Engineering |
| 5 | Salma Youssef | `salma.youssef@northstar.io` | Member | Backend Engineer | Engineering |
| 6 | Ahmed Samir | `ahmed.samir@northstar.io` | Member | Senior Frontend Engineer | Engineering |
| 7 | Nour Ali | `nour.ali@northstar.io` | Member | Frontend Engineer | Engineering |
| 8 | Hana Mostafa | `hana.mostafa@northstar.io` | Member | Product Designer | Product & Design |
| 9 | Youssef Tarek | `youssef.tarek@northstar.io` | Member | DevOps & Platform Engineer | Engineering |
| 10 | Mariam Khaled | `mariam.khaled@northstar.io` | Member | QA Engineer | Quality Assurance |
| 11 | Daniel Reed | `daniel.reed@northstar.io` | Member | Data & Analytics Engineer | Data |
| 12 | Sara Mahmoud | `sara.mahmoud@northstar.io` | Member | Customer Success Manager | Customer Success |
| 13 | Adam Wilson | `adam.wilson@northstar.io` | Member | Sales & Partnerships Manager | Sales |
| 14 | Reem Fawzy | `reem.fawzy@northstar.io` | Member | People Operations Specialist | People Operations |
| 15 | Ziad Emad | `ziad.emad@northstar.io` | Member | Junior Software Engineer | Engineering |

## Quick start

```bash
# 1. Bring the stack up
docker compose up -d

# 2. Seed the demo company (waits for the gateway, then loads users + channels + tasks)
docker compose --profile seed up seed

# 3. Log in at the web client with any email above + Northstar@2026
```

Maya Hassan owns the workspace, so log in as her to see everything.
