# Product FAQ

Frequently asked questions from biotech and life sciences buyers. These answers are
intended for use by sales reps and customer success managers during evaluations and
onboarding conversations.

---

## Compliance and Regulatory

**Q1: Is PulseIQ compliant with FDA 21 CFR Part 11?**

Yes. PulseIQ is fully compliant with FDA 21 CFR Part 11, which governs electronic records
and electronic signatures in regulated life sciences environments. This includes immutable
audit trails on all data modifications, role-based access controls with enforced separation
of duties, time-stamped electronic signatures, and system access logs. Enterprise customers
receive a complete validation documentation package including a Validation Master Plan and
IQ/OQ/PQ templates to support their internal validation process. Our compliance team is
available to participate in your validation review.

---

**Q2: Does PulseIQ support HL7/FHIR integration for clinical data exchange?**

Yes. PulseIQ supports HL7 v2.x and FHIR R4 for clinical data exchange. This enables
integration with EHR systems (Epic, Cerner, Oracle Health) and clinical data repositories.
FHIR-based integrations are included in the growth and enterprise tiers. For hospital
systems and clinical-stage companies requiring custom HL7 mappings, our professional
services team handles this as part of the implementation engagement.

---

**Q3: What validation documentation does PulseIQ provide?**

Enterprise customers receive a complete validation package including:
- Validation Master Plan (VMP)
- Installation Qualification (IQ) protocol and executed report
- Operational Qualification (OQ) protocol and executed report
- Performance Qualification (PQ) protocol template
- Traceability matrix mapping requirements to test cases
- System Description Document

Growth tier customers receive the VMP and IQ/OQ documentation. Starter tier customers
can purchase the validation package as an add-on for $5,000. All documents are reviewed
and updated with each major product release.

---

**Q4: Is PulseIQ HIPAA compliant?**

Yes. PulseIQ is HIPAA compliant for customers handling Protected Health Information (PHI).
We execute a Business Associate Agreement (BAA) with all customers who require one. PHI
data is encrypted at rest (AES-256) and in transit (TLS 1.3), access is logged and auditable,
and data processing is limited to contracted purposes. Our infrastructure is hosted on
HIPAA-eligible AWS services. Annual third-party HIPAA audits are conducted and results
are available to customers under NDA.

---

## Security and Infrastructure

**Q5: How is customer data secured and isolated?**

Each customer's data is stored in a dedicated, isolated database instance — we do not
use shared multi-tenant databases for data storage. All data is encrypted at rest using
AES-256 and encrypted in transit using TLS 1.3. Access to customer environments is
restricted to named individuals on our engineering team with a documented business need,
and all access is logged. We undergo annual SOC 2 Type II audits; the most recent report
is available to customers under NDA.

Customers can also choose single-tenant deployment (dedicated infrastructure) as an
add-on for regulated environments with strict data isolation requirements.

---

**Q6: What is PulseIQ's uptime SLA?**

PulseIQ offers a 99.9% uptime SLA for growth and enterprise customers, measured monthly
and excluding pre-announced maintenance windows. Enterprise customers are eligible for a
99.95% SLA. In the event of an SLA breach, customers receive service credits applied to
their next invoice (10% credit per full percentage point below SLA). Our status page is
publicly available at status.pulseiq.io and is updated in real time. Mean time to
resolution for P1 incidents is under 2 hours.

---

## Onboarding and Implementation

**Q7: How long does implementation take?**

Standard implementation takes 6-10 weeks from contract signature to go-live. The timeline
breaks down as follows:

- Weeks 1-2: Environment setup, SSO configuration, user provisioning
- Weeks 3-5: Data migration, integration configuration, and testing
- Weeks 6-8: User acceptance testing (UAT) and training
- Weeks 9-10: Go-live and hypercare support

For organizations with more than three system integrations or complex data migration
requirements, implementation may extend to 12-14 weeks. We agree on a fixed go-live date
in the contract and guarantee it — if we miss the date due to factors within our control,
we extend your subscription at no cost.

---

**Q8: What integrations does PulseIQ support out of the box?**

PulseIQ has pre-built connectors for the following systems and instruments:

**ELN/LIMS:** Benchling, LabVantage, IDBS E-WorkBook, LabArchives, Dotmatics

**Instruments:** Thermo Fisher (QuantStudio, Orbitrap), Waters ACQUITY, Agilent
(OpenLAB, MassHunter), Illumina BaseSpace, Pacific Biosciences

**Clinical/EHR:** Epic (via FHIR), Oracle Cerner (via HL7), Medidata Rave

**Infrastructure:** Okta, Azure Active Directory, AWS S3, Snowflake, Databricks

Custom integrations are available through our REST API, which is fully documented at
docs.pulseiq.io.

---

## Pricing and Contracts

**Q9: How does PulseIQ's pricing work?**

PulseIQ is priced as a monthly subscription based on lab size (number of active researchers
using the platform). See the pricing guide for detailed tier breakdowns. Annual contracts
are billed annually in advance and receive a 10% discount relative to month-to-month
pricing. Multi-year contracts receive additional discounts (15% for two years, 20% for
three years). All tiers include unlimited data storage up to the contracted data volume,
after which overage pricing applies at $0.05/GB/month.

---

**Q10: What happens to our data if we cancel our subscription?**

Upon cancellation, customers have 90 days to export all data in standard formats (CSV,
JSON, HL7, FHIR). We provide a full data export package at no charge as part of
offboarding. After the 90-day window, data is securely deleted from all PulseIQ systems
in accordance with our data retention policy. Customers requiring longer retention windows
can arrange an extended data custody period for a monthly fee. We will never hold your
data hostage or make export difficult — clean offboarding is part of our commitment to
trust.
