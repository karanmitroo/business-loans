from django.conf import settings

QUESTIONS_FOR_ELIGIBILITY = {
		"p1": [{
				"id": 1,
				"question": "What is the age of your business?",
				"return_type": "integer",
				"regex":""
			},
			{
				"id": 2,
				"question": "What is the loan amount that you need?",
				"return_type": "integer",
				"regex":""
			},
			{
				"id": 3,
				"question": "What was your last year's revenue?",
				"return_type": "integer",
				"regex":""
			}
		],
		"p2": [{
				"id": 1,
				"question": "Enter your PAN card Number?",
				"return_type":"regex",
				"regex":"[a-zA-Z]{5}[0-9]{4}[a-zA-Z]"
			},
			{
				"id": 2,
				"question": "What is your sector of Business?",
				"return_type":"option",
				"options": settings.SECTORS,
				"regex":""
			},
			{
				"id": 3,
				"question": "Enter the Pin Code of your office/factory.",
				"return_type":"regex",
				"regex":"[0-9]{6}"
			}
		]
	}
