# Project policy requires /help access to be limited to these exact Discord users.
HELP_ALLOWED_USER_IDS = {
    1493691258873319454,
    1299308718009356289,
}

APPROVED_SERVICES = (
    "Yoti",
    "OnlyFans",
    "LoyalFans",
    "FeetFinder",
    "FetishFinder",
    "YouPay",
)

APPROVED_DOMAINS = (
    "yoti.com",
    "onlyfans.com",
    "loyalfans.com",
    "feetfinder.com",
    "fetishfinder.com",
    "youpay.co",
    "youpay.com",
)

FORM_URL = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSd6x-wgZ1s-L4zlOdEV76cNcMNgF6JQ8KAV4F9c37uMBZ15mg/"
    "viewform?usp=header"
)

DUPLICATE_PENDING_RESPONSE = (
    "You already have a verification request waiting for staff review.\n\n"
    "Please wait for the moderation team to review your current submission."
)

DM_FAILURE_RESPONSE = (
    "I couldn't DM you. Please enable DMs from server members and try again."
)

ALREADY_VERIFIED_RESPONSE = "You are already verified and cannot re-verify."

UNAUTHORISED_STAFF_BUTTON_RESPONSE = (
    "You do not have permission to action verification requests."
)

UNAUTHORISED_HELP_RESPONSE = "You do not have permission to use this command."

WELCOME_TITLE = "Welcome to The Drain Server!"
WELCOME_DESCRIPTION = """Hello {user_mention} and welcome to The Drain Server!

you didn’t end up here by accident.
this is a space built on power, trust, and indulgence — where desire meets control and boundaries are respected above all else.

whether you’re here to serve, explore, or simply observe… take a moment to settle in.

🔒 read the rules
💬 choose your roles
💖 know your limits — and respect everyone else’s

this is a consensual, 18+ space. everything here runs on communication, respect, and mutual understanding.

now breathe, read the rules, verify… and enjoy your stay."""

VERIFICATION_PANEL_TITLE = "🔞🔒 Age Verification Required 🔒🔞"
VERIFICATION_PANEL_DESCRIPTION = """This server is strictly 18+ so in order to gain access, you must verify your age using one of the below approved methods:

- Yoti
- OnlyFans
- LoyalFans
- FeetFinder
- FetishFinder
- YouPay

FOR NOW THESE ARE THE ONLY ACCEPTED SERVICES

📩 How to verify:

Click the "Verify" button below and follow the steps sent to you via DM to submit your age verification to the staff.

Once staff have approved your age verification, I'll notify you via DM and give you more information around our server.

🚫 **NO VERIFICATION = NO ACCESS**

Please note verification is mandatory and will lead to your removal if not complete in 7 days.

Thank you
~ Princess Ren (sub)"""

INITIAL_VERIFICATION_DM_TITLE = "🔞🔒 Age Verification 🔒🔞"
INITIAL_VERIFICATION_DM_DESCRIPTION = """Hey there and welcome to The Drain Gang!

To submit your verification to the server staff, simply send a photo of your profile on one of our approved services or send a link to your page. To remind you of our approved services, here they are:

- Yoti
- OnlyFans
- LoyalFans
- FeetFinder
- FetishFinder
- YouPay

⚠️ This verification submission will expire in 5 minutes if nothing is received by the bot"""

ROLE_PROMPT_TITLE = "🔞🔒 Age Verification 🔒🔞"
ROLE_PROMPT_DESCRIPTION = """Thank you for submitting that!

To help us get you the right roles in the server, we just ask for the following:

- Are you a Domme or Submissive?

Please click the corresponding button below. This will automatically assign the right roles when your verification is approved."""

PENDING_REVIEW_TITLE = "🔞🔒 Age Verification 🔒🔞"
PENDING_REVIEW_DESCRIPTION = """Thank you!

You'll receive a DM from this bot shortly with the status of your verification.

While our staff review your verification, we ask that you please fill out the following form by clicking the link below. This form allows us to gain better ideas and suggestions to help improve this bot."""

APPROVED_DM_TITLE = "You've been verified!"
APPROVED_DM_DESCRIPTION = """Thank you for your patience! Our staff have approved your age verification!

Head over to {roles_channel} to grab yourself some roles and feel free to introduce yourself in {introductions_channel}!

While you're at it, feel free to say hello and join the conversation in {general_channel}

Again, welcome to The Drain Gang!"""

DENIED_UNDERAGE_DM_TITLE = "Verification Denied"
DENIED_UNDERAGE_DM_DESCRIPTION = """Your age verification has been denied as the submitted verification indicates you do not meet the 18+ requirement for this server.

This server is strictly 18+ and access cannot be granted."""

DENIED_INVALID_DM_TITLE = "Verification Denied"
DENIED_INVALID_DM_DESCRIPTION = """Your verification was denied because the submitted service is not currently accepted for this server.

At this time, we only accept:

- Yoti
- OnlyFans
- LoyalFans
- FeetFinder
- FetishFinder
- YouPay

Please return to the verification channel and submit your verification using one of the approved services."""

SESSION_EXPIRED_DM_TITLE = "Verification Expired"
SESSION_EXPIRED_DM_DESCRIPTION = """Your verification session has expired.

Please return to the verification channel and click the Verify button again when you're ready."""

INVALID_SUBMISSION_DM_TITLE = "Invalid Submission"
INVALID_SUBMISSION_DM_DESCRIPTION = """I couldn't detect a valid verification link or photo.

Please send either a link to one of the approved services or a photo/screenshot of your profile on one of the approved services."""

GENERAL_DOMME_MESSAGES = (
    "Make way, a new Domme has made their grand entrance. Welcome {user_mention}!",
    "Get ready subs, {user_mention} has entered the building and is chancing a new wallet",
    "{user_mention} just joined and already has people falling to their knees",
)

GENERAL_SUBMISSIVE_MESSAGES = (
    "Look who came crawling in 👀, it's a new sub! Welcome {user_mention}",
    "Attention all Dommes, {user_mention} is here and is ready to serve.",
    "{user_mention} just joined and is ready to serve.",
)

DOMME_SETUP_INTRO_TITLE = "Domme Profile Setup"
DOMME_SETUP_INTRO_DESCRIPTION = """This quick setup lets you create or update your Domme profile on The Drain Server.

Your profile can be shown with **/domme** (or **!domme**) and is used for things like:
• Payment links and tribute info
• Throne tracking so subs can see who's sending to you
• Introducing yourself to the server

**Everything is optional.** Skip anything you'd rather leave out and come back anytime.

Press **Continue** when you're ready, or **Later** if you'd like to come back another time."""

DOMME_SETUP_NAME_TITLE = "Step 1: Name & honorific"
DOMME_SETUP_NAME_DESCRIPTION = """How would you like subs to address you? Add your name and any honorifics here."""

DOMME_SETUP_DETAILS_TITLE = "Step 2: Details"
DOMME_SETUP_DETAILS_DESCRIPTION = """Add any details you'd like displayed on your profile."""

DOMME_SETUP_PAYMENTS_TITLE = "Step 3: Links"
DOMME_SETUP_PAYMENTS_DESCRIPTION = """Add your **Throne** link and up to 4 additional links (PayPal, CashApp, etc.)."""

DOMME_SETUP_THRONE_TITLE = "Step 4: Throne tracking"
DOMME_SETUP_THRONE_DESCRIPTION = """It looks like you added a Throne link.

Would you like to sign up for Throne tracking? When subs send to your Throne, their sends will be recorded in the server and shown on the leaderboard.

You can change this at any time."""

DOMME_SETUP_REVIEW_TITLE = "Final step: Review"
DOMME_SETUP_REVIEW_DESCRIPTION = """Take a look at your profile below.

Ready to save it?"""

DOMME_SETUP_COMPLETE_TITLE = "Domme profile saved!"
DOMME_SETUP_COMPLETE_DESCRIPTION = """Use **/domme** (or **!domme**) to show your profile in The Drain Server.

To delete it: use **/domme action:delete** or **!domme delete**."""

DOMME_SETUP_LATER_TITLE = "Domme Profile Setup"
DOMME_SETUP_LATER_DESCRIPTION = """No problem — you can continue anytime.

Run **/domme** (or **!domme**) in The Drain Server when you're ready."""

DOMME_SETUP_CANCELLED_TITLE = "Domme Profile Setup"
DOMME_SETUP_CANCELLED_DESCRIPTION = """Nothing was saved.

Run **/domme** (or **!domme**) anytime to start again."""

SUB_SETUP_INTRO_TITLE = "Sub Profile Setup"
SUB_SETUP_INTRO_DESCRIPTION = """This lets you link your Throne sending name to your Discord account.

When a Domme in the server receives a send on Throne, the bot will check if the sender's name matches yours and credit you on the server leaderboard.

Press **Continue** when you're ready, or **Later** to come back another time."""

SUB_SETUP_NAME_TITLE = "Throne Name"
SUB_SETUP_NAME_DESCRIPTION = """**What name do you use when sending on Throne?**

This will be linked to your Discord account and used to identify your sends on the server leaderboard."""

SUB_SETUP_REVIEW_TITLE = "Final step: Review"
SUB_SETUP_REVIEW_DESCRIPTION = """Take a look below and confirm your details."""

SUB_SETUP_COMPLETE_TITLE = "Sub profile saved!"
SUB_SETUP_COMPLETE_DESCRIPTION = """Your Throne name is now linked to your Discord account.

Any sends you've already made to Dommes in this server will be credited to you on the leaderboard.

Use **/sub action:delete** to remove your profile at any time."""

SUB_SETUP_LATER_TITLE = "Sub Profile Setup"
SUB_SETUP_LATER_DESCRIPTION = """No problem — you can continue anytime.

Run **/sub** when you're ready."""

SUB_SETUP_CANCELLED_TITLE = "Sub Profile Setup"
SUB_SETUP_CANCELLED_DESCRIPTION = """Nothing was saved.

Run **/sub** anytime to start again."""
