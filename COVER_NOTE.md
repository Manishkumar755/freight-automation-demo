Subject: Freight Automation Prototype (Python + Claude API) - Manish Kumar

Dear [Interviewer name],

I built a small working prototype of three freight-operations automations for you to review. It is in the attached zip file.

1. A rate-based quote engine (Air with volumetric weight, By Road, and Sea FCL 20' and 40').
2. Shipping document extraction with Claude, including validation and human-review flags for missing or uncertain fields.
3. Customer email triage with Claude, including routing and a draft reply. Drafts that contain prices are blocked, and a person approves every reply.

Everything runs locally. The rates and emails are sample data. The code has unit tests, and DEMO_GUIDE.md contains a 6-minute walkthrough. I am happy to walk through it live.

Limitations I want to be clear about: the rates are sample values, scanned PDFs need OCR first, and I have not yet measured accuracy on a labelled set of real documents. Those are the next steps.

Thank you for your time.

Manish Kumar
+91 9599674102 | manishkumar358668@gmail.com
linkedin.com/in/manish-kumar-4b0a69205 | github.com/Manishkumar755
