"""Official Government Data Sources Integration.

Connects to official Indian Government portals and public APIs:
- MyScheme (myscheme.gov.in)
- National Portal of India (india.gov.in)
- Open Government Data Platform (data.gov.in)
Includes curated fallback registries of central schemes to ensure uninterrupted service.
"""

import asyncio
from datetime import datetime, timezone
import logging
import re
import string
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from app.config import get_settings
from app.models.schemas import GovernmentScheme

logger = logging.getLogger(__name__)


class GovernmentSourceError(Exception):
    """Raised when an official government source cannot be reached."""
    pass


# Curated, authentic registry of flagship Indian Government schemes
# Used for instant responses, offline availability, or when external APIs are rate-limited.
CURATED_FLAGSHIP_SCHEMES: List[Dict[str, Any]] = [
    {
        "id": "pm-kisan",
        "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "name_hindi": "प्रधानमंत्री किसान सम्मान निधि (पीएम-किसान)",
        "name_telugu": "ప్రధాన మంత్రి కిసాన్ సమ్మాన్ నిధి (పీఎం-కిసాన్)",
        "description": "Income support scheme of ₹6,000 per year in three equal 4-monthly installments to all landholding farmer families across India.",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "state": None,
        "beneficiary_types": ["Farmers", "Small and Marginal Farmers", "Rural Landowners"],
        "benefits": [
            "₹6,000 per year transferred directly into bank accounts via DBT in three installments of ₹2,000 each.",
            "Funds can be used for agricultural inputs, seeds, fertilizers, and household needs."
        ],
        "eligibility_criteria": [
            "Must be a landholding farmer family with cultivable landholding in their name.",
            "All institutional landholders are excluded.",
            "Constitutional post holders, serving/retired government officers, and income-tax payers are excluded.",
            "Farmer family defined as husband, wife, and minor children."
        ],
        "required_documents": [
            "Aadhaar Card (Mandatory)",
            "Land ownership citizenship documents (Khata / Khasra / RoR)",
            "Aadhaar-seeded active bank account details with IFSC code",
            "Mobile number linked with Aadhaar for eKYC"
        ],
        "application_url": "https://pmkisan.gov.in/RegistrationFormNew.aspx",
        "official_url": "https://pmkisan.gov.in",
        "source": "myscheme",
        "category": "Agriculture",
    },
    {
        "id": "pm-jay-ayushman",
        "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
        "name_hindi": "आयुष्मान भारत - प्रधानमंत्री जन आरोग्य योजना (पीएम-जय)",
        "name_telugu": "ఆయుష్మాన్ భారత్ - ప్రధాన మంత్రి జన్ ఆరోగ్య యోజన (పీఎం-జేఏవై)",
        "description": "World's largest government-funded health assurance scheme providing health coverage of ₹5 lakh per family per year for secondary and tertiary hospitalization.",
        "ministry": "Ministry of Health and Family Welfare",
        "state": None,
        "beneficiary_types": ["Low Income Families", "BPL Families", "Vulnerable Citizens", "Senior Citizens (70+)"],
        "benefits": [
            "Cashless health insurance cover up to ₹5,00,000 per eligible family per year.",
            "Covers pre-hospitalization (3 days) and post-hospitalization (15 days) expenses.",
            "All pre-existing conditions covered from day one across 27,000+ empanelled hospitals.",
            "Recent expansion: All senior citizens aged 70 and above receive separate ₹5 lakh cover."
        ],
        "eligibility_criteria": [
            "Families identified based on Socio-Economic Caste Census (SECC 2011) rural/urban deprivation criteria.",
            "Active NFSA Ration Card holders as per state list.",
            "All Indian citizens aged 70 years and above (universal coverage without income ceiling)."
        ],
        "required_documents": [
            "Aadhaar Card or Government Photo Identity Card",
            "Ration Card or proof of family composition",
            "Mobile phone for OTP verification"
        ],
        "application_url": "https://beneficiary.nha.gov.in",
        "official_url": "https://nha.gov.in/PM-JAY",
        "source": "myscheme",
        "category": "Healthcare",
    },
    {
        "id": "pm-awas-gramin",
        "name": "Pradhan Mantri Awaas Yojana - Gramin (PMAY-G)",
        "name_hindi": "प्रधानमंत्री आवास योजना - ग्रामीण",
        "name_telugu": "ప్రధాన మంత్రి ఆవాస్ యోజన - గ్రామీణ్",
        "description": "Financial assistance to houseless rural households and those living in kutcha/dilapidated houses for construction of pucca houses with basic amenities.",
        "ministry": "Ministry of Rural Development",
        "state": None,
        "beneficiary_types": ["Rural Poor", "Homeless", "Kutcha House Dwellers", "Women Heads of Household"],
        "benefits": [
            "Financial grant of ₹1,20,000 in plain areas and ₹1,30,000 in hilly/difficult/northeastern states.",
            "Additional 90-95 person-days of unskilled labor under MGNREGS (approx ₹18,000 - ₹24,000).",
            "₹12,000 grant for toilet construction under Swachh Bharat Mission - Gramin."
        ],
        "eligibility_criteria": [
            "Rural families who do not own a pucca house anywhere in India.",
            "Identification based on SECC 2011 housing deprivation and Awaas+ survey verified by Gram Sabha.",
            "Families with monthly income below regional poverty levels."
        ],
        "required_documents": [
            "Aadhaar Card",
            "Bank passbook with IFSC code",
            "MGNREGA Job Card number",
            "Swachh Bharat Mission registration number",
            "Land ownership/allotment certificate"
        ],
        "application_url": "https://pmayg.nic.in",
        "official_url": "https://pmayg.nic.in",
        "source": "myscheme",
        "category": "Housing & Shelter",
    },
    {
        "id": "sukanya-samriddhi",
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "name_hindi": "सुकन्या समृद्धि योजना",
        "name_telugu": "సుకన్య సమృద్ధి యోజన",
        "description": "A government-backed small savings scheme designed exclusively for the girl child under the 'Beti Bachao Beti Padhao' campaign with high interest and tax exemptions.",
        "ministry": "Ministry of Finance",
        "state": None,
        "beneficiary_types": ["Girl Child", "Parents", "Guardians"],
        "benefits": [
            "High sovereign guaranteed interest rate (8.2% p.a., compounded annually).",
            "Triple tax benefit: Exemption under Section 80C, tax-free interest, and tax-free maturity.",
            "Partial withdrawal up to 50% allowed for higher education after girl turns 18."
        ],
        "eligibility_criteria": [
            "Account can be opened by parents/legal guardians for a girl child aged 10 years or younger.",
            "Maximum of two accounts per family (exceptions for triplets/twins).",
            "Account matures 21 years from opening date or upon girl's marriage after age 18."
        ],
        "required_documents": [
            "Birth Certificate of the girl child",
            "Identity Proof of parent/guardian (Aadhaar / Voter ID / Passport)",
            "Address proof of guardian",
            "Recent passport size photographs"
        ],
        "application_url": "https://www.indiapost.gov.in",
        "official_url": "https://www.indiapost.gov.in/Financial/Pages/Content/SSY.aspx",
        "source": "myscheme",
        "category": "Banking & Financial Services",
    },
    {
        "id": "pm-vishwakarma",
        "name": "PM Vishwakarma Scheme",
        "name_hindi": "पीएम विश्वकर्मा योजना",
        "name_telugu": "పీఎం విశ్వకర్మ పథకం",
        "description": "Comprehensive support scheme providing recognition, skill training, modern toolkit incentive, and collateral-free enterprise credit to traditional artisans and craftspeople.",
        "ministry": "Ministry of Micro, Small and Medium Enterprises",
        "state": None,
        "beneficiary_types": ["Artisans", "Craftspeople", "Carpenters", "Blacksmiths", "Potters", "Masons", "Tailors"],
        "benefits": [
            "Recognition as Vishwakarma through certificate and ID Card.",
            "Basic training of 5-7 days and advanced training of 15+ days with ₹500/day stipend.",
            "Modern Toolkit incentive grant of ₹15,000.",
            "Collateral-free enterprise development credit: 1st tranche up to ₹1,00,000 @ 5% concessional interest rate, 2nd tranche up to ₹2,00,000."
        ],
        "eligibility_criteria": [
            "An artisan or craftsperson working with hands and tools in one of the 18 identified traditional trades.",
            "Minimum age of 18 years on the date of registration.",
            "Beneficiary should not have availed credit under similar government schemes (PMEGP, PM SVANidhi, Mudra) in last 5 years.",
            "Limited to one member of a family."
        ],
        "required_documents": [
            "Aadhaar Card",
            "Active mobile number linked with Aadhaar",
            "Bank Account details",
            "Ration Card for family validation"
        ],
        "application_url": "https://pmvishwakarma.gov.in",
        "official_url": "https://pmvishwakarma.gov.in",
        "source": "myscheme",
        "category": "Skill Development & Employment",
    },
    {
        "id": "atal-pension-yojana",
        "name": "Atal Pension Yojana (APY)",
        "name_hindi": "अटल पेंशन योजना (एपीवाई)",
        "name_telugu": "అటల్ పెన్షన్ యోజన",
        "description": "Universal social security pension scheme focused on unorganized sector workers, guaranteeing lifelong monthly pension of ₹1,000 to ₹5,000 starting from age 60.",
        "ministry": "Ministry of Finance",
        "state": None,
        "beneficiary_types": ["Unorganized Workers", "Self Employed", "Daily Wage Earners", "Gig Workers"],
        "benefits": [
            "Guaranteed minimum monthly pension of ₹1,000, ₹2,000, ₹3,000, ₹4,000 or ₹5,000 after 60 years of age.",
            "Same pension amount continues to the spouse upon death of the subscriber.",
            "Accumulated pension corpus returned to the nominee after demise of both subscriber and spouse."
        ],
        "eligibility_criteria": [
            "Any Indian citizen aged between 18 and 40 years.",
            "Must have a savings bank account or post office savings account.",
            "Citizens who are or have been income-tax payers are not eligible to join APY."
        ],
        "required_documents": [
            "Aadhaar Card",
            "Active Savings Bank Account Number",
            "Nominee details and KYC documents",
            "Mobile number"
        ],
        "application_url": "https://enps.nsdl.com/eNPS/ApySubRegistration.html",
        "official_url": "https://www.npscra.nsdl.co.in/scheme-details.php",
        "source": "myscheme",
        "category": "Social Security & Pension",
    },
    {
        "id": "pm-mudra-yojana",
        "name": "Pradhan Mantri MUDRA Yojana (PMMY)",
        "name_hindi": "प्रधानमंत्री मुद्रा योजना (पीएमएमवाई)",
        "name_telugu": "ప్రధాన మంత్రి ముద్ర యోజన",
        "description": "Collateral-free institutional micro-credit loans up to ₹10-20 lakh for non-corporate, non-farm small and micro enterprises across Shishu, Kishore, and Tarun categories.",
        "ministry": "Ministry of Finance",
        "state": None,
        "beneficiary_types": ["Small Business Owners", "Shopkeepers", "Entrepreneurs", "Artisans", "Women Entrepreneurs"],
        "benefits": [
            "Shishu loans up to ₹50,000 for early stage ventures.",
            "Kishore loans above ₹50,000 and up to ₹5,00,000 for established setups.",
            "Tarun loans above ₹5,00,000 and up to ₹10,00,000 (extended up to ₹20,00,000 in recent union budget).",
            "Zero processing fee for Shishu and Kishore tranches with collateral-free guarantee."
        ],
        "eligibility_criteria": [
            "Any Indian citizen having a business plan for non-farm income-generating activity.",
            "Manufacturing, trading, processing, and service sector micro-enterprises.",
            "Applicant must not be a defaulter to any bank or financial institution."
        ],
        "required_documents": [
            "Identity Proof (Aadhaar / Voter ID / PAN Card)",
            "Proof of Residence (Electricity bill / Aadhaar / Ration card)",
            "Business enterprise registration or trade license (if existing)",
            "Bank account statements for the last 6 months"
        ],
        "application_url": "https://www.udyamimitra.in",
        "official_url": "https://www.mudra.org.in",
        "source": "myscheme",
        "category": "Banking & Financial Services",
    },
    {
        "id": "pm-svanidhi",
        "name": "PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
        "name_hindi": "पीएम स्ट्रीट वेंडर्स आत्मनिर्भर निधि (पीएम स्वनिधि)",
        "name_telugu": "పీఎం స్వనిధి పథకం (వీధి వ్యాపారుల రుణం)",
        "description": "Special micro-credit facility providing affordable collateral-free working capital loans of ₹10,000 to ₹50,000 to urban street vendors, hawkers, and thelewale.",
        "ministry": "Ministry of Housing and Urban Affairs",
        "state": None,
        "beneficiary_types": ["Street Vendors", "Hawkers", "Thelewale", "Urban Micro-retailers"],
        "benefits": [
            "Initial working capital loan of ₹10,000 without any collateral.",
            "Second tranche up to ₹20,000 and third tranche up to ₹50,000 upon timely repayment.",
            "7% interest subsidy per annum credited directly to bank account via DBT.",
            "Cashback incentives up to ₹1,200 per year on digital transactions."
        ],
        "eligibility_criteria": [
            "Street vendors vending in urban areas on or before March 24, 2020 (updated periodic verification).",
            "Possession of Certificate of Vending or Identity Card issued by Urban Local Body (ULB).",
            "Vendors left out of survey can get Letter of Recommendation (LoR) from Town Vending Committee."
        ],
        "required_documents": [
            "Aadhaar Card",
            "Vending Certificate or Letter of Recommendation (LoR) from Municipality / ULB",
            "Bank passbook or account details linked with Aadhaar",
            "Active mobile number"
        ],
        "application_url": "https://pmsvanidhi.mohua.gov.in",
        "official_url": "https://pmsvanidhi.mohua.gov.in",
        "source": "myscheme",
        "category": "Skill Development & Employment",
    },
    {
        "id": "pm-surya-ghar",
        "name": "PM Surya Ghar: Muft Bijli Yojana",
        "name_hindi": "पीएम सूर्य घर: मुफ्त बिजली योजना",
        "name_telugu": "పీఎం సూర్య ఘర్: ఉచిత విద్యుత్ పథకం (సౌర విద్యుత్)",
        "description": "Rooftop solar initiative providing direct central subsidy up to ₹78,000 to households for installing rooftop solar systems, offering up to 300 units of free electricity every month.",
        "ministry": "Ministry of New and Renewable Energy",
        "state": None,
        "beneficiary_types": ["Homeowners", "Residential Households", "Middle Class Families"],
        "benefits": [
            "Direct bank subsidy: ₹30,000 for 1 kW, ₹60,000 for 2 kW, and ₹78,000 for 3 kW and higher systems.",
            "Up to 300 units of free electricity per month for the household.",
            "Ability to sell surplus electricity back to the DISCOM grid via net metering.",
            "Low-interest concessional collateral-free bank loans (approx. 7% interest) for balance amount."
        ],
        "eligibility_criteria": [
            "Household must be an Indian citizen with a residential electricity connection in their name.",
            "Must possess suitable rooftop space capable of installing solar panels.",
            "Must not have availed any other central subsidy for solar panels previously."
        ],
        "required_documents": [
            "Recent Electricity Bill (Consumer number / CA number)",
            "Aadhaar Card of the electricity connection owner",
            "Bank Account Passbook (cancelled cheque) for DBT subsidy transfer",
            "Proof of roof ownership or house document"
        ],
        "application_url": "https://pmsuryaghar.gov.in",
        "official_url": "https://pmsuryaghar.gov.in",
        "source": "myscheme",
        "category": "Energy & Environment",
    },
    {
        "id": "pm-jan-dhan",
        "name": "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
        "name_hindi": "प्रधानमंत्री जन धन योजना (पीएमजेडीवाई)",
        "name_telugu": "ప్రధాన మంత్రి జన్ ధన్ యోజన",
        "description": "National Mission for Financial Inclusion ensuring universal access to banking services with zero-balance savings accounts, RuPay debit cards, and inbuilt insurance.",
        "ministry": "Ministry of Finance",
        "state": None,
        "beneficiary_types": ["Unbanked Citizens", "Rural Poor", "Women", "Low Income Households"],
        "benefits": [
            "Zero balance savings bank account (No minimum balance requirement).",
            "Free RuPay Debit Card with inbuilt ₹2,00,000 accidental insurance coverage.",
            "Overdraft (OD) facility up to ₹10,000 to eligible adult account holders.",
            "Direct recipient gateway for all central and state government DBT subsidies."
        ],
        "eligibility_criteria": [
            "Any Indian citizen aged 10 years or older without an existing bank account.",
            "Account can be opened at any commercial bank branch or Bank Mitra / Business Correspondent."
        ],
        "required_documents": [
            "Aadhaar Card or Voter ID / Passport / Driving License / NREGA Card",
            "Passport size photograph",
            "Active mobile number"
        ],
        "application_url": "https://www.pmjdy.gov.in",
        "official_url": "https://www.pmjdy.gov.in",
        "source": "myscheme",
        "category": "Banking & Financial Services",
    },
    {
        "id": "pm-ujjwala",
        "name": "Pradhan Mantri Ujjwala Yojana (PMUY - Ujjwala 2.0)",
        "name_hindi": "प्रधानमंत्री उज्ज्वला योजना (उज्ज्वला २.०)",
        "name_telugu": "ప్రధాన మంత్రి ఉజ్వల యోజన (ఉచిత గ్యాస్ కనెక్షన్)",
        "description": "Provides deposit-free LPG gas connections and targeted subsidies of ₹300 per 14.2 kg refill to adult women from poor and marginalized households across India.",
        "ministry": "Ministry of Petroleum and Natural Gas",
        "state": None,
        "beneficiary_types": ["Poor Women", "BPL Families", "SC/ST Households", "Rural Homemakers"],
        "benefits": [
            "Deposit-free LPG connection including regulator, safety hose, and domestic gas cylinder.",
            "First LPG refill and cooking stove (hotplate) provided completely free of cost.",
            "Direct target subsidy of ₹300 per refill (up to 12 refills per year) transferred via DBT."
        ],
        "eligibility_criteria": [
            "Applicant must be an adult woman aged 18 years or above.",
            "Belongs to BPL, SC/ST, PMAY (Gramin), Antyodaya Anna Yojana, or most backward classes.",
            "No member of the applicant's household should hold an existing active LPG connection."
        ],
        "required_documents": [
            "Aadhaar Card of the female applicant and adult family members",
            "Ration Card establishing family composition",
            "Active bank account with IFSC code",
            "Self-declaration of residential address"
        ],
        "application_url": "https://www.pmuy.gov.in/ujjwala2.html",
        "official_url": "https://www.pmuy.gov.in",
        "source": "myscheme",
        "category": "Energy & Environment",
    },
    {
        "id": "mgnrega",
        "name": "Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGA)",
        "name_hindi": "महात्मा गांधी राष्ट्रीय ग्रामीण रोजगार गारंटी अधिनियम (मनरेगा)",
        "name_telugu": "మహాత్మా గాంధీ జాతీయ గ్రామీణ ఉపాధి హామీ పథకం (నరేగా)",
        "description": "Legal guarantee providing at least 100 days of wage employment per financial year to every rural household whose adult members volunteer to do unskilled manual work.",
        "ministry": "Ministry of Rural Development",
        "state": None,
        "beneficiary_types": ["Rural Workers", "Daily Wage Laborers", "Agricultural Laborers", "Rural Households"],
        "benefits": [
            "Guaranteed 100 days of paid wage employment per household per year.",
            "Statutory minimum daily wage paid directly into the worker's bank or post office account via DBT.",
            "Unemployment allowance legally payable if work is not provided within 15 days of application.",
            "Works focused on water conservation, irrigation, village roads, and rural infrastructure."
        ],
        "eligibility_criteria": [
            "Must be an adult citizen (18+ years) residing in a rural gram panchayat area.",
            "Willing to undertake unskilled manual labor.",
            "Must be a registered member holding a valid MGNREGA Job Card."
        ],
        "required_documents": [
            "Aadhaar Card",
            "Gram Panchayat residence proof or Ration Card",
            "Bank or Post Office savings account passbook",
            "Passport size photograph"
        ],
        "application_url": "https://nrega.nic.in",
        "official_url": "https://nrega.nic.in",
        "source": "myscheme",
        "category": "Skill Development & Employment",
    },
    {
        "id": "national-scholarship",
        "name": "National Scholarship Portal Schemes (NSP Central Sector)",
        "name_hindi": "राष्ट्रीय छात्रवृत्ति पोर्टल (एनएसपी छात्रवृत्ति योजनाएं)",
        "name_telugu": "నేషనల్ స్కాలర్‌షిప్ పోర్టల్ (ఎన్‌ఎస్‌పీ ఉపకార వేతనాలు)",
        "description": "Central and state scholarships for pre-matric, post-matric, higher education, and technical studies for students belonging to SC, ST, OBC, EWS, and minority communities.",
        "ministry": "Ministry of Education",
        "state": None,
        "beneficiary_types": ["Students", "College Youth", "SC/ST/OBC Students", "Minorities", "Merit Scholars"],
        "benefits": [
            "Direct monetary scholarship covering tuition fees, maintenance allowance, and book grants.",
            "Amounts range from ₹10,000 to ₹50,000+ per academic year depending on course level.",
            "DBT disbursement directly to the student's Aadhaar-seeded bank account."
        ],
        "eligibility_criteria": [
            "Enrolled in a recognized school, college, university, or polytechnic/ITI in India.",
            "Minimum 50% or specified cutoff marks in the previous qualifying examination.",
            "Annual family income within prescribed limits (typically below ₹2.5 lakh to ₹8 lakh)."
        ],
        "required_documents": [
            "Aadhaar Card of the student",
            "Previous Year Academic Marksheet / Certificate",
            "Current Year College/School Admission Receipt or Bonafide Certificate",
            "Income Certificate issued by Tehsildar / Competent Authority",
            "Community / Caste Certificate (if applying under SC/ST/OBC category)",
            "Bank passbook in student's name"
        ],
        "application_url": "https://scholarships.gov.in",
        "official_url": "https://scholarships.gov.in",
        "source": "myscheme",
        "category": "Education & Learning",
    },
    {
        "id": "pm-fasal-bima",
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "name_hindi": "प्रधानमंत्री फसल बीमा योजना (पीएमएफबीवाई)",
        "name_telugu": "ప్రధాన మంత్రి ఫసల్ బీమా యోజన (పంటల బీమా)",
        "description": "Comprehensive agricultural crop insurance offering financial shield to farmers against non-preventable natural risks like drought, flood, pests, and post-harvest losses.",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "state": None,
        "beneficiary_types": ["Farmers", "Tenant Farmers", "Sharecroppers", "Agricultural Growers"],
        "benefits": [
            "Extremely low farmer premium share: 2% for Kharif crops, 1.5% for Rabi crops, and 5% for commercial/horticultural crops.",
            "Balance premium heavily subsidized by Central and State Governments.",
            "Complete coverage for localized perils (hailstorm, landslide, inundation) and post-harvest losses.",
            "Direct claim settlement into the farmer's bank account via National Crop Insurance Portal."
        ],
        "eligibility_criteria": [
            "All farmers growing notified crops in notified areas, including sharecroppers and tenant farmers.",
            "Loanee farmers with Kisan Credit Card (KCC) as well as non-loanee farmers are eligible."
        ],
        "required_documents": [
            "Aadhaar Card",
            "Land ownership record (RoR / Khasra-Khatauni) or Tenant agreement",
            "Sowing Certificate or crop declaration issued by Patwari / Village Agriculture Officer",
            "Bank account passbook with IFSC code"
        ],
        "application_url": "https://pmfby.gov.in",
        "official_url": "https://pmfby.gov.in",
        "source": "myscheme",
        "category": "Agriculture",
    }
]


class MySchemeSource:
    """Retrieves schemes from official MyScheme (myscheme.gov.in) API."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.MYSCHEME_API_BASE
        self.headers = {
            "User-Agent": "JanSahayak-AI-Explainer/1.0 (Public Service Citizen Assistant; contact@jansahayak.gov.in)",
            "Accept": "application/json",
        }

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(2),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def search_schemes(
        self,
        keyword: str = "",
        state: str = "",
        category: str = "",
        beneficiary: str = "",
        page_size: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search MyScheme public endpoint."""
        url = f"{self.base_url}/search/v4/schemes"
        params: Dict[str, Any] = {
            "pageSize": page_size,
            "pageNumber": 1,
            "lang": "en",
        }
        if keyword:
            params["keyword"] = keyword
        if state:
            params["state"] = state
        if category:
            params["category"] = category

        try:
            async with httpx.AsyncClient(timeout=10.0, headers=self.headers, verify=False) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    # MyScheme formats items under data or hits
                    items = data.get("data", {}).get("schemes", []) or data.get("hits", []) or []
                    logger.info("MyScheme API returned %d schemes for query '%s'", len(items), keyword)
                    return items
                else:
                    logger.warning("MyScheme API HTTP status %d: %s", response.status_code, response.text[:200])
                    raise GovernmentSourceError(f"MyScheme API returned status {response.status_code}")
        except Exception as e:
            logger.warning("MyScheme API call failed (%s). Falling back to curated registry.", e)
            raise GovernmentSourceError(f"MyScheme connection failure: {e}") from e

    def _parse_scheme(self, raw: Dict[str, Any]) -> GovernmentScheme:
        """Map MyScheme JSON schema to internal GovernmentScheme model."""
        now = datetime.now(timezone.utc)
        scheme_id = str(raw.get("id") or raw.get("slug") or raw.get("schemeId") or "scheme")
        name = raw.get("name") or raw.get("schemeName") or "Government Scheme"
        description = raw.get("description") or raw.get("briefDescription") or raw.get("details", "")
        
        # Extract criteria & benefits safely
        benefits = raw.get("benefits", [])
        if isinstance(benefits, str):
            benefits = [benefits]
            
        criteria = raw.get("eligibilityCriteria", []) or raw.get("eligibility", [])
        if isinstance(criteria, str):
            criteria = [criteria]
            
        docs = raw.get("documentsRequired", []) or raw.get("documents", [])
        if isinstance(docs, str):
            docs = [docs]

        return GovernmentScheme(
            id=scheme_id,
            name=name,
            name_hindi=raw.get("nameHindi"),
            name_telugu=raw.get("nameTelugu"),
            description=description,
            ministry=raw.get("ministryName") or raw.get("department"),
            state=raw.get("stateName"),
            beneficiary_types=raw.get("beneficiaries", []),
            benefits=benefits,
            eligibility_criteria=criteria,
            required_documents=docs,
            application_url=raw.get("applicationUrl") or raw.get("applyUrl"),
            official_url=raw.get("schemeUrl") or f"https://www.myscheme.gov.in/schemes/{scheme_id}",
            source="myscheme",
            last_verified=now,
            category=raw.get("categoryName") or raw.get("category"),
        )


class IndiaGovScraper:
    """Retrieves spotlight schemes from national portal of India (india.gov.in)."""
    BASE_URL = "https://www.india.gov.in"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JanSahayak/1.0",
            "Accept": "text/html,application/xhtml+xml",
        }

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(2),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def fetch_spotlight_schemes(self) -> List[Dict[str, Any]]:
        """Scrape current national spotlight schemes from india.gov.in/spotlight/."""
        url = f"{self.BASE_URL}/spotlight"
        spotlight_items: List[Dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(timeout=10.0, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    views_rows = soup.select(".view-spotlights .views-row") or soup.select(".item-list ul li")
                    
                    for row in views_rows[:8]:
                        title_tag = row.select_one("h2 a") or row.select_one("h3 a") or row.select_one("a")
                        desc_tag = row.select_one(".field-content p") or row.select_one("p")
                        
                        if title_tag:
                            title = title_tag.get_text(strip=True)
                            href = title_tag.get("href", "")
                            link = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                            desc = desc_tag.get_text(strip=True) if desc_tag else "National spotlight government initiative."
                            
                            spotlight_items.append({
                                "title": title,
                                "description": desc,
                                "url": link,
                                "source": "india_gov"
                            })
                    logger.info("Retrieved %d spotlight schemes from india.gov.in", len(spotlight_items))
                    return spotlight_items
                else:
                    raise GovernmentSourceError(f"india.gov.in responded with {response.status_code}")
        except Exception as e:
            logger.warning("IndiaGovScraper could not scrape spotlight: %s", e)
            return []


class DataGovSource:
    """Retrieves official open datasets and schemes from data.gov.in."""
    BASE_URL = "https://data.gov.in/api/3/action"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.DATA_GOV_API_KEY
        self.headers = {
            "User-Agent": "JanSahayak-AI/1.0",
            "Accept": "application/json",
        }
        if self.api_key:
            self.headers["api-key"] = self.api_key

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(2),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def search_datasets(self, query: str, rows: int = 5) -> List[Dict[str, Any]]:
        """Search CKAN package catalog on data.gov.in."""
        url = f"{self.BASE_URL}/package_search"
        params = {"q": f"{query} scheme", "rows": rows}
        
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=self.headers) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("result", {}).get("results", [])
                    return results
                else:
                    logger.warning("DataGovSource returned %d", response.status_code)
                    return []
        except Exception as e:
            logger.debug("DataGovSource query error: %s", e)
            return []


class GovernmentSourceAggregator:
    """Aggregates and normalizes results from multiple official government sources."""

    def __init__(self):
        self.myscheme = MySchemeSource()
        self.india_gov = IndiaGovScraper()
        self.data_gov = DataGovSource()
        self.curated_schemes = [GovernmentScheme(**scheme) for scheme in CURATED_FLAGSHIP_SCHEMES]

    def compute_scheme_relevance(self, query: str, scheme: GovernmentScheme) -> float:
        """Calculate high-precision relevance score between a query and a scheme."""
        q = query.lower().strip()
        if not q:
            return 1.0

        punct_map = str.maketrans({c: ' ' for c in string.punctuation})
        clean_q = q.translate(punct_map)
        q_words = [w for w in clean_q.split() if len(w) > 1]
        if not q_words:
            return 1.0

        # Generic words that appear across many schemes or questions (English, Telugu, Hindi)
        generic_words = {
            # English
            'pm', 'pradhan', 'mantri', 'yojana', 'scheme', 'bharat', 'national',
            'yojna', 'sarkar', 'india', 'portal', 'central', 'the', 'for', 'and',
            'about', 'how', 'can', 'get', 'apply', 'tell', 'me', 'what', 'is', 'are', 'in', 'to', 'of',
            # Telugu
            'పీఎం', 'పథకం', 'పథకాలు', 'గురించి', 'చెప్పండి', 'ఏమిటి', 'ఎలా', 'వివరాలు', 'ప్రభుత్వ', 'యోజన',
            # Hindi
            'पीएम', 'योजना', 'योजनाएं', 'के', 'बारे', 'में', 'बताएं', 'क्या', 'है', 'कैसे', 'सरकारी'
        }

        score = 0.0
        scheme_id_clean = scheme.id.lower().translate(punct_map)
        scheme_name_clean = scheme.name.lower().translate(punct_map)
        scheme_hi_clean = (scheme.name_hindi or '').lower().translate(punct_map)
        scheme_te_clean = (scheme.name_telugu or '').lower().translate(punct_map)

        # 1. Exact match on scheme ID or clean query in scheme ID / acronym
        if clean_q == scheme_id_clean or clean_q in scheme_id_clean:
            score += 700.0
        if clean_q in scheme_name_clean:
            score += 500.0
        if scheme_hi_clean and clean_q in scheme_hi_clean:
            score += 500.0
        if scheme_te_clean and clean_q in scheme_te_clean:
            score += 500.0

        # 2. Token-level matching with high weight on domain-specific keywords
        matched_specific_words = 0
        for w in q_words:
            is_generic = w in generic_words
            weight = 5.0 if is_generic else 60.0

            if w in scheme_id_clean:
                score += weight * 6.0
                if not is_generic:
                    matched_specific_words += 1
            if w in scheme_name_clean:
                score += weight * 5.0
                if not is_generic:
                    matched_specific_words += 1

            if scheme_hi_clean and w in scheme_hi_clean:
                score += weight * 6.0
                if not is_generic:
                    matched_specific_words += 1
            if scheme_te_clean and w in scheme_te_clean:
                score += weight * 6.0
                if not is_generic:
                    matched_specific_words += 1

            desc_clean = scheme.description.lower().translate(punct_map)
            if w in desc_clean:
                score += weight * 1.5

            cat_clean = (scheme.category or '').lower().translate(punct_map)
            if w in cat_clean:
                score += weight * 3.0

            bens_clean = ' '.join(scheme.beneficiary_types).lower().translate(punct_map)
            if w in bens_clean:
                score += weight * 3.0

        # Strong bonus if ALL specific words in query matched this scheme
        specific_query_words = [w for w in q_words if w not in generic_words]
        combined_text = f"{scheme_id_clean} {scheme_name_clean} {scheme_hi_clean} {scheme_te_clean}"
        if specific_query_words and all(w in combined_text for w in specific_query_words):
            score += 500.0

        return score

    async def search_all(
        self,
        query: str = "",
        state: str = "",
        category: str = "",
        beneficiary_type: str = "",
    ) -> Dict[str, Any]:
        """Search all sources concurrently. Return combined results with source info."""
        sources_queried = ["myscheme", "india_gov", "data_gov", "curated_registry"]
        sources_failed = []
        combined_schemes: List[GovernmentScheme] = []

        # 1. First score curated schemes in-memory (guaranteed, fast, highly accurate)
        q_lower = query.lower().strip() if query else ""

        curated_scored = []
        for cs in self.curated_schemes:
            match_state = (not state or not cs.state or state.lower() in cs.state.lower())
            match_cat = (not category or (cs.category and category.lower() in cs.category.lower()))
            if match_state and match_cat:
                s_score = self.compute_scheme_relevance(query, cs)
                if not q_lower or s_score > 0:
                    curated_scored.append((cs, s_score))

        # Sort curated schemes by relevance score descending
        curated_scored.sort(key=lambda item: item[1], reverse=True)
        combined_schemes = [cs for cs, _ in curated_scored]

        # 2. Run remote queries concurrently
        async def fetch_myscheme():
            try:
                raw_schemes = await self.myscheme.search_schemes(
                    keyword=query, state=state, category=category, beneficiary=beneficiary_type
                )
                return [self.myscheme._parse_scheme(r) for r in raw_schemes]
            except Exception as e:
                sources_failed.append(f"myscheme: {str(e)}")
                return []

        async def fetch_india_gov():
            try:
                return await self.india_gov.fetch_spotlight_schemes()
            except Exception as e:
                sources_failed.append(f"india_gov: {str(e)}")
                return []

        # Execute live queries concurrently
        myscheme_results, _ = await asyncio.gather(
            fetch_myscheme(),
            fetch_india_gov(),
            return_exceptions=True
        )

        if isinstance(myscheme_results, list):
            # Deduplicate schemes by ID
            seen_ids = {s.id for s in combined_schemes}
            for scheme in myscheme_results:
                if scheme.id not in seen_ids:
                    s_score = self.compute_scheme_relevance(query, scheme)
                    if not q_lower or s_score > 0:
                        combined_schemes.append(scheme)
                        seen_ids.add(scheme.id)

        # Final sort by relevance score descending
        if q_lower:
            combined_schemes.sort(
                key=lambda s: self.compute_scheme_relevance(query, s),
                reverse=True
            )

        return {
            "schemes": combined_schemes,
            "total": len(combined_schemes),
            "sources_queried": sources_queried,
            "sources_failed": sources_failed,
            "retrieved_at": datetime.now(timezone.utc),
        }

    async def fetch_scheme_details(self, scheme_id: str, source: str = "myscheme") -> Optional[GovernmentScheme]:
        """Fetch detailed information for a specific scheme by ID."""
        # 1. Check curated registry
        for scheme in self.curated_schemes:
            if scheme.id == scheme_id:
                return scheme

        # 2. If not found in curated, query MyScheme API
        try:
            results = await self.myscheme.search_schemes(keyword=scheme_id, page_size=5)
            for raw in results:
                parsed = self.myscheme._parse_scheme(raw)
                if parsed.id == scheme_id or scheme_id in parsed.id:
                    return parsed
        except Exception as e:
            logger.warning("Failed to fetch remote scheme details for %s: %s", scheme_id, e)

        # 3. Fallback: match by partial ID across curated list
        for scheme in self.curated_schemes:
            if scheme_id.lower() in scheme.id.lower() or scheme_id.lower() in scheme.name.lower():
                return scheme

        return None
