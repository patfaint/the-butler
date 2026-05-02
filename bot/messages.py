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
WELCOME_DESCRIPTION = """hey {user_mention}, glad you made it.

you didn't end up here by accident.
this is a space built on power, trust, and indulgence — where desire meets control and boundaries are respected above all else.

whether you're here to serve, explore, or just lurk a little… settle in.

read the rules, pick your roles, know your limits — and respect everyone else's.

18+ only. everything here runs on communication, respect, and mutual understanding.

now breathe, get verified, and enjoy your stay."""

VERIFICATION_PANEL_TITLE = "Age Verification"
VERIFICATION_PANEL_DESCRIPTION = """This server is strictly 18+. To get access you'll need to verify your age using one of these services:

- Yoti
- OnlyFans
- LoyalFans
- FeetFinder
- FetishFinder
- YouPay

**These are the only accepted services right now.**

Hit the Verify button below and follow the steps in your DMs. Once staff approve you, I'll let you know.

No verification = no access. You've got 7 days before the removal fairy pays a visit.

~ Princess Ren (sub)"""

INITIAL_VERIFICATION_DM_TITLE = "Age Verification"
INITIAL_VERIFICATION_DM_DESCRIPTION = """hey, welcome to The Drain Gang!

send me a link to your profile on one of our approved services, or drop a photo of your profile page. approved services:

- Yoti
- OnlyFans
- LoyalFans
- FeetFinder
- FetishFinder
- YouPay

heads up — this session expires in 5 minutes, so don't keep me waiting"""

ROLE_PROMPT_TITLE = "Age Verification"
ROLE_PROMPT_DESCRIPTION = """got it, thanks!

one last thing — are you a Domme or a Submissive?

tap the right button below and we'll get you set up with the correct roles once you're approved."""

PENDING_REVIEW_TITLE = "Verification Submitted"
PENDING_REVIEW_DESCRIPTION = """you're in the queue! staff will take a look shortly and I'll DM you once it's done.

while you wait, feel free to fill out the form below — it helps us make the bot better."""

APPROVED_DM_TITLE = "you're in!"
APPROVED_DM_DESCRIPTION = """welcome to the gang — staff have approved your verification!

head over to {roles_channel} to grab some roles, introduce yourself in {introductions_channel}, and say hi in {general_channel}.

enjoy the ride."""

DENIED_UNDERAGE_DM_TITLE = "Verification Denied"
DENIED_UNDERAGE_DM_DESCRIPTION = """sorry, but your verification was denied — it looks like you don't meet the 18+ requirement.

this is a strictly adults-only space and we can't make exceptions."""

DENIED_INVALID_DM_TITLE = "Verification Denied"
DENIED_INVALID_DM_DESCRIPTION = """your verification was denied because the service you submitted isn't accepted here.

we currently only accept: Yoti, OnlyFans, LoyalFans, FeetFinder, FetishFinder, or YouPay.

head back to the verification channel and give it another go with one of those."""

SESSION_EXPIRED_DM_TITLE = "Verification Expired"
SESSION_EXPIRED_DM_DESCRIPTION = """oops — your verification session timed out.

no worries, just head back to the verification channel and hit Verify again when you're ready."""

INVALID_SUBMISSION_DM_TITLE = "Hmm, that didn't work"
INVALID_SUBMISSION_DM_DESCRIPTION = """I couldn't make sense of that submission — I need either a link to your profile on an approved service, or a photo/screenshot of it.

give it another try!"""

GENERAL_DOMME_MESSAGES = (
    "make way — a new Domme just walked in. welcome {user_mention}!",
    "subs, take note: {user_mention} has entered the building and is already eyeing wallets",
    "{user_mention} just showed up and people are already on their knees",
)

GENERAL_SUBMISSIVE_MESSAGES = (
    "look who just crawled in — welcome {user_mention}!",
    "attention Dommes: {user_mention} is here and ready to serve",
    "{user_mention} just joined. don't keep them waiting.",
)

DOMME_SETUP_INTRO_TITLE = "Domme Profile Setup"
DOMME_SETUP_INTRO_DESCRIPTION = """let's get your profile sorted — payment links, Throne tracking, the works.

everything's optional, so skip whatever you don't want."""

DOMME_SETUP_NAME_TITLE = "Step 1 of 4 — Identity"
DOMME_SETUP_NAME_DESCRIPTION = """how do you want subs to address you?"""

DOMME_SETUP_DETAILS_TITLE = "Step 2 of 4 — Details"
DOMME_SETUP_DETAILS_DESCRIPTION = """anything else you want on your profile?"""

DOMME_SETUP_PAYMENTS_TITLE = "Step 3 of 4 — Links"
DOMME_SETUP_PAYMENTS_DESCRIPTION = """add your links using the buttons below, then hit **Continue** when you're done."""

DOMME_SETUP_THRONE_TITLE = "Throne Tracking"
DOMME_SETUP_THRONE_DESCRIPTION = """want to turn on Throne tracking? sends to your Throne will be logged and show up on the server leaderboard.

you can flip this on or off any time."""

DOMME_SETUP_COLOR_TITLE = "Step 4 of 4 — Profile Colour"
DOMME_SETUP_COLOR_DESCRIPTION = """pick a colour for your profile."""

DOMME_SETUP_REVIEW_TITLE = "Looking good — ready to save?"
DOMME_SETUP_REVIEW_DESCRIPTION = """here's what your profile looks like. happy with it?"""

DOMME_SETUP_COMPLETE_TITLE = "Profile saved!"
DOMME_SETUP_COMPLETE_DESCRIPTION = """use **/domme** to show it off. use **/domme action:delete** if you ever want to pull it down."""

DOMME_SETUP_LATER_TITLE = "No worries"
DOMME_SETUP_LATER_DESCRIPTION = """come back whenever — just run **/domme** when you're ready."""

DOMME_SETUP_CANCELLED_TITLE = "Cancelled"
DOMME_SETUP_CANCELLED_DESCRIPTION = """nothing was saved. run **/domme** anytime to start fresh."""

SUB_SETUP_INTRO_TITLE = "Sub Profile Setup"
SUB_SETUP_INTRO_DESCRIPTION = """let's get you set up — link your Throne name so your sends show up on the leaderboard."""

SUB_SETUP_PROFILE_TITLE = "Step 1 of 4 — Your Details"
SUB_SETUP_PROFILE_DESCRIPTION = """tell us a bit about yourself."""

SUB_SETUP_KINKS_LIMITS_TITLE = "Step 2 of 4 — Kinks & Limits"
SUB_SETUP_KINKS_LIMITS_DESCRIPTION = """totally optional — only share what you're comfortable with."""

SUB_SETUP_COLOR_TITLE = "Step 3 of 4 — Profile Colour"
SUB_SETUP_COLOR_DESCRIPTION = """pick a colour for your profile."""

SUB_SETUP_OWNER_TITLE = "Step 4 of 4 — Owned By"
SUB_SETUP_OWNER_DESCRIPTION = """owned by a Domme in this server? pick them. otherwise hit **None**."""

SUB_SETUP_REVIEW_TITLE = "Looking good — ready to save?"
SUB_SETUP_REVIEW_DESCRIPTION = """here's your profile. happy with it?"""

SUB_SETUP_COMPLETE_TITLE = "Profile saved!"
SUB_SETUP_COMPLETE_DESCRIPTION = """all set — your sends will be credited on the leaderboard from here on out.

use **/sub action:delete** to remove your profile any time."""

SUB_SETUP_LATER_TITLE = "No worries"
SUB_SETUP_LATER_DESCRIPTION = """come back whenever — just run **/sub** when you're ready."""

SUB_SETUP_CANCELLED_TITLE = "Cancelled"
SUB_SETUP_CANCELLED_DESCRIPTION = """nothing was saved. run **/sub** anytime to start fresh."""
