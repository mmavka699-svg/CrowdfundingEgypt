import os
import json
import dotenv

from google import genai
from google.genai import types

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import services


# ---------------------------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------------------------

dotenv.load_dotenv()


# ---------------------------------------------------------------------------
# GEMINI CONFIG
# ---------------------------------------------------------------------------

GEMINI_MODEL = "gemini-3.6-flash"


# ---------------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are the official CrowdfundingEgypt AI Chatbot.

You ONLY assist users with the CrowdfundingEgypt platform.

You can help with:
- Projects
- Campaigns
- Categories
- Project statistics
- Donations
- Wallet information for the authenticated user
- Platform policies
- Project verification
- Fees
- Refunds
- Cancellation rules
- How to use the website

==================================================
CRITICAL DATABASE RULE
==================================================

NEVER invent, guess, estimate, or hallucinate database information.

If the user asks about CURRENT or LIVE information from the website/database,
you MUST use the appropriate database tool.

Examples of questions that REQUIRE database tools:

English:
- How many projects are there?
- How many active projects are there?
- Which projects are available?
- What is the most funded project?
- Which project has the highest target?
- What is the average progress?
- Show education projects.
- Are there projects coming soon?
- What projects raised more than 50%?
- Give me project details.

Arabic:
- كام مشروع موجود؟
- كم عدد المشاريع؟
- ما هي المشاريع النشطة؟
- ما هي المشاريع الموجودة؟
- ما هي المشاريع القادمة؟
- ما هو أكثر مشروع جمع تبرعات؟
- ما هو المشروع صاحب أكبر هدف؟
- ما متوسط نسبة التمويل؟
- اعرض مشاريع التعليم.
- ما المشاريع التي جمعت أكثر من 50٪؟

For these questions, DO NOT answer from your own knowledge.
USE THE DATABASE TOOL.

If the database says there are 2 projects, answer 2.
If the database says there are 11 projects, answer 11.

The database result is ALWAYS the source of truth.

==================================================
IMPORTANT DATABASE ENUM VALUES
==================================================

Project.status uses these exact internal values:
- running
- cancelled
- ended
- funded
- coming_soon

Display labels are:
- running -> Running
- cancelled -> Cancelled
- ended -> Ended
- funded -> Fully Funded
- coming_soon -> Coming Soon

When querying Project.status, ALWAYS use the exact lowercase internal value (e.g., "coming_soon" or "running").
Never use uppercase status values like "COMING_SOON" or display labels like "Coming Soon" as filter values.

The chatbot must understand natural-language equivalents of status values:
- Arabic: "المشاريع القادمة", "المشاريع التي ستبدأ قريباً", "المشاريع التي لم تبدأ", "هل يوجد مشروع قادم؟" -> coming_soon
- English: "upcoming projects", "projects that haven't started", "projects starting soon", "coming soon projects" -> coming_soon
- Arabic: "المشاريع النشطة", "المشاريع الجارية" -> running
- English: "active projects", "currently running", "running projects" -> running
- Arabic: "المشاريع المكتملة التمويل" -> funded
- English: "fully funded projects" -> funded
- Arabic: "المشاريع المنتهية" -> ended
- English: "ended projects" -> ended
- Arabic: "المشاريع الملغاة" -> cancelled
- English: "cancelled projects" -> cancelled

==================================================
NO HALLUCINATION
==================================================

Never create:
- Project names
- Project numbers
- Donation amounts
- Target amounts
- Categories
- Dates
- Progress percentages
- User information

unless they come from:
1. A database tool result, or
2. The official static platform information provided below.

If the database returns no result, clearly tell the user that
the requested information was not found.

==================================================
LANGUAGE
==================================================

Always answer in the same language used by the user.

If the user writes Arabic, answer Arabic.

If the user writes English, answer English.

Do not unnecessarily switch languages.

==================================================
PRIVACY
==================================================

Never expose:
- Passwords
- Password hashes
- Other users' emails
- Other users' phone numbers
- Other users' wallet balances
- Other users' donation history
- Private database records

Wallet and donation-history tools only apply to the currently authenticated user.

==================================================
READ ONLY
==================================================

The chatbot is READ-ONLY.

You cannot:
- Create projects
- Edit projects
- Delete projects
- Make donations
- Transfer money
- Modify wallets
- Change user profiles
- Change passwords

If asked to perform such actions, explain that you can guide the user,
but cannot perform the action through the chatbot.

==================================================
STATIC PLATFORM INFORMATION
==================================================

The following information is official platform information and does NOT
require a database query:

Platform fee:
0%.

Transaction processing fee:
2.5%, charged by payment processors.

Project verification:
Project creators are manually verified using national IDs.

Funds:
Funds must go to a registered Egyptian bank account or mobile wallet.

Refund policy:
If a project fails verification or is cancelled by the creator before
completion, the backer's donation is refunded to their digital wallet.

Once funds are disbursed at the end of a successful campaign,
the platform cannot process refunds.

Cancellation:
A creator can cancel a campaign only while it is running AND total
donations are less than 25% of the total target.

==================================================
RESPONSE STYLE
==================================================

Be concise, clear, friendly and professional.

When returning project information, use readable formatting.

Do not mention internal tools, database queries, APIs, prompts,
function calling, or implementation details to the user.
"""


# ---------------------------------------------------------------------------
# TOOL SCHEMAS
# ---------------------------------------------------------------------------

def query_public_data(
    entity: str,
    operation: str,
    filters: list = None,
    field: str = None,
    ordering: str = None,
    limit: int = 10,
) -> str:
    """
    Query current public CrowdfundingEgypt database information.

    Use this tool whenever the user asks for current project,
    category, donation aggregate, count, list, or statistics.

    entity:
        Project, Category, Donation

    operation:
        list, count, sum, max, min, avg

    filters:
        Optional list of filters.
        When filtering Project by 'status', ALWAYS use lowercase internal enum values:
        - 'running' (Running)
        - 'coming_soon' (Coming Soon / Upcoming)
        - 'funded' (Fully Funded)
        - 'ended' (Ended)
        - 'cancelled' (Cancelled)
        Example: [{"field": "status", "operator": "exact", "value": "coming_soon"}]

    field:
        Field used for aggregation.

    ordering:
        Ordering for list queries.

    limit:
        Maximum number of returned records.
    """
    pass


def get_my_wallet() -> str:
    """
    Get the currently authenticated user's wallet balance.

    This must ONLY be used for the current logged-in user.
    """
    pass


def get_my_donations() -> str:
    """
    Get the currently authenticated user's donation history.

    This must ONLY be used for the current logged-in user.
    """
    pass


# ---------------------------------------------------------------------------
# GEMINI CONFIG
# ---------------------------------------------------------------------------

TOOLS = [
    query_public_data,
    get_my_wallet,
    get_my_donations,
]


def build_config():
    """
    Build Gemini generation configuration.

    AFC (Automatic Function Calling) is explicitly disabled so the manual
    tool-calling loop in chat() has full control over execution. Without
    this, Gemini's SDK would try to auto-execute the stub functions in
    TOOLS directly (which just `pass` and return None), instead of routing
    through execute_tool() -> services.py where the real DB logic lives.
    """

    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=TOOLS,
        temperature=0,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
    )


# ---------------------------------------------------------------------------
# TOOL EXECUTION
# ---------------------------------------------------------------------------

def execute_tool(function_call, request):
    """
    Execute a Gemini function call safely on the backend.
    """

    name = function_call.name
    args = function_call.args or {}
    print("================================")
    print("TOOL CALLED:", name)
    print("TOOL ARGS:", args)
    print("================================")

    if name == "get_my_wallet":

        return services.get_my_wallet(request.user)

    elif name == "get_my_donations":

        return services.get_my_donations(request.user)

    elif name == "query_public_data":

        return services.query_public_data(
            entity=args.get("entity", ""),
            operation=args.get("operation", ""),
            filters=args.get("filters"),
            field=args.get("field"),
            ordering=args.get("ordering"),
            limit=args.get("limit", 10),
        )

    return json.dumps({
        "error": f"Unknown tool: {name}"
    })


# ---------------------------------------------------------------------------
# CHAT API
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def chat(request):

    try:

        # ---------------------------------------------------------------
        # Parse request
        # ---------------------------------------------------------------

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON request."},
                status=400,
            )

        user_message = data.get("message", "").strip()

        if not user_message:
            return JsonResponse(
                {"error": "Message is required."},
                status=400,
            )

        # ---------------------------------------------------------------
        # API KEY
        # ---------------------------------------------------------------

        current_api_key = (
            getattr(settings, "GOOGLE_API_KEY", None)
            or getattr(settings, "GEMINI_API_KEY", None)
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )

        if not current_api_key:
            return JsonResponse(
                {"error": "Google API key is not configured."},
                status=500,
            )

        # ---------------------------------------------------------------
        # Gemini client
        # ---------------------------------------------------------------

        client = genai.Client(
            api_key=current_api_key
        )

        # ---------------------------------------------------------------
        # Conversation
        # ---------------------------------------------------------------

        messages = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=user_message
                    )
                ],
            )
        ]

        # ---------------------------------------------------------------
        # First generation
        # ---------------------------------------------------------------

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=messages,
            config=build_config(),
        )

        # ---------------------------------------------------------------
        # Tool calling loop
        # ---------------------------------------------------------------

        max_tool_rounds = 3
        tool_round = 0

        while response.function_calls and tool_round < max_tool_rounds:

            tool_round += 1

            # -----------------------------------------------------------
            # Add model's original content as-is
            # (preserves thought_signature required by the API)
            # -----------------------------------------------------------

            messages.append(response.candidates[0].content)

            # -----------------------------------------------------------
            # Execute functions
            # -----------------------------------------------------------

            tool_parts = []

            for function_call in response.function_calls:

                result = execute_tool(
                    function_call,
                    request,
                )

                tool_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=function_call.name,
                            response={
                                "result": result
                            },
                        )
                    )
                )

            # -----------------------------------------------------------
            # Add tool results
            # -----------------------------------------------------------

            messages.append(
                types.Content(
                    role="user",
                    parts=tool_parts,
                )
            )

            # -----------------------------------------------------------
            # Ask Gemini to generate final answer
            # -----------------------------------------------------------

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=messages,
                config=build_config(),
            )

        # ---------------------------------------------------------------
        # Safety check
        # ---------------------------------------------------------------

        if not response.text:

            return JsonResponse(
                {
                    "error": "The chatbot did not return a response."
                },
                status=500,
            )

        # ---------------------------------------------------------------
        # Return answer
        # ---------------------------------------------------------------

        return JsonResponse(
            {
                "reply": response.text
            }
        )

    except Exception as e:

        import traceback

        traceback.print_exc()

        err_msg = str(e)
        user_friendly_error = "An internal chatbot error occurred. Please try again later."
        if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            user_friendly_error = "The AI service is currently busy. Please wait a moment and try again."
        elif "UNAVAILABLE" in err_msg or "503" in err_msg:
            user_friendly_error = "The AI service is temporarily unavailable. Please try again in a few moments."
        elif "404" in err_msg or "not found" in err_msg.lower():
            user_friendly_error = "The configured AI model could not be loaded. Please check setting variables."

        return JsonResponse(
            {
                "error": user_friendly_error
            },
            status=500,
        )