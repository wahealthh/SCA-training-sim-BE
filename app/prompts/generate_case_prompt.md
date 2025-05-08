Generate a realistic primary care patient case for a GP trainee to practice a consultation.
The case should be challenging but realistic for a 12-minute consultation.

Provide the following in JSON format:

1. name: Patient name (first name only, common UK/Australian MALE name only - must be a male patient)
2. age: Patient age (an integer between 18-85)
3. presenting: The primary presenting complaint (1-2 sentences)
4. context: Additional background information to help set up the case (2-3 sentences)

Case types to consider (choose one randomly):

- Acute medical problem (e.g., infection, injury)
- Chronic disease management
- Mental health concerns
- Complex social issues with medical implications
- Preventative care discussions
- Vague symptoms requiring investigation

The case should be realistic, medically accurate, and have sufficient complexity for an engaging consultation.
IMPORTANT: The patient MUST be male. Use only male names like John, David, James, Michael, Robert, etc.

Respond with a JSON object in this format:
{
"name": "string",
"age": integer,
"presenting": "string",
"context": "string"
}
